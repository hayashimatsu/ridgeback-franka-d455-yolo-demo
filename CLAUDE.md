@AGENTS.md

# Claude Code Routing

The route is selected by Codex or explicitly by the user. Do not silently upgrade a `SONNET` route into an Opus or agent-team workflow.

## SONNET

Run the task directly when launched with Sonnet. Use the `isaac-sim-mcp-workflow` skill, remain within the supplied scope, and return evidence rather than spawning additional agents.

## OPUS

Perform analysis, planning, requirement reconciliation, or evidence review directly. Do not create implementation work merely to justify delegation.

## OPUS_TO_SONNET

As the Opus main session:

1. Confirm objective, scope, acceptance, authority, and stop conditions.
2. Delegate one bounded implementation task to `isaac-sim-executor`.
3. Resume that executor for closely related follow-ups instead of starting over.
4. Review the diff, active-stage provenance, runtime evidence, and acceptance result yourself.
5. Return to the user when authority or a material product decision is missing.

## AGENT_TEAM

Do not enable an agent team unless the user approved it and at least two workstreams are independent. Assign distinct file ownership or read-only hypotheses. Never allow two teammates to edit the same USD. Consolidate all results into one reviewed acceptance record.

## MCP

The configured server name is `isaac-sim`. Confirm it with `claude mcp get isaac-sim`. MCP connection does not prove the intended GUI stage is open; verify active-stage identity inside Isaac Sim before mutation.
