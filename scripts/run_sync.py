import argparse
import asyncio

from app.config import get_settings
from app.db import SessionLocal
from app.services.sync_service import SyncService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run club fan sync.")
    parser.add_argument("--member-id", type=int, default=None, help="Optional member_id to sync.")
    parser.add_argument("--requested-by", default="cli", help="Actor name.")
    args = parser.parse_args()

    settings = get_settings()
    db = SessionLocal()
    try:
        service = SyncService(db, settings)
        result = await service.run_sync(
            requested_by=args.requested_by,
            trigger_type="manual_command",
            source_type="uma_moe",
            member_id=args.member_id,
        )
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
