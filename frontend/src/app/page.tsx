"use client";

import {
  FormEvent,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { QRCodeSVG } from "qrcode.react";
import { api } from "../lib/api";

type Role = "STUDENT" | "FACULTY" | "EXTERNAL_FINDER" | "ADMIN";
type ReportType = "LOST" | "FOUND";
type Tab =
  | "dashboard"
  | "items"
  | "report"
  | "matches"
  | "claims"
  | "messages"
  | "handover"
  | "notifications"
  | "assistant";

type User = {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: Role;
  college_id?: string | null;
  is_staff: boolean;
  is_superuser: boolean;
};

type Item = {
  id: number;
  reference_code: string;
  report_type: ReportType;
  title: string;
  category: string;
  color: string;
  brand: string;
  description: string;
  location: string;
  event_date: string;
  status: string;
  reporter_name: string;
  image?: string | null;
  image_url?: string | null;
  created_at: string;
};

type MatchResult = {
  item: Item;
  score: number;
  explanation: string[];
};

type Claim = {
  id: number;
  item: number;
  item_title: string;
  item_reference: string;
  claimant_name: string;
  ownership_details: string;
  proof_text: string;
  status: string;
  review_note: string;
  created_at: string;
  handover_token?: string | null;
  handover_otp?: string | null;
  handover_expires_at?: string | null;
  message_count?: number;
};

type Notification = {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
};

type ClaimMessage = {
  id: number;
  claim: number;
  sender_name: string;
  message: string;
  created_at: string;
};

type Stats = {
  lost_active: number;
  found_active: number;
  claims_pending: number;
  returned: number;
  my_reports: number;
  resolution_rate: number;
};

type ItemForm = {
  report_type: ReportType;
  title: string;
  category: string;
  color: string;
  brand: string;
  description: string;
  location: string;
  event_date: string;
};

type RegisterForm = {
  username: string;
  email: string;
  college_id: string;
  role: "STUDENT" | "EXTERNAL_FINDER";
  password: string;
  passwordConfirm: string;
};

const initialItemForm: ItemForm = {
  report_type: "LOST",
  title: "",
  category: "",
  color: "",
  brand: "",
  description: "",
  location: "",
  event_date: new Date().toISOString().slice(0, 10),
};

const initialRegisterForm: RegisterForm = {
  username: "",
  email: "",
  college_id: "",
  role: "STUDENT",
  password: "",
  passwordConfirm: "",
};

const initialStats: Stats = {
  lost_active: 0,
  found_active: 0,
  claims_pending: 0,
  returned: 0,
  my_reports: 0,
  resolution_rate: 0,
};

const categories = [
  "Wallet",
  "Electronics",
  "ID Card",
  "Keys",
  "Bag",
  "Books",
  "Jewellery",
  "Clothing",
  "Other",
];

const navItems: { id: Tab; label: string; icon: string }[] = [
  { id: "dashboard", label: "Overview", icon: "⌂" },
  { id: "items", label: "Lost & Found", icon: "⌕" },
  { id: "report", label: "Report Item", icon: "+" },
  { id: "matches", label: "AI Matches", icon: "✦" },
  { id: "claims", label: "Claims", icon: "✓" },
  { id: "messages", label: "Messages", icon: "◌" },
  { id: "handover", label: "Handover", icon: "▦" },
  { id: "notifications", label: "Notifications", icon: "●" },
  { id: "assistant", label: "Assistant", icon: "◇" },
];

function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: unknown;
          status?: number;
        };
      }
    ).response;

    const data = response?.data;
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      const record = data as Record<string, unknown>;
      if (typeof record.detail === "string") return record.detail;
      const first = Object.entries(record)[0];
      if (first) {
        const value = first[1];
        if (Array.isArray(value)) {
          return `${first[0]}: ${String(value[0])}`;
        }
        return `${first[0]}: ${String(value)}`;
      }
    }
  }
  return "Something went wrong. Please try again.";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function roleLabel(role: Role): string {
  const labels: Record<Role, string> = {
    STUDENT: "Campus User",
    FACULTY: "Faculty Reviewer",
    EXTERNAL_FINDER: "External Finder",
    ADMIN: "Administrator",
  };
  return labels[role];
}

function statusTone(status: string): string {
  if (["RETURNED", "APPROVED"].includes(status)) return "success";
  if (["REJECTED", "CLOSED"].includes(status)) return "danger";
  if (["CLAIMED", "SUBMITTED"].includes(status)) return "warning";
  return "neutral";
}

function StatusPill({
  status,
  label,
}: {
  status: string;
  label?: string;
}) {
  return (
    <span className={`status-pill ${statusTone(status)}`}>
      <span />
      {label ?? status.replaceAll("_", " ")}
    </span>
  );
}

function EmptyState({
  icon,
  title,
  text,
  action,
}: {
  icon: string;
  title: string;
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}

function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand ${compact ? "compact" : ""}`}>
      <div className="brand-mark">
        <span className="brand-pin" />
        <span className="brand-ring" />
      </div>
      <div>
        <strong>TRACK-IT</strong>
        {!compact && <span>Smart Campus Recovery</span>}
      </div>
    </div>
  );
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [tab, setTab] = useState<Tab>("dashboard");
  const [items, setItems] = useState<Item[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [messages, setMessages] = useState<ClaimMessage[]>([]);
  const [stats, setStats] = useState<Stats>(initialStats);

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [toastTone, setToastTone] = useState<"success" | "error">("success");

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("ACTIVE");

  const [loginForm, setLoginForm] = useState({
    identifier: "",
    password: "",
  });
  const [registerForm, setRegisterForm] =
    useState<RegisterForm>(initialRegisterForm);
  const [authMode, setAuthMode] =
    useState<"login" | "register" | "otp">("login");
  const [verificationEmail, setVerificationEmail] = useState("");
  const [verificationOtp, setVerificationOtp] = useState("");

  const [itemForm, setItemForm] =
    useState<ItemForm>(initialItemForm);
  const [itemImage, setItemImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState("");

  const [claimItemId, setClaimItemId] = useState("");
  const [claimDetails, setClaimDetails] = useState("");
  const [proofText, setProofText] = useState("");
  const [reviewNote, setReviewNote] = useState("");

  const [selectedClaimId, setSelectedClaimId] = useState("");
  const [newMessage, setNewMessage] = useState("");

  const [handoverToken, setHandoverToken] = useState("");
  const [handoverOtp, setHandoverOtp] = useState("");
  const [handoverReceipt, setHandoverReceipt] =
    useState<Record<string, string> | null>(null);

  const [chatQuestion, setChatQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState<
    { from: "user" | "assistant"; text: string }[]
  >([
    {
      from: "assistant",
      text:
        "Hello! I can guide you through reporting, AI matches, claims, " +
        "email verification and secure handover.",
    },
  ]);

  const isReviewer =
    Boolean(user?.is_staff) ||
    Boolean(user?.is_superuser) ||
    user?.role === "ADMIN" ||
    user?.role === "FACULTY";

  const foundItems = useMemo(
    () =>
      items.filter(
        (item) =>
          item.report_type === "FOUND" &&
          item.status === "ACTIVE",
      ),
    [items],
  );

  const selectedClaim = useMemo(
    () =>
      claims.find(
        (claim) => String(claim.id) === selectedClaimId,
      ),
    [claims, selectedClaimId],
  );

  const unreadCount = useMemo(
    () =>
      notifications.filter(
        (notification) => !notification.is_read,
      ).length,
    [notifications],
  );

  const showToast = useCallback(
    (message: string, tone: "success" | "error" = "success") => {
      setToast(message);
      setToastTone(tone);
      window.setTimeout(() => setToast(""), 4200);
    },
    [],
  );

  const loadItems = useCallback(async () => {
    const response = await api.get("/items/", {
      params: {
        ...(search ? { search } : {}),
        ...(typeFilter ? { report_type: typeFilter } : {}),
        ...(statusFilter ? { status: statusFilter } : {}),
      },
    });
    setItems(response.data.results ?? response.data);
  }, [search, statusFilter, typeFilter]);

  const loadClaims = useCallback(async () => {
    const response = await api.get("/claims/");
    setClaims(response.data.results ?? response.data);
  }, []);

  const loadStats = useCallback(async () => {
    const response = await api.get("/items/dashboard/");
    setStats(response.data);
  }, []);

  const loadNotifications = useCallback(async () => {
    const response = await api.get("/notifications/");
    setNotifications(response.data.results ?? response.data);
  }, []);

  const refreshWorkspace = useCallback(async () => {
    if (!localStorage.getItem("trackit_token")) return;
    await Promise.all([
      loadItems(),
      loadClaims(),
      loadStats(),
      loadNotifications(),
    ]);
  }, [loadClaims, loadItems, loadNotifications, loadStats]);

  useEffect(() => {
    async function initialize() {
      const token = localStorage.getItem("trackit_token");
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const response = await api.get("/auth/me/");
        setUser(response.data);
        await refreshWorkspace();
      } catch {
        localStorage.removeItem("trackit_token");
      } finally {
        setLoading(false);
      }
    }
    initialize();
  }, [refreshWorkspace]);

  useEffect(() => {
    if (!user) return;

    const token = localStorage.getItem("trackit_token");
    const base =
      process.env.NEXT_PUBLIC_WS_URL ??
      "ws://127.0.0.1:8000/ws/notifications/";
    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(
        `${base}${base.includes("?") ? "&" : "?"}token=${token}`,
      );
      socket.onmessage = (event) => {
        const notification = JSON.parse(
          event.data,
        ) as Notification;
        setNotifications((current) => [
          notification,
          ...current,
        ]);
        showToast(notification.title);
      };
    } catch {
      // REST polling remains available when WebSockets are unavailable.
    }

    const poll = window.setInterval(
      () => loadNotifications().catch(() => undefined),
      30_000,
    );

    return () => {
      socket?.close();
      window.clearInterval(poll);
    };
  }, [loadNotifications, showToast, user]);

  useEffect(() => {
    if (!itemImage) {
      setImagePreview("");
      return;
    }
    const preview = URL.createObjectURL(itemImage);
    setImagePreview(preview);
    return () => URL.revokeObjectURL(preview);
  }, [itemImage]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionLoading(true);
    try {
      const response = await api.post("/auth/login/", loginForm);
      localStorage.setItem("trackit_token", response.data.token);
      setUser(response.data.user);
      setLoginForm({ identifier: "", password: "" });
      setTab("dashboard");
      await refreshWorkspace();
      showToast(`Welcome back, ${response.data.user.display_name}.`);
    } catch (error) {
      const data = (
        error as {
          response?: {
            data?: {
              verification_required?: boolean;
              email?: string;
            };
          };
        }
      ).response?.data;
      if (data?.verification_required && data.email) {
        setVerificationEmail(data.email);
        setAuthMode("otp");
      }
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
      setLoading(false);
    }
  }

  async function register(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (registerForm.password !== registerForm.passwordConfirm) {
      showToast("Passwords do not match.", "error");
      return;
    }

    setActionLoading(true);
    try {
      const email = registerForm.email.trim().toLowerCase();
      const response = await api.post("/auth/register/", {
        username: registerForm.username.trim(),
        email,
        password: registerForm.password,
        password_confirm: registerForm.passwordConfirm,
        role: registerForm.role,
        college_id:
          registerForm.role === "STUDENT"
            ? registerForm.college_id.trim()
            : null,
      });
      setVerificationEmail(email);
      setVerificationOtp("");
      setAuthMode("otp");
      showToast(response.data.message);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function verifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionLoading(true);
    try {
      const response = await api.post("/auth/verify-email/", {
        email: verificationEmail,
        otp: verificationOtp,
      });
      setVerificationOtp("");
      setRegisterForm(initialRegisterForm);
      setAuthMode("login");
      setLoginForm((current) => ({
        ...current,
        identifier: verificationEmail,
      }));
      showToast(response.data.message);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function resendOtp() {
    setActionLoading(true);
    try {
      const response = await api.post("/auth/resend-otp/", {
        email: verificationEmail,
      });
      showToast(response.data.message);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function logout() {
    try {
      await api.post("/auth/logout/");
    } catch {
      // A local logout must still work when the backend is unavailable.
    }
    localStorage.removeItem("trackit_token");
    setUser(null);
    setClaims([]);
    setNotifications([]);
    setStats(initialStats);
    setAuthMode("login");
    showToast("You have been logged out.");
  }

  async function createItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionLoading(true);
    try {
      const formData = new FormData();
      Object.entries(itemForm).forEach(([key, value]) => {
        formData.append(key, value);
      });
      if (itemImage) formData.append("image", itemImage);

      await api.post("/items/", formData);
      setItemForm(initialItemForm);
      setItemImage(null);
      setTab("items");
      await Promise.all([loadItems(), loadStats()]);
      showToast("Item report published successfully.");
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function runMatches(item: Item) {
    setActionLoading(true);
    try {
      const response = await api.get(
        `/items/${item.id}/matches/`,
      );
      setMatches(response.data);
      setTab("matches");
      if (!response.data.length) {
        showToast(
          "No active opposite-type reports are available yet.",
          "error",
        );
      } else {
        showToast(
          `${response.data.length} AI-assisted suggestions found.`,
        );
      }
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function createClaim(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionLoading(true);
    try {
      await api.post("/claims/", {
        item: Number(claimItemId),
        ownership_details: claimDetails,
        proof_text: proofText,
      });
      setClaimItemId("");
      setClaimDetails("");
      setProofText("");
      await Promise.all([loadClaims(), loadStats()]);
      showToast("Ownership claim submitted for secure review.");
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function reviewClaim(
    claim: Claim,
    action: "approve" | "reject",
  ) {
    setActionLoading(true);
    try {
      await api.post(`/claims/${claim.id}/${action}/`, {
        review_note:
          reviewNote.trim() ||
          (action === "approve"
            ? "Ownership evidence verified."
            : "Ownership evidence was insufficient."),
      });
      setReviewNote("");
      await Promise.all([loadClaims(), loadItems(), loadStats()]);
      showToast(
        action === "approve"
          ? "Claim approved and secure handover token generated."
          : "Claim rejected.",
      );
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function loadMessages(claimId: string) {
    setSelectedClaimId(claimId);
    if (!claimId) {
      setMessages([]);
      return;
    }
    try {
      const response = await api.get("/messages/", {
        params: { claim: claimId },
      });
      setMessages(response.data.results ?? response.data);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedClaimId) return;
    setActionLoading(true);
    try {
      await api.post("/messages/", {
        claim: Number(selectedClaimId),
        message: newMessage,
      });
      setNewMessage("");
      await loadMessages(selectedClaimId);
      showToast("Message sent.");
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function completeHandover(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setActionLoading(true);
    try {
      const response = await api.post(
        `/handover/${handoverToken.trim()}/complete/`,
        { otp: handoverOtp.trim() },
      );
      setHandoverReceipt(response.data.receipt);
      setHandoverToken("");
      setHandoverOtp("");
      await Promise.all([loadClaims(), loadItems(), loadStats()]);
      showToast(response.data.message);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    } finally {
      setActionLoading(false);
    }
  }

  async function askAssistant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = chatQuestion.trim();
    if (!question) return;

    setChatHistory((history) => [
      ...history,
      { from: "user", text: question },
    ]);
    setChatQuestion("");

    try {
      const response = await api.post("/chatbot/query/", {
        message: question,
      });
      setChatHistory((history) => [
        ...history,
        { from: "assistant", text: response.data.answer },
      ]);
    } catch (error) {
      setChatHistory((history) => [
        ...history,
        { from: "assistant", text: getErrorMessage(error) },
      ]);
    }
  }

  async function markNotificationRead(notification: Notification) {
    if (!notification.is_read) {
      await api.post(
        `/notifications/${notification.id}/mark_read/`,
      );
      setNotifications((current) =>
        current.map((item) =>
          item.id === notification.id
            ? { ...item, is_read: true }
            : item,
        ),
      );
    }
  }

  async function markAllRead() {
    await api.post("/notifications/mark_all_read/");
    setNotifications((current) =>
      current.map((item) => ({ ...item, is_read: true })),
    );
    showToast("All notifications marked as read.");
  }

  async function downloadExport(format: "pdf" | "xlsx") {
    try {
      const response = await api.get(
        `/items/export/${format}/`,
        { responseType: "blob" },
      );
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `trackit-items.${format}`;
      link.click();
      URL.revokeObjectURL(url);
      showToast(`${format.toUpperCase()} report downloaded.`);
    } catch (error) {
      showToast(getErrorMessage(error), "error");
    }
  }

  if (loading) {
    return (
      <main className="loading-screen">
        <BrandMark />
        <div className="loader" />
        <p>Preparing your secure workspace…</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="auth-page">
        <div className="auth-ambient ambient-one" />
        <div className="auth-ambient ambient-two" />

        <section className="auth-hero">
          <BrandMark />
          <div className="auth-copy">
            <span className="hero-chip">AI-assisted campus recovery</span>
            <h1>
              Lost something?
              <br />
              <em>Let intelligence find it.</em>
            </h1>
            <p>
              A trusted campus platform for reporting, matching,
              claiming and securely returning lost property.
            </p>
          </div>

          <div className="trust-grid">
            <article>
              <strong>Smart</strong>
              <span>Explainable match suggestions</span>
            </article>
            <article>
              <strong>Private</strong>
              <span>Evidence stays restricted</span>
            </article>
            <article>
              <strong>Secure</strong>
              <span>QR + OTP verified handover</span>
            </article>
          </div>
        </section>

        <section className="auth-card">
          <div className="auth-card-head">
            <span className="mobile-brand">
              <BrandMark compact />
            </span>
            <p className="eyebrow">WELCOME TO TRACK-IT</p>
            <h2>
              {authMode === "login" && "Sign in to your account"}
              {authMode === "register" && "Create your account"}
              {authMode === "otp" && "Verify your email"}
            </h2>
            <p>
              {authMode === "otp"
                ? `We sent a 6-digit code to ${verificationEmail}.`
                : "Secure access for students, faculty and verified finders."}
            </p>
          </div>

          {authMode === "login" && (
            <form className="auth-form" onSubmit={login}>
              <Field label="Username or email">
                <input
                  value={loginForm.identifier}
                  autoComplete="username"
                  placeholder="Enter username or email"
                  required
                  onChange={(event) =>
                    setLoginForm({
                      ...loginForm,
                      identifier: event.target.value,
                    })
                  }
                />
              </Field>
              <Field label="Password">
                <input
                  value={loginForm.password}
                  type="password"
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  required
                  onChange={(event) =>
                    setLoginForm({
                      ...loginForm,
                      password: event.target.value,
                    })
                  }
                />
              </Field>
              <button
                className="primary-button wide"
                disabled={actionLoading}
                type="submit"
              >
                {actionLoading ? "Signing in…" : "Sign in securely"}
              </button>
              <p className="auth-switch">
                New to TRACK-IT?{" "}
                <button
                  type="button"
                  onClick={() => setAuthMode("register")}
                >
                  Create account
                </button>
              </p>
            </form>
          )}

          {authMode === "register" && (
            <form className="auth-form" onSubmit={register}>
              <div className="form-two">
                <Field label="Username">
                  <input
                    value={registerForm.username}
                    autoComplete="username"
                    placeholder="Choose a username"
                    required
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        username: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Account type">
                  <select
                    value={registerForm.role}
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        role: event.target
                          .value as RegisterForm["role"],
                      })
                    }
                  >
                    <option value="STUDENT">Campus user</option>
                    <option value="EXTERNAL_FINDER">
                      External finder
                    </option>
                  </select>
                </Field>
              </div>

              <Field
                label="Email address"
                hint={
                  registerForm.role === "STUDENT"
                    ? "Campus users require an @gcet.edu.in address."
                    : "The verification OTP is sent to this address."
                }
              >
                <input
                  value={registerForm.email}
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  required
                  onChange={(event) =>
                    setRegisterForm({
                      ...registerForm,
                      email: event.target.value,
                    })
                  }
                />
              </Field>

              {registerForm.role === "STUDENT" && (
                <Field label="College ID">
                  <input
                    value={registerForm.college_id}
                    placeholder="Example: 22CS001"
                    required
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        college_id: event.target.value,
                      })
                    }
                  />
                </Field>
              )}

              <div className="form-two">
                <Field label="Password">
                  <input
                    value={registerForm.password}
                    type="password"
                    autoComplete="new-password"
                    placeholder="Strong password"
                    required
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        password: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Confirm password">
                  <input
                    value={registerForm.passwordConfirm}
                    type="password"
                    autoComplete="new-password"
                    placeholder="Repeat password"
                    required
                    onChange={(event) =>
                      setRegisterForm({
                        ...registerForm,
                        passwordConfirm: event.target.value,
                      })
                    }
                  />
                </Field>
              </div>

              <button
                className="primary-button wide"
                disabled={actionLoading}
                type="submit"
              >
                {actionLoading
                  ? "Creating account…"
                  : "Create & verify account"}
              </button>
              <p className="auth-switch">
                Already registered?{" "}
                <button
                  type="button"
                  onClick={() => setAuthMode("login")}
                >
                  Sign in
                </button>
              </p>
            </form>
          )}

          {authMode === "otp" && (
            <form className="auth-form otp-form" onSubmit={verifyOtp}>
              <div className="otp-icon">✉</div>
              <Field
                label="Verification code"
                hint="The code expires in 10 minutes."
              >
                <input
                  className="otp-input"
                  value={verificationOtp}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  placeholder="000000"
                  required
                  onChange={(event) =>
                    setVerificationOtp(
                      event.target.value.replace(/\D/g, ""),
                    )
                  }
                />
              </Field>
              <button
                className="primary-button wide"
                disabled={actionLoading}
                type="submit"
              >
                {actionLoading
                  ? "Verifying…"
                  : "Verify email address"}
              </button>
              <div className="otp-actions">
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={resendOtp}
                >
                  Resend code
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode("login")}
                >
                  Back to sign in
                </button>
              </div>
            </form>
          )}

          <div className="security-note">
            <span>◆</span>
            <p>
              Protected with verified email access and secure token
              authentication.
            </p>
          </div>
        </section>

        {toast && (
          <div className={`toast ${toastTone}`}>{toast}</div>
        )}
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <BrandMark />
        <nav className="side-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={tab === item.id ? "active" : ""}
              onClick={() => setTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
              {item.id === "notifications" && unreadCount > 0 && (
                <b>{unreadCount}</b>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <span className="sidebar-card-icon">✦</span>
          <strong>AI matching is advisory</strong>
          <p>
            Ownership is confirmed only through verified evidence and
            staff approval.
          </p>
        </div>

        <div className="sidebar-profile">
          <div className="avatar">{initials(user.display_name)}</div>
          <div>
            <strong>{user.display_name}</strong>
            <span>{roleLabel(user.role)}</span>
          </div>
          <button title="Log out" onClick={logout}>
            ↗
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              {new Intl.DateTimeFormat("en-IN", {
                weekday: "long",
                day: "2-digit",
                month: "long",
              }).format(new Date())}
            </p>
            <h1>
              {tab === "dashboard" && `Good day, ${user.display_name}`}
              {tab === "items" && "Lost & Found Registry"}
              {tab === "report" && "Create a New Report"}
              {tab === "matches" && "AI-Assisted Matches"}
              {tab === "claims" && "Ownership Claims"}
              {tab === "messages" && "Secure Claim Messages"}
              {tab === "handover" && "Verified Item Handover"}
              {tab === "notifications" && "Notification Centre"}
              {tab === "assistant" && "TRACK-IT Assistant"}
            </h1>
          </div>
          <div className="top-actions">
            <button
              className="icon-button notification-button"
              onClick={() => setTab("notifications")}
              aria-label="Open notifications"
            >
              ♢
              {unreadCount > 0 && <span>{unreadCount}</span>}
            </button>
            <button
              className="primary-button"
              onClick={() => setTab("report")}
            >
              <span>＋</span> Report item
            </button>
          </div>
        </header>

        {tab === "dashboard" && (
          <div className="page-stack">
            <section className="welcome-banner">
              <div>
                <span className="hero-chip">Campus recovery centre</span>
                <h2>Every item has a way back.</h2>
                <p>
                  Report accurately, review intelligent suggestions and
                  complete returns with verified QR + OTP handover.
                </p>
                <div className="banner-actions">
                  <button
                    className="light-button"
                    onClick={() => setTab("report")}
                  >
                    Report an item
                  </button>
                  <button
                    className="ghost-light-button"
                    onClick={() => setTab("items")}
                  >
                    Browse reports
                  </button>
                </div>
              </div>
              <div className="banner-visual" aria-hidden="true">
                <div className="radar-circle radar-one" />
                <div className="radar-circle radar-two" />
                <div className="radar-circle radar-three" />
                <div className="radar-pin">⌖</div>
              </div>
            </section>

            <section className="stats-grid">
              <article className="stat-card">
                <div className="stat-icon lost">↙</div>
                <div>
                  <span>Active lost</span>
                  <strong>{stats.lost_active}</strong>
                </div>
                <small>Open recovery reports</small>
              </article>
              <article className="stat-card">
                <div className="stat-icon found">↗</div>
                <div>
                  <span>Active found</span>
                  <strong>{stats.found_active}</strong>
                </div>
                <small>Items awaiting owners</small>
              </article>
              <article className="stat-card">
                <div className="stat-icon claim">✓</div>
                <div>
                  <span>Pending claims</span>
                  <strong>{stats.claims_pending}</strong>
                </div>
                <small>Require secure review</small>
              </article>
              <article className="stat-card">
                <div className="stat-icon returned">⌂</div>
                <div>
                  <span>Returned</span>
                  <strong>{stats.returned}</strong>
                </div>
                <small>{stats.resolution_rate}% resolution rate</small>
              </article>
            </section>

            <section className="dashboard-grid">
              <div className="panel recent-panel">
                <div className="panel-head">
                  <div>
                    <p className="eyebrow">LIVE REGISTRY</p>
                    <h2>Recent reports</h2>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setTab("items")}
                  >
                    View all →
                  </button>
                </div>
                <div className="compact-list">
                  {items.slice(0, 5).map((item) => (
                    <button
                      key={item.id}
                      className="compact-item"
                      onClick={() => runMatches(item)}
                    >
                      <div
                        className={`compact-thumb ${item.report_type.toLowerCase()}`}
                      >
                        {item.image_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={item.image_url} alt="" />
                        ) : (
                          <span>
                            {item.report_type === "LOST" ? "?" : "✓"}
                          </span>
                        )}
                      </div>
                      <div>
                        <strong>{item.title}</strong>
                        <span>
                          {item.location} • {formatDate(item.event_date)}
                        </span>
                      </div>
                      <StatusPill
                        status={item.status}
                        label={item.report_type}
                      />
                      <span className="row-arrow">›</span>
                    </button>
                  ))}
                  {!items.length && (
                    <EmptyState
                      icon="⌕"
                      title="No reports yet"
                      text="Create the first lost or found report."
                    />
                  )}
                </div>
              </div>

              <aside className="panel activity-panel">
                <div className="panel-head">
                  <div>
                    <p className="eyebrow">YOUR ACTIVITY</p>
                    <h2>Quick status</h2>
                  </div>
                </div>
                <div className="progress-ring">
                  <div>
                    <strong>{stats.my_reports}</strong>
                    <span>My reports</span>
                  </div>
                </div>
                <div className="activity-metrics">
                  <div>
                    <span>Unread updates</span>
                    <strong>{unreadCount}</strong>
                  </div>
                  <div>
                    <span>Claims visible</span>
                    <strong>{claims.length}</strong>
                  </div>
                </div>
                <button
                  className="secondary-button wide"
                  onClick={() => setTab("notifications")}
                >
                  Open notification centre
                </button>
              </aside>
            </section>
          </div>
        )}

        {tab === "items" && (
          <section className="panel registry-panel">
            <div className="panel-head registry-head">
              <div>
                <p className="eyebrow">SEARCHABLE REGISTRY</p>
                <h2>Active campus reports</h2>
                <p>
                  Public details are searchable. Ownership evidence stays
                  private.
                </p>
              </div>
              <div className="export-actions">
                <button
                  className="secondary-button"
                  onClick={() => downloadExport("pdf")}
                >
                  PDF
                </button>
                <button
                  className="secondary-button"
                  onClick={() => downloadExport("xlsx")}
                >
                  Excel
                </button>
              </div>
            </div>

            <div className="filter-bar">
              <div className="search-field">
                <span>⌕</span>
                <input
                  value={search}
                  placeholder="Search title, category, color or location"
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>
              <select
                value={typeFilter}
                onChange={(event) => setTypeFilter(event.target.value)}
              >
                <option value="">All report types</option>
                <option value="LOST">Lost items</option>
                <option value="FOUND">Found items</option>
              </select>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="">All statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="CLAIMED">Claim in progress</option>
                <option value="RETURNED">Returned</option>
                <option value="CLOSED">Closed</option>
              </select>
              <button
                className="primary-button"
                onClick={() =>
                  loadItems().catch((error) =>
                    showToast(getErrorMessage(error), "error"),
                  )
                }
              >
                Apply filters
              </button>
            </div>

            {items.length ? (
              <div className="item-grid">
                {items.map((item) => (
                  <article className="item-card" key={item.id}>
                    <div className="item-image">
                      {item.image_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={item.image_url} alt={item.title} />
                      ) : (
                        <div className="image-placeholder">
                          <span>{item.report_type === "LOST" ? "?" : "✓"}</span>
                          <small>No image provided</small>
                        </div>
                      )}
                      <span
                        className={`report-badge ${item.report_type.toLowerCase()}`}
                      >
                        {item.report_type}
                      </span>
                      <StatusPill status={item.status} />
                    </div>
                    <div className="item-content">
                      <div className="item-reference">
                        {item.reference_code}
                      </div>
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                      <div className="item-tags">
                        <span>{item.category}</span>
                        {item.color && <span>{item.color}</span>}
                        {item.brand && <span>{item.brand}</span>}
                      </div>
                      <div className="item-meta">
                        <span>⌖ {item.location}</span>
                        <span>◷ {formatDate(item.event_date)}</span>
                      </div>
                      <button
                        className="match-button"
                        disabled={actionLoading}
                        onClick={() => runMatches(item)}
                      >
                        <span>✦</span> Find intelligent matches
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                icon="⌕"
                title="No reports match these filters"
                text="Try a broader search or publish a new report."
                action={
                  <button
                    className="primary-button"
                    onClick={() => setTab("report")}
                  >
                    Report an item
                  </button>
                }
              />
            )}
          </section>
        )}

        {tab === "report" && (
          <section className="report-layout">
            <form className="panel report-form" onSubmit={createItem}>
              <div className="panel-head">
                <div>
                  <p className="eyebrow">NEW REPORT</p>
                  <h2>Tell us about the item</h2>
                  <p>
                    Clear, specific details improve the quality of AI
                    suggestions.
                  </p>
                </div>
              </div>

              <div className="segmented-control">
                <button
                  type="button"
                  className={
                    itemForm.report_type === "LOST" ? "active lost" : ""
                  }
                  onClick={() =>
                    setItemForm({
                      ...itemForm,
                      report_type: "LOST",
                    })
                  }
                >
                  <span>↙</span>
                  <div>
                    <strong>I lost an item</strong>
                    <small>Help me find it</small>
                  </div>
                </button>
                <button
                  type="button"
                  className={
                    itemForm.report_type === "FOUND" ? "active found" : ""
                  }
                  onClick={() =>
                    setItemForm({
                      ...itemForm,
                      report_type: "FOUND",
                    })
                  }
                >
                  <span>↗</span>
                  <div>
                    <strong>I found an item</strong>
                    <small>Help return it</small>
                  </div>
                </button>
              </div>

              <div className="form-two">
                <Field label="Item title">
                  <input
                    value={itemForm.title}
                    placeholder="Example: Black leather wallet"
                    required
                    onChange={(event) =>
                      setItemForm({
                        ...itemForm,
                        title: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Category">
                  <select
                    value={itemForm.category}
                    required
                    onChange={(event) =>
                      setItemForm({
                        ...itemForm,
                        category: event.target.value,
                      })
                    }
                  >
                    <option value="">Select category</option>
                    {categories.map((category) => (
                      <option key={category} value={category}>
                        {category}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="form-three">
                <Field label="Color">
                  <input
                    value={itemForm.color}
                    placeholder="Black"
                    onChange={(event) =>
                      setItemForm({
                        ...itemForm,
                        color: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Brand">
                  <input
                    value={itemForm.brand}
                    placeholder="Optional"
                    onChange={(event) =>
                      setItemForm({
                        ...itemForm,
                        brand: event.target.value,
                      })
                    }
                  />
                </Field>
                <Field label="Date">
                  <input
                    value={itemForm.event_date}
                    type="date"
                    required
                    onChange={(event) =>
                      setItemForm({
                        ...itemForm,
                        event_date: event.target.value,
                      })
                    }
                  />
                </Field>
              </div>

              <Field label="Campus location">
                <input
                  value={itemForm.location}
                  placeholder="Example: Block 5 Auditorium"
                  required
                  onChange={(event) =>
                    setItemForm({
                      ...itemForm,
                      location: event.target.value,
                    })
                  }
                />
              </Field>

              <Field
                label="Detailed description"
                hint="Avoid publishing highly sensitive ownership evidence here."
              >
                <textarea
                  value={itemForm.description}
                  placeholder="Describe material, shape, visible marks and where it was last seen…"
                  required
                  onChange={(event) =>
                    setItemForm({
                      ...itemForm,
                      description: event.target.value,
                    })
                  }
                />
              </Field>

              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    setItemForm(initialItemForm);
                    setItemImage(null);
                  }}
                >
                  Clear form
                </button>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={actionLoading}
                >
                  {actionLoading ? "Publishing…" : "Publish report"}
                </button>
              </div>
            </form>

            <aside className="panel upload-panel">
              <div>
                <p className="eyebrow">ITEM PHOTO</p>
                <h2>Add a clear image</h2>
                <p>
                  JPG, PNG or WEBP up to 6 MB. Images improve visual
                  recognition during manual review.
                </p>
              </div>
              <label className={`upload-zone ${imagePreview ? "has-image" : ""}`}>
                {imagePreview ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={imagePreview} alt="Selected item preview" />
                    <span className="replace-image">Replace image</span>
                  </>
                ) : (
                  <>
                    <div className="upload-icon">⇧</div>
                    <strong>Choose an item photo</strong>
                    <span>Click to browse from your device</span>
                  </>
                )}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) =>
                    setItemImage(event.target.files?.[0] ?? null)
                  }
                />
              </label>
              {itemImage && (
                <div className="file-row">
                  <span>✓</span>
                  <div>
                    <strong>{itemImage.name}</strong>
                    <small>
                      {(itemImage.size / 1024 / 1024).toFixed(2)} MB
                    </small>
                  </div>
                  <button
                    type="button"
                    onClick={() => setItemImage(null)}
                  >
                    ×
                  </button>
                </div>
              )}
              <div className="privacy-card">
                <span>◆</span>
                <div>
                  <strong>Privacy reminder</strong>
                  <p>
                    Keep serial numbers, hidden marks and private contents
                    for the ownership-claim form.
                  </p>
                </div>
              </div>
            </aside>
          </section>
        )}

        {tab === "matches" && (
          <section className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">EXPLAINABLE AI</p>
                <h2>Suggested item matches</h2>
                <p>
                  Scores combine text, category, color, brand, location
                  and date. They do not prove ownership.
                </p>
              </div>
              <button
                className="secondary-button"
                onClick={() => setTab("items")}
              >
                Choose another item
              </button>
            </div>

            {matches.length ? (
              <div className="match-list">
                {matches.map((match, index) => (
                  <article className="match-card" key={match.item.id}>
                    <div className="match-rank">
                      <span>#{index + 1}</span>
                      <strong>{match.score}%</strong>
                      <small>confidence</small>
                    </div>
                    <div className="match-item-image">
                      {match.item.image_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={match.item.image_url}
                          alt={match.item.title}
                        />
                      ) : (
                        <span>✦</span>
                      )}
                    </div>
                    <div className="match-body">
                      <div>
                        <span className="item-reference">
                          {match.item.reference_code}
                        </span>
                        <h3>{match.item.title}</h3>
                        <p>{match.item.description}</p>
                      </div>
                      <div className="match-reasons">
                        {match.explanation.map((reason) => (
                          <span key={reason}>✓ {reason}</span>
                        ))}
                      </div>
                      <div className="item-meta">
                        <span>⌖ {match.item.location}</span>
                        <span>◷ {formatDate(match.item.event_date)}</span>
                      </div>
                    </div>
                    {match.item.report_type === "FOUND" && (
                      <button
                        className="primary-button"
                        onClick={() => {
                          setClaimItemId(String(match.item.id));
                          setTab("claims");
                        }}
                      >
                        Submit claim
                      </button>
                    )}
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState
                icon="✦"
                title="No match results loaded"
                text="Open Lost & Found and select “Find intelligent matches” on a report."
                action={
                  <button
                    className="primary-button"
                    onClick={() => setTab("items")}
                  >
                    Browse reports
                  </button>
                }
              />
            )}
          </section>
        )}

        {tab === "claims" && (
          <section className="claims-layout">
            <form className="panel claim-form" onSubmit={createClaim}>
              <div className="panel-head">
                <div>
                  <p className="eyebrow">PRIVATE EVIDENCE</p>
                  <h2>Submit ownership claim</h2>
                  <p>
                    Evidence is restricted to the secure claim workflow.
                  </p>
                </div>
              </div>
              <Field label="Found item">
                <select
                  value={claimItemId}
                  required
                  onChange={(event) =>
                    setClaimItemId(event.target.value)
                  }
                >
                  <option value="">Select a found item</option>
                  {foundItems.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.reference_code} — {item.title}
                    </option>
                  ))}
                </select>
              </Field>
              <Field
                label="Ownership evidence"
                hint="Describe hidden marks, private contents, serial details or other facts only the owner would know."
              >
                <textarea
                  value={claimDetails}
                  minLength={20}
                  required
                  placeholder="Provide detailed, private ownership evidence…"
                  onChange={(event) =>
                    setClaimDetails(event.target.value)
                  }
                />
              </Field>
              <Field label="Additional proof notes">
                <textarea
                  value={proofText}
                  placeholder="Receipt details, identifying information or staff notes…"
                  onChange={(event) =>
                    setProofText(event.target.value)
                  }
                />
              </Field>
              <button
                className="primary-button wide"
                type="submit"
                disabled={actionLoading || !foundItems.length}
              >
                Submit secure claim
              </button>
            </form>

            <section className="panel claims-list-panel">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">
                    {isReviewer ? "REVIEW QUEUE" : "MY CLAIMS"}
                  </p>
                  <h2>
                    {isReviewer
                      ? "Ownership review"
                      : "Claim progress"}
                  </h2>
                </div>
                <StatusPill
                  status="SUBMITTED"
                  label={`${claims.filter((claim) => claim.status === "SUBMITTED").length} pending`}
                />
              </div>

              <div className="claim-list">
                {claims.map((claim) => (
                  <article className="claim-card" key={claim.id}>
                    <div className="claim-top">
                      <div>
                        <span className="item-reference">
                          {claim.item_reference}
                        </span>
                        <h3>{claim.item_title}</h3>
                        <p>
                          Claim #{claim.id} by {claim.claimant_name} •{" "}
                          {formatDate(claim.created_at)}
                        </p>
                      </div>
                      <StatusPill status={claim.status} />
                    </div>

                    <div className="evidence-box">
                      <span>Private ownership evidence</span>
                      <p>{claim.ownership_details}</p>
                      {claim.proof_text && (
                        <small>{claim.proof_text}</small>
                      )}
                    </div>

                    {claim.review_note && (
                      <div className="review-note">
                        <strong>Review note</strong>
                        <p>{claim.review_note}</p>
                      </div>
                    )}

                    {isReviewer && claim.status === "SUBMITTED" && (
                      <div className="review-controls">
                        <input
                          value={reviewNote}
                          placeholder="Optional review note"
                          onChange={(event) =>
                            setReviewNote(event.target.value)
                          }
                        />
                        <div>
                          <button
                            className="danger-button"
                            disabled={actionLoading}
                            onClick={() =>
                              reviewClaim(claim, "reject")
                            }
                          >
                            Reject
                          </button>
                          <button
                            className="primary-button"
                            disabled={actionLoading}
                            onClick={() =>
                              reviewClaim(claim, "approve")
                            }
                          >
                            Approve claim
                          </button>
                        </div>
                      </div>
                    )}

                    {claim.handover_token && (
                      <div className="handover-card">
                        <div className="qr-wrap">
                          <QRCodeSVG
                            value={claim.handover_token}
                            size={120}
                            marginSize={2}
                          />
                        </div>
                        <div>
                          <span>SECURE HANDOVER READY</span>
                          <strong>OTP: {claim.handover_otp}</strong>
                          <small>
                            Token: {claim.handover_token}
                          </small>
                          <p>
                            Expires{" "}
                            {claim.handover_expires_at
                              ? formatDate(
                                  claim.handover_expires_at,
                                )
                              : "soon"}
                          </p>
                        </div>
                        {isReviewer && (
                          <button
                            className="secondary-button"
                            onClick={() => {
                              setHandoverToken(
                                claim.handover_token ?? "",
                              );
                              setHandoverOtp(
                                claim.handover_otp ?? "",
                              );
                              setTab("handover");
                            }}
                          >
                            Open handover
                          </button>
                        )}
                      </div>
                    )}
                  </article>
                ))}

                {!claims.length && (
                  <EmptyState
                    icon="✓"
                    title="No claims yet"
                    text={
                      isReviewer
                        ? "New ownership claims will appear here for review."
                        : "Select an active found item to submit a claim."
                    }
                  />
                )}
              </div>
            </section>
          </section>
        )}

        {tab === "messages" && (
          <section className="messages-layout">
            <aside className="panel conversation-list">
              <div className="panel-head">
                <div>
                  <p className="eyebrow">CLAIM THREADS</p>
                  <h2>Conversations</h2>
                </div>
              </div>
              {claims.map((claim) => (
                <button
                  key={claim.id}
                  className={
                    selectedClaimId === String(claim.id)
                      ? "active"
                      : ""
                  }
                  onClick={() => loadMessages(String(claim.id))}
                >
                  <div className="avatar small">
                    {initials(claim.item_title)}
                  </div>
                  <div>
                    <strong>{claim.item_title}</strong>
                    <span>
                      Claim #{claim.id} • {claim.status}
                    </span>
                  </div>
                  <b>{claim.message_count ?? 0}</b>
                </button>
              ))}
              {!claims.length && (
                <EmptyState
                  icon="◌"
                  title="No claim conversations"
                  text="Messages become available after a claim is submitted."
                />
              )}
            </aside>

            <section className="panel chat-panel">
              {selectedClaim ? (
                <>
                  <div className="chat-head">
                    <div>
                      <span className="item-reference">
                        {selectedClaim.item_reference}
                      </span>
                      <h2>{selectedClaim.item_title}</h2>
                      <p>
                        Secure discussion for claim #{selectedClaim.id}
                      </p>
                    </div>
                    <StatusPill status={selectedClaim.status} />
                  </div>
                  <div className="message-stream">
                    {messages.map((message) => {
                      const mine =
                        message.sender_name === user.username;
                      return (
                        <div
                          className={`message-bubble ${
                            mine ? "mine" : ""
                          }`}
                          key={message.id}
                        >
                          <span>{message.sender_name}</span>
                          <p>{message.message}</p>
                          <small>
                            {new Intl.DateTimeFormat("en-IN", {
                              hour: "2-digit",
                              minute: "2-digit",
                              day: "2-digit",
                              month: "short",
                            }).format(new Date(message.created_at))}
                          </small>
                        </div>
                      );
                    })}
                    {!messages.length && (
                      <EmptyState
                        icon="◌"
                        title="Start the secure conversation"
                        text="Use this thread for claim-related clarification only."
                      />
                    )}
                  </div>
                  <form className="message-composer" onSubmit={sendMessage}>
                    <input
                      value={newMessage}
                      maxLength={2000}
                      placeholder="Write a secure claim message…"
                      required
                      onChange={(event) =>
                        setNewMessage(event.target.value)
                      }
                    />
                    <button
                      className="primary-button"
                      disabled={actionLoading}
                    >
                      Send
                    </button>
                  </form>
                </>
              ) : (
                <EmptyState
                  icon="◌"
                  title="Select a claim thread"
                  text="Choose a conversation from the left to view secure messages."
                />
              )}
            </section>
          </section>
        )}

        {tab === "handover" && (
          <section className="handover-layout">
            <form className="panel handover-form" onSubmit={completeHandover}>
              <div className="handover-hero-icon">▦</div>
              <p className="eyebrow">AUTHORIZED STAFF ONLY</p>
              <h2>Complete secure handover</h2>
              <p>
                Scan or enter the approved QR token, then verify the
                claimant&apos;s 6-digit OTP.
              </p>
              <Field label="QR handover token">
                <input
                  value={handoverToken}
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  required
                  onChange={(event) =>
                    setHandoverToken(event.target.value)
                  }
                />
              </Field>
              <Field label="One-time password">
                <input
                  className="otp-input"
                  value={handoverOtp}
                  inputMode="numeric"
                  maxLength={6}
                  placeholder="000000"
                  required
                  onChange={(event) =>
                    setHandoverOtp(
                      event.target.value.replace(/\D/g, ""),
                    )
                  }
                />
              </Field>
              <button
                className="primary-button wide"
                disabled={actionLoading || !isReviewer}
              >
                {actionLoading
                  ? "Verifying handover…"
                  : "Verify & complete return"}
              </button>
              {!isReviewer && (
                <div className="warning-card">
                  This action requires faculty or administrator access.
                </div>
              )}
            </form>

            <aside className="panel handover-guide">
              <p className="eyebrow">VERIFICATION PROTOCOL</p>
              <h2>Three secure checks</h2>
              <ol className="step-list">
                <li>
                  <span>1</span>
                  <div>
                    <strong>Confirm approved claim</strong>
                    <p>
                      Verify the claim status and authorized reviewer.
                    </p>
                  </div>
                </li>
                <li>
                  <span>2</span>
                  <div>
                    <strong>Validate QR token</strong>
                    <p>
                      Tokens are unique, time-limited and single-use.
                    </p>
                  </div>
                </li>
                <li>
                  <span>3</span>
                  <div>
                    <strong>Enter claimant OTP</strong>
                    <p>
                      The final OTP confirms the in-person return.
                    </p>
                  </div>
                </li>
              </ol>

              {handoverReceipt && (
                <div className="receipt-card">
                  <div className="receipt-check">✓</div>
                  <h3>Handover completed</h3>
                  {Object.entries(handoverReceipt).map(([key, value]) => (
                    <div key={key}>
                      <span>{key.replaceAll("_", " ")}</span>
                      <strong>{String(value)}</strong>
                    </div>
                  ))}
                </div>
              )}
            </aside>
          </section>
        )}

        {tab === "notifications" && (
          <section className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">REAL-TIME UPDATES</p>
                <h2>Notification centre</h2>
                <p>
                  Claim decisions, handover events and report activity.
                </p>
              </div>
              <button
                className="secondary-button"
                onClick={markAllRead}
                disabled={!unreadCount}
              >
                Mark all read
              </button>
            </div>

            <div className="notification-list">
              {notifications.map((notification) => (
                <button
                  key={notification.id}
                  className={
                    notification.is_read ? "" : "unread"
                  }
                  onClick={() => markNotificationRead(notification)}
                >
                  <span className="notification-icon">
                    {notification.notification_type === "CLAIM"
                      ? "✓"
                      : notification.notification_type === "HANDOVER"
                        ? "▦"
                        : notification.notification_type === "MESSAGE"
                          ? "◌"
                          : "●"}
                  </span>
                  <div>
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <small>{formatDate(notification.created_at)}</small>
                  </div>
                  {!notification.is_read && <b />}
                </button>
              ))}
              {!notifications.length && (
                <EmptyState
                  icon="●"
                  title="You are all caught up"
                  text="New activity will appear here automatically."
                />
              )}
            </div>
          </section>
        )}

        {tab === "assistant" && (
          <section className="assistant-layout">
            <div className="panel assistant-panel">
              <div className="assistant-head">
                <div className="assistant-orb">◇</div>
                <div>
                  <p className="eyebrow">INFORMATIONAL ASSISTANT</p>
                  <h2>Ask TRACK-IT</h2>
                  <p>
                    Guidance for reports, claims, matching and handover.
                  </p>
                </div>
              </div>
              <div className="assistant-stream">
                {chatHistory.map((message, index) => (
                  <div
                    key={`${message.from}-${index}`}
                    className={`assistant-message ${message.from}`}
                  >
                    {message.from === "assistant" && (
                      <span className="assistant-mini">◇</span>
                    )}
                    <p>{message.text}</p>
                  </div>
                ))}
              </div>
              <form className="assistant-composer" onSubmit={askAssistant}>
                <input
                  value={chatQuestion}
                  placeholder="Ask: How do I claim a found item?"
                  required
                  onChange={(event) =>
                    setChatQuestion(event.target.value)
                  }
                />
                <button className="primary-button">Ask assistant</button>
              </form>
            </div>

            <aside className="panel quick-help">
              <p className="eyebrow">QUICK QUESTIONS</p>
              <h2>Popular topics</h2>
              {[
                "How do I report a lost item?",
                "How does AI matching work?",
                "What evidence is needed for a claim?",
                "How does QR handover work?",
                "How is my privacy protected?",
              ].map((question) => (
                <button
                  key={question}
                  onClick={() => setChatQuestion(question)}
                >
                  <span>?</span>
                  {question}
                </button>
              ))}
              <div className="assistant-disclaimer">
                AI guidance is informational and never approves ownership.
              </div>
            </aside>
          </section>
        )}
      </section>

      {toast && <div className={`toast ${toastTone}`}>{toast}</div>}
    </main>
  );
}
