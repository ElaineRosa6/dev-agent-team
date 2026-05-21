# Skill: Auto-Fix Engineer

## When to use

Review found P0/P1 issues, needs safe fix execution.

## Workflow

1. Read fix plan from `docs/plans/fix-plan.md`
2. Read review report and audit report
3. Phase 0: locate issues, detect project environment
4. Phase 1: high-confidence quick fix (P1/P2 clear bugs)
5. Phase 2: fix requiring test verification
6. Phase 3: evaluate only (architecture-level issues)
7. Phase 4: skip (already fixed, style issues, needs rewrite)
8. Run build/test/lint validation
9. Output fix report to `docs/fixes/fix-report.md`

## Constraints

- Verify issue exists before fixing
- Minimum change principle
- Must not introduce new dependencies
- Must not change API contracts
- Must not modify unrelated code
- Must not delete files
