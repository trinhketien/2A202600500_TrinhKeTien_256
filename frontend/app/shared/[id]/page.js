"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SharedPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;
    fetch(`${API}/api/share/${id}`)
      .then((r) => {
        if (!r.ok) throw new Error("Link không tồn tại");
        return r.json();
      })
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [id]);

  if (loading) {
    return (
      <div className="shared-container">
        <div className="loading-card">⏳ Đang tải...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="shared-container">
        <div className="error-card">❌ {error}</div>
      </div>
    );
  }

  const report = data.report_card;
  const agentInfo = {
    market: { icon: "📊", display: "Thị Trường" },
    strategy: { icon: "🎯", display: "Chiến Lược" },
    finance: { icon: "💰", display: "Tài Chính" },
    technical: { icon: "⚙️", display: "Kỹ Thuật" },
    legal: { icon: "⚖️", display: "Pháp Lý" },
    moderator: { icon: "🏛️", display: "Tổng Kết" },
  };

  return (
    <div className="shared-container">
      <div className="shared-header">
        <h1>Cố Vấn Khởi Nghiệp AI</h1>
        <p>Chia sẻ bởi {data.shared_by}</p>
      </div>

      <div className="idea-display">
        <span className="idea-label">💡 Ý tưởng</span>
        <span className="idea-text-shared">{data.idea}</span>
        {data.industry && <span className="industry-tag">{data.industry}</span>}
      </div>

      {/* Agent messages */}
      {data.messages.map((msg, i) => {
        if (msg.agent_name === "user") return null;
        const info = agentInfo[msg.agent_name] || { icon: "💬", display: msg.agent_display };
        return (
          <div key={i} className={`agent-card ${msg.agent_name === "moderator" ? "moderator-card" : ""}`}>
            <div className="agent-header">
              <div className={`agent-icon ${msg.agent_name}`}>{info.icon}</div>
              <div className="agent-name">{info.display}</div>
            </div>
            <div className="agent-content" dangerouslySetInnerHTML={{ __html: formatMd(msg.content || "") }} />
          </div>
        );
      })}

      {/* Report Card (read-only) */}
      {report && (
        <div className="report-card">
          <h3>📋 Report Card</h3>
          <div style={{ display: "flex", justifyContent: "center", gap: "16px", flexWrap: "wrap", margin: "16px 0" }}>
            <div className={`score-badge ${report.overall_score >= 7 ? "score-high" : report.overall_score >= 5 ? "score-mid" : "score-low"}`}>
              <span className="score-value">{report.overall_score}</span>
              <span className="score-label">/10</span>
            </div>
            <div className={`recommendation-badge ${report.recommendation === "Go" ? "rec-go" : report.recommendation === "Pivot" ? "rec-pivot" : "rec-nogo"}`}>
              {report.recommendation === "Go" ? "🚀 GO" : report.recommendation === "Pivot" ? "🔄 PIVOT" : "🛑 NO-GO"}
            </div>
          </div>

          {/* Category scores */}
          <div className="category-scores" style={{ maxWidth: "400px", margin: "0 auto" }}>
            {Object.entries(report.category_scores || {}).map(([cat, score]) => (
              <div key={cat} className="score-category">
                <span className="cat-name">
                  {cat === "market" ? "📊 Thị Trường" : cat === "strategy" ? "🎯 Chiến Lược" :
                   cat === "finance" ? "💰 Tài Chính" : cat === "technical" ? "⚙️ Kỹ Thuật" : "⚖️ Pháp Lý"}
                </span>
                <div className="score-bar-track"><div className="score-bar-fill" style={{ width: `${score * 10}%` }} /></div>
                <span className="cat-score">{score}</span>
              </div>
            ))}
          </div>

          {/* Strengths & Weaknesses */}
          <div className="sw-grid" style={{ marginTop: "20px" }}>
            <div className="sw-col">
              <h4>✅ Điểm Mạnh</h4>
              {report.strengths?.map((s, i) => <div key={i} className="strength-item">✓ {s}</div>)}
            </div>
            <div className="sw-col">
              <h4>⚠️ Điểm Yếu</h4>
              {report.weaknesses?.map((w, i) => <div key={i} className="weakness-item">✗ {w}</div>)}
            </div>
          </div>
        </div>
      )}

      <div className="shared-footer">
        <a href="/">← Tạo phân tích của bạn</a>
      </div>
    </div>
  );
}

function formatMd(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/### (.+)/g, "<h3>$1</h3>").replace(/## (.+)/g, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^\- (.+)/gm, "• $1").replace(/\n/g, "<br/>");
}
