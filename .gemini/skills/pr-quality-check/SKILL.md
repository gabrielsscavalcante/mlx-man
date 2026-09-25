---
name: pr-quality-check
description: >-
  Use this skill BEFORE opening any Pull Request (PR). This skill enforces a mandatory quality check to ensure that the code is clean, well-tested, and aims for 100% test coverage (including snapshot tests for UI changes). If full coverage is impossible, you must consult the user.
---

# Pull Request Quality Check

This skill enforces mandatory quality control steps before you are allowed to open a Pull Request (via `gh pr create` or any other tool). 

Your goal is to ensure that code quality remains extremely high, with an aggressive target of **100% unit test coverage** and complete snapshot testing for any UI components.

## Mandatory Pre-PR Checklist

Before you execute the command to open a PR, you MUST complete all of the following steps:

### 1. Run Automated Formatting and Linting
- Ensure all code is cleanly formatted according to the project's standards.
- Run the project's linter (e.g., `uv run ruff check .` or equivalent) and fix any warnings or errors. Do not submit code with linting violations.

### 2. Verify Global Test Execution
- Run the entire test suite (e.g., `uv run pytest`) to ensure no existing tests were broken by your changes.
- All tests must pass. If any tests fail, fix the implementation or the tests before proceeding.

### 3. Check Test Coverage (Target: 100%)
- Run the coverage report for the project (e.g., `uv run pytest --cov=<module> tests/ --cov-report=term-missing`).
- Carefully review the missed lines.
- **Goal:** You must aggressively aim for 100% test coverage for the files you added or modified.
- **Snapshot Tests:** If you introduced or modified any UI components, Terminal User Interfaces (TUI), or frontend views, you MUST include snapshot tests that record the rendered output. 

### 4. Handle Missing Coverage
- If you find lines that are missing coverage, write tests to cover them. 
- If a block of code (like `__main__` entrypoints or complex hardware-specific OS calls) is truly untestable or unnecessary to test, use `# pragma: no cover` (or the language equivalent) and justify it.
- **CRITICAL:** If you are unable to reach 100% coverage because a specific edge case is too complex, impossible to mock, or you are unsure how to test it, you MUST stop and ask the user for guidance:
  * "I have achieved X% coverage, but I am struggling to test [specific function/edge case]. How would you like me to handle this before opening the PR?"

### 5. Final Approval
- Once the code is clean, tests are passing, and you have either achieved 100% coverage or received user approval for the exceptions, you may proceed to open the PR.

## Important Note
Do not skip these steps to save time. The user prefers quality over speed. If you cannot fulfill these requirements, explicitly document what is missing and ask the user for permission to proceed.
