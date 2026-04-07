"use client";

import "./globals.css";
import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getToken, getUser, removeToken } from "./lib/api";

export default function RootLayout({ children }) {
  const [theme, setTheme] = useState("dark");
  const [user, setUser] = useState(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Load saved theme
    const saved = localStorage.getItem("theme") || "dark";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);

    // Load user
    const u = getUser();
    const t = getToken();
    if (u && t) {
      setUser(u);
    } else if (
      pathname !== "/login" &&
      pathname !== "/register" &&
      pathname !== "/pricing" &&
      !pathname.startsWith("/shared")
    ) {
      router.push("/login");
    }
  }, [pathname]);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem("theme", next);
    document.documentElement.setAttribute("data-theme", next);
  }

  function handleLogout() {
    removeToken();
    localStorage.removeItem("user");
    setUser(null);
    router.push("/login");
  }

  const isAuthPage = pathname === "/login" || pathname === "/register";

  return (
    <html lang="vi" data-theme={theme}>
      <head>
        <title>Cố Vấn Khởi Nghiệp AI — Hội đồng 5 chuyên gia AI</title>
        <meta name="description" content="Phân tích ý tưởng khởi nghiệp với 5 chuyên gia AI tranh luận realtime" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        {/* Navbar */}
        <nav className="navbar">
          <div
            className="navbar-brand"
            style={{ cursor: "pointer" }}
            onClick={() => router.push("/")}
          >
            <span className="logo-icon">🧠</span>
            <span>Cố Vấn Khởi Nghiệp AI</span>
          </div>

          <div className="navbar-actions">
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              title={theme === "dark" ? "Chuyển sang sáng" : "Chuyển sang tối"}
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>

            {user && !isAuthPage && (
              <>
                {(user.tier === "free" || user.tier === "pro" || !user.tier) && (
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => router.push("/pricing")}
                    style={{ color: "var(--accent)" }}
                  >
                    💎 Nâng cấp
                  </button>
                )}
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  {user.email}
                </span>
                <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
                  Đăng xuất
                </button>
              </>
            )}
          </div>
        </nav>

        {/* Main content */}
        <main>{children}</main>
      </body>
    </html>
  );
}
