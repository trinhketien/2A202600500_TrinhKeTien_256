"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken, getUser, createDebateStream, createReplyStream } from "./lib/api";

/* Thông tin các agents */
const AGENTS = [
  { name: "market",    icon: "📊", display: "Thị Trường",  color: "market" },
  { name: "strategy",  icon: "🎯", display: "Chiến Lược",  color: "strategy" },
  { name: "finance",   icon: "💰", display: "Tài Chính",   color: "finance" },
  { name: "technical", icon: "⚙️", display: "Kỹ Thuật",   color: "technical" },
  { name: "legal",     icon: "⚖️", display: "Pháp Lý",    color: "legal" },
  { name: "moderator", icon: "🏛️", display: "Tổng Kết",   color: "moderator" },
];

/* Ngành nghề phổ biến */
const INDUSTRIES = [
  "", "F&B", "Tech / SaaS", "E-commerce", "Giáo dục / Edtech",
  "Tài chính / Fintech", "Y tế / Healthtech", "Bất động sản",
  "Du lịch", "Logistics", "Nông nghiệp", "Khác",
];

const TIER_LIMITS = {
  free: { max_rounds: 1, can_export_pdf: false, can_share: false },
  pro: { max_rounds: 2, can_export_pdf: false, can_share: true },
  premium: { max_rounds: 3, can_export_pdf: true, can_share: true },
};

export default function HomePage() {
  const [idea, setIdea] = useState("");
  const [industry, setIndustry] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [currentRound, setCurrentRound] = useState(1);
  const [responses, setResponses] = useState([]); // [{round, type, ...}]
  const [currentAgent, setCurrentAgent] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const [totalTokens, setTotalTokens] = useState(0);
  const [totalCost, setTotalCost] = useState(0);
  const [replyText, setReplyText] = useState("");
  const [clarification, setClarification] = useState(null); // {questions: [...]}
  const [clarAnswers, setClarAnswers] = useState({});       // {0: "...", 1: "..."}
  const [memoryInfo, setMemoryInfo] = useState(null);       // {memories_found, total_memories}
  const [reportCard, setReportCard] = useState(null);       // report card data
  const [shareToast, setShareToast] = useState(null);       // toast message
  const bottomRef = useRef(null);
  const eventSourceRef = useRef(null);
  const router = useRouter();

  // Tier-aware limits
  const user = typeof window !== "undefined" ? getUser() : null;
  const userTier = user?.tier || "free";
  const tierLimits = TIER_LIMITS[userTier] || TIER_LIMITS.free;
  const MAX_ROUNDS = tierLimits.max_rounds;

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, []);

  /* Auto-scroll to bottom */
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [responses, currentAgent, clarification]);

  /* ── Wire SSE events ──────────────────────────────── */
  function wireSSE(es, round) {
    es.addEventListener("session", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.session_id) setSessionId(data.session_id);
        if (data.round_number) setCurrentRound(data.round_number);
      } catch {}
    });

    es.addEventListener("memory", (e) => {
      try {
        const data = JSON.parse(e.data);
        setMemoryInfo(data);
      } catch {}
    });

    es.addEventListener("agent", (e) => {
      try {
        const data = JSON.parse(e.data);
        setResponses((prev) => [...prev, { ...data, round }]);
        setTotalTokens((t) => t + (data.tokens_used || 0));
        setTotalCost((c) => c + (data.cost_usd || 0));

        const idx = AGENTS.findIndex((a) => a.name === data.agent_name);
        if (idx < AGENTS.length - 1) setCurrentAgent(AGENTS[idx + 1].name);
      } catch {}
    });

    es.addEventListener("summary", (e) => {
      try {
        const data = JSON.parse(e.data);
        setResponses((prev) => [...prev, { ...data, round }]);
        if (data.total_tokens) setTotalTokens(data.total_tokens);
        if (data.total_cost) setTotalCost(data.total_cost);
        setCurrentAgent(null);
        setIsStreaming(false);
        setCurrentRound(round);
        // KHÔNG close ở đây — chờ report_card event (gửi sau summary)
        // Fallback: nếu report_card không tới trong 5s → close
        setTimeout(() => {
          if (es.readyState !== EventSource.CLOSED) {
            es.close();
          }
        }, 5000);
      } catch {}
    });

    es.addEventListener("report_card", (e) => {
      try {
        const data = JSON.parse(e.data);
        setReportCard(data);
      } catch {}
      // Report card là event cuối cùng → close connection
      es.close();
    });

    es.addEventListener("clarification", (e) => {
      try {
        const data = JSON.parse(e.data);
        setClarification(data);
        setIsStreaming(false);
        setCurrentAgent(null);
        es.close();
      } catch {}
    });

    es.addEventListener("error", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.error) {
          if (data.error.includes("Token") || data.error.includes("hết hạn")) {
            setError("Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.");
            setIsStreaming(false);
            es.close();
            return;
          }
          setResponses((prev) => [...prev, { type: "error", round, ...data }]);
        }
        if (data.done) {
          setIsStreaming(false);
          setCurrentAgent(null);
          es.close();
        }
      } catch {
        setError("Mất kết nối. Thử lại.");
        setIsStreaming(false);
        es.close();
      }
    });

    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) {
        setIsStreaming(false);
        setCurrentAgent(null);
      }
    };
  }

  /* ── Bắt đầu debate vòng 1 ────────────────────────── */
  function startDebate(overrideIdea) {
    const finalIdea = overrideIdea || idea.trim();
    if (!finalIdea || finalIdea.length < 5) {
      setError("Vui lòng nhập ý tưởng (tối thiểu 5 ký tự)");
      return;
    }

    setError("");
    setResponses([]);
    setCurrentAgent("market");
    setIsStreaming(true);
    setTotalTokens(0);
    setTotalCost(0);
    setCurrentRound(1);
    setSessionId(null);
    setClarification(null);
    setClarAnswers({});
    setReplyText("");
    setMemoryInfo(null);
    setReportCard(null);

    const token = getToken();
    const es = createDebateStream(finalIdea, industry || null, token);
    eventSourceRef.current = es;
    wireSSE(es, 1);
  }

  /* ── Gửi phản biện (vòng 2, 3) ────────────────────── */
  function sendReply() {
    if (!replyText.trim() || replyText.trim().length < 5) {
      setError("Phản biện tối thiểu 5 ký tự");
      return;
    }
    if (!sessionId) {
      setError("Không tìm thấy phiên. Thử lại.");
      return;
    }

    setError("");
    setCurrentAgent("market");
    setIsStreaming(true);
    const nextRound = currentRound + 1;

    // Thêm user reply vào responses (hiển thị trên UI)
    setResponses((prev) => [
      ...prev,
      {
        type: "user-reply",
        agent_name: "user",
        agent_display: "💬 Phản biện",
        content: replyText.trim(),
        round: nextRound,
      },
    ]);

    const token = getToken();
    const es = createReplyStream(sessionId, replyText.trim(), token);
    eventSourceRef.current = es;
    wireSSE(es, nextRound);
    setReplyText("");
  }

  /* ── Gửi clarification answers ────────────────────── */
  function submitClarification() {
    const answers = Object.values(clarAnswers).filter(Boolean);
    if (answers.length === 0) {
      setError("Vui lòng trả lời ít nhất 1 câu");
      return;
    }

    // Ghép idea + answers
    let enrichedIdea = idea.trim();
    clarification.questions.forEach((q, i) => {
      const ans = clarAnswers[i];
      if (ans) enrichedIdea += `\n${q}: ${ans}`;
    });

    setClarification(null);
    setClarAnswers({});
    setIdea(enrichedIdea);
    startDebate(enrichedIdea);
  }

  function stopDebate() {
    if (eventSourceRef.current) eventSourceRef.current.close();
    setIsStreaming(false);
    setCurrentAgent(null);
  }

  /* ── Tính progress vòng hiện tại ───────────────────── */
  const activeRound = isStreaming ? (currentRound + (responses.some(r => r.round > currentRound) ? 1 : 0)) : currentRound;
  const roundResponses = responses.filter(
    (r) => r.round === (isStreaming ? activeRound : currentRound) &&
           (r.type === "agent" || r.type === "summary")
  );
  const doneCount = roundResponses.length;
  const progressPct = (doneCount / 6) * 100;

  /* ── Nhóm responses theo round ─────────────────────── */
  const rounds = [];
  const allRounds = [...new Set(responses.map((r) => r.round))].sort();
  for (const rnd of allRounds) {
    rounds.push({
      round: rnd,
      items: responses.filter((r) => r.round === rnd),
    });
  }

  /* ── Done & can reply? ─────────────────────────────── */
  const isCompleted = !isStreaming && responses.some((r) => r.type === "summary");
  const canReply = isCompleted && currentRound < MAX_ROUNDS && sessionId;

  function getAgentInfo(name) {
    if (name === "user") return { icon: "💬", display: "Phản biện", color: "user" };
    return AGENTS.find((a) => a.name === name) || { icon: "💬", display: name, color: "" };
  }

  return (
    <div className="app-container">
      {/* Hero */}
      <div className="hero">
        <h1>Phân tích ý tưởng khởi nghiệp</h1>
        <p>
          5 chuyên gia AI tranh luận realtime — Thị Trường, Chiến Lược,
          Tài Chính, Kỹ Thuật, Pháp Lý — cho bạn góc nhìn 360°.
        </p>
      </div>

      {/* Idea Form */}
      <div className="idea-form">
        <div className="form-group" style={{ marginBottom: 0 }}>
          <textarea
            id="idea-input"
            className="form-textarea"
            placeholder="Mô tả ý tưởng kinh doanh... VD: Mở quán trà sữa healthy cho gymer tại TP.HCM, target Gen Z, giá 35-55k/ly"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            disabled={isStreaming || responses.length > 0}
            rows={4}
          />
        </div>

        <div className="idea-form-row">
          <select
            id="industry-select"
            className="form-select"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            disabled={isStreaming || responses.length > 0}
          >
            <option value="">Chọn ngành (tùy chọn)</option>
            {INDUSTRIES.filter(Boolean).map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>

          {responses.length === 0 && !isStreaming ? (
            <button
              id="start-debate-btn"
              className="btn btn-primary btn-lg"
              onClick={() => startDebate()}
              disabled={!idea.trim()}
            >
              🚀 Phân tích ý tưởng
            </button>
          ) : isStreaming ? (
            <button className="btn btn-danger btn-lg" onClick={stopDebate}>
              ⏹ Dừng lại
            </button>
          ) : (
            <button
              className="btn btn-ghost btn-lg"
              onClick={() => {
                setResponses([]);
                setSessionId(null);
                setCurrentRound(1);
                setIdea("");
                setIndustry("");
                setReplyText("");
                setClarification(null);
              }}
            >
              🔄 Phiên mới
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ maxWidth:700, margin:"0 auto 16px" }}>{error}</div>}

      {/* Clarification card (Bước 6) */}
      {clarification && (
        <div className="debate-area">
          <div className="clarification-card">
            <h3>🤔 Cần bổ sung thông tin</h3>
            <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", marginBottom: 16 }}>
              Ý tưởng cần thêm chi tiết để phân tích chính xác hơn:
            </p>
            {clarification.questions.map((q, i) => (
              <div key={i} className="clarification-question">
                <label>{q}</label>
                <input
                  className="form-input"
                  placeholder="Nhập câu trả lời..."
                  value={clarAnswers[i] || ""}
                  onChange={(e) => setClarAnswers({ ...clarAnswers, [i]: e.target.value })}
                />
              </div>
            ))}
            <div className="clarification-actions">
              <button className="btn btn-ghost" onClick={() => { setClarification(null); startDebate(); }}>
                Bỏ qua, phân tích luôn
              </button>
              <button className="btn btn-primary" onClick={submitClarification}>
                Tiếp tục phân tích →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Debate Area */}
      {(isStreaming || responses.length > 0) && !clarification && (
        <div className="debate-area">
          {/* Memory badge */}
          {memoryInfo && memoryInfo.memories_found > 0 && (
            <div className="memory-badge" style={{
              textAlign: "center",
              padding: "8px 16px",
              marginBottom: 16,
              background: "var(--accent-light)",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.82rem",
              color: "var(--accent)",
              fontWeight: 600,
              animation: "fadeIn 0.4s ease",
            }}>
              🧠 Tìm thấy {memoryInfo.memories_found} memory từ phiên trước | Tổng: {memoryInfo.total_memories} memories
            </div>
          )}

          {/* Progress Bar */}
          <div className="progress-container">
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="progress-steps">
              {AGENTS.map((a) => {
                const isDone = roundResponses.some((r) => r.agent_name === a.name);
                const isActive = currentAgent === a.name;
                return (
                  <div
                    key={a.name}
                    className={`progress-step ${isDone ? "done" : ""} ${isActive ? "active" : ""}`}
                  >
                    {a.icon} {a.display}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Responses grouped by round */}
          {rounds.map((roundGroup) => (
            <div key={roundGroup.round}>
              {/* Round divider */}
              {roundGroup.round > 1 && (
                <div className="round-divider">
                  <span className="round-badge">
                    🔄 Vòng {roundGroup.round}
                  </span>
                </div>
              )}

              {/* Messages */}
              {roundGroup.items.map((resp, idx) => {
                // User reply card
                if (resp.type === "user-reply") {
                  return (
                    <div key={`r${roundGroup.round}-user-${idx}`} className="agent-card user-reply">
                      <div className="agent-header">
                        <div className="agent-icon user">💬</div>
                        <div>
                          <div className="agent-name">Phản biện của bạn</div>
                          <div className="agent-meta">Vòng {roundGroup.round}</div>
                        </div>
                      </div>
                      <div className="agent-content">{resp.content}</div>
                    </div>
                  );
                }

                // Error
                if (resp.type === "error") {
                  return (
                    <div key={`r${roundGroup.round}-err-${idx}`} className="alert alert-error">
                      ⚠️ Agent {resp.agent_name}: {resp.error}
                    </div>
                  );
                }

                // Agent / Summary card
                const info = getAgentInfo(resp.agent_name);
                const isSummary = resp.type === "summary";

                return (
                  <div key={`r${roundGroup.round}-${resp.agent_name}-${idx}`} className={`agent-card ${isSummary ? "summary" : ""}`}>
                    <div className="agent-header">
                      <div className={`agent-icon ${info.color}`}>{info.icon}</div>
                      <div>
                        <div className="agent-name">{info.display}</div>
                        <div className="agent-meta">
                          {resp.tokens_used?.toLocaleString()} tokens
                          {resp.cost_usd ? ` · $${resp.cost_usd.toFixed(4)}` : ""}
                          {resp.rag_sources > 0 ? ` · 📚 ${resp.rag_sources} nguồn pháp lý` : ""}
                          {resp.search_results > 0 ? ` · 🔍 ${resp.search_results} nguồn${resp.search_tool ? ` (${
                            resp.search_tool === "serpapi" ? "Google" :
                            resp.search_tool === "tavily" ? "Tavily" : "DuckDuckGo"
                          })` : ""}` : ""}
                          {resp.trends_available ? " · 📈 Trends" : ""}
                          {roundGroup.round > 1 ? ` · Vòng ${roundGroup.round}` : ""}
                        </div>
                      </div>
                    </div>
                    <div
                      className="agent-content"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(resp.content || "") }}
                    />
                  </div>
                );
              })}
            </div>
          ))}

          {/* Typing indicator */}
          {isStreaming && currentAgent && (
            <div className="agent-card active">
              <div className="agent-header">
                <div className={`agent-icon ${getAgentInfo(currentAgent).color}`}>
                  {getAgentInfo(currentAgent).icon}
                </div>
                <div>
                  <div className="agent-name">{getAgentInfo(currentAgent).display}</div>
                  <div className="agent-meta">đang phân tích...</div>
                </div>
              </div>
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}

          {/* Reply form — sau khi hoàn thành, nếu chưa hết round */}
          {canReply && (
            <div className="reply-form">
              <h3>💬 Phản biện lại hội đồng</h3>
              <textarea
                id="reply-input"
                className="form-textarea"
                placeholder="Bạn không đồng ý điểm nào? Muốn hỏi thêm gì? Có thông tin bổ sung?"
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                rows={3}
              />
              <div className="reply-form-actions">
                <span className="round-info">
                  Vòng {currentRound}/{MAX_ROUNDS} · Còn {MAX_ROUNDS - currentRound} lượt phản biện
                </span>
                <button
                  id="send-reply-btn"
                  className="btn btn-primary"
                  onClick={sendReply}
                  disabled={!replyText.trim()}
                >
                  🗣️ Gửi phản biện
                </button>
              </div>
            </div>
          )}

          {/* ── Report Card ────────────────────────── */}
          {reportCard && (
            <div className="report-card">
              <h3>📋 Report Card</h3>

              <div className="report-card-grid">
                {/* Radar Chart SVG */}
                <div className="radar-chart">
                  <RadarChart scores={reportCard.category_scores} />
                </div>

                {/* Score summary */}
                <div className="report-scores">
                  <div className={`score-badge ${
                    reportCard.overall_score >= 7 ? "score-high" :
                    reportCard.overall_score >= 5 ? "score-mid" : "score-low"
                  }`}>
                    <span className="score-value">{reportCard.overall_score}</span>
                    <span className="score-label">/10</span>
                  </div>
                  <div className={`recommendation-badge ${
                    reportCard.recommendation === "Go" ? "rec-go" :
                    reportCard.recommendation === "Pivot" ? "rec-pivot" : "rec-nogo"
                  }`}>
                    {reportCard.recommendation === "Go" ? "🚀 GO" :
                     reportCard.recommendation === "Pivot" ? "🔄 PIVOT" : "🛑 NO-GO"}
                  </div>

                  {/* Category scores */}
                  <div className="category-scores">
                    {Object.entries(reportCard.category_scores).map(([cat, score]) => (
                      <div key={cat} className="score-category">
                        <span className="cat-name">
                          {cat === "market" ? "📊 Thị Trường" :
                           cat === "strategy" ? "🎯 Chiến Lược" :
                           cat === "finance" ? "💰 Tài Chính" :
                           cat === "technical" ? "⚙️ Kỹ Thuật" : "⚖️ Pháp Lý"}
                        </span>
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{ width: `${score * 10}%` }} />
                        </div>
                        <span className="cat-score">{score}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Strengths & Weaknesses */}
              <div className="sw-grid">
                <div className="sw-col">
                  <h4>✅ Điểm Mạnh</h4>
                  {reportCard.strengths?.map((s, i) => (
                    <div key={i} className="strength-item">✓ {s}</div>
                  ))}
                </div>
                <div className="sw-col">
                  <h4>⚠️ Điểm Yếu</h4>
                  {reportCard.weaknesses?.map((w, i) => (
                    <div key={i} className="weakness-item">✗ {w}</div>
                  ))}
                </div>
              </div>

              {/* Legal Checklist */}
              {reportCard.legal_checklist?.length > 0 && (
                <div className="legal-checklist">
                  <h4>⚖️ Checklist Pháp Lý</h4>
                  <table>
                    <thead>
                      <tr><th>Yêu cầu</th><th>Loại</th><th>Trạng thái</th></tr>
                    </thead>
                    <tbody>
                      {reportCard.legal_checklist.map((item, i) => (
                        <tr key={i}>
                          <td>{item.item}</td>
                          <td>{item.type}</td>
                          <td>☐ {item.status === "pending" ? "Cần xác minh" : item.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Action buttons */}
              <div className="report-actions">
                {tierLimits.can_export_pdf ? (
                  <button
                    className="btn btn-primary"
                    onClick={() => {
                      const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
                      window.open(
                        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/debate/${sessionId}/export/pdf?token=${token}`,
                        "_blank"
                      );
                    }}
                  >
                    📄 Tải báo cáo PDF
                  </button>
                ) : (
                  <button className="btn btn-ghost" disabled title="Nâng cấp Premium để xuất PDF">
                    🔒 Tải PDF (Premium)
                  </button>
                )}

                {tierLimits.can_share ? (
                  <button
                    className="btn btn-secondary"
                    onClick={async () => {
                      try {
                        const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
                        const res = await fetch(
                          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/share`,
                          {
                            method: "POST",
                            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                            body: JSON.stringify({ session_id: sessionId }),
                          }
                        );
                        if (!res.ok) {
                          const errData = await res.json().catch(() => ({}));
                          throw new Error(errData.detail || "Không thể tạo link");
                        }
                        const data = await res.json();
                        const url = `${window.location.origin}${data.url}`;
                        await navigator.clipboard.writeText(url);
                        setShareToast("Đã sao chép link chia sẻ!");
                        setTimeout(() => setShareToast(null), 3000);
                      } catch (e) {
                        setShareToast("Lỗi: " + e.message);
                        setTimeout(() => setShareToast(null), 3000);
                      }
                    }}
                  >
                    🔗 Chia sẻ
                  </button>
                ) : (
                  <button className="btn btn-ghost" disabled title="Nâng cấp Pro+ để chia sẻ">
                    🔒 Chia sẻ (Pro+)
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Hết round */}
          {isCompleted && currentRound >= MAX_ROUNDS && (
            <div className="alert alert-success" style={{ textAlign: "center" }}>
              ✅ Đã hoàn thành {MAX_ROUNDS} vòng tranh luận. Cảm ơn bạn!
            </div>
          )}

          {/* Total stats */}
          {!isStreaming && responses.length > 0 && (
            <div style={{
              textAlign: "center",
              padding: "20px 0",
              color: "var(--text-muted)",
              fontSize: "0.85rem",
              animation: "fadeIn 0.5s ease",
            }}>
              {isCompleted ? "✅" : "⏳"} {currentRound} vòng · {totalTokens.toLocaleString()} tokens · ${totalCost.toFixed(4)}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
      {shareToast && <div className="share-toast">{shareToast}</div>}
    </div>
  );
}

/**
 * Format markdown đơn giản → HTML (bold, headers, lists, line breaks)
 */
function formatMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/### (.+)/g, "<h3>$1</h3>")
    .replace(/## (.+)/g, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^\- (.+)/gm, "• $1")
    .replace(/^\d+\. (.+)/gm, "$&")
    .replace(/\n/g, "<br/>");
}

/**
 * SVG Radar Chart — 5 trục, thuần SVG, không cần Chart.js.
 */
function RadarChart({ scores }) {
  if (!scores) return null;

  const categories = [
    { key: "market", label: "Thị Trường", icon: "📊" },
    { key: "strategy", label: "Chiến Lược", icon: "🎯" },
    { key: "finance", label: "Tài Chính", icon: "💰" },
    { key: "technical", label: "Kỹ Thuật", icon: "⚙️" },
    { key: "legal", label: "Pháp Lý", icon: "⚖️" },
  ];

  const cx = 100, cy = 100, r = 75;
  const n = categories.length;

  // Tính tọa độ điểm trên trục
  function getPoint(index, value, maxR = r) {
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    const radius = (value / 10) * maxR;
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  }

  // Grid levels (2, 4, 6, 8, 10)
  const gridLevels = [2, 4, 6, 8, 10];

  // Data polygon
  const dataPoints = categories.map((c, i) => {
    const val = scores[c.key] || 0;
    return getPoint(i, val);
  });
  const dataPath = dataPoints.map((p) => `${p.x},${p.y}`).join(" ");

  // Axis lines + labels
  const axes = categories.map((c, i) => {
    const end = getPoint(i, 10);
    const labelPos = getPoint(i, 12.5);
    return { ...c, end, labelPos };
  });

  return (
    <svg viewBox="0 0 200 200" className="radar-svg">
      {/* Grid polygons */}
      {gridLevels.map((level) => {
        const pts = categories
          .map((_, i) => getPoint(i, level))
          .map((p) => `${p.x},${p.y}`)
          .join(" ");
        return (
          <polygon
            key={level}
            points={pts}
            fill="none"
            stroke="var(--border)"
            strokeWidth="0.5"
            opacity="0.5"
          />
        );
      })}

      {/* Axis lines */}
      {axes.map((a) => (
        <line
          key={a.key}
          x1={cx}
          y1={cy}
          x2={a.end.x}
          y2={a.end.y}
          stroke="var(--border)"
          strokeWidth="0.5"
          opacity="0.5"
        />
      ))}

      {/* Data polygon */}
      <polygon
        points={dataPath}
        fill="rgba(99, 102, 241, 0.2)"
        stroke="var(--accent)"
        strokeWidth="2"
      />

      {/* Data points */}
      {dataPoints.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r="3"
          fill="var(--accent)"
        />
      ))}

      {/* Labels */}
      {axes.map((a) => (
        <text
          key={a.key}
          x={a.labelPos.x}
          y={a.labelPos.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="7"
          fill="var(--text-secondary)"
        >
          {a.icon}
        </text>
      ))}
    </svg>
  );
}
