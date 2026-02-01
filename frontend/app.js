const API_BASE = "http://127.0.0.1:8000";

const storageKey = "access_token";

const authPage = document.querySelector('[data-page="auth"]');
const dashboardPage = document.querySelector('[data-page="dashboard"]');

const showMessage = (element, message, isError = false) => {
  if (!element) return;
  element.textContent = message;
  element.classList.add("show");
  element.style.background = isError ? "#fee2e2" : "#eef2ff";
  element.style.color = isError ? "#991b1b" : "#3730a3";
};

const clearMessage = (element) => {
  if (!element) return;
  element.textContent = "";
  element.classList.remove("show");
};

const saveToken = (token) => localStorage.setItem(storageKey, token);
const getToken = () => localStorage.getItem(storageKey);
const clearToken = () => localStorage.removeItem(storageKey);

const apiFetch = async (path, options = {}) => {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || "Something went wrong";
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
};

const register = async (payload) => {
  return apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

const login = async (payload) => {
  return apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

const fetchMe = async () => {
  return apiFetch("/me");
};

const generateWorksheet = async (payload) => {
  return apiFetch("/worksheet/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

const logout = () => {
  clearToken();
  window.location.href = "index.html";
};

const initTabs = () => {
  const tabs = document.querySelectorAll(".tab");
  const panels = document.querySelectorAll(".panel");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((item) => item.classList.remove("active"));
      panels.forEach((panel) => panel.classList.remove("active"));
      tab.classList.add("active");
      const target = document.querySelector(`[data-panel="${tab.dataset.tab}"]`);
      if (target) target.classList.add("active");
    });
  });
};

const initAuth = () => {
  initTabs();
  const message = document.getElementById("auth-message");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (getToken()) {
    window.location.href = "dashboard.html";
    return;
  }

  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(message);
    const formData = new FormData(loginForm);
    try {
      const data = await login({
        email: formData.get("email"),
        password: formData.get("password"),
      });
      saveToken(data.access_token);
      window.location.href = "dashboard.html";
    } catch (error) {
      showMessage(message, error.message, true);
    }
  });

  registerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(message);
    const formData = new FormData(registerForm);
    try {
      await register({
        email: formData.get("email"),
        password: formData.get("password"),
      });
      const data = await login({
        email: formData.get("email"),
        password: formData.get("password"),
      });
      saveToken(data.access_token);
      window.location.href = "dashboard.html";
    } catch (error) {
      showMessage(message, error.message, true);
    }
  });
};

const initDashboard = () => {
  const message = document.getElementById("dashboard-message");
  const logoutButton = document.getElementById("logout");
  const form = document.getElementById("worksheet-form");
  const resultSection = document.getElementById("result");
  const resultTitle = document.getElementById("result-title");
  const resultDuration = document.getElementById("result-duration");
  const resultContent = document.getElementById("result-content");
  const resultSolutions = document.getElementById("result-solutions");

  const setLoading = (isLoading) => {
    if (!form) return;
    const button = form.querySelector("button[type='submit']");
    if (button) {
      button.disabled = isLoading;
      button.textContent = isLoading ? "Generating..." : "Generate";
    }
  };

  logoutButton?.addEventListener("click", logout);

  const loadProfile = async () => {
    try {
      const me = await fetchMe();
      document.getElementById("user-email").textContent = me.email;
      document.getElementById("user-credits").textContent = `${me.credits}`;
    } catch (error) {
      if (error.status === 401) {
        logout();
        return;
      }
      showMessage(message, error.message, true);
    }
  };

  loadProfile();

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearMessage(message);
    if (resultSection) resultSection.hidden = true;

    const formData = new FormData(form);
    const activityTypes = form.querySelectorAll("input[name='activity_types']:checked");
    const activities = Array.from(activityTypes).map((item) => item.value);

    if (activities.length === 0) {
      showMessage(message, "Please select at least one activity type.", true);
      return;
    }

    const themeWords = formData
      .get("theme_words")
      .split(",")
      .map((word) => word.trim())
      .filter(Boolean);

    const payload = {
      level: formData.get("level"),
      topic: formData.get("topic"),
      age_group: formData.get("age_group"),
      duration: Number(formData.get("duration")),
      activity_types: activities,
      theme_words: themeWords.length ? themeWords : null,
    };

    try {
      setLoading(true);
      const result = await generateWorksheet(payload);
      if (resultSection) resultSection.hidden = false;
      resultTitle.textContent = result.title;
      resultDuration.textContent = result.estimated_duration;
      resultContent.innerHTML = result.content.map((item) => `<li>${item}</li>`).join("");
      resultSolutions.innerHTML = result.solutions.map((item) => `<li>${item}</li>`).join("");
      document.getElementById("user-credits").textContent = `${result.remaining_credits}`;
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        if (error.status === 401) {
          logout();
          return;
        }
        showMessage(message, error.message, true);
      } else {
        showMessage(message, error.message, true);
      }
    } finally {
      setLoading(false);
    }
  });
};

if (authPage) {
  initAuth();
}

if (dashboardPage) {
  if (!getToken()) {
    window.location.href = "index.html";
  } else {
    initDashboard();
  }
}
