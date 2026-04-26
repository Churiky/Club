from datetime import datetime

from sqlalchemy import Select, desc, select, text
from sqlalchemy.orm import Session

from app.models import Member


class MemberRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_members(self) -> list[Member]:
        stmt: Select[tuple[Member]] = select(Member).order_by(Member.club_member_name.asc())
        return list(self.db.scalars(stmt))

    def list_active_members(self) -> list[Member]:
        stmt = (
            select(Member)
            .where(Member.is_active.is_(True), Member.status_name == "active")
            .order_by(Member.club_member_name.asc())
        )
        return list(self.db.scalars(stmt))

    def get_by_id(self, member_id: int) -> Member | None:
        return self.db.get(Member, member_id)

    def get_by_name(self, club_member_name: str) -> Member | None:
        stmt = select(Member).where(Member.club_member_name == club_member_name)
        return self.db.scalar(stmt)

    def create_member(self, payload: dict) -> Member:
        created_at = datetime.utcnow().replace(microsecond=0)
        updated_at = created_at
        self.db.execute(
            text(
                """
                INSERT INTO app.members (
                    club_member_name,
                    external_name,
                    role_name,
                    status_name,
                    notes,
                    is_active,
                    created_at,
                    updated_at
                )
                VALUES (
                    :club_member_name,
                    :external_name,
                    :role_name,
                    :status_name,
                    :notes,
                    :is_active,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "club_member_name": payload["club_member_name"],
                "external_name": payload.get("external_name"),
                "role_name": payload["role_name"],
                "status_name": payload["status_name"],
                "notes": payload.get("notes"),
                "is_active": payload.get("is_active", True),
                "created_at": created_at,
                "updated_at": updated_at,
            },
        )
        stmt = (
            select(Member)
            .where(Member.club_member_name == payload["club_member_name"])
            .order_by(desc(Member.member_id))
        )
        member = self.db.scalars(stmt).first()
        if member is None:
            raise RuntimeError("Failed to load member after insert.")
        return member

    def update_member(self, member: Member, values: dict) -> Member:
        for key, value in values.items():
            setattr(member, key, value)
        member.updated_at = datetime.utcnow().replace(microsecond=0)
        self.db.flush()
        self.db.refresh(member)
        return member
