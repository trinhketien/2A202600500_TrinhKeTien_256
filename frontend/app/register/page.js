"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register, setToken, setUser } from "../lib/api";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
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
      const data = await register(email, password, fullName);
      setToken(data.access_token);
      setUser(data.user);
      router.push("/");
    } catch (err) {
      if (err.status === 409) {
        setError("Email đã được đăng ký. Vui lòng đăng nhập.");
      } else {
        setError(err.detail || "Đăng ký thất bại. Thử lại sau.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-container">
      <div className="card card-auth" style={{ animation: "fadeIn 0.5s ease" }}>
        <h1>🚀 Đăng ký</h1>
        <p className="subtitle">Tạo tài khoản để sử dụng Cố Vấn AI</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Họ và tên</label>
            <input
              id="register-name"
              className="form-input"
              type="text"
              placeholder="Nguyễn Văn A"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input
              id="register-email"
              className="form-input"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Mật khẩu (tối thiểu 8 ký tự)</label>
            <input
              id="register-password"
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
            id="register-submit"
            className="btn btn-primary btn-block btn-lg"
            type="submit"
            disabled={loading}
          >
            {loading ? (
              <><div className="spinner" style={{borderTopColor:"white"}}></div> Đang tạo tài khoản...</>
            ) : (
              "Tạo tài khoản"
            )}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 24, fontSize: "0.88rem", color: "var(--text-muted)" }}>
          Đã có tài khoản?{" "}
          <span className="link" onClick={() => router.push("/login")}>
            Đăng nhập
          </span>
        </p>
      </div>
    </div>
  );
}
