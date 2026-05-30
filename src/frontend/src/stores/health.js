import { ref } from "vue";
import { defineStore } from "pinia";
import { useAuthStore } from "@/stores/auth";

export const useHealthStore = defineStore("health", () => {
  const authStore = useAuthStore();

  const wellbeingEntries = ref([]);
  const menstrualData = ref(null); // { cycles, predicted_next_start, avg_cycle_length }

  async function fetchWellbeing(month = null) {
    const q = month ? `?month=${month}` : "";
    const res = await authStore.apiFetch(`/api/health/wellbeing${q}`);
    if (res.ok) wellbeingEntries.value = await res.json();
  }

  async function fetchMenstrual() {
    const res = await authStore.apiFetch("/api/health/menstrual");
    if (res.ok) menstrualData.value = await res.json();
  }

  return { wellbeingEntries, menstrualData, fetchWellbeing, fetchMenstrual };
});
