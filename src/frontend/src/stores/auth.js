import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { signInWithPopup, signOut, onAuthStateChanged } from "firebase/auth";
import { auth, googleProvider, messaging, getToken } from "@/firebase";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const loading = ref(true);
  // Firebase ID token cached for API calls
  const idToken = ref(null);

  const isAuthenticated = computed(() => !!user.value);

  async function _getIdToken(firebaseUser) {
    const token = await firebaseUser.getIdToken();
    idToken.value = token;
    return token;
  }

  async function _loginToBackend(token) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken: token }),
    });
    return res.ok ? res.json() : null;
  }

  /** Register FCM token with backend. Caller must ensure permission is already 'granted'. */
  async function registerFcmToken() {
    const vapidKey = import.meta.env.VITE_FIREBASE_VAPID_KEY;
    if (!vapidKey || !("Notification" in window)) return;
    if (Notification.permission !== "granted") return;
    try {
      const fcmToken = await getToken(messaging, {
        vapidKey,
        serviceWorkerRegistration: await navigator.serviceWorker.register(
          "/firebase-messaging-sw.js"
        ),
      });
      if (fcmToken && idToken.value) {
        await fetch(`${API_BASE}/api/reminders/fcm-token`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${idToken.value}`,
          },
          body: JSON.stringify({ token: fcmToken }),
        });
      }
    } catch (e) {
      console.warn("[FCM] token registration:", e.message);
    }
  }

  function init() {
    return new Promise((resolve) => {
      onAuthStateChanged(auth, async (firebaseUser) => {
        if (firebaseUser) {
          const token = await _getIdToken(firebaseUser);
          const profile = await _loginToBackend(token);
          user.value = profile;
          // Only silently re-register if permission already granted — no prompts on init
          if (profile && "Notification" in window && Notification.permission === "granted") {
            registerFcmToken();
          }
        } else {
          user.value = null;
          idToken.value = null;
        }
        loading.value = false;
        resolve();
      });
    });
  }

  async function loginWithGoogle() {
    const result = await signInWithPopup(auth, googleProvider);
    const token = await _getIdToken(result.user);
    const profile = await _loginToBackend(token);
    if (!profile) {
      await signOut(auth);
      throw new Error("Account not authorized for this application.");
    }
    user.value = profile;
    // Only silently register if permission already granted
    if ("Notification" in window && Notification.permission === "granted") {
      registerFcmToken();
    }
  }

  async function logout() {
    await signOut(auth);
    user.value = null;
    idToken.value = null;
  }

  /** Make an authenticated fetch to /api/* */
  async function apiFetch(path, options = {}) {
    const token = idToken.value;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    return fetch(`${API_BASE}${path}`, { ...options, headers });
  }

  return { user, loading, isAuthenticated, idToken, init, loginWithGoogle, logout, apiFetch, registerFcmToken };
});
