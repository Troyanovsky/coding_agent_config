# Engineering Guidelines

## Workflow

- Scale planning and verification to the task’s complexity and risk.
- Before implementation, resolve uncertainty using code, documentation, and available context. Ask clarifying questions about remaining ambiguities in scope, behavior, or approach.
- Establish clear requirements, assumptions, success criteria, and an implementation plan with verification steps before coding.
- If a clearly better approach exists, explain its tradeoffs. Proceed with the requested approach when reasonable; seek a decision if it risks serious harm or wasted work.
- During implementation, resolve routine details independently within the agreed scope. Revisit clarification only when new evidence materially changes requirements or approach.
- For bug fixes, first write a failing test that reproduces the bug.
- Verify the result and preserve existing functionality. Summarize changes, verification, and any remaining limitations.

## Scope and Change Integrity

- Keep every change tied to the task. Avoid unrelated removal, renaming, or refactoring, and match existing style.
- Preserve existing behavior unless a change is explicitly intended and documented.
- Verify assumptions against existing code and documentation; do not invent APIs, requirements, or speculative functionality.
- Remove code made obsolete by your changes. Mention pre-existing dead code separately unless your change directly replaces it.
- Clean up temporary build directories automatically, including those in `/private/tmp`, or document why they are retained.

## Code Quality and Security

- Prioritize correctness, clarity, security, and maintainability.
- Apply DRY, KISS, YAGNI, and SOLID pragmatically. Prefer the simplest readable design that meets current requirements; introduce abstractions when they reduce complexity.
- Give functions, classes, and components a single clear responsibility. Keep related logic together and avoid deep nesting.
- Use descriptive, consistent names. Use named constants for values with domain meaning or repeated use, and configuration for values that need to vary.
- Never read or commit secrets, credentials, tokens, or API keys, including secret-bearing `.env` files.
- Consider the security implications of changed code.

## Documentation

- Document purpose, contracts, and behavior where they are not obvious, using language-standard documentation mechanisms.
- Keep affected documentation current, including file-level documentation when responsibilities change. Update relevant documentation before merging.
- Write comments that explain reasoning rather than restate code.

## Git, Review, and Tools

- Keep commits logically scoped and atomic.
- Use `<type>(<scope>): <message>` for commit messages, such as `fix(auth): correct token expiration handling`.
- Explain intent, context, and impact in concise commit-body bullets.
- Ground review feedback in correctness, clarity, scope, security, and maintainability rather than personal preference. Address violations before merging.
- Allow realistic completion time for long-running tools and sub-agents; avoid repeated polling when no new information is expected.
