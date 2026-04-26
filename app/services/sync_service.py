import json
from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.providers.base import ProviderMemberSnapshot
from app.providers.uma_moe import UmaMoeProvider
from app.repositories.members import MemberRepository
from app.repositories.snapshots import SnapshotRepository
from app.repositories.sync_runs import SyncRunRepository


class SyncService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.members = MemberRepository(db)
        self.snapshots = SnapshotRepository(db)
        self.sync_runs = SyncRunRepository(db)
        self.provider = UmaMoeProvider(settings)

    async def run_sync(
        self,
        *,
        requested_by: str,
        trigger_type: str = "manual_command",
        source_type: str = "uma_moe",
        member_id: int | None = None,
        auto_create_missing_members: bool = True,
    ) -> dict:
        sync_run = self.sync_runs.create_run(
            trigger_type=trigger_type,
            source_type=source_type,
            requested_by=requested_by,
            total_members=0,
            raw_payload=json.dumps(
                {
                    "club_id": self.settings.club_id,
                    "member_id": member_id,
                    "auto_create_missing_members": auto_create_missing_members,
                }
            ),
        )

        success_count = 0
        fail_count = 0

        try:
            provider_items = self._active_provider_items(
                await self.provider.fetch_club_members(self.settings.club_id)
            )
            provider_map = {self._normalize_name(item.member_name): item for item in provider_items}

            if auto_create_missing_members:
                self._upsert_members_from_provider(provider_items)

            target_members = self._resolve_target_members(member_id)
            sync_run.total_members = len(target_members)
            snapshots_new_payload = []

            for member in target_members:
                provider_item = self._resolve_provider_member(member.club_member_name, member.external_name, provider_map)
                if provider_item is None:
                    fail_count += 1
                    self.sync_runs.log_member(
                        sync_run_id=sync_run.sync_run_id,
                        member_id=member.member_id,
                        status_name="failed",
                        fan_count=None,
                        message="Member not found in provider response.",
                    )
                    continue

                snapshots_new_payload.append(
                    {
                        "member_id": member.member_id,
                        "fan_count": provider_item.fan_count,
                        "monthly_gain": provider_item.monthly_gain,
                        "daily_gain": provider_item.daily_gain,
                        "seven_day_avg": provider_item.seven_day_avg,
                        "captured_at": provider_item.captured_at,
                        "source_type": "uma_moe",
                        "source_ref": provider_item.source_ref,
                        "note": "Latest imported snapshot",
                    }
                )
                success_count += 1
                self.sync_runs.log_member(
                    sync_run_id=sync_run.sync_run_id,
                    member_id=member.member_id,
                    status_name="success",
                    fan_count=provider_item.fan_count,
                    message="Synced successfully from uma.moe.",
                )

            self.snapshots.replace_latest_snapshots_new(
                sync_run_id=sync_run.sync_run_id,
                snapshots=snapshots_new_payload,
            )

            status_name = "success" if fail_count == 0 else "partial_success"
            self.sync_runs.complete_run(
                sync_run,
                status_name=status_name,
                success_count=success_count,
                fail_count=fail_count,
            )
            self.db.commit()
        except Exception as exc:
            self.sync_runs.complete_run(
                sync_run,
                status_name="failed",
                success_count=success_count,
                fail_count=max(fail_count, 1),
                error_message=str(exc),
            )
            self.db.commit()
            raise

        return {
            "sync_run_id": sync_run.sync_run_id,
            "status_name": sync_run.status_name,
            "success_count": success_count,
            "fail_count": fail_count,
        }

    async def import_members_from_web(self, requested_by: str) -> dict:
        provider_items = self._active_provider_items(
            await self.provider.fetch_club_members(self.settings.club_id)
        )
        created_count, updated_count = self._upsert_members_from_provider(provider_items)
        self.db.commit()
        return {
            "requested_by": requested_by,
            "club_id": self.settings.club_id,
            "total_provider_members": len(provider_items),
            "created_count": created_count,
            "updated_count": updated_count,
        }

    async def import_old_date_from_web(
        self,
        *,
        requested_by: str,
        snapshot_date: date,
        source_type: str = "uma_moe",
        auto_create_missing_members: bool = True,
    ) -> dict:
        sync_run = self.sync_runs.create_run(
            trigger_type="manual_command",
            source_type=source_type,
            requested_by=requested_by,
            total_members=0,
            raw_payload=json.dumps(
                {
                    "club_id": self.settings.club_id,
                    "snapshot_date": snapshot_date.isoformat(),
                    "auto_create_missing_members": auto_create_missing_members,
                }
            ),
        )

        success_count = 0
        fail_count = 0

        try:
            provider_items = self._active_provider_items(
                await self.provider.fetch_club_members_by_date(self.settings.club_id, snapshot_date)
            )
            provider_map = {self._normalize_name(item.member_name): item for item in provider_items}

            if auto_create_missing_members:
                self._upsert_members_from_provider(provider_items)

            target_members = self.members.list_members()
            sync_run.total_members = len(target_members)
            old_snapshots_payload = []

            for member in target_members:
                provider_item = self._resolve_provider_member(member.club_member_name, member.external_name, provider_map)
                if provider_item is None:
                    fail_count += 1
                    self.sync_runs.log_member(
                        sync_run_id=sync_run.sync_run_id,
                        member_id=member.member_id,
                        status_name="failed",
                        fan_count=None,
                        message=f"No historical data found for {snapshot_date.isoformat()}.",
                    )
                    continue

                old_snapshots_payload.append(
                    {
                        "member_id": member.member_id,
                        "fan_count": provider_item.fan_count,
                        "monthly_gain": provider_item.monthly_gain,
                        "daily_gain": provider_item.daily_gain,
                        "seven_day_avg": provider_item.seven_day_avg,
                        "captured_at": provider_item.captured_at,
                        "source_type": "uma_moe",
                        "source_ref": provider_item.source_ref,
                        "note": f"Historical imported snapshot for {snapshot_date.isoformat()}",
                    }
                )
                success_count += 1
                self.sync_runs.log_member(
                    sync_run_id=sync_run.sync_run_id,
                    member_id=member.member_id,
                    status_name="success",
                    fan_count=provider_item.fan_count,
                    message=f"Imported historical snapshot for {snapshot_date.isoformat()}.",
                )

            self.snapshots.replace_old_snapshots_for_date(
                sync_run_id=sync_run.sync_run_id,
                snapshots=old_snapshots_payload,
            )

            status_name = "success" if fail_count == 0 else "partial_success"
            self.sync_runs.complete_run(
                sync_run,
                status_name=status_name,
                success_count=success_count,
                fail_count=fail_count,
            )
            self.db.commit()
        except Exception as exc:
            self.sync_runs.complete_run(
                sync_run,
                status_name="failed",
                success_count=success_count,
                fail_count=max(fail_count, 1),
                error_message=str(exc),
            )
            self.db.commit()
            raise

        return {
            "sync_run_id": sync_run.sync_run_id,
            "status_name": sync_run.status_name,
            "snapshot_date": snapshot_date.isoformat(),
            "success_count": success_count,
            "fail_count": fail_count,
        }

    def _resolve_provider_member(
        self,
        club_member_name: str,
        external_name: str | None,
        provider_map: dict[str, ProviderMemberSnapshot],
    ) -> ProviderMemberSnapshot | None:
        for candidate in (club_member_name, external_name):
            if not candidate:
                continue
            item = provider_map.get(self._normalize_name(candidate))
            if item is not None:
                return item
        return None

    @staticmethod
    def _normalize_name(value: str) -> str:
        return " ".join(value.strip().lower().split())

    @staticmethod
    def _active_provider_items(provider_items: list[ProviderMemberSnapshot]) -> list[ProviderMemberSnapshot]:
        return [item for item in provider_items if item.status_name == "active"]

    def _resolve_target_members(self, member_id: int | None):
        if member_id is not None:
            member = self.members.get_by_id(member_id)
            return [member] if member is not None else []
        return self.members.list_members()

    def _upsert_members_from_provider(
        self,
        provider_items: list[ProviderMemberSnapshot],
    ) -> tuple[int, int]:
        created_count = 0
        updated_count = 0

        for item in provider_items:
            existing = self.members.get_by_name(item.member_name)
            payload = {
                "external_name": item.member_name,
                "role_name": item.role_name,
                "status_name": item.status_name,
                "is_active": item.status_name == "active",
                "notes": f"Imported from uma.moe ({item.source_ref})",
            }

            if existing is None:
                self.members.create_member(
                    {
                        "club_member_name": item.member_name,
                        **payload,
                    }
                )
                created_count += 1
                continue

            changed = False
            for key, value in payload.items():
                if getattr(existing, key) != value:
                    changed = True
                    break

            if changed:
                self.members.update_member(existing, payload)
                updated_count += 1

        return created_count, updated_count
