<template>
  <div>
    <!-- Header -->
    <div class="dash-header">
      <div>
        <h1 class="page-title">{{ greeting }}, {{ firstName }} 👋</h1>
        <p class="page-subtitle">{{ todayLabel }}</p>
      </div>
    </div>

    <!-- KPI row -->
    <div class="kpi-grid">
      <div class="kpi-card" v-for="card in kpiCards" :key="card.label">
        <div class="kpi-icon" :style="{ background: card.iconBg }">
          <i :class="`bi ${card.icon}`" :style="{ color: card.iconColor }"></i>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">{{ card.label }}</div>
          <div class="kpi-value" :class="card.valueClass">{{ card.value }}</div>
          <div v-if="card.sub" class="kpi-sub">{{ card.sub }}</div>
        </div>
        <div class="kpi-bar" :style="{ background: card.iconColor }"></div>
      </div>
    </div>

    <!-- Panels -->
    <div class="panel-grid">
      <!-- Shared Spending -->
      <div class="panel">
        <div class="panel-hd">
          <i class="bi bi-pie-chart-fill" style="color:#2563eb"></i>
          <span>Shared Spending</span>
          <RouterLink :to="{ name: 'Finance' }" class="panel-link ms-auto">View all →</RouterLink>
        </div>
        <div v-if="!summary" class="panel-empty">
          <div class="spinner-border spinner-border-sm text-muted me-2"></div>Loading…
        </div>
        <div v-else-if="!summary.shared_categories?.length" class="panel-empty">
          No shared categories yet.
        </div>
        <div v-else class="panel-body">
          <div class="row-item" v-for="cat in [...summary.shared_categories].sort((a,b) => b.total_spent - a.total_spent)" :key="cat.category_id">
            <div class="row-icon" :style="{ background: cat.category_color + '20', color: cat.category_color }">
              <i :class="`bi ${cat.category_icon}`"></i>
            </div>
            <span class="row-name">{{ cat.category_name }}</span>
            <span class="row-amt">₹{{ fmt(cat.total_spent) }}</span>
          </div>
        </div>
      </div>

      <!-- My Budget -->
      <div class="panel">
        <div class="panel-hd">
          <i class="bi bi-graph-up-arrow" style="color:#16a34a"></i>
          <span>My Budget This Month</span>
        </div>
        <div v-if="!mySpend" class="panel-empty">
          <div class="spinner-border spinner-border-sm text-muted me-2"></div>Loading…
        </div>
        <div v-else class="panel-body">
          <div v-if="mySpend.total_budget" class="mb-3">
            <div class="d-flex justify-content-between align-items-baseline mb-1">
              <span class="small text-muted">Total spent</span>
              <span class="small fw-semibold">
                ₹{{ fmt(mySpend.total_spent) }}
                <span class="text-muted">/ ₹{{ fmt(mySpend.total_budget) }}</span>
              </span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="mySpend.total_pct >= 100 ? 'bar-over' : mySpend.total_pct >= 80 ? 'bar-warn' : ''"
                :style="{ width: Math.min(mySpend.total_pct || 0, 100) + '%' }"
              ></div>
            </div>
            <div class="d-flex justify-content-end mt-1">
              <span class="small" :class="mySpend.total_pct >= 100 ? 'text-danger' : 'text-muted'">
                {{ Math.round(mySpend.total_pct || 0) }}% used
              </span>
            </div>
          </div>
          <div v-for="cat in [...mySpend.categories].sort((a,b) => b.spent - a.spent)" :key="cat.category_id" class="cat-row">
            <span class="cat-dot" :style="{ background: cat.category_color }"></span>
            <span class="cat-name">{{ cat.category_name }}</span>
            <div class="cat-bar-track">
              <div
                class="cat-bar-fill"
                :style="{ width: catPct(cat) + '%', background: cat.category_color }"
              ></div>
            </div>
            <span class="cat-amt">₹{{ fmt(cat.spent) }}</span>
          </div>
          <div v-if="!mySpend.categories.length" class="panel-empty small">
            No categories assigned yet.
          </div>
        </div>
      </div>

      <!-- Upcoming Reminders -->
      <div class="panel">
        <div class="panel-hd">
          <i class="bi bi-bell-fill" style="color:#f59e0b"></i>
          <span>Upcoming Reminders</span>
          <RouterLink :to="{ name: 'Reminders' }" class="panel-link ms-auto">Manage →</RouterLink>
        </div>
        <div v-if="remindersLoading" class="panel-empty">
          <div class="spinner-border spinner-border-sm text-muted me-2"></div>Loading…
        </div>
        <div v-else-if="!upcomingReminders.length" class="panel-empty">
          <i class="bi bi-check-circle me-2 text-success"></i>No upcoming reminders.
        </div>
        <div v-else class="panel-body">
          <div class="reminder-row" v-for="r in upcomingReminders" :key="r.id">
            <div class="reminder-dot" :class="isToday(r.due_datetime) ? 'dot-today' : isOverdue(r.due_datetime) ? 'dot-overdue' : 'dot-future'"></div>
            <div class="reminder-info">
              <div class="reminder-title">{{ r.title }}</div>
              <div class="reminder-when" :class="isOverdue(r.due_datetime) ? 'text-danger' : 'text-muted'">
                {{ fmtDue(r.due_datetime) }}
              </div>
            </div>
            <span v-if="r.repeat !== 'none'" class="badge-repeat">{{ r.repeat }}</span>
          </div>
        </div>
      </div>

      <!-- Today's Health -->
      <div class="panel">
        <div class="panel-hd">
          <i class="bi bi-heart-pulse-fill" style="color:#9333ea"></i>
          <span>Today's Well-being</span>
          <RouterLink :to="{ name: 'Health' }" class="panel-link ms-auto">Log →</RouterLink>
        </div>
        <div v-if="healthLoading" class="panel-empty">
          <div class="spinner-border spinner-border-sm text-muted me-2"></div>Loading…
        </div>
        <div v-else-if="!todayEntries.length" class="panel-empty">
          <i class="bi bi-plus-circle me-2" style="color:#9333ea"></i>
          <RouterLink :to="{ name: 'Health' }" style="color:#9333ea;text-decoration:none">Log how you're feeling today</RouterLink>
        </div>
        <div v-else class="panel-body">
          <div class="health-entry" v-for="entry in todayEntries" :key="entry.id">
            <div class="health-avatar">
              <img v-if="entry.user_photo" :src="entry.user_photo" class="avatar-img" />
              <div v-else class="avatar-initials">{{ initials(entry.user_name) }}</div>
            </div>
            <div class="health-meta">
              <div class="health-name">{{ entry.user_name?.split(' ')[0] }}</div>
              <div class="health-metrics">
                <span class="metric-chip" :style="{ background: moodBg(entry.mood), color: moodColor(entry.mood) }">
                  {{ moodEmoji(entry.mood) }} {{ entry.mood }}/10
                </span>
                <span class="metric-chip" :style="{ background: '#eff6ff', color: '#2563eb' }">
                  ⚡ {{ entry.energy }}/10
                </span>
                <span v-if="entry.sleep_hours" class="metric-chip" style="background:#f0fdf4;color:#16a34a">
                  😴 {{ entry.sleep_hours }}h
                </span>
              </div>
              <div v-if="entry.notes" class="health-notes">{{ entry.notes }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useFinanceStore } from "@/stores/finance";
import { useHealthStore } from "@/stores/health";

const authStore = useAuthStore();
const financeStore = useFinanceStore();
const healthStore = useHealthStore();

const firstName = computed(() => authStore.user?.display_name?.split(" ")[0] ?? "there");

const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
});

const todayLabel = computed(() => {
  return new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
});

// ─── Finance ──────────────────────────────────────────────────────────────────

const summary = computed(() => financeStore.summary);

const mySpend = computed(() => {
  const uid = authStore.user?.id;
  if (!summary.value || !uid) return null;
  return summary.value.users?.find((u) => u.user_id === uid) ?? null;
});

const totalSpend = computed(() => {
  if (!summary.value) return "—";
  const t = summary.value.users?.reduce((s, u) => s + (u.total_spent || 0), 0) ?? 0;
  return "₹" + fmt(t);
});

const balanceText = computed(() => {
  const bal = summary.value?.balance;
  if (!bal || !bal.amount) return null;
  const uid = authStore.user?.id;
  if (bal.debtor_id === uid) return `You owe ₹${fmt(bal.amount)}`;
  return `${bal.debtor_name?.split(" ")[0]} owes ₹${fmt(bal.amount)}`;
});

function fmt(n) {
  return Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function catPct(cat) {
  if (!cat.budget || !cat.spent) return 0;
  return Math.min((cat.spent / cat.budget) * 100, 100);
}

// ─── Reminders ────────────────────────────────────────────────────────────────

const reminders = ref([]);
const remindersLoading = ref(true);

const upcomingReminders = computed(() => {
  const now = new Date();
  return reminders.value
    .filter((r) => !r.is_sent && (new Date(r.due_datetime) >= now || isToday(r.due_datetime)))
    .sort((a, b) => new Date(a.due_datetime) - new Date(b.due_datetime))
    .slice(0, 5);
});

const upcomingCount = computed(() => upcomingReminders.value.length);

function isToday(dt) {
  const d = new Date(dt);
  const t = new Date();
  return d.toDateString() === t.toDateString();
}

function isOverdue(dt) {
  return new Date(dt) < new Date() && !isToday(dt);
}

function fmtDue(dt) {
  const d = new Date(dt);
  const now = new Date();
  if (isToday(dt)) {
    return "Today · " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
  const tomorrow = new Date(now); tomorrow.setDate(now.getDate() + 1);
  if (d.toDateString() === tomorrow.toDateString()) {
    return "Tomorrow · " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }) +
    " · " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

// ─── Health / Well-being ─────────────────────────────────────────────────────

const healthLoading = ref(true);

const todayStr = new Date().toISOString().slice(0, 10);

const todayEntries = computed(() => {
  return (healthStore.wellbeingEntries || []).filter((e) => e.entry_date === todayStr);
});

const myTodayMood = computed(() => {
  const uid = authStore.user?.id;
  return todayEntries.value.find((e) => e.created_by === uid);
});

function moodEmoji(v) {
  if (v >= 8) return "😄";
  if (v >= 6) return "🙂";
  if (v >= 4) return "😐";
  return "😔";
}
function moodColor(v) {
  if (v >= 8) return "#16a34a";
  if (v >= 6) return "#ca8a04";
  if (v >= 4) return "#ea580c";
  return "#dc2626";
}
function moodBg(v) {
  if (v >= 8) return "#f0fdf4";
  if (v >= 6) return "#fefce8";
  if (v >= 4) return "#fff7ed";
  return "#fef2f2";
}
function initials(name) {
  return (name || "?").split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
}

// ─── KPI cards ───────────────────────────────────────────────────────────────

const kpiCards = computed(() => [
  {
    label: "Combined Spend",
    value: totalSpend.value,
    icon: "bi-wallet2",
    iconBg: "#eff6ff",
    iconColor: "#2563eb",
  },
  {
    label: "Net Balance",
    value: balanceText.value ?? "Settled ✓",
    icon: "bi-arrow-left-right",
    iconBg: "#fefce8",
    iconColor: "#ca8a04",
    valueClass: balanceText.value ? "" : "text-success",
  },
  {
    label: "Reminders",
    value: remindersLoading.value ? "…" : (upcomingCount.value || "None"),
    // sub: remindersLoading.value ? "" : (upcomingCount.value ? "upcoming" : "all clear"),
    icon: "bi-bell",
    iconBg: "#fffbeb",
    iconColor: "#f59e0b",
  },
  {
    label: "My Mood Today",
    value: myTodayMood.value
      ? moodEmoji(myTodayMood.value.mood) + " " + myTodayMood.value.mood + "/10"
      : healthLoading.value ? "…" : "Not logged",
    icon: "bi-emoji-smile",
    iconBg: "#fdf4ff",
    iconColor: "#9333ea",
  },
]);

// ─── Load ─────────────────────────────────────────────────────────────────────

onMounted(async () => {
  const currentMonth = new Date().toISOString().slice(0, 7);

  financeStore.fetchSummary();

  authStore.apiFetch("/api/reminders/")
    .then(async (res) => {
      if (res.ok) reminders.value = await res.json();
    })
    .finally(() => { remindersLoading.value = false; });

  await healthStore.fetchWellbeing(currentMonth).catch(() => {});
  healthLoading.value = false;
});
</script>

<style scoped>
.dash-header {
  margin-bottom: 1.5rem;
}
.page-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}
.page-subtitle {
  font-size: 0.82rem;
  color: #9ca3af;
  margin: 0.15rem 0 0;
}

/* ─── KPI grid ─────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.85rem;
  margin-bottom: 1.25rem;
  align-items: start;
}
@media (min-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(4, 1fr); }
}

.kpi-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #f3f4f6;
  padding: 1rem 1.1rem;
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  transition: box-shadow 0.15s;
}
.kpi-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.08); }

.kpi-bar {
  position: absolute;
  top: 0; left: 0;
  width: 3px;
  height: 100%;
  border-radius: 14px 0 0 14px;
  opacity: 0.55;
}

.kpi-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}

.kpi-body { min-width: 0; }

.kpi-label {
  font-size: 0.72rem;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  line-height: 1.3;
  margin-bottom: 0.2rem;
}

.kpi-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
  word-break: break-word;
}

.kpi-sub {
  font-size: 0.72rem;
  color: #9ca3af;
  margin-top: 0.1rem;
}

/* ─── Panel grid ───────────────────────────────── */
.panel-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
@media (min-width: 640px) {
  .panel-grid { grid-template-columns: repeat(2, 1fr); }
}

.panel {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  overflow: hidden;
}

.panel-hd {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.85rem 1.1rem;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  border-bottom: 1px solid #f9fafb;
}

.panel-link {
  font-size: 0.75rem;
  color: #6b7280;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.1s;
}
.panel-link:hover { color: #111827; }

.panel-empty {
  display: flex;
  align-items: center;
  padding: 1.5rem 1.1rem;
  color: #9ca3af;
  font-size: 0.82rem;
  gap: 0.4rem;
}

.panel-body { padding: 0.6rem 1.1rem 0.9rem; }

/* ─── Shared spending rows ─────────────────────── */
.row-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0;
  border-bottom: 1px solid #f9fafb;
}
.row-item:last-child { border-bottom: none; }

.row-icon {
  width: 28px; height: 28px;
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;
}

.row-name {
  flex: 1;
  font-size: 0.82rem;
  color: #374151;
}

.row-amt {
  font-size: 0.85rem;
  font-weight: 700;
  color: #111827;
}

/* ─── Budget bars ──────────────────────────────── */
.bar-track {
  height: 7px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 99px;
  transition: width 0.4s ease;
}
.bar-warn { background: #f59e0b; }
.bar-over { background: #dc2626; }

.cat-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0;
}
.cat-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.cat-name {
  font-size: 0.78rem;
  color: #6b7280;
  width: 90px;
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cat-bar-track {
  flex: 1;
  height: 4px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
}
.cat-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s;
}
.cat-amt {
  font-size: 0.78rem;
  font-weight: 600;
  color: #111827;
  width: 60px;
  text-align: right;
  flex-shrink: 0;
}

/* ─── Reminder rows ────────────────────────────── */
.reminder-row {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f9fafb;
}
.reminder-row:last-child { border-bottom: none; }

.reminder-dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.3rem;
}
.dot-today { background: #f59e0b; }
.dot-overdue { background: #dc2626; }
.dot-future { background: #d1d5db; }

.reminder-info { flex: 1; min-width: 0; }
.reminder-title {
  font-size: 0.83rem;
  font-weight: 500;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.reminder-when {
  font-size: 0.74rem;
  margin-top: 0.1rem;
}

.badge-repeat {
  font-size: 0.66rem;
  background: #f3f4f6;
  color: #6b7280;
  padding: 2px 6px;
  border-radius: 99px;
  text-transform: capitalize;
  flex-shrink: 0;
  align-self: center;
}

/* ─── Health panel ─────────────────────────────── */
.health-entry {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f9fafb;
}
.health-entry:last-child { border-bottom: none; }

.health-avatar { flex-shrink: 0; }
.avatar-img {
  width: 32px; height: 32px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-initials {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #374151;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}

.health-meta { flex: 1; min-width: 0; }
.health-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.3rem;
}
.health-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.metric-chip {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}
.health-notes {
  font-size: 0.74rem;
  color: #9ca3af;
  margin-top: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─── Mobile ─────────────────────────────────── */
@media (max-width: 480px) {
  .kpi-card { padding: 0.75rem 0.85rem; gap: 0.6rem; }
  .kpi-icon { width: 34px; height: 34px; font-size: 1rem; }
  .kpi-value { font-size: 0.95rem; }
  .kpi-label { font-size: 0.66rem; }

  .cat-name { width: 70px; }
  .cat-amt { width: 50px; font-size: 0.72rem; }

  .panel-hd { padding: 0.7rem 0.9rem; font-size: 0.8rem; }
  .panel-body { padding: 0.5rem 0.9rem 0.75rem; }
  .panel-empty { padding: 1.2rem 0.9rem; }
}
</style>
