# AI Execution Protocol

This document defines how AI agents (e.g., Codex) are to behave when contributing to this codebase.

---

## Execution Behavior

1. Parse and confirm contents of `Master System Documentation.md`
2. Execute the roadmap **step-by-step**, one step at a time.
3. For each step:
   - Analyze the step's objective
   - Plan the solution and list required files
   - Write only the necessary code
   - Test it completely
   - Log what was done in `codex_log.md`
   - Commit the change
   - STOP and wait for review

---

## Constraints

- ❌ Do not combine steps  
- ❌ Do not modify unrelated files  
- ❌ Do not add speculative features  
- ✅ Only touch files defined in the current step  
- ✅ Confirm test pass rate before commit  
- ✅ All logs go to `codex_log.md`  

---

## Required Files
- `Master System Documentation.md`: defines execution order
- `codex_log.md`: stores decisions, actions, and test results
- `AI_EXECUTION_PROTOCOL.md`: you are reading it

---

## Error Handling

If a dependency is missing, or the roadmap is ambiguous:
- Stop execution
- Log the issue in `codex_log.md`
- Request clarification before proceeding

---

## Commit Rules

- One commit per roadmap step  
- Commit message format:  
  `Step N: [Short description of what was done]`  

---

This protocol is mandatory. Do not proceed without adherence.