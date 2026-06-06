<template>
  <nav class="app-nav sticky-top">
    <div class="app-nav-inner">
      <!-- Brand -->
      <RouterLink class="app-brand" to="/dashboard">
        <i class="bi bi-house-heart-fill"></i>
        <span>H&M</span>
      </RouterLink>

      <!-- Mobile toggle -->
      <button
        class="nav-toggler d-lg-none"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#mainNav"
        aria-controls="mainNav"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <i class="bi bi-list fs-4"></i>
      </button>

      <!-- Nav links + user -->
      <div class="collapse navbar-collapse" id="mainNav">
        <ul class="nav-links">
          <li v-for="link in navLinks" :key="link.to">
            <RouterLink :to="link.to" class="nav-link-item" active-class="nav-link-active">
              <i :class="`bi ${link.icon}`"></i>
              <span>{{ link.label }}</span>
            </RouterLink>
          </li>
        </ul>

        <div class="nav-user">
          <img
            v-if="authStore.user?.photo_url"
            :src="authStore.user.photo_url"
            :alt="authStore.user.display_name"
            class="user-avatar"
            referrerpolicy="no-referrer"
          />
          <div v-else class="user-avatar-placeholder">
            <i class="bi bi-person-fill"></i>
          </div>
          <span class="user-name d-none d-xl-inline">{{ firstName }}</span>
          <button class="btn-signout" @click="authStore.logout()" title="Sign out">
            <i class="bi bi-box-arrow-right"></i>
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

const firstName = computed(() => authStore.user?.display_name?.split(" ")[0] ?? "");

const navLinks = [
  { to: "/dashboard", icon: "bi-speedometer2", label: "Dashboard" },
  { to: "/finance", icon: "bi-wallet2", label: "Finance" },
  { to: "/reminders", icon: "bi-bell", label: "Reminders" },
  { to: "/notes", icon: "bi-journal-text", label: "Notes" },
  { to: "/health", icon: "bi-heart-pulse", label: "Health" },
  { to: "/settings", icon: "bi-gear", label: "Settings" },
];
</script>

<style scoped>
.app-nav {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  z-index: 1030;
}

.app-nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.25rem;
  height: 58px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.app-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1rem;
  color: #0d6efd;
  text-decoration: none;
  white-space: nowrap;
}

.app-brand i {
  font-size: 1.25rem;
}

.nav-toggler {
  background: none;
  border: none;
  padding: 0.25rem;
  color: #374151;
  margin-left: auto;
  cursor: pointer;
}

.navbar-collapse {
  display: flex !important;
  align-items: center;
  flex: 1;
}

@media (max-width: 991.98px) {
  .navbar-collapse {
    display: none !important;
    position: absolute;
    top: 58px;
    left: 0;
    right: 0;
    background: #fff;
    border-bottom: 1px solid #e5e7eb;
    padding: 0.75rem 1.25rem 1rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    z-index: 1029;
  }

  .navbar-collapse.show {
    display: flex !important;
  }
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
}

@media (max-width: 991.98px) {
  .nav-links {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
}

.nav-link-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}

.nav-link-item:hover {
  background: #f3f4f6;
  color: #111827;
}

.nav-link-active {
  background: #eff6ff;
  color: #0d6efd !important;
}

@media (max-width: 991.98px) {
  .nav-link-item {
    width: 100%;
    padding: 0.55rem 0.75rem;
  }
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-left: auto;
}

@media (max-width: 991.98px) {
  .nav-user {
    margin-left: 0;
    padding-top: 0.5rem;
    border-top: 1px solid #f3f4f6;
    width: 100%;
  }
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #e5e7eb;
}

.user-avatar-placeholder {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 1rem;
}

.user-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.btn-signout {
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.3rem 0.55rem;
  color: #6b7280;
  cursor: pointer;
  font-size: 0.95rem;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}

.btn-signout:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}
</style>
