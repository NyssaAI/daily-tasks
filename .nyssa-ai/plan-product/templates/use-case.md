---
feature: F-00.01
id: UC-00.01.01
status: planned
---

# UC-00.01.01 Use Case Name

## Actor

Name the user, persona, or actor performing the workflow.

## Goal

Describe the outcome the actor needs in plain, non-technical language.

## Starting Context

Describe what the actor already has, sees, knows, or what state exists before the workflow starts (and optionally link to the parent concept or macro-flow stage in `../../concepts/`).

## Entry Route

Describe how the actor reaches or invokes the workflow. If the user does not know, write `Unknown; not inferred.`

## Trigger

Describe what starts the workflow.

## Process

```text
Actor reaches the goal
+-- Starting context: what already exists
+-- Entry route: how the actor gets to the workflow
+-- Trigger: what starts the workflow
+-- Step 1: observable actor action or system response
|   +-- Decision or branch, if any
|   \-- Failure path, if any
+-- Step 2: observable actor action or system response
\-- Success: completed state for the actor
```

## Step Details

Add short descriptions only for complex process nodes in plain actor-behavior language (avoid internal code, database, or technology details). If no step needs extra explanation, write `None.` Otherwise, add one subsection per complex node using `### Step N: Name`.

## Success

Describe the completed state observable by the actor.

## Failure Cases

- Missing input.
- Invalid state.
- Permission or validation failure.

## Consistency Check

- Unique coverage: Describe what this use case covers that existing sibling use cases do not.
- Closest related use cases: List related `UC-gg.nn.uu` files and the boundary between them.
- Contradictions: Write `None found.` or describe the resolved contradiction.

## Acceptance

- The ASCII process tree can be followed from the feature guide.
- Expected actor outcomes are clear and free of implementation or technology selections.
- Failure cases produce clear user-observable guidance.
- The consistency check shows no unresolved duplicate coverage or contradictions.
