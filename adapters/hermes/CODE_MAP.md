# Code Map: `hermes`
## 1. Upward Ingress
None (Top-level entry point or independent root package).

---

## 2. Local Interface & Public Surface
* **Responsibility**: Register bundled Daily Tasks skills with the Hermes Agent plugin runtime.

```text
__init__.py
`-- def register(ctx: _HermesPluginContext) -> None
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
