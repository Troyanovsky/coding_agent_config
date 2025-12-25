## General Workflow
1. Understand the user request and examine the existing codebase thoroughly.  
2. Propose a step-by-step solution plan.  
3. Implement changes according to the plan.  
4. Verify changes through tests while preserving existing functionality.  
5. Summarize changes concisely.  


## Core Engineering Principles

- Code must prioritize **correctness, clarity, security, and maintainability**.
- Apply **DRY, KISS, YAGNI, and SOLID** principles when they reduce complexity—not as dogma.
- Prefer explicit, readable code over clever or overly compact implementations.


## Structure, Scope, and Complexity

- Every function, class, or component must have a **single, clear responsibility**.
- Prefer small, composable units over large, multi-purpose ones.
- Avoid deep nesting and complex control flow; refactor when logic becomes difficult to follow.
- Group related logic into **logical modules or helpers**.
- Limit changes to the **explicit scope of the task or PR**.
- Do not remove, rename, or refactor unrelated code.
- Preserve existing behavior unless a change is explicitly intended and documented.


## Naming, Constants, and Security

- Use **descriptive, consistent names** that reflect domain intent.
- Avoid magic numbers and hardcoded literals; use named constants or configuration.
- **Never commit secrets, credentials, tokens, or API keys**.
- Always consider security implications when modifying or introducing code.


## Documentation Standards

- Every source file must begin with **concise, language-standard documentation** describing its **purpose and responsibility**, using the **canonical, tool-supported mechanism** for that language.
- File-level documentation must be **kept up to date whenever responsibilities change**.
- Public functions, classes, and non-obvious logic must be documented.
- Comments should explain **why** something exists or behaves a certain way—**not restate what the code does**.
- Update relevant documentation files **before merging changes**.


## Change Integrity & Correctness

- Always verify assumptions by **reading existing code and documentation**.
- Do not invent behavior, APIs, or changes beyond what is explicitly requested.
- Avoid speculative or hypothetical implementations.
- Ensure changes are correct, safe, and consistent with existing design.


## Git & Commit Hygiene

- Commits must be **logically scoped and atomic**.
- Commit messages must follow:

```

<type>(<scope>): <message>

```

Examples:
- `fix(auth): correct token expiration handling`
- `feat(profile): add user profile picture upload`

- Use a commit body for complex changes to explain **intent, context, and impact**.


## Review Expectations

- Code reviews focus on **correctness, clarity, scope, security, and maintainability**.
- Stylistic feedback should be grounded in these standards, not personal preference.
- If a rule is violated, it must be addressed before merge.


## Final Guiding Rule

> Leave the codebase **clearer, safer, and easier to maintain** than you found it.