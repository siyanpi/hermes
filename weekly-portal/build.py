#!/usr/bin/env python3
"""
应天周报门户 — 构建脚本
读取3个周报md文件 → 生成HTML网页 → 归档旧文件
"""

import os
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

BRIEFING_DIR = Path.home() / "Desktop/Infinitus/weekly_briefings"
PORTAL_DIR = Path.home() / "Desktop/Infinitus/weekly_portal"
ARCHIVE_DIR = PORTAL_DIR / "archive"

NOW = datetime.now()
WEEK_LABEL = NOW.strftime("%Y-W%U")
DATE_CN = NOW.strftime("%Y年%m月%d日")

BRIEFINGS = {
    "academic": {
        "id": "academic",
        "title": "抗衰老学术前沿",
        "subtitle": "药物 · 食品 · 中草药 · 化妆品 · 检测",
        "icon": "🔬",
        "color": "#1a5276",
        "pattern": "briefing1_academic_",
        "bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    },
    "industry": {
        "id": "industry",
        "title": "抗衰老产业进展",
        "subtitle": "长寿诊所 · 药物管线 · 保健品 · 中草药产业",
        "icon": "🏭",
        "color": "#0e6655",
        "pattern": "briefing2_industry_",
        "bg": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
    },
    "ai": {
        "id": "ai",
        "title": "AI × 抗衰老",
        "subtitle": "学术前沿 + 产业落地 · 中草药AI · 大模型抗衰",
        "icon": "🤖",
        "color": "#6c3483",
        "pattern": "briefing3_ai_aging_",
        "bg": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    },
}


from typing import Optional

def find_latest_briefing(pattern: str) -> Optional[Path]:
    """Find the most recent briefing file matching pattern."""
    files = sorted(BRIEFING_DIR.glob(f"{pattern}*.md"), reverse=True)
    return files[0] if files else None


def md_to_html_sections(md_text: str) -> str:
    """Convert markdown briefing to HTML sections."""
    lines = md_text.split("\n")
    sections = []
    current_section = None
    current_items = []

    for line in lines:
        line = line.rstrip()

        # H1 → skip (already in page header)
        if line.startswith("# "):
            continue

        # H2 → start new section
        if line.startswith("## "):
            if current_section and current_items:
                sections.append((current_section, current_items))
            current_section = line[3:].strip()
            current_items = []
            continue

        # H3 → new item
        if line.startswith("### "):
            current_items.append({"title": line[4:].strip(), "lines": []})
            continue

        # Collect lines for current item
        if current_items:
            current_items[-1]["lines"].append(line)

    if current_section and current_items:
        sections.append((current_section, current_items))

    # Build HTML
    html_parts = []
    for section_title, items in sections:
        # Skip calibration footer and empty sections
        if "校准" in section_title or "✅" in section_title:
            continue
        if not items:
            continue

        html_parts.append(f'<div class="section"><h3>{section_title}</h3>')

        for item in items:
            title = item["title"]
            html_parts.append(f'<div class="item"><h4>{title}</h4>')

            body_lines = []
            source_link = ""
            meta_info = ""

            for l in item["lines"]:
                stripped = l.strip()
                if not stripped:
                    continue
                if stripped.startswith("来源：") or stripped.startswith("[来源]"):
                    # Extract URL
                    url_match = re.search(r"https?://[^\s)\]]+", stripped)
                    if url_match:
                        source_link = url_match.group(0)
                elif stripped.startswith("对标：") or stripped.startswith("证据等级") or stripped.startswith("落地") or stripped.startswith("相关方向"):
                    meta_info += f'<span class="meta">{stripped}</span> '
                elif stripped.startswith("- "):
                    body_lines.append(f"<li>{stripped[2:]}</li>")
                else:
                    body_lines.append(f"<p>{stripped}</p>")

            if body_lines:
                html_parts.append(f'<div class="body">{"".join(body_lines)}</div>')
            if meta_info:
                html_parts.append(f'<div class="meta-row">{meta_info}</div>')
            if source_link:
                html_parts.append(
                    f'<a href="{source_link}" target="_blank" class="source-link">📎 查看来源</a>'
                )

            html_parts.append("</div>")  # close item

        html_parts.append("</div>")  # close section

    return "\n".join(html_parts)


def generate_archive_index() -> str:
    """Generate archive listing HTML."""
    # Group archived files by week
    weeks = {}
    for f in sorted(ARCHIVE_DIR.glob("**/*.md"), reverse=True):
        week_dir = f.parent.name
        if week_dir not in weeks:
            weeks[week_dir] = []
        weeks[week_dir].append(f)

    if not weeks:
        return "<p class='empty'>暂无归档记录</p>"

    html = '<div class="archive-list">'
    for week, files in sorted(weeks.items(), reverse=True):
        html += f'<div class="archive-week"><h4>📅 {week}</h4><ul>'
        for f in sorted(files):
            label = {
                "academic": "🔬 学术前沿",
                "industry": "🏭 产业进展",
                "ai": "🤖 AI×抗衰老",
            }
            key = None
            for k in label:
                if k in f.stem:
                    key = k
                    break
            display = label.get(key, f.stem)
            rel_path = f.relative_to(PORTAL_DIR)
            html += f'<li><a href="{rel_path}">{display}</a></li>'
        html += "</ul></div>"
    html += "</div>"
    return html


def build():
    """Main build function."""
    briefing_html = {}

    for key, cfg in BRIEFINGS.items():
        f = find_latest_briefing(cfg["pattern"])
        if f:
            content = f.read_text(encoding="utf-8")
            briefing_html[key] = {
                "config": cfg,
                "path": str(f),
                "html": md_to_html_sections(content),
                "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m/%d"),
            }

    # Read the HTML template
    template = (PORTAL_DIR / "template.html").read_text(encoding="utf-8")

    # Fill in modules
    for key, data in briefing_html.items():
        cfg = data["config"]
        placeholder = f"<!-- {key}_module -->" if f"<!-- {key}_module -->" in template else None
        if not placeholder:
            continue

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
                {data['html']}
            </div>
        </div>
        """
        template = template.replace(f"<!-- {key}_module -->", card_html)

    # Archive section
    archive_html = generate_archive_index()
    template = template.replace("<!-- archive -->", archive_html)

    # Date
    template = template.replace("{{date}}", DATE_CN)
    template = template.replace("{{week}}", WEEK_LABEL)

    # Write output
    output_path = PORTAL_DIR / "index.html"
    output_path.write_text(template, encoding="utf-8")
    print(f"✅ 门户页面已生成: {output_path}")

    # Archive current files
    week_archive = ARCHIVE_DIR / WEEK_LABEL
    week_archive.mkdir(parents=True, exist_ok=True)

    for key, data in briefing_html.items():
        src = Path(data["path"])
        dst = week_archive / f"{key}_{src.name}"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"📁 已归档: {dst.name}")

    return str(output_path)


if __name__ == "__main__":
    build()
