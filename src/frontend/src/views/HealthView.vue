<template>
  <div>
    <div class="page-header">
      <h1 class="page-title"><i class="bi bi-heart-pulse me-2 text-primary"></i>Health</h1>
      <p class="page-subtitle">Well-being & cycle tracker</p>
    </div>

    <!-- Tabs -->
    <div class="health-tabs mb-4">
      <button
        class="health-tab"
        :class="{ active: tab === 'wellbeing' }"
        @click="tab = 'wellbeing'"
      >
        <i class="bi bi-emoji-smile me-1"></i> Well-being
      </button>
      <button
        class="health-tab"
        :class="{ active: tab === 'cycle' }"
        @click="tab = 'cycle'"
      >
        <i class="bi bi-calendar-heart me-1"></i> Cycle
      </button>
    </div>

    <!-- ── Well-being tab ── -->
    <div v-if="tab === 'wellbeing'">
      <!-- Month nav + Log button -->
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-outline-secondary px-2" @click="shiftMonth(-1)">
            <i class="bi bi-chevron-left"></i>
          </button>
          <span class="month-label">{{ monthLabel }}</span>
          <button class="btn btn-sm btn-outline-secondary px-2" @click="shiftMonth(1)" :disabled="isCurrentMonth">
            <i class="bi bi-chevron-right"></i>
          </button>
        </div>
        <button class="btn btn-sm btn-primary d-flex align-items-center gap-1" @click="openWellbeingModal()">
          <i class="bi bi-plus-lg"></i> Log Today
        </button>
      </div>

      <!-- Charts -->
      <div v-if="!wbLoading && myWbEntries.length >= 2" class="charts-row mb-4">
        <div class="chart-card">
          <div class="chart-title">Mood &amp; Energy</div>
          <div class="chart-wrap">
            <Line :data="wbChartData" :options="lineOptions" />
          </div>
        </div>
        <div class="chart-card" v-if="sleepEntries.length >= 2">
          <div class="chart-title">Sleep Hours</div>
          <div class="chart-wrap">
            <Bar :data="sleepChartData" :options="sleepBarOptions" />
          </div>
        </div>
      </div>

      <div v-if="wbLoading" class="text-center py-5 text-muted">
        <div class="spinner-border spinner-border-sm me-2"></div> Loading…
      </div>

      <div v-else-if="wellbeingEntries.length === 0" class="empty-state">
        <i class="bi bi-emoji-neutral"></i>
        <p>No entries this month. Log your first check-in!</p>
      </div>

      <div v-else class="wb-list">
        <template v-for="(group, d) in groupedWellbeing" :key="d">
          <div class="date-heading">{{ formatDate(d) }}</div>
          <div class="wb-card" v-for="entry in group" :key="entry.id">
            <div class="wb-user-col">
              <img v-if="entry.user_photo" :src="entry.user_photo" class="wb-avatar" :alt="entry.user_name" />
              <div v-else class="wb-avatar-placeholder">{{ initials(entry.user_name) }}</div>
              <span class="wb-user-name">{{ entry.user_name?.split(' ')[0] }}</span>
            </div>
            <div class="wb-metrics">
              <div class="wb-metric">
                <span class="wb-metric-label">Mood</span>
                <div class="wb-bar-wrap">
                  <div class="wb-bar-fill" :style="{ width: (entry.mood / 10 * 100) + '%', background: moodColor(entry.mood) }"></div>
                </div>
                <span class="wb-metric-val">{{ entry.mood }}/10</span>
              </div>
              <div class="wb-metric">
                <span class="wb-metric-label">Energy</span>
                <div class="wb-bar-wrap">
                  <div class="wb-bar-fill" :style="{ width: (entry.energy / 10 * 100) + '%', background: energyColor(entry.energy) }"></div>
                </div>
                <span class="wb-metric-val">{{ entry.energy }}/10</span>
              </div>
              <div v-if="entry.sleep_hours != null" class="wb-sleep">
                <i class="bi bi-moon-stars me-1"></i>{{ entry.sleep_hours }}h sleep
              </div>
              <div v-if="entry.notes" class="wb-notes">{{ entry.notes }}</div>
            </div>
            <div v-if="entry.created_by === currentUserId" class="wb-actions">
              <button class="icon-btn" @click="openWellbeingModal(entry)" title="Edit"><i class="bi bi-pencil"></i></button>
              <button class="icon-btn danger" @click="deleteWellbeing(entry)" title="Delete"><i class="bi bi-trash"></i></button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ── Cycle tab ── -->
    <div v-if="tab === 'cycle'">
      <!-- Prediction card -->
      <div v-if="menstrualData" class="prediction-card mb-4">
        <div class="prediction-inner">
          <div class="prediction-icon"><i class="bi bi-calendar-heart"></i></div>
          <div>
            <div class="prediction-label">Next period predicted</div>
            <div class="prediction-date">
              {{ menstrualData.predicted_next_start ? formatDateFull(menstrualData.predicted_next_start) : 'Log at least 2 cycles to predict' }}
            </div>
            <div v-if="menstrualData.avg_cycle_length" class="prediction-avg">
              Avg cycle: {{ menstrualData.avg_cycle_length }} days
            </div>
          </div>
        </div>
        <button class="btn btn-sm btn-primary" @click="openCycleModal()">
          <i class="bi bi-plus-lg me-1"></i>Log cycle
        </button>
      </div>

      <div v-if="cycleLoading" class="text-center py-5 text-muted">
        <div class="spinner-border spinner-border-sm me-2"></div> Loading…
      </div>

      <div v-else-if="!menstrualData?.cycles?.length" class="empty-state">
        <i class="bi bi-calendar-x"></i>
        <p>No cycles logged yet.</p>
      </div>

      <div v-else class="cycle-list">
        <div v-for="cycle in menstrualData.cycles" :key="cycle.id" class="cycle-card">
          <div class="cycle-dot" :class="cycle.cycle_end ? 'dot-done' : 'dot-active'"></div>
          <div class="cycle-body">
            <div class="cycle-dates">
              <span class="cycle-start">{{ formatDateFull(cycle.cycle_start) }}</span>
              <span class="cycle-arrow">→</span>
              <span v-if="cycle.cycle_end" class="cycle-end">{{ formatDateFull(cycle.cycle_end) }}</span>
              <span v-else class="cycle-ongoing">ongoing</span>
            </div>
            <div class="cycle-meta">
              <span v-if="cycle.cycle_length" class="cycle-len">{{ cycle.cycle_length }} days</span>
              <div v-if="cycle.symptoms?.length" class="cycle-symptoms">
                <span v-for="s in cycle.symptoms" :key="s" class="symptom-chip">{{ s }}</span>
              </div>
              <div v-if="cycle.notes" class="cycle-notes">{{ cycle.notes }}</div>
            </div>
          </div>
          <div class="cycle-actions">
            <button v-if="!cycle.cycle_end" class="btn btn-sm btn-outline-success" @click="endCycle(cycle)">
              End cycle
            </button>
            <button class="icon-btn" @click="openCycleModal(cycle)" title="Edit"><i class="bi bi-pencil"></i></button>
            <button class="icon-btn danger" @click="deleteCycle(cycle)" title="Delete"><i class="bi bi-trash"></i></button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Well-being modal ── -->
    <div class="modal-backdrop-custom" v-if="wbModal.open" @click.self="wbModal.open = false">
      <div class="modal-card">
        <div class="modal-card-header">
          <span>{{ wbModal.id ? 'Edit entry' : 'Log check-in' }}</span>
          <button class="modal-close" @click="wbModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <div class="mb-3">
            <label class="form-label form-label-sm">Date</label>
            <input v-model="wbModal.entry_date" type="date" class="form-control form-control-sm" :max="todayIso" />
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm d-flex justify-content-between">
              <span>Mood <span class="text-danger">*</span></span>
              <span class="score-badge" :style="{ background: moodColor(wbModal.mood) }">{{ wbModal.mood }}/10</span>
            </label>
            <input type="range" min="1" max="10" step="1" v-model.number="wbModal.mood" class="form-range" />
            <div class="range-labels"><span>😞</span><span>😐</span><span>😊</span><span>🤩</span></div>
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm d-flex justify-content-between">
              <span>Energy <span class="text-danger">*</span></span>
              <span class="score-badge" :style="{ background: energyColor(wbModal.energy) }">{{ wbModal.energy }}/10</span>
            </label>
            <input type="range" min="1" max="10" step="1" v-model.number="wbModal.energy" class="form-range" />
            <div class="range-labels"><span>🪫</span><span>😴</span><span>⚡</span><span>🚀</span></div>
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm">Sleep hours</label>
            <input v-model.number="wbModal.sleep_hours" type="number" min="0" max="24" step="0.5" class="form-control form-control-sm" placeholder="e.g. 7.5" />
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm">Notes</label>
            <textarea v-model="wbModal.notes" class="form-control form-control-sm" rows="2" placeholder="How are you feeling?"></textarea>
          </div>

          <div v-if="wbModal.error" class="alert alert-danger py-2 small">{{ wbModal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="wbModal.open = false">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="wbModal.saving" @click="saveWellbeing">
            <span v-if="wbModal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ wbModal.id ? 'Save' : 'Log' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Cycle modal ── -->
    <div class="modal-backdrop-custom" v-if="cycleModal.open" @click.self="cycleModal.open = false">
      <div class="modal-card">
        <div class="modal-card-header">
          <span>{{ cycleModal.id ? 'Edit cycle' : 'Log cycle' }}</span>
          <button class="modal-close" @click="cycleModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label form-label-sm">Start date <span class="text-danger">*</span></label>
              <input v-model="cycleModal.cycle_start" type="date" class="form-control form-control-sm" :max="todayIso" />
            </div>
            <div class="col-6">
              <label class="form-label form-label-sm">End date</label>
              <input v-model="cycleModal.cycle_end" type="date" class="form-control form-control-sm" :min="cycleModal.cycle_start" :max="todayIso" />
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm">Symptoms</label>
            <div class="symptom-grid">
              <label v-for="s in SYMPTOMS" :key="s" class="symptom-check">
                <input type="checkbox" :value="s" v-model="cycleModal.symptoms" />
                <span>{{ s }}</span>
              </label>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm">Notes</label>
            <textarea v-model="cycleModal.notes" class="form-control form-control-sm" rows="2" placeholder="Optional…"></textarea>
          </div>

          <div v-if="cycleModal.error" class="alert alert-danger py-2 small">{{ cycleModal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="cycleModal.open = false">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="cycleModal.saving" @click="saveCycle">
            <span v-if="cycleModal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ cycleModal.id ? 'Save' : 'Log' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useHealthStore } from "@/stores/health";
import { Line, Bar } from "vue-chartjs";
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Tooltip, Legend, Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler);

const authStore = useAuthStore();
const healthStore = useHealthStore();

const tab = ref("wellbeing");
const wbLoading = ref(true);
const cycleLoading = ref(false);

const todayIso = new Date().toISOString().slice(0, 10);
const currentUserId = computed(() => authStore.user?.id ?? "");

const SYMPTOMS = [
  "Cramps", "Headache", "Bloating", "Fatigue",
  "Mood swings", "Back pain", "Nausea", "Breast tenderness",
];

// ── Month navigation ────────────────────────────────────────────────────────
const today = new Date();
const selYear = ref(today.getFullYear());
const selMonth = ref(today.getMonth() + 1);

const isCurrentMonth = computed(() =>
  selYear.value === today.getFullYear() && selMonth.value === today.getMonth() + 1
);

const monthKey = computed(() =>
  `${selYear.value}-${String(selMonth.value).padStart(2, "0")}`
);

const monthLabel = computed(() => {
  const d = new Date(selYear.value, selMonth.value - 1, 1);
  return d.toLocaleString("en-IN", { month: "long", year: "numeric" });
});

function shiftMonth(delta) {
  let m = selMonth.value + delta;
  let y = selYear.value;
  if (m > 12) { m = 1; y++; }
  if (m < 1) { m = 12; y--; }
  selMonth.value = m;
  selYear.value = y;
}

watch(monthKey, () => loadWellbeing());

// ── Data ────────────────────────────────────────────────────────────────────
const wellbeingEntries = computed(() => healthStore.wellbeingEntries);
const menstrualData = computed(() => healthStore.menstrualData);

const groupedWellbeing = computed(() => {
  const g = {};
  for (const e of wellbeingEntries.value) {
    if (!g[e.entry_date]) g[e.entry_date] = [];
    g[e.entry_date].push(e);
  }
  return g;
});

// ── Charts ─────────────────────────────────────────────────────────────────
const myWbEntries = computed(() =>
  [...wellbeingEntries.value]
    .filter((e) => e.created_by === currentUserId.value)
    .sort((a, b) => a.entry_date.localeCompare(b.entry_date))
);

const sleepEntries = computed(() => myWbEntries.value.filter((e) => e.sleep_hours != null));

const wbChartData = computed(() => {
  const labels = myWbEntries.value.map((e) =>
    new Date(e.entry_date + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" })
  );
  return {
    labels,
    datasets: [
      {
        label: "Mood",
        data: myWbEntries.value.map((e) => e.mood),
        borderColor: "#22c55e",
        backgroundColor: "#22c55e22",
        tension: 0.35,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: "#22c55e",
      },
      {
        label: "Energy",
        data: myWbEntries.value.map((e) => e.energy),
        borderColor: "#60a5fa",
        backgroundColor: "#60a5fa22",
        tension: 0.35,
        fill: true,
        pointRadius: 4,
        pointBackgroundColor: "#60a5fa",
      },
    ],
  };
});

const sleepChartData = computed(() => ({
  labels: sleepEntries.value.map((e) =>
    new Date(e.entry_date + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" })
  ),
  datasets: [{
    label: "Sleep",
    data: sleepEntries.value.map((e) => e.sleep_hours),
    backgroundColor: "#a78bfa55",
    borderColor: "#7c3aed",
    borderWidth: 2,
    borderRadius: 6,
  }],
}));

const lineOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { labels: { boxWidth: 10, font: { size: 11 } } },
    tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw}/10` } },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
    y: { min: 0, max: 10, grid: { color: "#f3f4f6" }, ticks: { font: { size: 10 }, stepSize: 2 } },
  },
};

const sleepBarOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (ctx) => ` ${ctx.raw}h` } },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
    y: { min: 0, grid: { color: "#f3f4f6" }, ticks: { font: { size: 10 }, callback: (v) => v + "h" } },
  },
};

async function loadWellbeing() {
  wbLoading.value = true;
  await healthStore.fetchWellbeing(monthKey.value);
  wbLoading.value = false;
}

async function loadMenstrual() {
  cycleLoading.value = true;
  await healthStore.fetchMenstrual();
  cycleLoading.value = false;
}

watch(tab, (t) => {
  if (t === "cycle" && !menstrualData.value) loadMenstrual();
});

onMounted(async () => {
  await loadWellbeing();
});

// ── Helpers ─────────────────────────────────────────────────────────────────
function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric", month: "short", weekday: "short",
  });
}

function formatDateFull(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric", month: "long", year: "numeric",
  });
}

function initials(name) {
  if (!name) return "?";
  return name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
}

function moodColor(v) {
  if (v <= 3) return "#ef4444";
  if (v <= 5) return "#f97316";
  if (v <= 7) return "#eab308";
  return "#22c55e";
}

function energyColor(v) {
  if (v <= 3) return "#94a3b8";
  if (v <= 5) return "#60a5fa";
  if (v <= 7) return "#34d399";
  return "#a78bfa";
}

// ── Well-being modal ────────────────────────────────────────────────────────
const wbModal = ref({ open: false, id: null, entry_date: todayIso, mood: 7, energy: 7, sleep_hours: "", notes: "", saving: false, error: "" });

function openWellbeingModal(entry = null) {
  if (entry) {
    wbModal.value = {
      open: true, id: entry.id,
      entry_date: entry.entry_date,
      mood: entry.mood,
      energy: entry.energy,
      sleep_hours: entry.sleep_hours ?? "",
      notes: entry.notes ?? "",
      saving: false, error: "",
    };
  } else {
    wbModal.value = {
      open: true, id: null,
      entry_date: todayIso,
      mood: 7, energy: 7,
      sleep_hours: "", notes: "",
      saving: false, error: "",
    };
  }
}

async function saveWellbeing() {
  const m = wbModal.value;
  m.error = "";
  m.saving = true;
  try {
    const payload = {
      entry_date: m.entry_date,
      mood: m.mood,
      energy: m.energy,
      sleep_hours: m.sleep_hours !== "" ? parseFloat(m.sleep_hours) : null,
      notes: m.notes || null,
    };
    const res = await authStore.apiFetch(
      m.id ? `/api/health/wellbeing/${m.id}` : "/api/health/wellbeing",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const d = await res.json();
      m.error = d.error || "Save failed.";
      return;
    }
    wbModal.value.open = false;
    await loadWellbeing();
  } catch {
    m.error = "Network error.";
  } finally {
    m.saving = false;
  }
}

async function deleteWellbeing(entry) {
  if (!confirm(`Delete entry for ${formatDate(entry.entry_date)}?`)) return;
  await authStore.apiFetch(`/api/health/wellbeing/${entry.id}`, { method: "DELETE" });
  await loadWellbeing();
}

// ── Cycle modal ─────────────────────────────────────────────────────────────
const cycleModal = ref({ open: false, id: null, cycle_start: todayIso, cycle_end: "", symptoms: [], notes: "", saving: false, error: "" });

function openCycleModal(cycle = null) {
  if (cycle) {
    cycleModal.value = {
      open: true, id: cycle.id,
      cycle_start: cycle.cycle_start,
      cycle_end: cycle.cycle_end ?? "",
      symptoms: [...(cycle.symptoms || [])],
      notes: cycle.notes ?? "",
      saving: false, error: "",
    };
  } else {
    cycleModal.value = {
      open: true, id: null,
      cycle_start: todayIso, cycle_end: "",
      symptoms: [], notes: "",
      saving: false, error: "",
    };
  }
}

async function saveCycle() {
  const m = cycleModal.value;
  m.error = "";
  if (!m.cycle_start) { m.error = "Start date required."; return; }
  m.saving = true;
  try {
    const payload = {
      cycle_start: m.cycle_start,
      cycle_end: m.cycle_end || null,
      symptoms: m.symptoms,
      notes: m.notes || null,
    };
    const res = await authStore.apiFetch(
      m.id ? `/api/health/menstrual/${m.id}` : "/api/health/menstrual",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const d = await res.json();
      m.error = d.error || "Save failed.";
      return;
    }
    cycleModal.value.open = false;
    await loadMenstrual();
  } catch {
    m.error = "Network error.";
  } finally {
    m.saving = false;
  }
}

async function endCycle(cycle) {
  const res = await authStore.apiFetch(`/api/health/menstrual/${cycle.id}`, {
    method: "PUT",
    body: JSON.stringify({ cycle_end: todayIso }),
  });
  if (res.ok) await loadMenstrual();
}

async function deleteCycle(cycle) {
  if (!confirm(`Delete cycle starting ${formatDateFull(cycle.cycle_start)}?`)) return;
  await authStore.apiFetch(`/api/health/menstrual/${cycle.id}`, { method: "DELETE" });
  await loadMenstrual();
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-title { font-size: 1.5rem; font-weight: 700; color: #111827; margin: 0; }
.page-subtitle { font-size: 0.875rem; color: #6b7280; margin: 0.2rem 0 0; }

/* Tabs */
.health-tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 2px solid #f3f4f6;
}
.health-tab {
  background: none;
  border: none;
  padding: 0.6rem 1.25rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  border-radius: 6px 6px 0 0;
  transition: color 0.15s, border-color 0.15s;
}
.health-tab.active { color: #0d6efd; border-bottom-color: #0d6efd; }
.health-tab:hover:not(.active) { color: #374151; background: #f9fafb; }

.month-label { font-size: 0.9rem; font-weight: 600; color: #374151; min-width: 120px; text-align: center; }

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: #9ca3af;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #f3f4f6;
}
.empty-state i { font-size: 2.5rem; display: block; margin-bottom: 0.75rem; }

/* Date heading */
.date-heading {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  padding: 0.6rem 0 0.3rem;
}

/* Well-being list */
.wb-list { display: flex; flex-direction: column; }

.wb-card {
  background: #fff;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  padding: 0.9rem 1.1rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.5rem;
  transition: box-shadow 0.12s;
}
.wb-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }

.wb-user-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
  min-width: 48px;
}

.wb-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
}

.wb-avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e0e7ff;
  color: #4338ca;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
}

.wb-user-name { font-size: 0.7rem; color: #9ca3af; font-weight: 500; }

.wb-metrics { flex: 1; min-width: 0; }

.wb-metric {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}
.wb-metric-label { font-size: 0.72rem; color: #9ca3af; width: 42px; flex-shrink: 0; }
.wb-bar-wrap { flex: 1; height: 8px; background: #f3f4f6; border-radius: 99px; overflow: hidden; }
.wb-bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s ease; }
.wb-metric-val { font-size: 0.72rem; font-weight: 700; color: #374151; width: 36px; text-align: right; flex-shrink: 0; }

.wb-sleep { font-size: 0.75rem; color: #6b7280; margin-top: 0.2rem; }
.wb-notes { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; font-style: italic; }

.wb-actions {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  flex-shrink: 0;
}

/* Range slider labels */
.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 1rem;
  margin-top: 0.15rem;
}

.score-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
}

/* Prediction card */
.prediction-card {
  background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
  border: 1px solid #fbcfe8;
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.prediction-inner { display: flex; align-items: center; gap: 1rem; }
.prediction-icon { font-size: 2rem; color: #db2777; }
.prediction-label { font-size: 0.78rem; color: #9d174d; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }
.prediction-date { font-size: 1.1rem; font-weight: 700; color: #831843; margin-top: 0.15rem; }
.prediction-avg { font-size: 0.75rem; color: #9d174d; margin-top: 0.1rem; }

/* Cycle list */
.cycle-list { display: flex; flex-direction: column; gap: 0.6rem; }

.cycle-card {
  background: #fff;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  padding: 1rem 1.1rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  transition: box-shadow 0.12s;
}
.cycle-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }

.cycle-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 0.3rem;
  flex-shrink: 0;
}
.dot-active { background: #ec4899; box-shadow: 0 0 0 3px #fce7f3; }
.dot-done { background: #d1d5db; }

.cycle-body { flex: 1; min-width: 0; }

.cycle-dates {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: #111827;
}
.cycle-arrow { color: #d1d5db; }
.cycle-ongoing { color: #ec4899; font-weight: 500; }

.cycle-meta { margin-top: 0.35rem; }
.cycle-len { font-size: 0.75rem; color: #6b7280; }

.cycle-symptoms { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.4rem; }
.symptom-chip {
  font-size: 0.7rem;
  background: #fce7f3;
  color: #be185d;
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
  font-weight: 500;
}

.cycle-notes { font-size: 0.75rem; color: #9ca3af; margin-top: 0.3rem; font-style: italic; }

.cycle-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}

/* Symptom checkbox grid */
.symptom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.35rem;
}
.symptom-check {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: #374151;
  cursor: pointer;
}
.symptom-check input { cursor: pointer; }

/* Icon buttons */
.icon-btn {
  background: none;
  border: none;
  color: #9ca3af;
  padding: 0.25rem 0.35rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: background 0.12s, color 0.12s;
}
.icon-btn:hover { background: #f3f4f6; color: #374151; }
.icon-btn.danger:hover { background: #fee2e2; color: #dc2626; }

/* Charts */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 600px) {
  .charts-row { grid-template-columns: 1fr; }
}
.chart-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 1rem 1.25rem 0.75rem;
}
.chart-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  margin-bottom: 0.75rem;
}
.chart-wrap { height: 180px; position: relative; }

/* Modal */
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}
.modal-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
}
.modal-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem 0.75rem;
  font-weight: 600;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
}
.modal-close {
  background: none; border: none; color: #9ca3af;
  cursor: pointer; font-size: 1rem; padding: 0.2rem;
  border-radius: 6px; transition: background 0.12s, color 0.12s;
}
.modal-close:hover { background: #f3f4f6; color: #374151; }
.modal-card-body { padding: 1rem 1.25rem; }
.modal-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem 1rem;
  border-top: 1px solid #f3f4f6;
  position: sticky;
  bottom: 0;
  background: #fff;
}
</style>
