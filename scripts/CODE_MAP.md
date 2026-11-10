# Code Map: `scripts`
## 1. Upward Ingress
None (Top-level entry point or independent root package).

---

## 2. Local Interface & Public Surface
* **Responsibility**: Assemble host plugin manifests and distribution bundles from canonical skills and Python sources.

```text
assemble.py
|-- ROOT = ...
|-- def assemble(argv: list[str] | None = None) -> int
|-- def build_packages() -> tuple[dict[str, str], dict[str, dict[str, str]]]
|-- def digest(files: dict[str, str]) -> str
`-- def tree(directory: Path, prefix: str = "", exclude_private: bool = False) -> dict[str, str]

validate.py
|-- def validate() -> int
`-- def validate_repository(root: Path = ROOT) -> list[str]
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
