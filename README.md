# NodeGuard

NodeGuard is an AI-powered code review and analysis pipeline built with LangGraph. It leverages LLMs (like Groq's `llama-3.3-70b-versatile` or OpenAI's `gpt-4o-mini`) to automatically inspect, audit, and provide automated fixes for JavaScript codebases. NodeGuard operates through a pipeline of specialized agents that analyze logic, security, style, and compile comprehensive HTML and Markdown reports.

## Features

- **Multi-Agent Architecture**: Uses distinct agents for reviewing different aspects of the codebase (Logic, Security, Style).
- **Automated Fixes**: Conditionally invokes a code fixer agent if critical severity issues are identified.
- **GitHub Integration**: Can scan an entire GitHub repository to evaluate all JavaScript files automatically.
- **Rich Reporting**: Compiles repository-wide summaries, per-file Markdown reports, and an intuitive HTML dashboard.
- **CI/CD Ready**: Includes a pre-configured GitHub Action (`.github/workflows/nodeguard.yml`) for seamless integration into your pull request or build pipeline.

## Architecture

NodeGuard uses `langgraph` to create a directed graph of agents representing the code review lifecycle:

1. **Logic Analyst**: Scans the code for logical errors, inefficient algorithms, and edge-case mishandlings.
2. **Security Auditor**: Checks for vulnerabilities, insecure patterns, and potential exploits.
3. **Style Enforcer**: Ensures the code conforms to standard JavaScript formatting and best practices.
4. **Report Compiler**: Synthesizes the findings of the previous agents into a unified per-file report.
5. **Severity Router**: Evaluates the compiled report and decides if the `Code Fixer` needs to intervene.
6. **Code Fixer**: (Conditional) Generates corrected code snippets to resolve critical issues found.

## Prerequisites

- Python 3.11 or higher
- A [Groq API Key](https://console.groq.com/keys) or [OpenAI API Key](https://platform.openai.com/api-keys)

## Installation

1. **Install via pip (recommended):**
   ```bash
   pip install nodeguard
   ```

   *Alternatively, install from source:*
   ```bash
   git clone https://github.com/fayeloja/nodeguard.git
   cd nodeguard
   pip install -e .
   ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Usage

NodeGuard supports two main operational modes: Local File Mode and GitHub Repo Mode.

### Local File Mode
To review a single JavaScript file on your local machine:
```bash
nodeguard path/to/your/file.js
```
The output report and any generated fixes will be saved in the `reports/local/` directory.

### GitHub Repo Mode
To review all JavaScript files in a public GitHub repository:
```bash
nodeguard https://github.com/username/repository
```
The outputs will be saved in the `reports/<repository-name>/` directory, containing:
- Individual Markdown reports for each analyzed file (`*_review.md`).
- Fixed code files if applicable (`*_fixed.js`).
- A repository-wide summary (`_SUMMARY.md`).
- A comprehensive HTML dashboard (`_REPORT.html`).

### CLI Options
NodeGuard comes with a robust CLI. You can use the `--help` flag for more information:
```bash
nodeguard --help
```

**Key Flags:**
- `--provider <groq|openai>`: Select the LLM provider to use (default: groq).
- `--model <model_name>`: Override the default model for the selected provider.
- `--output <dir>`: Specify a custom directory for reports.
- `--verbose`, `-v`: Enable detailed logging.

**LLM Fallbacks:**
If you select the OpenAI provider but no `OPENAI_API_KEY` is found, NodeGuard will automatically attempt to fall back to Groq.

## GitHub Actions Integration

NodeGuard can run automatically in your CI/CD pipeline using the included GitHub workflow.

To enable it:
1. Go to your repository settings on GitHub.
2. Navigate to **Secrets and variables > Actions**.
3. Add a new repository secret named `GROQ_API_KEY` with your Groq API key.
4. The workflow will automatically run on pushes to the `main` branch or when manually triggered, uploading the generated HTML report as an artifact.
