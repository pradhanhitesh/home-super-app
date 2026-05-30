<template>
  <div>
    <div class="page-header d-flex align-items-center justify-content-between">
      <div>
        <h1 class="page-title"><i class="bi bi-gear me-2 text-primary"></i>Finance Settings</h1>
        <p class="page-subtitle">Manage categories, assignments & monthly budgets</p>
      </div>
      <RouterLink :to="{ name: 'Finance' }" class="btn btn-sm btn-outline-secondary">
        <i class="bi bi-arrow-left me-1"></i>Back
      </RouterLink>
    </div>

    <div v-if="loadState === 'loading'" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div> Loading…
    </div>

    <div v-else-if="!isAdmin" class="alert alert-warning">
      <i class="bi bi-shield-lock me-2"></i>Only the household admin can manage finance settings.
    </div>

    <template v-else>
      <!-- ─ Categories ──────────────────────────────────────────────── -->
      <div class="settings-card mb-4">
        <div class="settings-card-header">
          <span>Categories</span>
          <button class="btn btn-sm btn-primary" @click="openCatCreate">
            <i class="bi bi-plus-lg me-1"></i>New Category
          </button>
        </div>
        <div class="settings-card-body">
          <div v-if="categories.length === 0" class="text-muted small py-3 text-center">
            No categories yet. Create one to get started.
          </div>
          <div class="cat-table" v-else>
            <div class="cat-row cat-row-head">
              <span>Name</span><span>Shared</span><span>Assign to</span><span></span>
            </div>
            <div class="cat-row" v-for="cat in categories" :key="cat.id">
              <!-- Color dot + name -->
              <div class="d-flex align-items-center gap-2">
                <span class="cat-color-dot" :style="{ background: cat.color }"></span>
                <i :class="`bi ${cat.icon}`" style="font-size:0.95rem; color: #6b7280;"></i>
                <span class="fw-semibold" style="font-size:0.88rem;">{{ cat.name }}</span>
              </div>
              <!-- Shared toggle -->
              <div>
                <div class="form-check form-switch mb-0">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :checked="cat.is_shared"
                    @change="toggleShared(cat)"
                  />
                </div>
              </div>
              <!-- Assignment checkboxes -->
              <div class="d-flex gap-3">
                <div v-for="u in users" :key="u.id" class="form-check mb-0 d-flex align-items-center gap-1">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :id="`assign-${cat.id}-${u.id}`"
                    :checked="isAssigned(u.id, cat.id)"
                    @change="toggleAssignment(u.id, cat.id, $event.target.checked)"
                  />
                  <label class="form-check-label small" :for="`assign-${cat.id}-${u.id}`">
                    {{ firstName(u.display_name) }}
                  </label>
                </div>
              </div>
              <!-- Actions -->
              <div class="d-flex gap-1 justify-content-end">
                <button class="note-btn" @click="openCatEdit(cat)" title="Edit">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="note-btn note-btn-danger" @click="confirmDeleteCat(cat)" title="Delete">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ─ Monthly Budgets ─────────────────────────────────────────── -->
      <div class="settings-card mb-4">
        <div class="settings-card-header">
          <span>Monthly Budgets</span>
          <div class="d-flex align-items-center gap-2">
            <button class="btn btn-sm btn-outline-secondary px-2" @click="shiftBudgetMonth(-1)">
              <i class="bi bi-chevron-left"></i>
            </button>
            <span class="month-label-sm">{{ budgetMonthLabel }}</span>
            <button class="btn btn-sm btn-outline-secondary px-2" @click="shiftBudgetMonth(1)">
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
        <div class="settings-card-body">
          <div v-for="u in users" :key="u.id" class="budget-user-block mb-4">
            <div class="budget-user-name">{{ u.display_name }}</div>
            <!-- Total budget -->
            <div class="budget-input-row">
              <label class="budget-input-label">Total monthly budget</label>
              <div class="input-group input-group-sm" style="max-width:180px;">
                <span class="input-group-text">₹</span>
                <input
                  type="number"
                  class="form-control"
                  min="0"
                  step="100"
                  :value="getBudget(u.id, null)"
                  @change="setBudget(u.id, null, $event.target.value)"
                />
              </div>
            </div>
            <!-- Per-category budgets for this user -->
            <div
              v-for="cat in categoriesForUser(u.id)"
              :key="cat.id"
              class="budget-input-row"
            >
              <label class="budget-input-label">
                <span class="cat-color-dot small" :style="{ background: cat.color }"></span>
                {{ cat.name }}
              </label>
              <div class="input-group input-group-sm" style="max-width:180px;">
                <span class="input-group-text">₹</span>
                <input
                  type="number"
                  class="form-control"
                  min="0"
                  step="100"
                  :value="getBudget(u.id, cat.id)"
                  @change="setBudget(u.id, cat.id, $event.target.value)"
                />
              </div>
            </div>
            <div v-if="categoriesForUser(u.id).length === 0" class="text-muted small">
              No categories assigned to this user yet.
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Category create / edit modal -->
    <div class="modal-backdrop-custom" v-if="catModal.open" @click.self="catModal.open = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>{{ catModal.id ? "Edit Category" : "New Category" }}</span>
          <button class="modal-close" @click="catModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <div class="mb-3">
            <label class="form-label form-label-sm">Name <span class="text-danger">*</span></label>
            <input v-model="catModal.name" type="text" class="form-control form-control-sm" maxlength="100" placeholder="e.g. Groceries" />
          </div>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label form-label-sm">Icon (Bootstrap icon class)</label>
              <div class="input-group input-group-sm">
                <span class="input-group-text"><i :class="`bi ${catModal.icon}`"></i></span>
                <input v-model="catModal.icon" type="text" class="form-control" placeholder="bi-tag" />
              </div>
            </div>
            <div class="col-6">
              <label class="form-label form-label-sm">Color</label>
              <div class="d-flex gap-2 align-items-center">
                <input v-model="catModal.color" type="color" class="form-control form-control-color form-control-sm" />
                <span class="small text-muted">{{ catModal.color }}</span>
              </div>
            </div>
          </div>
          <div class="form-check">
            <input class="form-check-input" type="checkbox" v-model="catModal.is_shared" id="cat-shared" />
            <label class="form-check-label small" for="cat-shared">Show on shared dashboard</label>
          </div>
          <div v-if="catModal.error" class="alert alert-danger py-2 small mt-2">{{ catModal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="catModal.open = false">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="catModal.saving" @click="saveCat">
            <span v-if="catModal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ catModal.id ? "Save" : "Create" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete cat confirm -->
    <div class="modal-backdrop-custom" v-if="deleteCatTarget" @click.self="deleteCatTarget = null">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Delete category?</span>
          <button class="modal-close" @click="deleteCatTarget = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="mb-0">Delete <strong>{{ deleteCatTarget?.name }}</strong>? All expenses in this category will lose their category link.</p>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="deleteCatTarget = null">Cancel</button>
          <button class="btn btn-sm btn-danger" :disabled="deletingCat" @click="deleteCat">
            <span v-if="deletingCat" class="spinner-border spinner-border-sm me-1"></span>
            Delete
          </button>
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

const authStore = useAuthStore();
const financeStore = useFinanceStore();

const loadState = ref("loading");

// ── Reactive copies of settings data ──────────────────────────────────────
const categories = ref([]);
const assignments = ref([]);
const budgets = ref([]);
const users = ref([]);
const isAdmin = ref(false);
const currentMonth = ref("");

// ── Budget month navigation ────────────────────────────────────────────────
const today = new Date();
const budgetYear = ref(today.getFullYear());
const budgetMonth = ref(today.getMonth() + 1);

const budgetMonthKey = computed(() =>
  `${budgetYear.value}-${String(budgetMonth.value).padStart(2, "0")}`
);
const budgetMonthLabel = computed(() => {
  const d = new Date(budgetYear.value, budgetMonth.value - 1, 1);
  return d.toLocaleString("en-IN", { month: "long", year: "numeric" });
});

function shiftBudgetMonth(delta) {
  let m = budgetMonth.value + delta;
  let y = budgetYear.value;
  if (m > 12) { m = 1; y++; }
  if (m < 1) { m = 12; y--; }
  budgetMonth.value = m;
  budgetYear.value = y;
  // reload budgets for this month from server
  loadBudgetsForMonth();
}

async function loadBudgetsForMonth() {
  const res = await authStore.apiFetch(`/api/finance/settings`);
  if (res.ok) {
    const data = await res.json();
    // We need budgets for the selected month, not just current.
    // For simplicity, fetch summary for that month which triggers rollover
    const sumRes = await authStore.apiFetch(`/api/finance/summary?month=${budgetMonthKey.value}`);
    if (sumRes.ok) {
      // re-fetch settings to get rolled-over budgets
      const settRes = await authStore.apiFetch("/api/finance/settings");
      if (settRes.ok) {
        const sett = await settRes.json();
        budgets.value = sett.budgets;
      }
    }
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────

function firstName(name) {
  return (name || "").split(" ")[0];
}

function isAssigned(userId, categoryId) {
  return assignments.value.some((a) => a.user_id === userId && a.category_id === categoryId);
}

function categoriesForUser(userId) {
  const ids = new Set(assignments.value.filter((a) => a.user_id === userId).map((a) => a.category_id));
  return categories.value.filter((c) => ids.has(c.id));
}

function getBudget(userId, categoryId) {
  const entry = budgets.value.find(
    (b) => b.user_id === userId && (categoryId ? b.category_id === categoryId : b.category_id === null)
  );
  return entry ? entry.amount : 0;
}

// ── Budget set (debounce-free: fires on blur via @change) ─────────────────

async function setBudget(userId, categoryId, rawValue) {
  const amount = parseFloat(rawValue);
  if (isNaN(amount) || amount < 0) return;
  const res = await authStore.apiFetch("/api/finance/budgets", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      category_id: categoryId || null,
      month: budgetMonthKey.value,
      amount,
    }),
  });
  if (res.ok) {
    const saved = await res.json();
    const idx = budgets.value.findIndex(
      (b) => b.user_id === userId && (categoryId ? b.category_id === categoryId : b.category_id === null)
    );
    if (idx >= 0) budgets.value[idx] = saved;
    else budgets.value.push(saved);
  }
}

// ── Assignments toggle ─────────────────────────────────────────────────────

async function toggleAssignment(userId, categoryId, checked) {
  if (checked) {
    const res = await authStore.apiFetch("/api/finance/assignments", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, category_id: categoryId }),
    });
    if (res.ok) {
      const saved = await res.json();
      if (!assignments.value.some((a) => a.id === saved.id)) {
        assignments.value.push(saved);
      }
    }
  } else {
    const a = assignments.value.find((a) => a.user_id === userId && a.category_id === categoryId);
    if (!a) return;
    const res = await authStore.apiFetch(`/api/finance/assignments/${a.id}`, { method: "DELETE" });
    if (res.ok || res.status === 204) {
      assignments.value = assignments.value.filter((x) => x.id !== a.id);
    }
  }
}

// ── Shared toggle ─────────────────────────────────────────────────────────

async function toggleShared(cat) {
  const res = await authStore.apiFetch(`/api/finance/categories/${cat.id}`, {
    method: "PUT",
    body: JSON.stringify({ is_shared: !cat.is_shared }),
  });
  if (res.ok) {
    const saved = await res.json();
    const idx = categories.value.findIndex((c) => c.id === cat.id);
    if (idx >= 0) categories.value[idx] = saved;
  }
}

// ── Category modal ────────────────────────────────────────────────────────

const catModal = ref({ open: false, id: null, name: "", icon: "bi-tag", color: "#0d6efd", is_shared: true, saving: false, error: "" });
const deleteCatTarget = ref(null);
const deletingCat = ref(false);

// Common icon + color presets
const ICON_PRESETS = [
  { icon: "bi-cart3", color: "#16a34a" },
  { icon: "bi-cup-hot", color: "#ca8a04" },
  { icon: "bi-film", color: "#9333ea" },
  { icon: "bi-house", color: "#0d6efd" },
  { icon: "bi-heart-pulse", color: "#dc2626" },
  { icon: "bi-lightning", color: "#f97316" },
];

function openCatCreate() {
  catModal.value = { open: true, id: null, name: "", icon: "bi-tag", color: "#0d6efd", is_shared: true, saving: false, error: "" };
}

function openCatEdit(cat) {
  catModal.value = { open: true, id: cat.id, name: cat.name, icon: cat.icon, color: cat.color, is_shared: cat.is_shared, saving: false, error: "" };
}

async function saveCat() {
  const m = catModal.value;
  m.error = "";
  if (!m.name.trim()) { m.error = "Name required."; return; }
  m.saving = true;
  try {
    const payload = { name: m.name.trim(), icon: m.icon, color: m.color, is_shared: m.is_shared };
    const res = await authStore.apiFetch(
      m.id ? `/api/finance/categories/${m.id}` : "/api/finance/categories",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const d = await res.json();
      m.error = d.error || "Save failed.";
      return;
    }
    const saved = await res.json();
    if (m.id) {
      const idx = categories.value.findIndex((c) => c.id === m.id);
      if (idx >= 0) categories.value[idx] = saved;
    } else {
      categories.value.push(saved);
      categories.value.sort((a, b) => a.name.localeCompare(b.name));
    }
    catModal.value.open = false;
  } catch {
    m.error = "Network error.";
  } finally {
    m.saving = false;
  }
}

function confirmDeleteCat(cat) { deleteCatTarget.value = cat; }

async function deleteCat() {
  deletingCat.value = true;
  try {
    const res = await authStore.apiFetch(`/api/finance/categories/${deleteCatTarget.value.id}`, { method: "DELETE" });
    if (res.ok || res.status === 204) {
      const id = deleteCatTarget.value.id;
      categories.value = categories.value.filter((c) => c.id !== id);
      assignments.value = assignments.value.filter((a) => a.category_id !== id);
      budgets.value = budgets.value.filter((b) => b.category_id !== id);
      deleteCatTarget.value = null;
    }
  } finally {
    deletingCat.value = false;
  }
}

// ── Load ──────────────────────────────────────────────────────────────────

onMounted(async () => {
  await financeStore.fetchSettings();
  const s = financeStore.settings;
  if (s) {
    categories.value = [...s.categories];
    assignments.value = [...s.assignments];
    budgets.value = [...s.budgets];
    users.value = [...s.users];
    isAdmin.value = s.is_admin;
    currentMonth.value = s.month;
  }
  loadState.value = "ok";
});
</script>

<style scoped>
.settings-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow: hidden;
}

.settings-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.25rem;
  font-weight: 700;
  font-size: 0.9rem;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
  background: #fafafa;
}

.settings-card-body {
  padding: 1rem 1.25rem;
}

/* Category table */
.cat-table {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.cat-row {
  display: grid;
  grid-template-columns: 1fr 80px 1fr 80px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0;
  border-bottom: 1px solid #f9fafb;
}

.cat-row:last-child { border-bottom: none; }

.cat-row-head {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  padding-bottom: 0.5rem;
}

.cat-color-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.cat-color-dot.small {
  width: 8px;
  height: 8px;
}

/* Budget section */
.budget-user-block {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}
.budget-user-block:last-child { border-bottom: none; margin-bottom: 0 !important; }

.budget-user-name {
  font-weight: 700;
  font-size: 0.9rem;
  color: #111827;
  margin-bottom: 0.75rem;
}

.budget-input-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  gap: 1rem;
}

.budget-input-label {
  font-size: 0.83rem;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex: 1;
}

.month-label-sm {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  min-width: 110px;
  text-align: center;
}

/* Shared modal styles */
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
  max-width: 520px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
}
.modal-card-sm { max-width: 420px; }

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
</style>
