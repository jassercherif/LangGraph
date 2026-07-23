// ── State ─────────────────────────────────────────────────────────────────────
let currentSessionId = null;
let latestAnswerMarkdown = "";

// ── Auth helpers ──────────────────────────────────────────────────────────────
function getToken() { return localStorage.getItem("tm_token"); }
function getUsername() { return localStorage.getItem("tm_username"); }

function saveAuth(token, username) {
    localStorage.setItem("tm_token", token);
    localStorage.setItem("tm_username", username);
}

function clearAuth() {
    localStorage.removeItem("tm_token");
    localStorage.removeItem("tm_username");
}

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${getToken()}`
    };
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    if (getToken()) {
        bootstrapAuthenticatedState();
    } else {
        showAuthModal();
    }
});

async function bootstrapAuthenticatedState() {
    try {
        const res = await fetch("/auth/me", {
            headers: {
                "Authorization": `Bearer ${getToken()}`
            }
        });
        if (!res.ok) {
            logout();
            return;
        }
        const data = await res.json();
        if (data.username) {
            localStorage.setItem("tm_username", data.username);
        }
        showApp();
    } catch {
        logout();
    }
}

function showAuthModal() {
    document.getElementById("authOverlay").classList.remove("hidden");
    document.getElementById("mainLayout").classList.add("hidden");
    document.getElementById("topBar").classList.add("hidden");
    document.getElementById("mainFooter").classList.add("hidden");
}

function showApp() {
    document.getElementById("authOverlay").classList.add("hidden");
    document.getElementById("mainLayout").classList.remove("hidden");
    document.getElementById("topBar").classList.remove("hidden");
    document.getElementById("mainFooter").classList.remove("hidden");
    document.getElementById("topBarUsername").textContent = getUsername();
    loadSessions();
}

// ── Auth tab toggle ───────────────────────────────────────────────────────────
function switchTab(tab) {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const loginTab = document.getElementById("loginTab");
    const registerTab = document.getElementById("registerTab");

    if (tab === "login") {
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
        loginTab.classList.add("active");
        registerTab.classList.remove("active");
    } else {
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
        loginTab.classList.remove("active");
        registerTab.classList.add("active");
    }
}

// ── Login ─────────────────────────────────────────────────────────────────────
async function handleLogin(event) {
    event.preventDefault();
    const errEl = document.getElementById("loginError");
    errEl.classList.add("hidden");
    setAuthLoading("login", true);

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (!res.ok) {
            errEl.textContent = data.detail || "Login failed.";
            errEl.classList.remove("hidden");
            return;
        }

        saveAuth(data.access_token, data.username);
        showApp();
    } catch {
        errEl.textContent = "Network error. Please try again.";
        errEl.classList.remove("hidden");
    } finally {
        setAuthLoading("login", false);
    }
}

// ── Register ──────────────────────────────────────────────────────────────────
async function handleRegister(event) {
    event.preventDefault();
    const errEl = document.getElementById("registerError");
    const successEl = document.getElementById("registerSuccess");
    errEl.classList.add("hidden");
    successEl.classList.add("hidden");
    setAuthLoading("register", true);

    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;

    try {
        const res = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();

        if (!res.ok) {
            errEl.textContent = data.detail || "Registration failed.";
            errEl.classList.remove("hidden");
            return;
        }

        successEl.textContent = "Account created! You can now log in.";
        successEl.classList.remove("hidden");
        document.getElementById("registerForm").reset();
        setTimeout(() => switchTab("login"), 1500);
    } catch {
        errEl.textContent = "Network error. Please try again.";
        errEl.classList.remove("hidden");
    } finally {
        setAuthLoading("register", false);
    }
}

function setAuthLoading(form, isLoading) {
    const btn = document.getElementById(`${form}Btn`);
    const text = document.getElementById(`${form}BtnText`);
    const loader = document.getElementById(`${form}BtnLoader`);
    btn.disabled = isLoading;
    text.classList.toggle("hidden", isLoading);
    loader.classList.toggle("hidden", !isLoading);
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
    clearAuth();
    currentSessionId = null;
    document.getElementById("resultSection").classList.add("hidden");
    document.getElementById("errorBox").classList.add("hidden");
    closeSidebar();
    showAuthModal();
    document.getElementById("topBarUsername").textContent = "";
}

// ── Mobile sidebar ────────────────────────────────────────────────────────────
function toggleSidebar() {
    document.getElementById("sessionsPanel").classList.toggle("open");
    document.getElementById("sidebarOverlay").classList.toggle("open");
}

function closeSidebar() {
    document.getElementById("sessionsPanel").classList.remove("open");
    document.getElementById("sidebarOverlay").classList.remove("open");
}

// ── Sessions ──────────────────────────────────────────────────────────────────
async function loadSessions() {
    try {
        const res = await fetch("/api/sessions", { headers: authHeaders() });
        if (res.status === 401) { logout(); return; }
        if (!res.ok) return;
        const data = await res.json();
        renderSessions(data.sessions || []);
        updateNewTripButtonState((data.sessions || []).length > 0);
    } catch { /* silent */ }
}

function updateNewTripButtonState(hasSessions) {
    const btn = document.querySelector(".new-session-btn");
    if (!btn) return;
    btn.disabled = !hasSessions && !currentSessionId;
    btn.title = btn.disabled ? "Start by generating your first trip" : "New Trip";
}

function renderSessions(sessions) {
    const list = document.getElementById("sessionsList");
    list.innerHTML = "";

    if (sessions.length === 0) {
        list.innerHTML = '<li class="sessions-empty">No trips yet</li>';
        return;
    }

    sessions.forEach(s => {
        const li = document.createElement("li");
        li.className = "session-item" + (s.session_id === currentSessionId ? " active" : "");
        li.dataset.sessionId = s.session_id;

        const title = document.createElement("span");
        title.className = "session-title";
        title.textContent = s.title || "Untitled Trip";
        title.title = s.title;
        title.onclick = () => switchSession(s.session_id, s.title);

        const delBtn = document.createElement("button");
        delBtn.className = "session-delete";
        delBtn.textContent = "×";
        delBtn.title = "Delete session";
        delBtn.onclick = (e) => { e.stopPropagation(); deleteSession(s.session_id); };

        li.appendChild(title);
        li.appendChild(delBtn);
        list.appendChild(li);
    });
}

// Switching to a past trip now actually loads its saved plan instead of
// just clearing the view. Assumes GET /api/sessions/{id} returns
// { session_id, title, answer } — adjust the field names below if your
// backend's response shape differs.
async function switchSession(sessionId, title) {
    currentSessionId = sessionId;
    hideError();
    closeSidebar();

    document.querySelectorAll(".session-item").forEach(el => {
        el.classList.toggle("active", el.dataset.sessionId === sessionId);
    });

    document.getElementById("userInput").value = "";

    const resultSection = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    resultBox.innerHTML = '<p class="loading-text">Loading trip…</p>';
    resultSection.classList.remove("hidden");
    document.getElementById("sessionInfo").textContent = `Session: ${title || sessionId}`;

    try {
        const res = await fetch(`/api/sessions/${sessionId}`, { headers: authHeaders() });
        if (res.status === 401) { logout(); return; }
        if (!res.ok) throw new Error("Could not load this trip.");
        const data = await res.json();

        if (data.answer) {
            showResult(data.answer, sessionId);
            document.getElementById("sessionInfo").textContent = `Session: ${data.title || sessionId}`;
        } else {
            resultSection.classList.add("hidden");
            showError("This session has no saved response yet. Send a message to generate one.");
        }
    } catch (err) {
        resultSection.classList.add("hidden");
        showError(err.message || "Could not load this trip.");
    }
}

async function deleteSession(sessionId) {
    if (!confirm("Delete this trip session?")) return;
    try {
        const res = await fetch(`/api/sessions/${sessionId}`, {
            method: "DELETE",
            headers: authHeaders()
        });
        if (res.status === 401) { logout(); return; }
        if (sessionId === currentSessionId) {
            currentSessionId = null;
            document.getElementById("resultSection").classList.add("hidden");
        }
        await loadSessions();
    } catch { /* silent */ }
}

function startNewSession() {
    currentSessionId = null;
    document.getElementById("userInput").value = "";
    document.getElementById("resultSection").classList.add("hidden");
    document.getElementById("errorBox").classList.add("hidden");
    document.querySelectorAll(".session-item").forEach(el => el.classList.remove("active"));
    closeSidebar();
    updateNewTripButtonState(true);
}

// ── Travel planner ────────────────────────────────────────────────────────────
function setPrompt(text) {
    document.getElementById("userInput").value = text;
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById("sendBtn");
    document.getElementById("btnText").classList.toggle("hidden", isLoading);
    document.getElementById("btnLoader").classList.toggle("hidden", !isLoading);
    sendBtn.disabled = isLoading;
}

function showError(message) {
    const el = document.getElementById("errorBox");
    el.textContent = message;
    el.classList.remove("hidden");
}

function hideError() {
    const el = document.getElementById("errorBox");
    el.classList.add("hidden");
    el.textContent = "";
}

function showResult(answer, sessionId) {
    latestAnswerMarkdown = answer;
    const resultBox = document.getElementById("resultBox");

    if (typeof marked !== "undefined") {
        resultBox.innerHTML = marked.parse(answer);
    } else {
        resultBox.innerText = answer;
    }

    document.getElementById("sessionInfo").textContent = `Session: ${sessionId}`;
    const resultSection = document.getElementById("resultSection");
    resultSection.classList.remove("hidden");
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function sendMessage() {
    hideError();

    const message = document.getElementById("userInput").value.trim();
    if (!message) {
        showError("Please enter your travel request first.");
        return;
    }

    if (!getToken()) { logout(); return; }

    setLoading(true);

    try {
        const res = await fetch("/api/travel", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ message, session_id: currentSessionId })
        });

        if (res.status === 401) { logout(); return; }

        const data = await res.json();

        if (!res.ok || !data.success) {
            throw new Error(data.error || "Something went wrong.");
        }

        currentSessionId = data.session_id;
        showResult(data.answer, data.session_id);
        await loadSessions(); // refresh sidebar
        document.querySelectorAll(".session-item").forEach(el => {
            el.classList.toggle("active", el.dataset.sessionId === data.session_id);
        });

    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

// ── Copy / PDF ────────────────────────────────────────────────────────────────
function copyResult() {
    const text = document.getElementById("resultBox").innerText;
    if (!text) return;

    navigator.clipboard.writeText(text)
        .then(() => {
            const btn = document.querySelector(".copy-btn");
            const old = btn.textContent;
            btn.textContent = "Copied!";
            setTimeout(() => { btn.textContent = old; }, 1400);
        })
        .catch(() => showError("Could not copy result."));
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");
    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const btn = document.querySelector(".download-btn");
    const old = btn.textContent;
    btn.textContent = "Preparing PDF...";
    btn.disabled = true;

    // .pdf-title is hidden on screen (it's redundant with the page header),
    // but html2canvas snapshots the DOM as-is and ignores @media print rules,
    // so it must be shown explicitly here or it never appears in the PDF.
    const titleEl = pdfContent.querySelector(".pdf-title");
    if (titleEl) titleEl.style.display = "block";

    html2pdf()
        .set({
            margin: 0.5,
            filename: "ai-travel-plan.pdf",
            image: { type: "jpeg", quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
            jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
            pagebreak: { mode: ["avoid-all", "css", "legacy"] }
        })
        .from(pdfContent)
        .save()
        .then(() => {
            if (titleEl) titleEl.style.display = "none";
            btn.textContent = old;
            btn.disabled = false;
        })
        .catch(() => {
            if (titleEl) titleEl.style.display = "none";
            btn.textContent = old;
            btn.disabled = false;
            showError("Could not download PDF.");
        });
}

// ── Keyboard shortcut ─────────────────────────────────────────────────────────
document.addEventListener("keydown", e => {
    if (e.ctrlKey && e.key === "Enter") sendMessage();
    if (e.key === "Escape") closeSidebar();
});