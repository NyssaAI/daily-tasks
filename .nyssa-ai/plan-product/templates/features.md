# Product Feature Progress

| Feature Group | Complete / Total | % Complete |
| --- | --- | --- |
| Group 00: Foundation | 0 / 0 | 0% |
| **Overall** | **0 / 0** | **0%** |

---

## How to Use This Feature Inventory

This document catalogs product capabilities in non-technical, user-focused language, organized by functional capability groups.

| Numbering Pattern | Canonical Name | Segment Definitions | Path / Location |
| :--- | :--- | :--- | :--- |
| **`F-gg.nn`**<br>*(e.g. `F-01.02`)* | **Feature ID** | • **`gg` = Feature Group** (`00`–`99`): Cohesive functional area clustering related features (`00` = Foundation).<br>• **`nn` = Feature Number** (`01`–`99`): Sequential feature within that Feature Group. | `docs/features/f-gg.nn/feature.md` |
| **`UC-gg.nn.uu`**<br>*(e.g. `UC-01.02.01`)* | **Use Case ID** | • **`gg` = Feature Group** (`00`–`99`): Inherited from parent Feature.<br>• **`nn` = Feature Number** (`01`–`99`): Inherited from parent Feature.<br>• **`uu` = Use Case Number** (`01`–`99`): Sequential actor workflow within `F-gg.nn`. | `docs/features/f-gg.nn/uc-gg.nn.uu-short-slug.md` |
| **`R-pp.ss`**<br>*(e.g. `R-01.03`)* | **Roadmap Step ID** | • **`pp` = Phase** (`00`–`99` or `01`–`99`): Technical delivery stage in build order.<br>• **`ss` = Step** (`01`–`99`): Ordered unit of delivery work within Phase `pp` that completes/verifies target `UC-gg.nn.uu`s (or `F-gg.nn` fallback). | `docs/roadmap.md` |

* **User-Focused Language:** Describe features in plain, use-case language explaining what users can accomplish—not internal file paths or implementation details.
* **Checklist Summary:** Keep `## Feature Checklist Summary` scannable with `- [ ] F-gg.nn: Feature Title` only (no links needed, as `F-gg.nn` maps directly to `features/f-gg.nn/feature.md`).
* **Status:** Mark an item complete (`[x]`) only when the capability is implemented, documented, and verified.

---

## Feature Checklist Summary

### Group 00: Foundation

- [ ] F-00.01: Example foundation feature

---

## Feature Inventory

### Group 00: Foundation

**F-00.01: Example foundation feature**  
Brief non-technical description of what this capability enables for the user.  
[Feature Guide: Example Foundation Feature](features/f-00.01/feature.md)
