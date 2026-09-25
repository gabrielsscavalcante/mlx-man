---
name: mlx-man-testing
description: Guidelines and requirements for unit testing in the MLX-Man project.
---

# MLX-Man Testing Guidelines

Testing is a critical requirement for MLX-Man. Every time a new feature is added, an existing feature is modified, or a bug is fixed, unit tests MUST be updated or added before the task is considered complete.

## 1. Test Suite Execution
- **Command:** Always run `uv run make test` (or `make test` if the environment is activated) to verify the entire test suite passes.
- **Coverage:** If making significant logic changes, verify coverage using `make test-cov`.

## 2. Testing Principles
- **No side effects:** Tests must never write to the actual user `~/.config/mlx-man/` directory or interact with live processes un-mocked.
- **Mocking:** 
  - Always mock `psutil`, `os.system`, and `subprocess` when testing process management.
  - Use the `mock_config_dir` and `mock_hf_cache` fixtures provided in `tests/conftest.py` for filesystem operations.
- **UI Rendering Tests:** The presentation layer (`ram_manager_view.py`, `insights_view.py`, etc.) should be tested to ensure components render without crashing. Use `rich.console.Console(record=True)` to capture the output and assert that key elements (text, styling) are present in `console.export_text()`.

## 3. GitHub Actions (CI)
MLX-Man uses a GitHub Actions CI pipeline (`.github/workflows/ci.yml`).
- The CI runs the test suite across multiple Python versions (3.9 - 3.12) on macOS runners whenever a Pull Request is opened against `main`, or when code is pushed to `main`.
- **Merge Requirement:** All tests in the CI pipeline MUST pass before a PR can be merged.

## 4. Test File Structure
Tests are located in the `tests/` directory and map logically to the modules they test:
- `test_setup.py`: Packaging, XDG config paths, versioning.
- `test_cli.py`: Menu routing, main dashboard components.
- `test_insights.py`: Usage history, metrics logic, and insights view rendering.
- `test_models_view.py`: Model metadata building, tier assignment, inspector rendering.
- `test_ram_cleaner.py`: Process classification, safe termination fallbacks, table rendering.

When creating a new domain or infrastructure module, create a corresponding `test_<module_name>.py` file.
