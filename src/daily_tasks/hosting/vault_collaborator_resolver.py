"""Responsibility: Resolve per-vault SessionCollaborators across records, communications, and planning slices.
Public interface:
`-- VaultCollaboratorResolver
    +-- new(overrides, clock, communication, environ, cwd)
    `-- resolve(vault_root)
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import final

from nyssa_ai_result import ErrorCategory, Result, fail, ok

from daily_tasks.communications.cursor_store_json import CursorStoreJson
from daily_tasks.communications.suggestions_repository_json import SuggestionsRepositoryJson
from daily_tasks.core.communications.communication_client import CommunicationClient
from daily_tasks.core.planning.session_collaborators import SessionCollaborators
from daily_tasks.core.planning.types import PlanningContext
from daily_tasks.hosting.resolve_server_settings import resolve_default_vault_root, resolve_server_settings
from daily_tasks.hosting.types import ServerOverrides
from daily_tasks.hosting.vault_reader_markdown import VaultReaderMarkdown
from daily_tasks.planning.decision_log_store_json import DecisionLogStoreJson
from daily_tasks.planning.session_committer_local import SessionCommitterLocal
from daily_tasks.planning.session_store_json import SessionStoreJson
from daily_tasks.records.file_store_local import FileStoreLocal


def _projects_prefix(vault_root: Path, projects_root: Path) -> str:
    return (
        projects_root.relative_to(vault_root).as_posix()
        if projects_root.is_relative_to(vault_root)
        else projects_root.name
    )


@final
class VaultCollaboratorResolver:
    """Entity-first `CollaboratorResolver` building vault and runtime collaborators on demand."""

    def __init__(
        self,
        overrides: ServerOverrides,
        clock: Callable[[], datetime],
        communication: CommunicationClient | None = None,
        environ: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        """Keep CLI/env overrides, UTC clock, and optional standalone communication client."""
        self._overrides = overrides
        self._clock = clock
        self._communication = communication
        self._environ = environ
        self._cwd = cwd
        self._by_vault: dict[str, SessionCollaborators] = {}

    def resolve(self, vault_root: str | None) -> Result[SessionCollaborators]:
        """Resolve `ServerSettings` for `vault_root` and return cached `SessionCollaborators`."""
        explicit_path: Path | None = None
        if vault_root is not None:
            trimmed = vault_root.strip()
            if not trimmed:
                return fail("vault_root must be a non-empty absolute path.", ErrorCategory.VALIDATION)
            explicit_path = Path(trimmed).expanduser()
            if not explicit_path.is_absolute():
                return fail("vault_root must be an absolute path.", ErrorCategory.VALIDATION)
        elif self._overrides.vault_root is not None:
            explicit_path = self._overrides.vault_root
        else:
            default_res = resolve_default_vault_root(
                config_dir=self._overrides.config_dir,
                repo_root=self._overrides.repo_root,
            )
            if not default_res.ok:
                return fail(default_res.message, default_res.category)
            explicit_path = default_res.value
            if explicit_path is None:
                return fail(
                    "No vault_root was supplied and no defaultVaultRoot is configured in "
                    "~/.nyssa-ai/daily-tasks/config.json. Run the Daily Tasks Setup workflow or pass vault_root.",
                    ErrorCategory.VALIDATION,
                )

        settings_res = resolve_server_settings(
            explicit_path,
            self._overrides,
            environ=self._environ,
            cwd=self._cwd,
        )
        if not settings_res.ok:
            return fail(settings_res.message, settings_res.category)
        settings = settings_res.value
        vault_key = settings.vault_root.as_posix()

        cached = self._by_vault.get(vault_key)
        if cached is not None:
            return ok(cached)

        cursor_store = CursorStoreJson(settings.runtime_root, vault_key)
        suggestions_repo = SuggestionsRepositoryJson(settings.runtime_root, vault_key, self._clock)
        decision_log_store = DecisionLogStoreJson(settings.runtime_root, vault_key)
        session_store = SessionStoreJson(settings.runtime_root)
        file_store = FileStoreLocal(
            settings.vault_root,
            self._clock,
            records_root=settings.projects_root,
            daily_plans_root=settings.daily_plans_root,
        )
        committer = SessionCommitterLocal(
            file_store=file_store,
            decision_log_store=decision_log_store,
            session_store=session_store,
            suggestions_repository=suggestions_repo,
            cursor_store=cursor_store,
        )
        reader = VaultReaderMarkdown(
            settings=settings,
            communication=self._communication,
            cursor_store=cursor_store,
        )
        context = PlanningContext(
            vault_root=vault_key,
            projects_prefix=_projects_prefix(settings.vault_root, settings.projects_root),
            user_email=settings.user.email,
            initial_lookback_days=settings.initial_lookback_days,
        )
        collaborators = SessionCollaborators(
            context=context,
            reader=reader,
            committer=committer,
            cursor_store=cursor_store,
        )
        self._by_vault[vault_key] = collaborators
        return ok(collaborators)
