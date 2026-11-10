"""Responsibility: Hold the explicitly registered cloud key vault factories secret storage may use.
Public interface:
`-- VaultRegistry
    +-- default()
    +-- factories()
    +-- find(kind)
    +-- kinds()
    +-- new(factories)
    `-- register(factory)

Pluggable `CloudKeyVaultFactory` registry; factories are registered explicitly, never discovered by scanning.
"""

from collections.abc import Iterable
from typing import final

from nyssa_ai_configuration import CloudKeyVaultFactory, CloudKeyVaultFactoryBitwarden
from nyssa_ai_result import Result, fail, ok


@final
class VaultRegistry:
    """Immutable set of vault factories keyed by `kind`; a later registration of a kind replaces the earlier one."""

    def __init__(self, factories: Iterable[CloudKeyVaultFactory] = ()) -> None:
        """Keep `factories` in registration order."""
        by_kind: dict[str, CloudKeyVaultFactory] = {}
        for factory in factories:
            by_kind[factory.kind] = factory
        self._by_kind = by_kind

    @classmethod
    def default(cls) -> "VaultRegistry":
        """Return the registry of the factories `nyssa-ai-configuration` ships: Bitwarden Secrets Manager (`bws`)."""
        kinds = (
            CloudKeyVaultFactoryBitwarden.DEFAULT_KIND,
            CloudKeyVaultFactoryBitwarden.SHORT_KIND,
            CloudKeyVaultFactoryBitwarden.LEGACY_KIND,
        )
        return cls(CloudKeyVaultFactoryBitwarden(kind) for kind in kinds)

    def register(self, factory: CloudKeyVaultFactory) -> "VaultRegistry":
        """Return a new registry that also holds `factory`."""
        return VaultRegistry((*self._by_kind.values(), factory))

    def factories(self) -> tuple[CloudKeyVaultFactory, ...]:
        """Return every registered factory, for `ConfigurationClient.create(vault_factories=...)`."""
        return tuple(self._by_kind.values())

    def kinds(self) -> tuple[str, ...]:
        """Return the registered vault kinds in registration order."""
        return tuple(self._by_kind)

    def find(self, kind: str) -> Result[CloudKeyVaultFactory]:
        """Return the factory for `kind`; fails with `Validation` naming the registered kinds."""
        factory = self._by_kind.get(kind)
        if factory is None:
            return fail(f"No vault factory is registered for kind '{kind}' ({', '.join(self.kinds())}).", "Validation")
        return ok(factory)
