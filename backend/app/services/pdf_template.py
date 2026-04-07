"""
PDF Template — HTML + inline CSS cho Playwright render.

Thiết kế chuyên nghiệp, hỗ trợ tiếng Việt, SVG radar chart inline.
"""

import html
from datetime import datetime


def render_pdf_template(session_data: dict) -> str:
    """
    Render HTML template từ session data.

    Args:
        session_data: {idea, industry, messages, report_card, created_at}

    Returns:
        str: HTML string
    """
    idea = html.escape(session_data.get("idea", ""))
    industry = html.escape(session_data.get("industry", "") or "Chưa chọn")
    messages = session_data.get("messages", [])
    report = session_data.get("report_card") or {}
    created = session_data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Build agent sections
    agent_sections = ""
    agent_icons = {
        "market": "📊", "strategy": "🎯", "finance": "💰",
        "technical": "⚙️", "legal": "⚖️", "moderator": "🏛️",
    }
    agent_names = {
        "market": "Thị Trường", "strategy": "Chiến Lược", "finance": "Tài Chính",
        "technical": "Kỹ Thuật", "legal": "Pháp Lý", "moderator": "Tổng Kết",
    }

    for msg in messages:
        name = msg.get("agent_name", "")
        if name == "user":
            continue
        icon = agent_icons.get(name, "💬")
        display = agent_names.get(name, name)
        content = _format_content(msg.get("content", ""))
        is_mod = name == "moderator"

        agent_sections += f"""
        <div class="agent-section {'moderator-section' if is_mod else ''}">
            <div class="agent-header-pdf">
                <span class="agent-icon-pdf">{icon}</span>
                <span class="agent-title-pdf">{display}</span>
            </div>
            <div class="agent-body-pdf">{content}</div>
        </div>
        """

    # Build report card section
    report_section = ""
    if report:
        overall = report.get("overall_score", 0)
        scores = report.get("category_scores", {})
        rec = report.get("recommendation", "Pivot")
        strengths = report.get("strengths", [])
        weaknesses = report.get("weaknesses", [])
        checklist = report.get("legal_checklist", [])

        rec_color = "#10b981" if rec == "Go" else "#f59e0b" if rec == "Pivot" else "#ef4444"
        rec_icon = "🚀" if rec == "Go" else "🔄" if rec == "Pivot" else "🛑"

        # SVG Radar chart
        radar_svg = _build_radar_svg(scores)

        # Score bars
        score_bars = ""
        cat_labels = {"market": "📊 Thị Trường", "strategy": "🎯 Chiến Lược",
                      "finance": "💰 Tài Chính", "technical": "⚙️ Kỹ Thuật", "legal": "⚖️ Pháp Lý"}
        for cat, label in cat_labels.items():
            val = scores.get(cat, 5)
            pct = val * 10
            score_bars += f"""
            <div class="score-row">
                <span class="score-label-pdf">{label}</span>
                <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
                <span class="score-num">{val}</span>
            </div>
            """

        # Strengths & weaknesses
        sw_html = '<div class="sw-container">'
        sw_html += '<div class="sw-col-pdf"><h4>✅ Điểm Mạnh</h4>'
        for s in strengths:
            sw_html += f'<div class="str-item">✓ {html.escape(s)}</div>'
        sw_html += '</div><div class="sw-col-pdf"><h4>⚠️ Điểm Yếu</h4>'
        for w in weaknesses:
            sw_html += f'<div class="weak-item">✗ {html.escape(w)}</div>'
        sw_html += '</div></div>'

        # Legal checklist
        legal_html = ""
        if checklist:
            legal_html = '<h4 style="margin-top:16px">⚖️ Checklist Pháp Lý</h4><table class="legal-table">'
            legal_html += '<tr><th>Yêu cầu</th><th>Loại</th><th>Trạng thái</th></tr>'
            for item in checklist:
                legal_html += f'<tr><td>{html.escape(item.get("item",""))}</td><td>{html.escape(item.get("type",""))}</td><td>☐ Cần xác minh</td></tr>'
            legal_html += '</table>'

        report_section = f"""
        <div class="report-section">
            <h2>📋 Report Card</h2>
            <div class="report-grid">
                <div class="radar-col">{radar_svg}</div>
                <div class="scores-col">
                    <div class="overall-badge" style="background:{rec_color}">
                        <span class="overall-num">{overall}</span><span class="overall-label">/10</span>
                    </div>
                    <div class="rec-badge" style="border-color:{rec_color};color:{rec_color}">
                        {rec_icon} {rec}
                    </div>
                    {score_bars}
                </div>
            </div>
            {sw_html}
            {legal_html}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a2e; line-height: 1.6; font-size: 11px; }}
.header {{ background: linear-gradient(135deg, #6366f1, #818cf8); color: white; padding: 24px 32px; }}
.header h1 {{ font-size: 20px; margin-bottom: 4px; }}
.header p {{ opacity: 0.85; font-size: 11px; }}
.content {{ padding: 24px 32px; }}
.idea-box {{ background: #f8f9ff; border: 1px solid #e0e1eb; border-radius: 8px; padding: 16px; margin-bottom: 20px; }}
.idea-box h3 {{ color: #6366f1; font-size: 12px; margin-bottom: 6px; }}
.idea-text {{ font-size: 13px; font-weight: 600; }}
.industry-tag {{ display: inline-block; background: #6366f1; color: white; padding: 2px 10px; border-radius: 12px; font-size: 10px; margin-top: 6px; }}
.agent-section {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 12px; page-break-inside: avoid; }}
.moderator-section {{ border-color: #6366f1; background: #fafafe; }}
.agent-header-pdf {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; font-weight: 700; font-size: 12px; color: #374151; }}
.agent-icon-pdf {{ font-size: 16px; }}
.agent-body-pdf {{ font-size: 11px; color: #4b5563; white-space: pre-wrap; }}
.agent-body-pdf h3 {{ font-size: 12px; color: #1f2937; margin: 10px 0 4px; }}
.agent-body-pdf strong {{ color: #1f2937; }}
.report-section {{ border: 2px solid #6366f1; border-radius: 10px; padding: 20px; margin-top: 20px; page-break-inside: avoid; }}
.report-section h2 {{ text-align: center; color: #6366f1; font-size: 16px; margin-bottom: 16px; }}
.report-grid {{ display: flex; gap: 24px; align-items: flex-start; }}
.radar-col {{ flex: 0 0 180px; }}
.scores-col {{ flex: 1; text-align: center; }}
.overall-badge {{ display: inline-flex; align-items: baseline; gap: 2px; padding: 8px 20px; border-radius: 10px; color: white; }}
.overall-num {{ font-size: 32px; font-weight: 800; line-height: 1; }}
.overall-label {{ font-size: 14px; opacity: 0.8; }}
.rec-badge {{ display: inline-block; margin-top: 8px; padding: 4px 16px; border: 2px solid; border-radius: 20px; font-weight: 700; font-size: 12px; }}
.score-row {{ display: flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 10px; }}
.score-label-pdf {{ width: 100px; text-align: left; font-weight: 600; }}
.bar-track {{ flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, #6366f1, #818cf8); border-radius: 3px; }}
.score-num {{ width: 24px; text-align: right; font-weight: 700; color: #6366f1; }}
.sw-container {{ display: flex; gap: 16px; margin-top: 16px; }}
.sw-col-pdf {{ flex: 1; }}
.sw-col-pdf h4 {{ font-size: 11px; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #e5e7eb; }}
.str-item {{ padding: 3px 8px; margin-bottom: 4px; background: rgba(16,185,129,0.08); border-left: 3px solid #10b981; font-size: 10px; }}
.weak-item {{ padding: 3px 8px; margin-bottom: 4px; background: rgba(239,68,68,0.08); border-left: 3px solid #ef4444; font-size: 10px; }}
.legal-table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
.legal-table th {{ text-align: left; padding: 6px 8px; background: #f0f1ff; color: #6366f1; font-weight: 600; border-bottom: 2px solid #e5e7eb; }}
.legal-table td {{ padding: 6px 8px; border-bottom: 1px solid #f3f4f6; }}
.footer {{ text-align: center; padding: 16px; color: #9ca3af; font-size: 9px; border-top: 1px solid #e5e7eb; margin-top: 24px; }}
</style>
</head>
<body>
    <div class="header">
        <h1>Cố Vấn Khởi Nghiệp AI</h1>
        <p>Báo cáo phân tích ý tưởng · {created}</p>
    </div>
    <div class="content">
        <div class="idea-box">
            <h3>💡 Ý tưởng kinh doanh</h3>
            <div class="idea-text">{idea}</div>
            <span class="industry-tag">{industry}</span>
        </div>
        <h2 style="font-size:14px;margin-bottom:12px;color:#374151">🎯 Phân tích từ Hội đồng Cố vấn</h2>
        {agent_sections}
        {report_section}
    </div>
    <div class="footer">
        Cố Vấn Khởi Nghiệp AI — covankn.ai · Báo cáo tự động · {created}
    </div>
</body>
</html>"""


def _format_content(text: str) -> str:
    """Format markdown → HTML cho PDF."""
    if not text:
        return ""
    text = html.escape(text)
    text = text.replace("### ", "<h3>").replace("\n", "<br>")
    text = text.replace("**", "<strong>", 1)
    # Simple bold pairs
    import re
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def _build_radar_svg(scores: dict) -> str:
    """Build SVG radar chart (inline) cho PDF."""
    import math

    categories = ["market", "strategy", "finance", "technical", "legal"]
    labels = ["📊", "🎯", "💰", "⚙️", "⚖️"]
    cx, cy, r = 80, 80, 60
    n = 5

    def get_point(idx, val, max_r=r):
        angle = (math.pi * 2 * idx) / n - math.pi / 2
        radius = (val / 10) * max_r
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    # Grid
    grid = ""
    for level in [2, 4, 6, 8, 10]:
        pts = " ".join(f"{get_point(i, level)[0]:.1f},{get_point(i, level)[1]:.1f}" for i in range(n))
        grid += f'<polygon points="{pts}" fill="none" stroke="#e5e7eb" stroke-width="0.5"/>'

    # Axes
    axes = ""
    for i in range(n):
        ex, ey = get_point(i, 10)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#e5e7eb" stroke-width="0.5"/>'

    # Data
    data_pts = []
    for i, cat in enumerate(categories):
        val = scores.get(cat, 5)
        px, py = get_point(i, val)
        data_pts.append(f"{px:.1f},{py:.1f}")

    data_polygon = " ".join(data_pts)

    # Dots
    dots = ""
    for pt in data_pts:
        x, y = pt.split(",")
        dots += f'<circle cx="{x}" cy="{y}" r="2.5" fill="#6366f1"/>'

    # Labels
    label_texts = ""
    for i, lbl in enumerate(labels):
        lx, ly = get_point(i, 13)
        label_texts += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="10">{lbl}</text>'

    return f"""<svg viewBox="0 0 160 160" width="160" height="160" xmlns="http://www.w3.org/2000/svg">
{grid}{axes}
<polygon points="{data_polygon}" fill="rgba(99,102,241,0.2)" stroke="#6366f1" stroke-width="1.5"/>
{dots}{label_texts}
</svg>"""
