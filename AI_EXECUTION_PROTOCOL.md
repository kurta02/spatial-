AI_Execution_Protocol.md
# AI Execution Protocol

You are a supervised Codex agent. Follow these rules exactly.

## Master Roadmap
All actions must align with the project roadmap defined in:
**`Master System Documentation.md`**

## Task Flow
1. Confirm `codex_log.md` exists.
2. Begin at Step 1 in `Master System Documentation.md`
3. Do **not** skip or combine steps.
4. At the end of each step:
   - Log actions in `codex_log.md`
   - Commit with: `Step 1: [short description]`
   - Stop at `<!-- HALT -->` markers and wait.
5. Repeat for Step 2 and beyond.

## Guardrails
- Do not generate placeholder code unless explicitly told.
- Do not hallucinate missing files—raise an error instead.
- Do not exceed the scope of the current step.

## Coordination
If more than one agent is working:
- Each agent must write to a **separate** section of `codex_log.md`
- Conflicting file edits must be halted and flagged.

