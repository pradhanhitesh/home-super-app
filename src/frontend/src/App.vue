<template>
  <!-- Full-screen spinner while Firebase resolves auth state -->
  <div v-if="authStore.loading" class="app-loading">
    <div class="spinner-border text-primary" role="status" style="width: 2.5rem; height: 2.5rem;">
      <span class="visually-hidden">Loading…</span>
    </div>
  </div>

  <div v-else>
    <NavBar v-if="authStore.isAuthenticated" />
    <main :class="authStore.isAuthenticated ? 'app-main' : ''">
      <RouterView />
    </main>
  </div>

  <!-- Foreground FCM toast -->
  <Transition name="toast-slide">
    <div v-if="fcmToast" class="fcm-toast" @click="fcmToast = null">
      <i class="bi bi-bell-fill fcm-toast-icon"></i>
      <div class="fcm-toast-text">
        <div class="fcm-toast-title">{{ fcmToast.title }}</div>
        <div v-if="fcmToast.body" class="fcm-toast-body">{{ fcmToast.body }}</div>
      </div>
      <button class="fcm-toast-close" @click.stop="fcmToast = null"><i class="bi bi-x"></i></button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import NavBar from "@/components/NavBar.vue";
import { messaging, onMessage } from "@/firebase";

const authStore = useAuthStore();
const router = useRouter();

// Redirect to login whenever auth is lost (logout, session expiry).
watch(
  () => authStore.isAuthenticated,
  (authed) => {
    if (!authed && !authStore.loading) {
      router.push({ name: "Login" });
    }
  }
);

// Foreground FCM messages — show in-app toast
const fcmToast = ref(null);
let toastTimer = null;

try {
  onMessage(messaging, (payload) => {
    clearTimeout(toastTimer);
    fcmToast.value = {
      title: payload.notification?.title ?? "Home App",
      body: payload.notification?.body ?? "",
    };
    toastTimer = setTimeout(() => { fcmToast.value = null; }, 6000);
  });
} catch {
  // messaging not available (e.g. unsupported browser)
}
</script>

<style>
body {
  background-color: #f0f2f5;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}

.app-loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-main {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem;
}

/* FCM foreground toast */
.fcm-toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  background: #1f2937;
  color: #f9fafb;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  max-width: 320px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.25);
  cursor: pointer;
}
.fcm-toast-icon { font-size: 1rem; color: #facc15; margin-top: 0.1rem; flex-shrink: 0; }
.fcm-toast-text { flex: 1; min-width: 0; }
.fcm-toast-title { font-size: 0.85rem; font-weight: 600; }
.fcm-toast-body { font-size: 0.78rem; color: #d1d5db; margin-top: 0.2rem; }
.fcm-toast-close {
  background: none; border: none; color: #9ca3af; cursor: pointer;
  font-size: 1rem; padding: 0; line-height: 1; flex-shrink: 0;
}
.fcm-toast-close:hover { color: #f9fafb; }

.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.25s ease; }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateX(1.5rem); }

/* Global page header pattern — used across all views */
.page-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: #9ca3af;
  margin: 0.25rem 0 0;
}
</style>
