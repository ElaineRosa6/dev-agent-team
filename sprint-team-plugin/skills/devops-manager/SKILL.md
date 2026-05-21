# Skill: DevOps Manager

## When to use

Start a new iteration or close an iteration (cleanup, record, archive, summary).

## Workflow - Iteration Start

1. Read previous iteration summary (if exists)
2. Confirm iteration goal and scope
3. Prepare input materials
4. Output iteration start record to `docs/iterations/iteration-{N}-start.md`

## Workflow - Iteration Close

1. Scan project for garbage files, list them, confirm before cleanup
2. Record all work items from this iteration
3. Generate iteration summary to `docs/iterations/iteration-{N}-summary.md`
4. Archive all documents to correct directories
5. Ask if starting next iteration

## Constraints

- Must list cleanup items before executing
- Must verify project builds after cleanup
- Must not delete code files
- Must record legacy issues with next-iteration plan
