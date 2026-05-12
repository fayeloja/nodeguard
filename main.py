import sys
import os
import re
from graph.pipeline import build_pipeline
from utils.github_fetcher import get_js_files_from_repo
from utils.html_reporter import generate_html_report

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

def review_single_file(file_path: str, code: str, output_dir: str) -> dict:
    pipeline = build_pipeline()
    result = pipeline.invoke({"code": code})

    # Save report
    safe_name = sanitize_filename(file_path).replace(".js", "")
    report_path = os.path.join(output_dir, f"{safe_name}_review.md")
    with open(report_path, "w") as f:
        f.write(result["final_report"])
    print(f"  📄 Report: {report_path}")

    # Save fixed code if generated
    if result.get("fixed_code"):
        fixed_path = os.path.join(output_dir, f"{safe_name}_fixed.js")
        fixed_code = extract_code_block(result["fixed_code"])
        with open(fixed_path, "w") as f:
            f.write(fixed_code)
        print(f"  🔧 Fixed: {fixed_path}")

    return {
        "path": file_path,
        "report": result["final_report"],
        "fixed": bool(result.get("fixed_code"))
    }

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "samples/sample.js"

    if is_github_url(target):
        # GitHub repo mode
        print(f"\n🌐 NodeGuard — GitHub Repo Mode")
        
        files = get_js_files_from_repo(target)
        
        # Create output directory named after repo
        repo_name = target.rstrip("/").split("/")[4] if len(target.split("/")) > 4 else "repo"
        output_dir = f"reports/{repo_name}"
        os.makedirs(output_dir, exist_ok=True)

        all_reports = []

        for file in files:
            print(f"\n🔍 Reviewing: {file['path']}")
            result = review_single_file(file["path"], file["content"], output_dir)
            all_reports.append(result)

        # Generate repo-wide summary
        print("\n📊 Compiling repository summary...\n")
        from agents.summary_compiler import summary_compiler
        summary = summary_compiler(all_reports)

        summary_path = os.path.join(output_dir, "_SUMMARY.md")
        with open(summary_path, "w") as f:
            f.write(summary)

        print(summary)

        # Generate HTML dashboard
        html_path = os.path.join(output_dir, "_REPORT.html")
        generate_html_report(
            all_reports=all_reports,
            summary=summary,
            repo_url=target,
            output_path=html_path
        )

        print(f"\n✅ All reports saved to: {output_dir}/")
        print(f"📊 Summary saved to: {summary_path}")
        print(f"🌐 HTML dashboard saved to: {html_path}\n")

    else:
        # Local file mode — original behaviour preserved
        print(f"\n🔍 NodeGuard — Local File Mode")
        print(f"Reviewing: {target}\n")
        
        os.makedirs("reports/local", exist_ok=True)
        code = load_code(target)
        review_single_file(target, code, "reports/local")
        print("\n✅ Done\n")

if __name__ == "__main__":
    main()