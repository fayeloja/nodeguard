# NodeGuard: User Manual

Welcome to **NodeGuard**! NodeGuard is an AI-powered code review assistant that acts as a specialized team of reviewers for your JavaScript/Node.js codebase. It automatically scans your code for logic bugs, security vulnerabilities, and style violations—and even auto-fixes critical issues.

This manual will get you up and running quickly.

---

## 1. Before You Begin

You only need two things to use NodeGuard:
1. **Python 3.11+** installed on your system.
2. An **API Key** from either [Groq](https://console.groq.com/keys) (which is free and very fast) or [OpenAI](https://platform.openai.com/api-keys).

---

## 2. Installation

Install NodeGuard globally on your machine using `pip`:

```bash
pip install nodeguard
```

*(Note: If you run into permissions errors, you can use `pip install --user nodeguard` or install it inside a Python virtual environment).*

---

## 3. Initial Setup

NodeGuard needs your API key to power its AI reviewers. 

The easiest way to provide this is to create a `.env` file in the folder where you run the tool. You can copy the provided `.env.example` file to get started:

```bash
# In your terminal
cp .env.example .env
```

Open `.env` in your text editor and paste your API key:
```env
# Use Groq by default
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_api_key_here
```

*(NodeGuard also prompts you for a key interactively in the terminal if it doesn't find one in your `.env` file).*

---

## 4. How to Use NodeGuard

NodeGuard has two main operating modes: **Local File Mode** and **GitHub Repo Mode**.

### Mode A: Reviewing a Local File
Want to quickly review a single script on your computer? Just point NodeGuard to it:

```bash
nodeguard src/server.js
```

**What happens next?**
- NodeGuard will analyze `server.js`.
- It will generate a Markdown report detailing any issues found.
- If it detects **HIGH severity** issues, it will attempt to automatically write a corrected version of the code (saved as `server_fixed.js`).
- Results are saved by default in `reports/local/`.

### Mode B: Scanning an Entire GitHub Repository
Want to audit a whole public repository? Give NodeGuard the URL:

```bash
nodeguard https://github.com/fayeloja/nodeguard
```

**What happens next?**
- NodeGuard automatically fetches the code tree (skipping folders like `node_modules` or `dist`).
- It reviews the files in small batches to respect API rate limits.
- It compiles all individual reports into a **beautiful, interactive HTML Dashboard**.
- Results are saved in `reports/<repo-name>/`. Open `_REPORT.html` in your web browser to view the findings!

---

## 5. Understanding the Output

After a successful run, NodeGuard generates a `reports/` directory. Here is what you will find inside:

*   **`_REPORT.html`**: The crown jewel. Open this file in your web browser. It provides a visual dashboard of your code's health, categorizing files by severity, showing exactly what is wrong, and highlighting what the AI auto-fixed.
*   **`_SUMMARY.md`**: A quick text-based executive summary of the worst issues found across your codebase.
*   **`filename_review.md`**: Detailed AI commentary on a specific file, broken down by Logic, Security, and Style.
*   **`filename_fixed.js`**: If NodeGuard found critical vulnerabilities, it writes a suggested fixed version of the file for you to review and adopt.

---

## 6. Advanced Customization

You can tweak how NodeGuard runs by passing command-line flags.

**Switching AI Providers:**
```bash
# Force the use of OpenAI instead of Groq
nodeguard src/app.js --provider openai
```

**Changing Output Folders:**
```bash
# Save the reports somewhere else
nodeguard src/app.js --output /path/to/custom/folder
```

**Bypassing the Cache:**
NodeGuard caches its reviews to save you time and API costs. If you want to force it to re-analyze a file that hasn't changed, use `--no-cache`:
```bash
nodeguard src/app.js --no-cache
```

**Need more help?**
Run `nodeguard --help` in your terminal to see a full list of available commands.

---

**Happy Coding!** Let NodeGuard catch the bugs so you can focus on building features.
