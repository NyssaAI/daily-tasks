"""Responsibility: Hold a secret value in memory so it never leaks through string, log or JSON output.
Public interface:
`-- SecretString
    +-- REDACTED
    +-- new(value)
    `-- reveal()

Masked secret container: `str`, `repr`, formatting and Pydantic dumps all show `[REDACTED]`.
"""

from typing import ClassVar, Final, final

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

_REDACTED: Final = "[REDACTED]"


@final
class SecretString:
    """Immutable in-memory secret; only `reveal()` returns the value.

    Not a dataclass on purpose: `dataclasses.asdict` would copy the value out of a dataclass wrapper.
    """

    __slots__ = ("_value",)
    REDACTED: ClassVar[str] = _REDACTED
    _value: str

    def __init__(self, value: str) -> None:
        """Wrap `value`; an empty secret is a caller error and raises `ValueError`."""
        if not value:
            raise ValueError("secret value must not be empty")
        object.__setattr__(self, "_value", value)

    def reveal(self) -> str:
        """Return the plaintext secret; call it only where the value is handed to its consumer."""
        return self._value

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("SecretString is immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("SecretString is immutable")

    def __str__(self) -> str:
        return _REDACTED

    def __repr__(self) -> str:
        return f"SecretString('{_REDACTED}')"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SecretString) and other._value == self._value

    def __hash__(self) -> int:
        return hash((SecretString, self._value))

    def __copy__(self) -> "SecretString":
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "SecretString":
        return self

    def __reduce__(self) -> str:
        raise TypeError("SecretString cannot be pickled")

    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[object], handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validate from a string or a `SecretString`; always serialize as `[REDACTED]`."""
        from_str = core_schema.no_info_after_validator_function(cls, core_schema.str_schema(min_length=1))
        return core_schema.union_schema(
            [core_schema.is_instance_schema(cls), from_str],
            serialization=core_schema.plain_serializer_function_ser_schema(lambda _: _REDACTED),
        )
