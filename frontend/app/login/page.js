"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, setToken, setUser } from "../lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await login(email, password);
      setToken(data.access_token);
      setUser(data.user);
      router.push("/");
    } catch (err) {
      setError(err.detail || "Đăng nhập thất bại. Kiểm tra email và mật khẩu.");
    } finally {
      setLoading(false);
    }
  }

  // ── Google Sign-In callback ──────────────────────
  async function handleGoogleLogin(response) {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: response.credential }),
      });
      const data = await res.json();
      if (!res.ok) throw { detail: data.detail || "Google login thất bại" };
      setToken(data.access_token);
      setUser(data.user);
      router.push("/");
    } catch (err) {
      setError(err.detail || "Google login thất bại");
    } finally {
      setLoading(false);
    }
  }

  // Mount Google Sign-In button
  if (typeof window !== "undefined") {
    window.handleGoogleLogin = handleGoogleLogin;
  }

  return (
    <div className="app-container">
      <div className="card card-auth" style={{ animation: "fadeIn 0.5s ease" }}>
        <h1>🧠 Đăng nhập</h1>
        <p className="subtitle">Cố Vấn Khởi Nghiệp AI — Hội đồng 5 chuyên gia</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              id="login-email"
              className="form-input"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mật khẩu</label>
            <input
              id="login-password"
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>

          <button
            id="login-submit"
            className="btn btn-primary btn-block btn-lg"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" style={{borderTopColor:"white"}}></div> Đang đăng nhập...</>
            ) : (
              "Đăng nhập"
            )}
          </button>
        </form>

        {/* Google Sign-In divider */}
        <div className="auth-divider">
          <span>hoặc</span>
        </div>

        {/* Google Sign-In Button */}
        <div id="google-signin-container">
          <button
            className="btn btn-google btn-block"
            type="button"
            onClick={() => {
              // Trigger Google Sign-In popup (requires GSI script loaded)
              if (window.google && window.google.accounts) {
                window.google.accounts.id.prompt();
              } else {
                setError("Google Sign-In chưa được cấu hình. Liên hệ admin.");
              }
            }}
          >
            <svg width="18" height="18" viewBox="0 0 48 48" style={{marginRight: 8, verticalAlign: "middle"}}>
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            Đăng nhập bằng Google
          </button>
        </div>

        <p style={{ textAlign: "center", marginTop: 24, fontSize: "0.88rem", color: "var(--text-muted)" }}>
          Chưa có tài khoản?{" "}
          <span className="link" onClick={() => router.push("/register")}>
            Đăng ký ngay
          </span>
        </p>
      </div>
    </div>
  );
}
