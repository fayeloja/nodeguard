import sys
import os
import re
import time
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
from utils.cache import get_cached_result, save_cached_result
from utils.token_utils import estimate_tokens

console = Console()


def _is_auth_error(exc: BaseException) -> bool:
    """Return True if *exc* is an authentication / invalid-key error."""
    return type(exc).__name__ in ("AuthenticationError", "PermissionDeniedError")


def _print_auth_error(exc: BaseException) -> None:
    console.print(
        f"\n[bold red]❌ Authentication failed — invalid or missing API key.[/bold red]"
        f"\n   Provider said: [red]{exc}[/red]"
        f"\n   → Check your [cyan].env[/cyan] file and make sure the key is correct."
        f"\n   → Re-run [cyan]python main.py[/cyan] to be prompted for a new key.\n"
    )

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

def review_single_file(
    file_path: str,
    code: str,
    output_dir: str,
    verbose: bool = False,
    use_cache: bool = True,
) -> dict:
    """
    Run the full LLM review pipeline for *code* and save outputs to *output_dir*.

    If *use_cache* is True and a fresh cache entry exists for this content,
    the pipeline is skipped entirely and results are restored from cache —
    saving all LLM token costs for that file.
    """
    safe_name = sanitize_filename(file_path).replace(".js", "")
    report_path = os.path.join(output_dir, f"{safe_name}_review.md")
    fixed_path  = os.path.join(output_dir, f"{safe_name}_fixed.js")

    # ── Cache check ────────────────────────────────────────────────────────────
    if use_cache:
        cached = get_cached_result(code)
        if cached is not None:
            est_tokens = estimate_tokens(code)
            console.print(
                f"  [bold green]⚡ Cache HIT[/bold green] — skipped ~{est_tokens} tokens "
                f"for [cyan]{file_path}[/cyan]"
            )
            # Restore files from the cached result so reports are still written
            result = cached
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(result["report"])
            if result.get("fixed"):
                # fixed_code is stored in cache only if it was generated
                if result.get("fixed_code"):
                    fixed_code = extract_code_block(result["fixed_code"])
                    with open(fixed_path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)
            return {
                "path": file_path,
                "report": result["report"],
                "fixed": result.get("fixed", False),
                "from_cache": True,
            }

    # ── Full pipeline ──────────────────────────────────────────────────────────
    pipeline = build_pipeline()
    result = pipeline.invoke({"code": code})

    # Save report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result["final_report"])

    if verbose:
        console.print(f"  [green]📄 Report:[/green] {report_path}")

    # Save fixed code if generated
    fixed_code_raw = result.get("fixed_code")
    if fixed_code_raw:
        fixed_code = extract_code_block(fixed_code_raw)
        with open(fixed_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        if verbose:
            console.print(f"  [blue]🔧 Fixed:[/blue] {fixed_path}")

    outcome = {
        "path": file_path,
        "report": result["final_report"],
        "fixed": bool(fixed_code_raw),
        "fixed_code": fixed_code_raw,  # stored in cache for restoration
        "from_cache": False,
    }

    # Persist to cache so the next identical run is instant
    if use_cache:
        save_cached_result(code, outcome)

    return outcome

def main():
    parser = argparse.ArgumentParser(description="NodeGuard: AI-powered code review and analysis pipeline.")
    parser.add_argument("target", nargs="?", default="samples/sample.js", help="Path to local JS file or GitHub repo URL.")
    parser.add_argument("--provider", type=str, choices=["groq", "openai"], default=os.getenv("LLM_PROVIDER", "groq").lower(), help="LLM Provider to use.")
    parser.add_argument("--model", type=str, help="Specific LLM model to use (overrides default).")
    parser.add_argument("--output", type=str, help="Custom output directory.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging.")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the result cache and force a fresh LLM analysis for every file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("NODEGUARD_BATCH_SIZE", "5")),
        metavar="N",
        help="Number of files to process per batch (default: 5). "
             "A short pause between batches reduces burst API pressure.",
    )
    parser.add_argument(
        "--batch-delay",
        type=float,
        default=float(os.getenv("NODEGUARD_BATCH_DELAY", "2.0")),
        metavar="SECS",
        help="Seconds to wait between batches (default: 2.0).",
    )

    args = parser.parse_args()

    # Set environment based on CLI
    os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["LLM_MODEL"] = args.model

    use_cache = not args.no_cache

    # Interactive key prompt if missing
    setup_environment(args.provider)

    target = args.target

    if is_github_url(target):
        # ── GitHub repo mode ───────────────────────────────────────────────────
        console.print(f"\n[bold cyan]🌐 NodeGuard — GitHub Repo Mode[/bold cyan]")

        files = get_js_files_from_repo(target)

        # Create output directory
        repo_name = target.rstrip("/").split("/")[4] if len(target.split("/")) > 4 else "repo"
        output_dir = args.output or f"reports/{repo_name}"
        os.makedirs(output_dir, exist_ok=True)

        all_reports = []
        total = len(files)
        batch_size = args.batch_size

        if not use_cache:
            console.print("[yellow]⚠️  Cache disabled — all files will be re-analysed.[/yellow]")

        console.print(
            f"\n[bold]Scanning {total} files "
            f"(batch size: {batch_size}, delay: {args.batch_delay}s)…[/bold]"
        )

        # Process files in batches
        for batch_start in range(0, total, batch_size):
            batch = files[batch_start : batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            console.print(
                f"\n[bold magenta]── Batch {batch_num}/{total_batches} "
                f"({len(batch)} file{'s' if len(batch) > 1 else ''}) ──[/bold magenta]"
            )

            for file in track(batch, description="Analyzing…"):
                if args.verbose:
                    console.print(f"🔍 Reviewing: {file['path']}")
                try:
                    result = review_single_file(
                        file["path"], file["content"], output_dir,
                        verbose=args.verbose, use_cache=use_cache,
                    )
                    all_reports.append(result)
                except BaseException as exc:
                    if _is_auth_error(exc):
                        _print_auth_error(exc)
                        sys.exit(1)
                    console.print(
                        f"[bold red]❌ Failed to review {file['path']}: "
                        f"{type(exc).__name__}: {exc}[/bold red]"
                    )

            # Inter-batch pause (skip after the last batch)
            if batch_start + batch_size < total:
                console.print(
                    f"  [dim]⏸  Pausing {args.batch_delay}s before next batch…[/dim]"
                )
                time.sleep(args.batch_delay)

        # ── Summary & HTML report ──────────────────────────────────────────────
        console.print("\n[bold]📊 Compiling repository summary…[/bold]\n")
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
            output_path=html_path,
        )

        # ── Final stats ────────────────────────────────────────────────────────
        cached_count = sum(1 for r in all_reports if r.get("from_cache"))
        if cached_count:
            console.print(
                f"[bold green]⚡ {cached_count}/{total} file(s) served from cache "
                f"— LLM calls saved![/bold green]"
            )

        console.print(f"\n[bold green]✅ All reports saved to: {output_dir}/[/bold green]")
        console.print(f"📊 Summary saved to: {summary_path}")
        console.print(f"🌐 HTML dashboard saved to: {html_path}\n")

    else:
        # ── Local file mode ────────────────────────────────────────────────────
        console.print(f"\n[bold magenta]🔍 NodeGuard — Local File Mode[/bold magenta]")
        console.print(f"Reviewing: {target}\n")

        if not use_cache:
            console.print("[yellow]⚠️  Cache disabled — forcing fresh analysis.[/yellow]")

        output_dir = args.output or "reports/local"
        os.makedirs(output_dir, exist_ok=True)
        try:
            code = load_code(target)
            review_single_file(target, code, output_dir, verbose=True, use_cache=use_cache)
            console.print("\n[bold green]\u2705 Done[/bold green]\n")
        except FileNotFoundError:
            console.print(f"[bold red]\u274c Error: File '{target}' not found.[/bold red]")
        except BaseException as exc:
            if _is_auth_error(exc):
                _print_auth_error(exc)
            else:
                console.print(f"[bold red]\u274c Unexpected error: {type(exc).__name__}: {exc}[/bold red]")
            sys.exit(1)

if __name__ == "__main__":
    main()