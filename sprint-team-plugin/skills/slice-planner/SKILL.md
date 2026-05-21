# Skill: Slice Planner

## When to use

User has an architecture plan and needs to create safe, rollback-able execution steps.

## Workflow

1. Read architecture plan from `docs/architecture/architecture-plan.md`
2. Qualify change type (new/modify/refactor/migrate)
3. Map dependency chain (data → service → API → frontend)
4. Design compatibility strategy for breaking changes
5. Output execution plan with steps 1→N to `docs/plans/execution-plan.md`

## Output requirements

- Each step must have: purpose, actions, acceptance criteria, rollback plan, dependencies
- Steps must be ordered by dependency
- Each step must be independently rollback-able
- Must not generate code
