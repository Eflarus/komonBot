import json

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        changes: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=json.dumps(changes, default=str) if changes else None,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    @staticmethod
    def compute_diff(old_values: dict, new_values: dict) -> dict:
        """Compute diff between old and new values: {field: [old, new]}."""
        diff = {}
        for key, new_val in new_values.items():
            old_val = old_values.get(key)
            if old_val != new_val:
                diff[key] = [old_val, new_val]
        return diff
