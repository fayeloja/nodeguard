from datetime import datetime

def severity_color(severity: str) -> str:
    return {
        "HIGH": "#ef4444",
        "MEDIUM": "#f59e0b",
        "LOW": "#22c55e"
    }.get(severity.upper(), "#6b7280")

def severity_bg(severity: str) -> str:
    return {
        "HIGH": "#fef2f2",
        "MEDIUM": "#fffbeb",
        "LOW": "#f0fdf4"
    }.get(severity.upper(), "#f9fafb")

def extract_severity(report: str) -> str:
    for line in report.split("\n"):
        if "Overall Severity:" in line:
            if "HIGH" in line: return "HIGH"
            if "MEDIUM" in line: return "MEDIUM"
            if "LOW" in line: return "LOW"
    return "UNKNOWN"

def extract_section(report: str, heading: str) -> str:
    """Extract content under a markdown heading."""
    lines = report.split("\n")
    capturing = False
    result = []
    for line in lines:
        if line.strip().startswith("## " + heading):
            capturing = True
            continue
        if capturing and line.strip().startswith("## "):
            break
        if capturing:
            result.append(line)
    return "\n".join(result).strip()

def md_to_html(text: str) -> str:
    """Minimal markdown to HTML converter."""
    import re
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Numbered list items
    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if re.match(r'^\d+\.', stripped):
            if not in_list:
                html_lines.append("<ol>")
                in_list = True
            content = re.sub(r'^\d+\.\s*', '', stripped)
            html_lines.append(f"<li>{content}</li>")
        elif stripped.startswith("* ") or stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = stripped[2:]
            html_lines.append(f"<li>{content}</li>")
        else:
            if in_list:
                tag = "ol" if re.match(r'^\d+\.', lines[max(0,lines.index(line)-1)].strip()) else "ul"
                html_lines.append(f"</{tag}>")
                in_list = False
            if stripped:
                html_lines.append(f"<p>{stripped}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)

def build_file_card(file_report: dict, index: int) -> str:
    path = file_report["path"]
    report = file_report["report"]
    fixed = file_report.get("fixed", False)
    severity = extract_severity(report)
    color = severity_color(severity)
    bg = severity_bg(severity)

    summary = md_to_html(extract_section(report, "Summary"))
    critical = md_to_html(extract_section(report, "Critical Issues"))
    recommendations = md_to_html(extract_section(report, "Recommendations"))
    logic = md_to_html(extract_section(report, "Logic"))
    security = md_to_html(extract_section(report, "Security"))
    style = md_to_html(extract_section(report, "Style"))

    fixed_badge = """
        <span style="background:#dcfce7;color:#16a34a;padding:3px 10px;
        border-radius:20px;font-size:12px;font-weight:600;">
        🔧 Auto-fixed
        </span>""" if fixed else ""

    return f"""
    <div class="file-card" style="border-left: 4px solid {color}; background: {bg};">
        <div class="file-header" onclick="toggleCard({index})">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                <span class="file-icon">📄</span>
                <span class="file-path">{path}</span>
                {fixed_badge}
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <span class="severity-badge" style="background:{color};">{severity}</span>
                <span class="chevron" id="chevron-{index}">▼</span>
            </div>
        </div>

        <div class="file-body" id="body-{index}">
            <div class="section">
                <h4>📋 Summary</h4>
                {summary}
            </div>

            <div class="section">
                <h4>🚨 Critical Issues</h4>
                {critical if critical else "<p style='color:#6b7280'>None found.</p>"}
            </div>

            <div class="section">
                <h4>✅ Recommendations</h4>
                {recommendations}
            </div>

            <div class="tabs">
                <button class="tab active" onclick="switchTab(event, 'logic-{index}', {index})">Logic</button>
                <button class="tab" onclick="switchTab(event, 'security-{index}', {index})">Security</button>
                <button class="tab" onclick="switchTab(event, 'style-{index}', {index})">Style</button>
            </div>

            <div class="tab-content active" id="logic-{index}">{logic}</div>
            <div class="tab-content" id="security-{index}">{security}</div>
            <div class="tab-content" id="style-{index}">{style}</div>
        </div>
    </div>
    """

def generate_html_report(
    all_reports: list,
    summary: str,
    repo_url: str = "",
    output_path: str = "reports/nodeguard_report.html"
) -> str:

    repo_name = repo_url.rstrip("/").split("/")[-1] if repo_url else "Local Review"
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

    # Extract repo-level severity from summary
    repo_severity = "UNKNOWN"
    for line in summary.split("\n"):
        if "Repository Severity:" in line:
            if "HIGH" in line: repo_severity = "HIGH"
            elif "MEDIUM" in line: repo_severity = "MEDIUM"
            elif "LOW" in line: repo_severity = "LOW"

    repo_color = severity_color(repo_severity)

    # Stats
    severities = [extract_severity(r["report"]) for r in all_reports]
    high_count = severities.count("HIGH")
    medium_count = severities.count("MEDIUM")
    low_count = severities.count("LOW")
    fixed_count = sum(1 for r in all_reports if r.get("fixed"))

    # Build file cards
    cards_html = "\n".join([
        build_file_card(r, i) for i, r in enumerate(all_reports)
    ])

    # Extract summary sections
    overall_assessment = md_to_html(extract_section(summary, "Overall Assessment"))
    cross_cutting = md_to_html(extract_section(summary, "Top 5 Cross-Cutting Issues"))
    priority_order = md_to_html(extract_section(summary, "Priority Fix Order"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NodeGuard Report — {repo_name}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
  }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid #1e293b;
    padding: 32px 40px;
  }}
  .header-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .logo {{ display: flex; align-items: center; gap: 12px; }}
  .logo-icon {{
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
  }}
  .logo-text h1 {{ font-size: 22px; font-weight: 700; color: #f8fafc; }}
  .logo-text p {{ font-size: 13px; color: #94a3b8; margin-top: 2px; }}
  .repo-badge {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
    color: #94a3b8;
  }}
  .repo-badge strong {{ color: #f8fafc; }}
  .timestamp {{ font-size: 12px; color: #64748b; margin-top: 12px; }}

  /* Stats bar */
  .stats-bar {{
    background: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 20px 40px;
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
  }}
  .stat {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .stat-value {{
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
  }}
  .stat-label {{
    font-size: 12px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .repo-severity {{
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: #94a3b8;
  }}
  .repo-severity-badge {{
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 14px;
    color: white;
    background: {repo_color};
  }}

  /* Main layout */
  .main {{ display: flex; gap: 0; min-height: calc(100vh - 160px); }}

  /* Sidebar */
  .sidebar {{
    width: 300px;
    min-width: 300px;
    background: #1e293b;
    border-right: 1px solid #334155;
    padding: 24px;
    position: sticky;
    top: 0;
    height: calc(100vh - 160px);
    overflow-y: auto;
  }}
  .sidebar h3 {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 12px;
  }}
  .sidebar-section {{ margin-bottom: 28px; }}
  .summary-text {{ font-size: 13px; color: #94a3b8; line-height: 1.6; }}
  .summary-text p {{ margin-bottom: 8px; }}
  .cross-cutting {{ font-size: 13px; color: #94a3b8; line-height: 1.6; }}
  .cross-cutting ol, .cross-cutting ul {{
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .priority {{ font-size: 13px; color: #94a3b8; line-height: 1.6; }}
  .priority ol {{
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}

  /* Content area */
  .content {{ flex: 1; padding: 28px 32px; overflow-y: auto; }}
  .content-header {{
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    margin-bottom: 20px;
  }}

  /* File cards */
  .file-card {{
    background: white;
    border-radius: 10px;
    margin-bottom: 16px;
    overflow: hidden;
    color: #1e293b;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }}
  .file-header {{
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;
  }}
  .file-header:hover {{ background: rgba(0,0,0,0.04); }}
  .file-icon {{ font-size: 18px; }}
  .file-path {{
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
  }}
  .severity-badge {{
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
  }}
  .chevron {{
    font-size: 12px;
    color: #64748b;
    transition: transform 0.2s;
  }}
  .chevron.open {{ transform: rotate(180deg); }}

  .file-body {{
    display: none;
    padding: 0 20px 20px;
    border-top: 1px solid #f1f5f9;
  }}
  .file-body.open {{ display: block; }}

  .section {{ margin-top: 16px; }}
  .section h4 {{
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .section p {{ font-size: 14px; color: #374151; line-height: 1.6; margin-bottom: 6px; }}
  .section ol, .section ul {{
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .section li {{ font-size: 14px; color: #374151; line-height: 1.5; }}
  .section code {{
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
  }}

  /* Tabs */
  .tabs {{
    display: flex;
    gap: 4px;
    margin-top: 20px;
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 0;
  }}
  .tab {{
    padding: 8px 16px;
    border: none;
    background: none;
    font-size: 13px;
    font-weight: 500;
    color: #94a3b8;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: all 0.15s;
  }}
  .tab:hover {{ color: #374151; }}
  .tab.active {{ color: #3b82f6; border-bottom-color: #3b82f6; }}
  .tab-content {{ display: none; padding-top: 14px; }}
  .tab-content.active {{ display: block; }}
  .tab-content p {{ font-size: 14px; color: #374151; line-height: 1.6; margin-bottom: 6px; }}
  .tab-content ol, .tab-content ul {{
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .tab-content li {{ font-size: 14px; color: #374151; line-height: 1.5; }}
  .tab-content code {{
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
  }}

  code {{ font-family: 'SF Mono', 'Fira Code', monospace; }}
  strong {{ font-weight: 600; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-top">
    <div class="logo">
      <div class="logo-icon">🛡️</div>
      <div class="logo-text">
        <h1>NodeGuard</h1>
        <p>AI-Powered Code Review Pipeline</p>
      </div>
    </div>
    <div class="repo-badge">
      Repository: <strong>{repo_name}</strong>
    </div>
  </div>
  <div class="timestamp">Generated on {timestamp}</div>
</div>

<div class="stats-bar">
  <div class="stat">
    <span class="stat-value" style="color:#f8fafc">{len(all_reports)}</span>
    <span class="stat-label">Files Reviewed</span>
  </div>
  <div class="stat">
    <span class="stat-value" style="color:#ef4444">{high_count}</span>
    <span class="stat-label">High Severity</span>
  </div>
  <div class="stat">
    <span class="stat-value" style="color:#f59e0b">{medium_count}</span>
    <span class="stat-label">Medium Severity</span>
  </div>
  <div class="stat">
    <span class="stat-value" style="color:#22c55e">{low_count}</span>
    <span class="stat-label">Low Severity</span>
  </div>
  <div class="stat">
    <span class="stat-value" style="color:#3b82f6">{fixed_count}</span>
    <span class="stat-label">Auto-Fixed</span>
  </div>
  <div class="repo-severity">
    Repository Severity:
    <span class="repo-severity-badge">{repo_severity}</span>
  </div>
</div>

<div class="main">
  <aside class="sidebar">
    <div class="sidebar-section">
      <h3>Overall Assessment</h3>
      <div class="summary-text">{overall_assessment}</div>
    </div>
    <div class="sidebar-section">
      <h3>Cross-Cutting Issues</h3>
      <div class="cross-cutting">{cross_cutting}</div>
    </div>
    <div class="sidebar-section">
      <h3>Priority Fix Order</h3>
      <div class="priority">{priority_order}</div>
    </div>
  </aside>

  <div class="content">
    <div class="content-header">{len(all_reports)} files reviewed</div>
    {cards_html}
  </div>
</div>

<script>
  function toggleCard(index) {{
    const body = document.getElementById('body-' + index);
    const chevron = document.getElementById('chevron-' + index);
    body.classList.toggle('open');
    chevron.classList.toggle('open');
  }}

  function switchTab(event, tabId, cardIndex) {{
    // Deactivate all tabs and contents in this card
    const card = event.target.closest('.file-card');
    card.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    card.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    // Activate clicked
    event.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');
  }}

  // Open first card by default
  toggleCard(0);
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path