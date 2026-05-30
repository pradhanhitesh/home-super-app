import { createRouter, createWebHistory } from "vue-router";
import { watch } from "vue";
import { useAuthStore } from "@/stores/auth";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    name: "Dashboard",
    component: () => import("@/views/DashboardView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/finance",
    name: "Finance",
    component: () => import("@/views/FinanceView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/finance/settings",
    name: "FinanceSettings",
    component: () => import("@/views/FinanceSettingsView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/reminders",
    name: "Reminders",
    component: () => import("@/views/RemindersView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/notes",
    name: "Notes",
    component: () => import("@/views/NotesView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/health",
    name: "Health",
    component: () => import("@/views/HealthView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("@/views/SettingsView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/NotFoundView.vue"),
    meta: { public: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  // Wait for Firebase auth to initialize before making routing decisions.
  // Without this, the guard sees isAuthenticated=false on every page refresh
  // and incorrectly redirects to /login before the token is verified.
  if (authStore.loading) {
    await new Promise((resolve) => {
      const unwatch = watch(
        () => authStore.loading,
        (loading) => {
          if (!loading) {
            unwatch();
            resolve();
          }
        }
      );
    });
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "Login" };
  }
  if (to.path === "/login" && authStore.isAuthenticated) {
    return { name: "Dashboard" };
  }
});

export default router;
