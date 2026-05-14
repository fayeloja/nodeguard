# Contributing to NodeGuard

First off, thank you for considering contributing to NodeGuard! It's people like you that make the open-source community such a great place to learn, inspire, and create.

## How Can I Contribute?

### Reporting Bugs

If you find a bug in the source code, you can help us by submitting an issue using our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Enhancements

If you have an idea for a new feature, you can suggest it using our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).

### Pull Requests

1. **Fork the repo** and create your branch from `main`.
2. **Setup your environment:**
   ```bash
   pip install -r requirements.txt
   ```
3. **If you've added code that should be tested, add tests.** (Testing infrastructure coming soon)
4. **Ensure the code meets our style guidelines.**
5. **Create a pull request** using the provided template.

## Adding a New Agent

NodeGuard's strength is its modular, multi-agent LangGraph architecture. To add a new agent (e.g., a "Dependency Analyst" or "License Checker"):

1. Create a new file in `agents/` (e.g., `agents/license_checker.py`).
2. Write a prompt that returns a strict, predictable format.
3. Update `graph/state.py` to add a new key in `ReviewState` for your agent's output.
4. Update `graph/pipeline.py` to add your node and weave it into the sequential edge flow.
5. Update `agents/report_compiler.py` to include your agent's output in the final report template.
6. Update `utils/html_reporter.py` if you want a dedicated tab for your agent in the UI.

## Adding a New LLM Provider

1. Open `graph/llm.py`.
2. Import the LangChain provider class.
3. Add an `elif provider == "your_provider":` block in the `get_llm` function.
4. Wrap the returned instance in `_apply_retry(llm)`.
5. Update `README.md` and `.env.example` with the new environment variables needed.

## Style Guide

*   Use type hints wherever possible.
*   Keep functions small and focused.
*   Write clear, descriptive commit messages.

Thank you for contributing!
