## General Workflow
1. Understand the user request and examine the existing codebase thoroughly.  
2. Propose a step-by-step solution plan.  
3. Implement changes according to the plan.  
4. Verify changes through tests while preserving existing functionality.  
5. Summarize changes concisely.  

## Code Quality Principles
- Follow DRY, KISS, YAGNI, and SOLID principles.  
- Avoid duplicate code; use helper functions.  
- Ensure correctness, efficiency, security, error prevention, and maintainability.  

## Structure and Formatting
- Keep line length, function/component size, and complexity reasonable.  
- Use logical modules/helpers.  
- Explicitly mark code changes (keep/remove/edit).  
- Split multiple changes into separate code blocks.  

## Naming and Security
- Use descriptive, consistent names.  
- Avoid hardcoded literals or credentials.  
- Never commit secrets/API keys.

## Documentation
- For every code file you create or update, you MUST include/update a concise 3-line header comment at the very top: Input (what this depends on), Output (what this offers), File Pos (what's the role/position of this file in the system).
- Include meaningful, non-redundant block comments for functions and inline comments.  
- Git commit message format: <type>(<scope>): <message>. Use one line for simple changes, body message for complex changes. e.g. `fix(auth): correct token expiration handling`, `feat(profile): add user profile picture upload`.
- Before Git commits, you should update relevant documentation files.

## Other Guidelines
- **Verify Information**: ALWAYS verify information before presenting it by reading relevant files. Do not make assumptions or speculate without clear evidence.
- **No Inventions**: Don't invent changes other than what's explicitly requested.
- **Preserve Existing Code**: Don't remove unrelated code or functionalities. Pay attention to preserving existing structures.
- **Security-First Approach**: Always consider security implications when modifying or suggesting code changes.