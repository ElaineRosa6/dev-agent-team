# Skill: Product Architect

## When to use

User needs to design system architecture from requirements, or start a new sprint planning phase.

## Workflow

1. Read requirements from user input or `docs/requirements.md`
2. Identify MVP boundaries
3. Define API contracts
4. Design external dependency anti-corruption layers
5. Plan observability and fallback strategies
6. Output evolutionary architecture plan to `docs/architecture/architecture-plan.md`

## Output requirements

- Must include 4 phases: MVP boundary, API contract, MVP implementation, observability
- Each phase must have clear acceptance criteria
- Must not generate code implementation
- Must follow YAGNI principle
