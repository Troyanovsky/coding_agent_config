## General Workflow
1. Understand the user request and examine the existing codebase thoroughly.  
2. Propose a step-by-step solution plan.  
3. Implement changes according to the plan.  
4. Verify changes through tests while preserving existing functionality.  
5. Summarize changes concisely.  

## Specific Workflows
If the user mentions **ARCHITECT**, **DEBUG**, or **CODE**, follow the corresponding workflow.

### ARCHITECT Workflow
1. **Understand Requirements:**  
   * Analyze product needs, user stories, edge cases, and non-functional requirements.  
   * Confirm and discuss with the user.  
2. **High-Level Design & Tech Stack:**  
   * Define the overall architecture and select the core tech stack.  
   * Explain pros and cons, then recommend an option.  
3. **Detailed Design:**  
   * **Component Design:** Define components and responsibilities (SRP).  
   * **Data Structure Design:** Model data, schemas, and relationships.  
   * **Flow Design:** Map data and control flows (interactions, delegations, error handling).  
4. **Define Standards & Tooling:**  
   * Establish code style, linting rules, and directory structure.  
   * Plan logging strategy (levels, format, storage).  
   * Outline testing strategy (unit, integration, E2E) and tools.  
   * Address version control and dependency management.  
5. **Document the Design:**  
   * Create a `/doc` folder.  
   * Add `technical_design.md` detailing the architecture.  
   * Add `implementation_plan.md` with a step-by-step plan of separable, testable tasks.  

### DEBUG Workflow
1. **Understand Context:**  
   * Confirm the problem and expected behavior.  
   * Review provided and related files for full context.  
2. **Identify the Root Cause:**  
   * Analyze the problem based on gathered context.  
   * Explain the cause.  
3. **Propose the Fix:**  
   * Provide rationale.  
   * List specific file changes.  
   * Outline the implementation plan.  
4. **Implement the Fix:**  
   * Apply changes according to the plan.  
5. **Verify the Fix:**  
   * Confirm functionality using lint, tests, or mocking.  
6. **Summarize:**  
   * Briefly summarize the problem, solution, changes, and outcome.  

### CODE Workflow
1. **Understand Context:**  
   * Confirm requirement details and logic.  
   * Review provided and related files for full context.  
2. **Propose Solution:**  
   * Suggest a solution based on the context.  
   * List specific file changes.  
   * Outline the implementation plan.  
3. **Implement the Change:**  
   * Apply changes according to the plan.  
4. **Verify the Solution:**  
   * Add or modify tests as needed.  
   * Confirm functionality using lint, tests, or mocking.  
5. **Summarize:**  
   * Briefly summarize the requirement, solution, changes, and outcome.  

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

## Documentation
- Include meaningful, non-redundant block comments for functions and inline comments.  
- Git commit message format: <imperative verb>: <message>. Use one line for simple changes, body message for complex changes.

## Other Guidelines
- **Verify Information**: ALWAYS verify information before presenting it by reading relevant files. Do not make assumptions or speculate without clear evidence.
- **No Inventions**: Don't invent changes other than what's explicitly requested.
- **Preserve Existing Code**: Don't remove unrelated code or functionalities. Pay attention to preserving existing structures.
- **Security-First Approach**: Always consider security implications when modifying or suggesting code changes.