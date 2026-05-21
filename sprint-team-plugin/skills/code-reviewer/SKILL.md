# Skill: Code Reviewer

## When to use

Code implementation is complete, needs four-dimensional code review.

## Workflow

1. Analyze project structure and tech stack
2. Follow core business flow to check code
3. Find pseudo-implementations (declared but not implemented)
4. Four-dimension scan:
   - Functional bugs (boundary, exception, concurrency, type, resource)
   - Security (injection, auth, data leak, dependency)
   - Code quality (smell, design, performance, readability)
   - Business logic (scenario missing, consistency, timing)
5. Sort by severity: P0 > P1 > P2 > P3
6. Output review report to `docs/reviews/code-review.md`

## Output requirements

- Each issue must include file path and line number
- P0/P1 issues must include fix code snippet
- Must not modify code files
- Must cover all four dimensions
