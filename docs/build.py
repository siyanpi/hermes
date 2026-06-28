#!/usr/bin/env python3
"""
应天周报门户 v2 — 4模块构建脚本
读取4个周报md文件 → 生成HTML网页（DOI/source可点击）→ 归档 → 部署
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

BRIEFING_DIR = Path("/Users/cc/Desktop/Hermes")
PORTAL_DIR = Path.home() / "Desktop/Infinitus/weekly_portal/docs"
ARCHIVE_DIR = PORTAL_DIR / "archive"
TEMPLATE_PATH = PORTAL_DIR / "template.html"

NOW = datetime.now()
WEEK_LABEL = NOW.strftime("%Y-W%U")
DATE_CN = NOW.strftime("%Y年%m月%d日")

BRIEFINGS = {
    "academic": {
        "id": "academic",
        "title": "抗衰老学术前沿",
        "subtitle": "线粒体 · 细胞衰老 · 中草药 · 表观遗传 · 检测工具",
        "icon": "🔬",
        "pattern": "briefing1_academic_",
        "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "file_label": "briefing1_academic",
    },
    "industry": {
        "id": "industry",
        "title": "抗衰老产业进展",
        "subtitle": "逆龄疗法 · 药物管线 · 产业融资 · 中草药产业 · 检测",
        "icon": "🏭",
        "pattern": "briefing2_industry_",
        "bg": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "file_label": "briefing2_industry",
    },
    "ai_aging": {
        "id": "ai_aging",
        "title": "AI × 抗衰老",
        "subtitle": "AI药物发现 · 衰老时钟 · 中草药AI · 蛋白质组学",
        "icon": "🤖",
        "pattern": "briefing3_AI_aging_",
        "bg": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "file_label": "briefing3_AI_aging",
    },
    "ai_apps": {
        "id": "ai_apps",
        "title": "AI 抗衰应用落地",
        "subtitle": "AI药物临床 · 长寿委员会 · 大模型 · 数字孪生 · 投融资",
        "icon": "⚡",
        "pattern": "briefing4_ai_apps_",
        "bg": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
        "file_label": "briefing4_ai_apps",
    },
}


def find_latest_briefing(pattern: str) -> Optional[Path]:
    files = sorted(BRIEFING_DIR.glob(f"{pattern}*.md"), reverse=True)
    return files[0] if files else None


def process_line_for_links(line: str) -> str:
    """Convert DOIs and URLs into clickable HTML links."""
    # DOI pattern: "DOI: 10.xxx/xxx" or "DOI:10.xxx/xxx"
    line = re.sub(
        r'DOI:?\s*(10\.\d{4,}/[^\s)\].,;]+)',
        r'<a href="https://doi.org/\1" target="_blank" class="source-link">DOI: \1</a>',
        line,
    )

    # URL pattern: bare https:// links
    line = re.sub(
        r'(https?://[^\s)\].,;]+)',
        r'<a href="\1" target="_blank" class="source-link">\1</a>',
        line,
    )

    # Source mentions: （来源：XXX）→ italicized
    line = re.sub(
        r'（(来源[：:].+?)）',
        r'<span class="source-ref">（\1）</span>',
        line,
    )

    return line


def md_to_html(content: str) -> str:
    """Convert markdown briefing to HTML with clickable links."""
    lines = content.split("\n")
    html_parts = []
    in_blockquote = False
    skip_header = True  # Skip the # title line

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Skip H1
        if line.startswith("# ") and skip_header:
            skip_header = False
            i += 1
            continue
        skip_header = False

        # H2 → section header
        if line.startswith("## "):
            section = line[3:].strip()
            # Strip emoji prefix for cleaner display
            html_parts.append(f'<div class="section"><h3>{section}</h3>')
            i += 1
            continue

        # H3 → item title, collect everything until next H2/H3 or end
        if line.startswith("### "):
            title = line[4:].strip()
            html_parts.append(f'<div class="item"><h4>{process_line_for_links(title)}</h4>')
            i += 1

            # Collect all content until next heading or separator
            body = []
            while i < len(lines):
                l = lines[i].rstrip()
                if l.startswith("## ") or l.startswith("### ") or l.startswith("---"):
                    break
                if l.strip():
                    body.append(process_line_for_links(l))
                i += 1

            if body:
                html_parts.append(f'<div class="body">{" ".join(f"<p>{b}</p>" for b in body)}</div>')
            html_parts.append("</div>")
            continue

        # Separator
        if line.startswith("---"):
            if in_blockquote:
                html_parts.append("</blockquote>")
                in_blockquote = False
            i += 1
            continue

        i += 1

    # Close last section
    html_parts.append("</div>")
    return "\n".join(html_parts)


def generate_archive_index() -> str:
    weeks = {}
    for f in sorted(ARCHIVE_DIR.glob("**/*.md"), reverse=True):
        week_dir = f.parent.name
        if week_dir not in weeks:
            weeks[week_dir] = []
        weeks[week_dir].append(f)

    if not weeks:
        return "<p class='empty'>暂无归档记录</p>"

    label_map = {
        "academic": "🔬 学术前沿",
        "industry": "🏭 产业进展",
        "ai_aging": "🤖 AI×抗衰老",
        "ai_apps": "⚡ AI应用落地",
    }

    html = '<div class="archive-list">'
    for week, files in sorted(weeks.items(), reverse=True):
        html += f'<div class="archive-week"><h4>📅 {week}</h4><ul>'
        for f in sorted(files):
            key = None
            for k in label_map:
                if k in f.stem:
                    key = k
                    break
            display = label_map.get(key, f.stem)
            rel_path = f.relative_to(PORTAL_DIR)
            html += f'<li><a href="{rel_path}">{display}</a></li>'
        html += "</ul></div>"
    html += "</div>"
    return html


def build():
    briefing_data = {}
    full_reports = []

    for key, cfg in BRIEFINGS.items():
        f = find_latest_briefing(cfg["pattern"])
        if f:
            content = f.read_text(encoding="utf-8")
            briefing_data[key] = {
                "config": cfg,
                "path": str(f),
                "filename": f.name,
                "html": md_to_html(content),
                "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d"),
            }
            full_reports.append((cfg["file_label"], f))

    # Copy full .md files to docs/ for deep-dive access
    for file_label, src_path in full_reports:
        dst_path = PORTAL_DIR / f"{file_label}.md"
        shutil.copy2(src_path, dst_path)
        print(f"📄 完整报告: {dst_path}")

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Fill modules
    for key, data in briefing_data.items():
        cfg = data["config"]
        md_file = f"{cfg['file_label']}.md"
        placeholder = f"<!-- {key}_module -->"

        card_html = f"""
        <div class="module-card" id="{cfg['id']}">
            <div class="module-header" style="background: {cfg['bg']}">
                <div class="module-icon">{cfg['icon']}</div>
                <div class="module-title-group">
                    <h2>{cfg['title']}</h2>
                    <span class="module-subtitle">{cfg['subtitle']} · {data['date']}</span>
                </div>
            </div>
            <div class="module-body">
                <a href="{md_file}" class="full-report-link" target="_blank">📄 查看完整报告</a>
                {data['html']}
            </div>
        </div>
        """
        template = template.replace(placeholder, card_html)

    archive_html = generate_archive_index()
    template = template.replace("<!-- archive -->", archive_html)
    template = template.replace("{{date}}", DATE_CN)
    template = template.replace("{{week}}", WEEK_LABEL)

    output_path = PORTAL_DIR / "index.html"
    output_path.write_text(template, encoding="utf-8")
    print(f"✅ 门户页面已生成: {output_path}")

    # Archive
    week_archive = ARCHIVE_DIR / WEEK_LABEL
    week_archive.mkdir(parents=True, exist_ok=True)
    for key, data in briefing_data.items():
        src = Path(data["path"])
        dst = week_archive / f"{key}_{src.name}"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"📁 已归档: {dst.name}")

    return str(output_path)


def deploy():
    import subprocess
    repo_dir = PORTAL_DIR.parent
    try:
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"weekly update {WEEK_LABEL} - {DATE_CN}"],
            cwd=repo_dir, capture_output=True,
        )
        result = subprocess.run(["git", "push"], cwd=repo_dir, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🚀 已部署到 https://siyanpi.github.io/hermes/")
        else:
            print(f"⚠️ 推送: {result.stderr}")
    except Exception as e:
        print(f"⚠️ 部署异常: {e}")


if __name__ == "__main__":
    build()
    deploy()
