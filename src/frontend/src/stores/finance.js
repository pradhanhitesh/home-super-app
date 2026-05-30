import { defineStore } from "pinia";
import { ref } from "vue";
import { useAuthStore } from "./auth";

export const useFinanceStore = defineStore("finance", () => {
  const authStore = useAuthStore();

  const settings = ref(null);
  const summary = ref(null);

  async function fetchSettings() {
    const res = await authStore.apiFetch("/api/finance/settings");
    if (res.ok) settings.value = await res.json();
  }

  async function fetchSummary(month = null) {
    const q = month ? `?month=${month}` : "";
    const res = await authStore.apiFetch(`/api/finance/summary${q}`);
    if (res.ok) summary.value = await res.json();
  }

  function categoriesForUser(userId) {
    if (!settings.value) return [];
    const { categories, assignments } = settings.value;
    const ids = new Set(
      assignments.filter((a) => a.user_id === userId).map((a) => a.category_id)
    );
    return categories.filter((c) => ids.has(c.id));
  }

  return { settings, summary, fetchSettings, fetchSummary, categoriesForUser };
});
