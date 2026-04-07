"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "0đ",
    period: "mãi mãi",
    features: [
      "1 vòng tranh luận",
      "5 phiên/tháng",
      "GPT-4o-mini (tất cả agents)",
      "DuckDuckGo search",
      "10 bộ nhớ Mem0",
    ],
    notIncluded: ["PDF Export", "Chia sẻ link", "Google Trends"],
    accent: "#6b7280",
    popular: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$5",
    period: "/tháng",
    features: [
      "2 vòng tranh luận",
      "30 phiên/tháng",
      "GPT-4o (Chiến Lược + Pháp Lý)",
      "Tavily Search",
      "50 bộ nhớ Mem0",
      "Chia sẻ link",
    ],
    notIncluded: ["PDF Export"],
    accent: "#6366f1",
    popular: true,
  },
  {
    id: "premium",
    name: "Premium",
    price: "$15",
    period: "/tháng",
    features: [
      "3 vòng tranh luận",
      "100 phiên/tháng",
      "GPT-4o (tất cả agents)",
      "SerpAPI + Google Trends",
      "200 bộ nhớ Mem0",
      "Chia sẻ link",
      "PDF Export",
    ],
    notIncluded: [],
    accent: "#10b981",
    popular: false,
  },
];

export default function PricingPage() {
  const router = useRouter();
  const [currentTier, setCurrentTier] = useState("free");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetch(`${API}/api/billing/status`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.json())
        .then((d) => setCurrentTier(d.tier || "free"))
        .catch(() => {});
    }
  }, []);

  const handleUpgrade = async (planId) => {
    if (planId === "free") return;

    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API}/api/billing/checkout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ target_tier: planId }),
      });
      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        alert(data.detail || "Stripe chưa được cấu hình");
      }
    } catch (e) {
      alert("Lỗi: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pricing-container">
      <div className="pricing-header">
        <h1>Chọn gói phù hợp</h1>
        <p>Nâng cấp để mở khóa toàn bộ sức mạnh AI phân tích</p>
      </div>

      <div className="pricing-grid">
        {PLANS.map((plan) => (
          <div
            key={plan.id}
            className={`pricing-card ${plan.popular ? "popular" : ""} ${currentTier === plan.id ? "current" : ""}`}
          >
            {plan.popular && <div className="popular-badge">Phổ biến nhất</div>}
            {currentTier === plan.id && <div className="current-badge">Gói hiện tại</div>}

            <h2 style={{ color: plan.accent }}>{plan.name}</h2>
            <div className="price">
              <span className="price-amount">{plan.price}</span>
              <span className="price-period">{plan.period}</span>
            </div>

            <ul className="feature-list">
              {plan.features.map((f, i) => (
                <li key={i} className="feature-yes">✓ {f}</li>
              ))}
              {plan.notIncluded.map((f, i) => (
                <li key={i} className="feature-no">✗ {f}</li>
              ))}
            </ul>

            <button
              className={`btn ${currentTier === plan.id ? "btn-disabled" : plan.popular ? "btn-primary" : "btn-secondary"}`}
              onClick={() => handleUpgrade(plan.id)}
              disabled={currentTier === plan.id || loading || plan.id === "free"}
            >
              {currentTier === plan.id
                ? "Đang sử dụng"
                : plan.id === "free"
                ? "Miễn phí"
                : loading
                ? "Đang xử lý..."
                : "Nâng cấp"}
            </button>
          </div>
        ))}
      </div>

      <div className="pricing-footer">
        <a href="/">← Quay về trang chính</a>
      </div>
    </div>
  );
}
