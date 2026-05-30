<template>
  <div>
    <div class="page-header d-flex align-items-center justify-content-between">
      <div>
        <h1 class="page-title"><i class="bi bi-bell me-2 text-primary"></i>Reminders</h1>
        <p class="page-subtitle">Smart reminders with push notifications</p>
      </div>
      <div class="d-flex align-items-center gap-2">
        <button
          v-if="notifSupported && notifPerm === 'default'"
          class="btn btn-sm btn-outline-warning d-flex align-items-center gap-1"
          @click="requestNotifPerm"
          title="Enable push notifications"
        >
          <i class="bi bi-bell-slash"></i>
          <span class="d-none d-md-inline">Enable notifications</span>
        </button>
        <span v-if="notifPerm === 'denied'" class="badge bg-warning-subtle text-warning d-flex align-items-center gap-1" title="Open browser settings → Site permissions to unblock">
          <i class="bi bi-bell-slash"></i>
          <span class="d-none d-md-inline">Blocked — enable in settings</span>
        </span>
        <span v-if="notifPerm === 'granted'" class="badge bg-success-subtle text-success">
          <i class="bi bi-bell-fill me-1"></i>Notifications on
        </span>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-1" @click="openCreate">
          <i class="bi bi-plus-lg"></i> New
        </button>
      </div>
    </div>

    <!-- Filter pills -->
    <div v-if="fetchState === 'ok'" class="filter-pills mb-3">
      <button
        class="pill"
        :class="{ 'pill-active': filterTab === 'upcoming' }"
        @click="filterTab = 'upcoming'"
      >
        <i class="bi bi-bell me-1"></i>Upcoming
        <span v-if="upcomingReminders.length" class="pill-count">{{ upcomingReminders.length }}</span>
      </button>
      <button
        class="pill"
        :class="{ 'pill-active': filterTab === 'completed' }"
        @click="filterTab = 'completed'"
      >
        <i class="bi bi-check2-circle me-1"></i>Completed
        <span v-if="completedReminders.length" class="pill-count">{{ completedReminders.length }}</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="fetchState === 'loading'" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div> Loading…
    </div>

    <div v-else-if="fetchState === 'error'" class="alert alert-danger">Failed to load reminders.</div>

    <!-- Empty -->
    <div v-else-if="filteredReminders.length === 0" class="reminders-empty">
      <i :class="filterTab === 'upcoming' ? 'bi bi-bell-slash' : 'bi bi-check2-all'"></i>
      <p>{{ filterTab === 'upcoming' ? 'No upcoming reminders. Add one to get started.' : 'No completed reminders yet.' }}</p>
    </div>

    <!-- Reminder list -->
    <div v-else class="reminder-list">
      <div
        v-for="r in filteredReminders"
        :key="r.id"
        class="reminder-item"
        :class="{
          'reminder-overdue': isOverdue(r),
          'reminder-sent': r.is_sent,
        }"
      >
        <div class="reminder-status-dot" :class="statusDotClass(r)"></div>
        <div class="reminder-content">
          <div class="reminder-title">{{ r.title }}</div>
          <div v-if="r.body" class="reminder-body">{{ r.body }}</div>
          <div class="reminder-meta">
            <span class="reminder-time" :class="{ 'text-danger': isOverdue(r) }">
              <i class="bi bi-clock me-1"></i>{{ formatDue(r.due_datetime) }}
            </span>
            <span v-if="r.repeat !== 'none'" class="reminder-repeat">
              <i class="bi bi-arrow-repeat me-1"></i>{{ r.repeat }}
            </span>
            <span v-if="r.is_sent" class="reminder-done">
              <i class="bi bi-check2-circle me-1"></i>Sent
            </span>
            <span v-if="isOverdue(r) && !r.is_sent" class="reminder-overdue-badge">
              Overdue
            </span>
          </div>
        </div>
        <div class="reminder-actions">
          <button class="note-btn" @click="openEdit(r)" title="Edit">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="note-btn note-btn-danger" @click="confirmDelete(r)" title="Delete">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Create / Edit modal -->
    <div class="modal-backdrop-custom" v-if="modal.open" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-card-header">
          <span>{{ modal.id ? "Edit Reminder" : "New Reminder" }}</span>
          <button class="modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <div class="mb-3">
            <label class="form-label form-label-sm">Title <span class="text-danger">*</span></label>
            <input
              v-model="modal.title"
              type="text"
              class="form-control form-control-sm"
              placeholder="Reminder title"
              maxlength="200"
            />
          </div>
          <div class="mb-3">
            <label class="form-label form-label-sm">Description</label>
            <textarea
              v-model="modal.body"
              class="form-control form-control-sm"
              rows="3"
              placeholder="Optional details…"
            ></textarea>
          </div>
          <div class="row g-2 mb-2">
            <div class="col-8">
              <label class="form-label form-label-sm">Due date & time <span class="text-danger">*</span></label>
              <input v-model="modal.due" type="datetime-local" class="form-control form-control-sm" />
            </div>
            <div class="col-4">
              <label class="form-label form-label-sm">Repeat</label>
              <select v-model="modal.repeat" class="form-select form-select-sm">
                <option value="none">None</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>
          <div v-if="modal.error" class="alert alert-danger py-2 small mt-2">{{ modal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="modal.saving" @click="saveReminder">
            <span v-if="modal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ modal.id ? "Save changes" : "Create" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div class="modal-backdrop-custom" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Delete reminder?</span>
          <button class="modal-close" @click="deleteTarget = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="mb-0">Delete <strong>{{ deleteTarget?.title }}</strong>? Cannot be undone.</p>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="deleteTarget = null">Cancel</button>
          <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteReminder">
            <span v-if="deleting" class="spinner-border spinner-border-sm me-1"></span>
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

const reminders = ref([]);
const fetchState = ref("loading");

const filterTab = ref("upcoming");

const upcomingReminders = computed(() => reminders.value.filter((r) => !r.is_sent));
const completedReminders = computed(() =>
  reminders.value
    .filter((r) => r.is_sent)
    .sort((a, b) => new Date(b.due_datetime) - new Date(a.due_datetime))
);
const filteredReminders = computed(() =>
  filterTab.value === "upcoming" ? upcomingReminders.value : completedReminders.value
);

const notifSupported = "Notification" in window;
const notifPerm = ref(notifSupported ? Notification.permission : "denied");

const modal = ref({ open: false, id: null, title: "", body: "", due: "", repeat: "none", saving: false, error: "" });
const deleteTarget = ref(null);
const deleting = ref(false);

function isOverdue(r) {
  return !r.is_sent && new Date(r.due_datetime) < new Date();
}

function statusDotClass(r) {
  if (r.is_sent) return "dot-sent";
  if (isOverdue(r)) return "dot-overdue";
  return "dot-upcoming";
}

function formatDue(iso) {
  const d = new Date(iso);
  return d.toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/** Convert UTC ISO → datetime-local format (YYYY-MM-DDTHH:MM) for the input */
function toLocalInput(iso) {
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function requestNotifPerm() {
  const perm = await Notification.requestPermission();
  notifPerm.value = perm;
  if (perm === "granted") {
    await authStore.registerFcmToken();
  }
}

async function fetchReminders() {
  fetchState.value = "loading";
  try {
    const res = await authStore.apiFetch("/api/reminders/");
    if (!res.ok) throw new Error();
    reminders.value = await res.json();
    fetchState.value = "ok";
  } catch {
    fetchState.value = "error";
  }
}

function openCreate() {
  const now = new Date();
  now.setHours(now.getHours() + 1, 0, 0, 0);
  modal.value = { open: true, id: null, title: "", body: "", due: toLocalInput(now.toISOString()), repeat: "none", saving: false, error: "" };
}

function openEdit(r) {
  modal.value = { open: true, id: r.id, title: r.title, body: r.body, due: toLocalInput(r.due_datetime), repeat: r.repeat, saving: false, error: "" };
}

function closeModal() { modal.value.open = false; }

async function saveReminder() {
  const m = modal.value;
  m.error = "";
  if (!m.title.trim()) { m.error = "Title is required."; return; }
  if (!m.due) { m.error = "Due date & time is required."; return; }
  m.saving = true;

  // Convert local datetime-local value to ISO with timezone
  const dueIso = new Date(m.due).toISOString();
  const payload = { title: m.title.trim(), body: m.body, due_datetime: dueIso, repeat: m.repeat };

  try {
    const res = await authStore.apiFetch(
      m.id ? `/api/reminders/${m.id}` : "/api/reminders/",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const data = await res.json();
      m.error = data.error || "Save failed.";
      return;
    }
    const saved = await res.json();
    if (m.id) {
      const idx = reminders.value.findIndex((r) => r.id === m.id);
      if (idx >= 0) reminders.value[idx] = saved;
    } else {
      reminders.value.push(saved);
      reminders.value.sort((a, b) => new Date(a.due_datetime) - new Date(b.due_datetime));
    }
    closeModal();
  } catch {
    m.error = "Network error. Try again.";
  } finally {
    m.saving = false;
  }
}

function confirmDelete(r) { deleteTarget.value = r; }

async function deleteReminder() {
  deleting.value = true;
  try {
    const res = await authStore.apiFetch(`/api/reminders/${deleteTarget.value.id}`, { method: "DELETE" });
    if (res.ok) {
      reminders.value = reminders.value.filter((r) => r.id !== deleteTarget.value.id);
      deleteTarget.value = null;
    }
  } finally {
    deleting.value = false;
  }
}

onMounted(fetchReminders);
</script>

<style scoped>
.reminders-empty {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #f3f4f6;
  padding: 4rem 2rem;
  text-align: center;
  color: #9ca3af;
}

.reminders-empty i {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.75rem;
}

.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.reminder-item {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 0.9rem 1.1rem;
  transition: box-shadow 0.15s;
}

.reminder-item:hover {
  box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}

.reminder-overdue {
  border-color: #fecaca;
  background: #fff5f5;
}

.reminder-sent {
  opacity: 0.55;
}

.reminder-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}

.dot-upcoming { background: #0d6efd; }
.dot-overdue  { background: #dc2626; }
.dot-sent     { background: #d1d5db; }

.reminder-content { flex: 1; min-width: 0; }

.reminder-title {
  font-weight: 600;
  color: #111827;
  font-size: 0.925rem;
}

.reminder-body {
  font-size: 0.83rem;
  color: #6b7280;
  margin-top: 0.2rem;
  white-space: pre-wrap;
}

.reminder-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.4rem;
}

.reminder-time {
  font-size: 0.78rem;
  color: #6b7280;
}

.reminder-repeat,
.reminder-done {
  font-size: 0.72rem;
  background: #f3f4f6;
  color: #6b7280;
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
}

.reminder-overdue-badge {
  font-size: 0.72rem;
  background: #fee2e2;
  color: #dc2626;
  padding: 0.1rem 0.5rem;
  border-radius: 99px;
  font-weight: 600;
}

.reminder-actions {
  display: flex;
  gap: 0.2rem;
  flex-shrink: 0;
}

/* Reuse note modal/button styles */
.note-btn {
  background: none;
  border: none;
  color: #9ca3af;
  padding: 0.2rem 0.35rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.12s, color 0.12s;
}

.note-btn:hover { background: #f3f4f6; color: #374151; }
.note-btn-danger:hover { background: #fee2e2; color: #dc2626; }

.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
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
  max-width: 520px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
}

.modal-card-sm { max-width: 380px; }

.modal-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem 0.75rem;
  font-weight: 600;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
}

.modal-close {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem;
  border-radius: 6px;
  transition: background 0.12s, color 0.12s;
}

.modal-close:hover { background: #f3f4f6; color: #374151; }

.modal-card-body { padding: 1rem 1.25rem; }

.modal-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem 1rem;
  border-top: 1px solid #f3f4f6;
}

/* Filter pills */
.filter-pills {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.3rem 0.85rem;
  border-radius: 99px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.pill:hover { background: #f3f4f6; color: #374151; border-color: #d1d5db; }
.pill-active { background: #111827; color: #fff; border-color: #111827; }
.pill-count {
  font-size: 0.7rem;
  background: rgba(255,255,255,0.2);
  color: inherit;
  padding: 0.05rem 0.4rem;
  border-radius: 99px;
  margin-left: 0.1rem;
}
.pill:not(.pill-active) .pill-count {
  background: #f3f4f6;
  color: #6b7280;
}
</style>
