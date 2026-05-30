<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <i class="bi bi-house-heart-fill"></i>
      </div>
      <h1 class="login-title">Home App</h1>
      <p class="login-subtitle">Your household, organised.</p>

      <div v-if="error" class="login-error">
        <i class="bi bi-exclamation-circle-fill me-2"></i>{{ error }}
      </div>

      <button class="google-btn" :disabled="loading" @click="login">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 48 48" style="flex-shrink:0">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
        </svg>
        {{ loading ? "Signing in…" : "Continue with Google" }}
      </button>

      <p class="login-note">Private — authorised accounts only.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();
const loading = ref(false);
const error = ref("");

async function login() {
  loading.value = true;
  error.value = "";
  try {
    await authStore.loginWithGoogle();
    router.push({ name: "Dashboard" });
  } catch (e) {
    error.value = e.message || "Sign-in failed. Try again.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  padding: 1rem;
}

.login-card {
  background: #fff;
  border-radius: 20px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 380px;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.login-logo {
  width: 64px;
  height: 64px;
  background: #eff6ff;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 2rem;
  color: #0d6efd;
}

.login-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.login-subtitle {
  font-size: 0.9rem;
  color: #9ca3af;
  margin: 0.3rem 0 1.75rem;
}

.login-error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  font-size: 0.85rem;
  text-align: left;
  margin-bottom: 1rem;
}

.google-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.7rem 1rem;
  background: #fff;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 0.925rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.google-btn:hover:not(:disabled) {
  border-color: #9ca3af;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  background: #f9fafb;
}

.google-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-note {
  font-size: 0.78rem;
  color: #d1d5db;
  margin: 1.25rem 0 0;
}
</style>
