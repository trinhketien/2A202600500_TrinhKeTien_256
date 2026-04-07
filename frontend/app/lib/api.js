const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * API helper — gọi backend FastAPI
 */

export async function apiPost(path, body, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

export async function apiGet(path, token = null) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { headers });
  const data = await res.json();
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

/**
 * Auth API
 */
export async function login(email, password) {
  return apiPost("/api/auth/login", { email, password });
}

export async function register(email, password, full_name) {
  return apiPost("/api/auth/register", { email, password, full_name });
}

export async function getProfile(token) {
  return apiGet("/api/auth/me", token);
}

/**
 * Debate SSE — tạo EventSource stream
 */
export function createDebateStream(idea, industry, token) {
  const params = new URLSearchParams({ idea, token });
  if (industry) params.set("industry", industry);
  const url = `${API_BASE}/api/debate/stream?${params.toString()}`;
  return new EventSource(url);
}

/**
 * Reply SSE — phản biện lại (vòng 2, 3)
 */
export function createReplyStream(sessionId, message, token) {
  const params = new URLSearchParams({ message, token });
  const url = `${API_BASE}/api/debate/${sessionId}/reply/stream?${params.toString()}`;
  return new EventSource(url);
}

/**
 * Token helpers
 */
export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function removeToken() {
  localStorage.removeItem("token");
}

export function setUser(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

export function getUser() {
  if (typeof window === "undefined") return null;
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
}
