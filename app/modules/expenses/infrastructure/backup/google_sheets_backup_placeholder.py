from typing import Protocol


class GoogleSheetsBackupService(Protocol):
    """Future hook: export snapshots to Sheets without touching domain/application."""

    async def push_backup(self, payload: object) -> None:
        """Serialize domain DTOs or reports and upload to Sheets."""
        ...


class NoopGoogleSheetsBackupService:
    """Placeholder until credentials and spreadsheet IDs are configured."""

    async def push_backup(self, payload: object) -> None:
        _ = payload
        return None
