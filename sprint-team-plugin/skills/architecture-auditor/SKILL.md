# Skill: Architecture Auditor

## When to use

After code review, needs macro-level architecture audit.

## Workflow

1. Read project docs and architecture plan
2. Evaluate module division, coupling, layering, extensibility
3. Walk through core business flows end-to-end
4. Check exception handling and frontend-backend closure
5. Calculate completion percentage
6. Classify defects into P0/P1/P2
7. Output audit report to `docs/audits/architecture-audit.md`

## Output requirements

- Must conclude with: pass / conditional pass / fail
- Completion percentage must be based on actual code
- Must include defect table with location, description, impact, fix suggestion
- Must not modify code files
