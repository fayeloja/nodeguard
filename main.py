import sys
import os
import re
import argparse
from dotenv import load_dotenv, set_key

# Load .env before checking keys
load_dotenv()

from rich.console import Console
from rich.progress import track
from rich.prompt import Prompt

from graph.pipeline import build_pipeline
from utils.github_fetcher import get_js_files_from_repo
from utils.html_reporter import generate_html_report

console = Console()

def setup_environment(provider):
    # Ensure provider key is available
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            console.print("[yellow]GROQ_API_KEY not found.[/yellow]")
            key = Prompt.ask("Please enter your Groq API key")
            os.environ["GROQ_API_KEY"] = key
            set_key(".env", "GROQ_API_KEY", key)
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            console.print("[yellow]OPENAI_API_KEY not found.[/yellow]")
            key = Prompt.ask("Please enter your OpenAI API key (or press enter to fallback to Groq)", default="")
            if key:
                os.environ["OPENAI_API_KEY"] = key
                set_key(".env", "OPENAI_API_KEY", key)

def load_code(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

def extract_code_block(text: str) -> str:
    match = re.search(r"```(?:javascript|js)?\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()

def is_github_url(input_str: str) -> bool:
    return input_str.startswith("https://github.com/")

def sanitize_filename(path: str) -> str:
    return path.replace("/", "_").replace("\\", "_")

def review_single_file(file_path: str, code: str, output_dir: str, verbose: bool = False) -> dict:
    pipeline = build_pipeline()
    result = pipeline.invoke({"code": code})

    # Save report
    safe_name = sanitize_filename(file_path).replace(".js", "")
    report_path = os.path.join(output_dir, f"{safe_name}_review.md")
    with open(report_path, "w") as f:
        f.write(result["final_report"])
    
    if verbose:
        console.print(f"  [green]📄 Report:[/green] {report_path}")

    # Save fixed code if generated
    if result.get("fixed_code"):
        fixed_path = os.path.join(output_dir, f"{safe_name}_fixed.js")
        fixed_code = extract_code_block(result["fixed_code"])
        with open(fixed_path, "w") as f:
            f.write(fixed_code)
        if verbose:
            console.print(f"  [blue]🔧 Fixed:[/blue] {fixed_path}")

    return {
        "path": file_path,
        "report": result["final_report"],
        "fixed": bool(result.get("fixed_code"))
    }

def main():
    parser = argparse.ArgumentParser(description="NodeGuard: AI-powered code review and analysis pipeline.")
    parser.add_argument("target", nargs="?", default="samples/sample.js", help="Path to local JS file or GitHub repo URL.")
    parser.add_argument("--provider", type=str, choices=["groq", "openai"], default=os.getenv("LLM_PROVIDER", "groq").lower(), help="LLM Provider to use.")
    parser.add_argument("--model", type=str, help="Specific LLM model to use (overrides default).")
    parser.add_argument("--output", type=str, help="Custom output directory.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args()

    # Set environment based on CLI
    os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    # Interactive key prompt if missing
    setup_environment(args.provider)

    target = args.target

    if is_github_url(target):
        # GitHub repo mode
        console.print(f"\n[bold cyan]🌐 NodeGuard — GitHub Repo Mode[/bold cyan]")
        
        files = get_js_files_from_repo(target)
        
        # Create output directory
        repo_name = target.rstrip("/").split("/")[4] if len(target.split("/")) > 4 else "repo"
        output_dir = args.output or f"reports/{repo_name}"
        os.makedirs(output_dir, exist_ok=True)

        all_reports = []

        console.print(f"\n[bold]Scanning {len(files)} files...[/bold]")
        
        for file in track(files, description="Analyzing..."):
            if args.verbose:
                console.print(f"🔍 Reviewing: {file['path']}")
            result = review_single_file(file["path"], file["content"], output_dir, args.verbose)
            all_reports.append(result)

        # Generate repo-wide summary
        console.print("\n[bold]📊 Compiling repository summary...[/bold]\n")
        from agents.summary_compiler import summary_compiler
        summary = summary_compiler(all_reports)

        summary_path = os.path.join(output_dir, "_SUMMARY.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary)

        if args.verbose:
            console.print(summary)

        # Generate HTML dashboard
        html_path = os.path.join(output_dir, "_REPORT.html")
        generate_html_report(
            all_reports=all_reports,
            summary=summary,
            repo_url=target,
            output_path=html_path
        )

        console.print(f"\n[bold green]✅ All reports saved to: {output_dir}/[/bold green]")
        console.print(f"📊 Summary saved to: {summary_path}")
        console.print(f"🌐 HTML dashboard saved to: {html_path}\n")

    else:
        # Local file mode
        console.print(f"\n[bold magenta]🔍 NodeGuard — Local File Mode[/bold magenta]")
        console.print(f"Reviewing: {target}\n")
        
        output_dir = args.output or "reports/local"
        os.makedirs(output_dir, exist_ok=True)
        try:
            code = load_code(target)
            review_single_file(target, code, output_dir, True)
            console.print("\n[bold green]✅ Done[/bold green]\n")
        except FileNotFoundError:
            console.print(f"[bold red]❌ Error: File '{target}' not found.[/bold red]")

if __name__ == "__main__":
    main()