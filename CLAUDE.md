# Project Guidelines

## Python Coding Style
- **Version**: Python 3.10+
- **Type Annotations**: Always use pipe syntax (`X | Y`) for Unions and Optionals.
  - ✅ `str | None`, `int | float`
  - ❌ `Optional[str]`, `Union[int, float]`
- **Linting**: We use Ruff. Strictly follow rule `UP007`.

## Development Commands
- Run: `uv run main.py`
- Lint/Format: `ruff check --fix .`
