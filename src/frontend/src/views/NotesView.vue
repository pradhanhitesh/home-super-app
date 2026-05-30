<template>
  <div>
    <!-- Header -->
    <div class="page-header d-flex align-items-center justify-content-between">
      <div>
        <h1 class="page-title"><i class="bi bi-journal-text me-2" style="color:#6366f1"></i>Notes</h1>
        <p class="page-subtitle">Shared notes for the household</p>
      </div>
      <div class="d-flex gap-2">
        <button v-if="isAdmin" class="btn btn-sm btn-outline-secondary" @click="catModal.open = true">
          <i class="bi bi-tags me-1"></i> Tags
        </button>
        <button class="btn btn-sm btn-primary d-flex align-items-center gap-1" @click="openCreate">
          <i class="bi bi-plus-lg"></i> New Note
        </button>
      </div>
    </div>

    <!-- Category filter -->
    <div class="cat-filter-row" v-if="categories.length">
      <button
        class="cat-filter-pill"
        :class="{ active: !filterCatId }"
        @click="filterCatId = null"
      >All</button>
      <button
        v-for="cat in categories"
        :key="cat.id"
        class="cat-filter-pill"
        :class="{ active: filterCatId === cat.id }"
        :style="filterCatId === cat.id ? { background: cat.color, color: '#fff', borderColor: cat.color } : { borderColor: cat.color + '55', color: cat.color }"
        @click="filterCatId = filterCatId === cat.id ? null : cat.id"
      >
        <i :class="`bi ${cat.icon}`"></i> {{ cat.name }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="fetchState === 'loading'" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div>Loading notes…
    </div>

    <!-- Error -->
    <div v-else-if="fetchState === 'error'" class="alert alert-danger">Failed to load notes.</div>

    <!-- Empty -->
    <div v-else-if="filteredNotes.length === 0" class="notes-empty">
      <i class="bi bi-journal-plus"></i>
      <p>{{ filterCatId ? "No notes in this category." : "No notes yet. Create your first one!" }}</p>
    </div>

    <!-- Notes grid -->
    <div v-else class="notes-grid">
      <div class="note-card" v-for="note in filteredNotes" :key="note.id">
        <!-- Category strip -->
        <div
          v-if="note.category"
          class="note-cat-strip"
          :style="{ background: note.category.color }"
        ></div>

        <div class="note-card-body">
          <!-- Title row -->
          <div class="note-title-row">
            <i
              :class="`bi ${note.note_type === 'checklist' ? 'bi-check2-square' : 'bi-file-text'}`"
              class="note-type-icon"
            ></i>
            <h6 class="note-title">{{ note.title }}</h6>
          </div>

          <!-- Category chip -->
          <div v-if="note.category" class="mb-2">
            <span class="cat-chip" :style="{ background: note.category.color + '18', color: note.category.color }">
              <i :class="`bi ${note.category.icon} me-1`"></i>{{ note.category.name }}
            </span>
          </div>

          <!-- Text content -->
          <p v-if="note.note_type === 'text' && note.body" class="note-preview">{{ note.body }}</p>

          <!-- Checklist content -->
          <div v-if="note.note_type === 'checklist'" class="note-checklist">
            <div
              v-for="item in note.checklist.slice(0, 5)"
              :key="item.id"
              class="check-item"
              @click="toggleItem(note, item)"
            >
              <span class="check-box" :class="{ checked: item.done }">
                <i v-if="item.done" class="bi bi-check-lg"></i>
              </span>
              <span class="check-text" :class="{ 'check-done': item.done }">{{ item.text }}</span>
            </div>
            <div v-if="note.checklist.length > 5" class="check-more">
              +{{ note.checklist.length - 5 }} more
            </div>
            <div v-if="!note.checklist.length" class="text-muted small">Empty checklist</div>
          </div>
        </div>

        <div class="note-card-footer">
          <span class="note-author">{{ note.author_name || "—" }}</span>
          <span class="note-date">{{ relativeTime(note.updated_at) }}</span>
          <button class="note-btn" @click="openEdit(note)" title="Edit">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="note-btn note-btn-danger" @click="confirmDelete(note)" title="Delete">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- ─── Create / Edit Modal ────────────────────────────────────────────── -->
    <div class="modal-backdrop-custom" v-if="modal.open" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-card-header">
          <span>{{ modal.id ? "Edit Note" : "New Note" }}</span>
          <button class="modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <!-- Title -->
          <div class="mb-3">
            <label class="form-label form-label-sm">Title <span class="text-danger">*</span></label>
            <input v-model="modal.title" type="text" class="form-control form-control-sm" placeholder="Note title" maxlength="300" />
          </div>

          <!-- Type toggle -->
          <div class="mb-3">
            <label class="form-label form-label-sm">Type</label>
            <div class="type-toggle">
              <button
                class="type-btn"
                :class="{ active: modal.note_type === 'text' }"
                @click="modal.note_type = 'text'"
              >
                <i class="bi bi-file-text me-1"></i>Text
              </button>
              <button
                class="type-btn"
                :class="{ active: modal.note_type === 'checklist' }"
                @click="modal.note_type = 'checklist'"
              >
                <i class="bi bi-check2-square me-1"></i>Checklist
              </button>
            </div>
          </div>

          <!-- Text body -->
          <div class="mb-3" v-if="modal.note_type === 'text'">
            <label class="form-label form-label-sm">Content</label>
            <textarea v-model="modal.body" class="form-control form-control-sm" rows="6" placeholder="Write your note…"></textarea>
          </div>

          <!-- Checklist editor -->
          <div class="mb-3" v-if="modal.note_type === 'checklist'">
            <label class="form-label form-label-sm d-flex justify-content-between">
              <span>Items</span>
              <span class="text-muted small">{{ doneCount }}/{{ modal.checklist.length }} done</span>
            </label>
            <div class="checklist-editor">
              <div v-for="(item, idx) in modal.checklist" :key="item.id" class="check-edit-row">
                <button class="check-toggle-btn" :class="{ checked: item.done }" @click="item.done = !item.done" type="button">
                  <i v-if="item.done" class="bi bi-check-lg"></i>
                </button>
                <input
                  v-model="item.text"
                  type="text"
                  class="form-control form-control-sm check-input"
                  :class="{ 'text-muted': item.done }"
                  placeholder="Item text…"
                  @keydown.enter.prevent="addChecklistItem(idx)"
                />
                <button class="check-del-btn" @click="removeChecklistItem(idx)" type="button">
                  <i class="bi bi-x"></i>
                </button>
              </div>
              <button class="add-item-btn" @click="addChecklistItem()" type="button">
                <i class="bi bi-plus me-1"></i>Add item
              </button>
            </div>
          </div>

          <!-- Category -->
          <div class="mb-3" v-if="categories.length">
            <label class="form-label form-label-sm">Category</label>
            <div class="cat-picker">
              <button
                class="cat-pick-pill"
                :class="{ active: !modal.category_id }"
                @click="modal.category_id = null"
              >None</button>
              <button
                v-for="cat in categories"
                :key="cat.id"
                class="cat-pick-pill"
                :class="{ active: modal.category_id === cat.id }"
                :style="modal.category_id === cat.id ? { background: cat.color, color: '#fff', borderColor: cat.color } : { borderColor: cat.color + '55', color: cat.color }"
                @click="modal.category_id = modal.category_id === cat.id ? null : cat.id"
              >
                <i :class="`bi ${cat.icon}`"></i> {{ cat.name }}
              </button>
            </div>
          </div>

          <div v-if="modal.error" class="alert alert-danger py-2 small mt-2">{{ modal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="modal.saving" @click="saveNote">
            <span v-if="modal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ modal.id ? "Save changes" : "Create note" }}
          </button>
        </div>
      </div>
    </div>

    <!-- ─── Delete Confirm Modal ───────────────────────────────────────────── -->
    <div class="modal-backdrop-custom" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Delete note?</span>
          <button class="modal-close" @click="deleteTarget = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="mb-0">Delete <strong>{{ deleteTarget?.title }}</strong>? Cannot be undone.</p>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="deleteTarget = null">Cancel</button>
          <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteNote">
            <span v-if="deleting" class="spinner-border spinner-border-sm me-1"></span>
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- ─── Category Manager Modal (Admin) ────────────────────────────────── -->
    <div class="modal-backdrop-custom" v-if="catModal.open" @click.self="catModal.open = false">
      <div class="modal-card">
        <div class="modal-card-header">
          <span><i class="bi bi-tags me-2"></i>Manage Tags / Categories</span>
          <button class="modal-close" @click="catModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <!-- Existing categories -->
          <div v-if="!categories.length" class="text-muted small mb-3">No categories yet.</div>
          <div v-else class="cat-list mb-4">
            <div class="cat-list-row" v-for="cat in categories" :key="cat.id">
              <div class="cat-list-preview" :style="{ background: cat.color + '22', color: cat.color }">
                <i :class="`bi ${cat.icon}`"></i>
              </div>
              <div v-if="catModal.editId === cat.id" class="cat-edit-inline flex-1">
                <input v-model="catModal.editName" class="form-control form-control-sm" placeholder="Name" />
              </div>
              <span v-else class="cat-list-name">{{ cat.name }}</span>
              <div class="cat-list-actions">
                <button v-if="catModal.editId !== cat.id" class="note-btn" @click="startEditCat(cat)"><i class="bi bi-pencil"></i></button>
                <button v-if="catModal.editId === cat.id" class="note-btn text-success" @click="saveEditCat(cat)"><i class="bi bi-check-lg"></i></button>
                <button v-if="catModal.editId === cat.id" class="note-btn" @click="catModal.editId = null"><i class="bi bi-x"></i></button>
                <button class="note-btn note-btn-danger" @click="deleteCat(cat)"><i class="bi bi-trash"></i></button>
              </div>
            </div>
          </div>

          <!-- Add new category -->
          <div class="cat-add-section">
            <p class="small fw-semibold text-muted mb-2">Add new category</p>
            <div class="mb-2">
              <input v-model="catModal.newName" class="form-control form-control-sm" placeholder="Category name" maxlength="100" />
            </div>
            <!-- Color picker -->
            <div class="mb-2">
              <label class="form-label form-label-sm">Color</label>
              <div class="color-picker-row">
                <button
                  v-for="c in COLOR_PRESETS"
                  :key="c"
                  class="color-swatch"
                  :style="{ background: c }"
                  :class="{ 'color-swatch-active': catModal.newColor === c }"
                  @click="catModal.newColor = c"
                ></button>
              </div>
            </div>
            <!-- Icon picker -->
            <div class="mb-3">
              <label class="form-label form-label-sm">Icon</label>
              <div class="icon-picker-row">
                <button
                  v-for="ic in ICON_PRESETS"
                  :key="ic"
                  class="icon-swatch"
                  :class="{ 'icon-swatch-active': catModal.newIcon === ic }"
                  :style="catModal.newIcon === ic ? { background: catModal.newColor, color: '#fff' } : {}"
                  @click="catModal.newIcon = ic"
                >
                  <i :class="`bi ${ic}`"></i>
                </button>
              </div>
            </div>
            <div v-if="catModal.error" class="alert alert-danger py-1 small mb-2">{{ catModal.error }}</div>
            <button class="btn btn-sm btn-primary w-100" :disabled="catModal.saving" @click="createCat">
              <span v-if="catModal.saving" class="spinner-border spinner-border-sm me-1"></span>
              <i class="bi bi-plus me-1"></i>Add category
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.is_admin);

// ─── Constants ───────────────────────────────────────────────────────────────

const COLOR_PRESETS = ["#ef4444","#f97316","#eab308","#22c55e","#3b82f6","#8b5cf6","#ec4899","#6b7280","#0ea5e9","#14b8a6"];
const ICON_PRESETS = ["bi-tag","bi-house","bi-cart","bi-heart","bi-star","bi-bookmark","bi-calendar","bi-people","bi-briefcase","bi-gift","bi-lightning","bi-camera","bi-music-note","bi-book","bi-trophy"];

// ─── State ───────────────────────────────────────────────────────────────────

const notes = ref([]);
const categories = ref([]);
const fetchState = ref("loading");
const filterCatId = ref(null);

const deleteTarget = ref(null);
const deleting = ref(false);

const modal = ref({
  open: false, id: null, title: "", note_type: "text",
  body: "", checklist: [], category_id: null, saving: false, error: "",
});

const catModal = ref({
  open: false,
  newName: "", newColor: "#6366f1", newIcon: "bi-tag",
  editId: null, editName: "",
  saving: false, error: "",
});

// ─── Computed ─────────────────────────────────────────────────────────────────

const filteredNotes = computed(() => {
  if (!filterCatId.value) return notes.value;
  return notes.value.filter((n) => n.category_id === filterCatId.value);
});

const doneCount = computed(() => modal.value.checklist.filter((i) => i.done).length);

// ─── Helpers ─────────────────────────────────────────────────────────────────

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function newItemId() {
  return Math.random().toString(36).slice(2);
}

// ─── Fetch ────────────────────────────────────────────────────────────────────

async function fetchAll() {
  fetchState.value = "loading";
  try {
    const [nRes, cRes] = await Promise.all([
      authStore.apiFetch("/api/notes/"),
      authStore.apiFetch("/api/notes/categories"),
    ]);
    if (!nRes.ok || !cRes.ok) throw new Error();
    notes.value = await nRes.json();
    categories.value = await cRes.json();
    fetchState.value = "ok";
  } catch {
    fetchState.value = "error";
  }
}

// ─── Note Modal ───────────────────────────────────────────────────────────────

function openCreate() {
  modal.value = {
    open: true, id: null, title: "", note_type: "text",
    body: "", checklist: [], category_id: null, saving: false, error: "",
  };
}

function openEdit(note) {
  modal.value = {
    open: true,
    id: note.id,
    title: note.title,
    note_type: note.note_type || "text",
    body: note.body || "",
    checklist: (note.checklist || []).map((i) => ({ ...i })),
    category_id: note.category_id || null,
    saving: false,
    error: "",
  };
}

function closeModal() { modal.value.open = false; }

function addChecklistItem(afterIdx = null) {
  const item = { id: newItemId(), text: "", done: false };
  if (afterIdx !== null) {
    modal.value.checklist.splice(afterIdx + 1, 0, item);
  } else {
    modal.value.checklist.push(item);
  }
}

function removeChecklistItem(idx) {
  modal.value.checklist.splice(idx, 1);
}

async function saveNote() {
  const m = modal.value;
  m.error = "";
  if (!m.title.trim()) { m.error = "Title is required."; return; }
  if (m.note_type === "checklist" && m.checklist.every((i) => !i.text.trim())) {
    m.error = "Add at least one checklist item."; return;
  }
  m.saving = true;

  const payload = {
    title: m.title.trim(),
    note_type: m.note_type,
    body: m.note_type === "text" ? (m.body || null) : null,
    checklist: m.note_type === "checklist" ? m.checklist.filter((i) => i.text.trim()) : [],
    tags: [],
    category_id: m.category_id || null,
  };

  try {
    const res = await authStore.apiFetch(
      m.id ? `/api/notes/${m.id}` : "/api/notes/",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const d = await res.json();
      m.error = d.error || "Save failed."; return;
    }
    const saved = await res.json();
    if (m.id) {
      const idx = notes.value.findIndex((n) => n.id === m.id);
      if (idx >= 0) notes.value[idx] = saved;
    } else {
      notes.value.unshift(saved);
    }
    closeModal();
  } catch {
    m.error = "Network error. Try again.";
  } finally {
    m.saving = false;
  }
}

// ─── Inline checklist toggle ─────────────────────────────────────────────────

async function toggleItem(note, item) {
  item.done = !item.done;
  const updated = note.checklist.map((i) =>
    i.id === item.id ? { ...i, done: item.done } : i
  );
  const res = await authStore.apiFetch(`/api/notes/${note.id}`, {
    method: "PUT",
    body: JSON.stringify({ checklist: updated }),
  });
  if (res.ok) {
    const saved = await res.json();
    const idx = notes.value.findIndex((n) => n.id === note.id);
    if (idx >= 0) notes.value[idx] = saved;
  } else {
    item.done = !item.done; // revert on failure
  }
}

// ─── Delete ───────────────────────────────────────────────────────────────────

function confirmDelete(note) { deleteTarget.value = note; }

async function deleteNote() {
  deleting.value = true;
  try {
    const res = await authStore.apiFetch(`/api/notes/${deleteTarget.value.id}`, { method: "DELETE" });
    if (res.ok) {
      notes.value = notes.value.filter((n) => n.id !== deleteTarget.value.id);
      deleteTarget.value = null;
    }
  } finally { deleting.value = false; }
}

// ─── Category Management ─────────────────────────────────────────────────────

function startEditCat(cat) {
  catModal.value.editId = cat.id;
  catModal.value.editName = cat.name;
}

async function saveEditCat(cat) {
  if (!catModal.value.editName.trim()) return;
  const res = await authStore.apiFetch(`/api/notes/categories/${cat.id}`, {
    method: "PUT",
    body: JSON.stringify({ name: catModal.value.editName.trim() }),
  });
  if (res.ok) {
    const updated = await res.json();
    const idx = categories.value.findIndex((c) => c.id === cat.id);
    if (idx >= 0) categories.value[idx] = updated;
    catModal.value.editId = null;
  }
}

async function deleteCat(cat) {
  if (!confirm(`Delete category "${cat.name}"? Notes in this category won't be deleted.`)) return;
  const res = await authStore.apiFetch(`/api/notes/categories/${cat.id}`, { method: "DELETE" });
  if (res.ok) {
    categories.value = categories.value.filter((c) => c.id !== cat.id);
    notes.value = notes.value.map((n) =>
      n.category_id === cat.id ? { ...n, category_id: null, category: null } : n
    );
    if (filterCatId.value === cat.id) filterCatId.value = null;
  }
}

async function createCat() {
  const cm = catModal.value;
  cm.error = "";
  if (!cm.newName.trim()) { cm.error = "Name required."; return; }
  cm.saving = true;
  try {
    const res = await authStore.apiFetch("/api/notes/categories", {
      method: "POST",
      body: JSON.stringify({ name: cm.newName.trim(), color: cm.newColor, icon: cm.newIcon }),
    });
    if (!res.ok) {
      const d = await res.json();
      cm.error = d.error || "Failed."; return;
    }
    const cat = await res.json();
    categories.value.push(cat);
    cm.newName = ""; cm.newColor = "#6366f1"; cm.newIcon = "bi-tag";
  } catch {
    cm.error = "Network error.";
  } finally {
    cm.saving = false;
  }
}

onMounted(fetchAll);
</script>

<style scoped>
/* ─── Category filter bar ──────────────────────────────── */
.cat-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1.1rem;
}

.cat-filter-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  font-size: 0.78rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.12s;
}

.cat-filter-pill.active {
  background: #111827;
  color: #fff;
  border-color: #111827;
}

.cat-filter-pill:hover:not(.active) {
  border-color: #9ca3af;
  color: #374151;
}

/* ─── Notes grid ───────────────────────────────────────── */
.notes-empty {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #f3f4f6;
  padding: 4rem 2rem;
  text-align: center;
  color: #9ca3af;
}

.notes-empty i {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.75rem;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 1rem;
}

.note-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.15s;
}

.note-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.09); }

.note-cat-strip {
  height: 3px;
  width: 100%;
  flex-shrink: 0;
}

.note-card-body {
  padding: 0.9rem 1rem 0.5rem;
  flex: 1;
}

.note-title-row {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  margin-bottom: 0.4rem;
}

.note-type-icon {
  color: #9ca3af;
  font-size: 0.88rem;
  margin-top: 0.1rem;
  flex-shrink: 0;
}

.note-title {
  font-weight: 600;
  color: #111827;
  margin: 0;
  font-size: 0.9rem;
  word-break: break-word;
  line-height: 1.3;
}

.cat-chip {
  display: inline-flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}

.note-preview {
  font-size: 0.82rem;
  color: #6b7280;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: pre-wrap;
}

/* ─── Checklist on card ────────────────────────────────── */
.note-checklist { display: flex; flex-direction: column; gap: 0.25rem; }

.check-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.1rem 0;
}

.check-box {
  width: 16px; height: 16px;
  border-radius: 4px;
  border: 1.5px solid #d1d5db;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.65rem;
  color: #fff;
  transition: all 0.1s;
}

.check-box.checked {
  background: #22c55e;
  border-color: #22c55e;
}

.check-text {
  font-size: 0.8rem;
  color: #374151;
}

.check-done {
  text-decoration: line-through;
  color: #9ca3af;
}

.check-more {
  font-size: 0.74rem;
  color: #9ca3af;
  padding-top: 0.15rem;
}

.note-card-footer {
  padding: 0.55rem 1rem 0.7rem;
  border-top: 1px solid #f9fafb;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.note-author {
  font-size: 0.74rem;
  color: #9ca3af;
  flex: 1;
}

.note-date {
  font-size: 0.72rem;
  color: #d1d5db;
}

.note-btn {
  background: none;
  border: none;
  color: #9ca3af;
  padding: 0.18rem 0.3rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.82rem;
  transition: background 0.12s, color 0.12s;
  line-height: 1;
}
.note-btn:hover { background: #f3f4f6; color: #374151; }
.note-btn-danger:hover { background: #fee2e2; color: #dc2626; }

/* ─── Modal shared ─────────────────────────────────────── */
.modal-backdrop-custom {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; padding: 1rem;
}

.modal-card {
  background: #fff;
  border-radius: 16px;
  width: 100%; max-width: 540px;
  max-height: 90vh;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex; flex-direction: column;
  overflow: hidden;
}

.modal-card-sm { max-width: 380px; }

.modal-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 1.25rem 0.75rem;
  font-weight: 600; color: #111827;
  border-bottom: 1px solid #f3f4f6;
  flex-shrink: 0;
}

.modal-close {
  background: none; border: none; color: #9ca3af;
  cursor: pointer; font-size: 1rem; padding: 0.2rem;
  border-radius: 6px; transition: background 0.12s, color 0.12s;
}
.modal-close:hover { background: #f3f4f6; color: #374151; }

.modal-card-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
}

.modal-card-footer {
  display: flex; justify-content: flex-end; gap: 0.5rem;
  padding: 0.75rem 1.25rem 1rem;
  border-top: 1px solid #f3f4f6;
  flex-shrink: 0;
}

/* ─── Type toggle ──────────────────────────────────────── */
.type-toggle {
  display: flex; gap: 0;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  width: fit-content;
}

.type-btn {
  padding: 0.4rem 1rem;
  background: #fff;
  border: none;
  font-size: 0.82rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.type-btn.active {
  background: #111827;
  color: #fff;
}

/* ─── Checklist editor ─────────────────────────────────── */
.checklist-editor {
  display: flex; flex-direction: column; gap: 0.35rem;
}

.check-edit-row {
  display: flex; align-items: center; gap: 0.4rem;
}

.check-toggle-btn {
  width: 20px; height: 20px;
  border-radius: 5px;
  border: 1.5px solid #d1d5db;
  background: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; color: #fff;
  cursor: pointer; flex-shrink: 0;
  transition: all 0.1s;
}
.check-toggle-btn.checked { background: #22c55e; border-color: #22c55e; }

.check-input { flex: 1; }

.check-del-btn {
  background: none; border: none;
  color: #9ca3af; cursor: pointer;
  font-size: 1rem; padding: 0.1rem 0.2rem;
  border-radius: 4px;
  transition: color 0.1s;
}
.check-del-btn:hover { color: #dc2626; }

.add-item-btn {
  background: none; border: 1.5px dashed #e5e7eb;
  border-radius: 6px; color: #9ca3af;
  font-size: 0.8rem; padding: 0.3rem 0.75rem;
  cursor: pointer; text-align: left;
  transition: border-color 0.12s, color 0.12s;
  width: fit-content;
}
.add-item-btn:hover { border-color: #6366f1; color: #6366f1; }

/* ─── Category picker in modal ─────────────────────────── */
.cat-picker {
  display: flex; flex-wrap: wrap; gap: 0.4rem;
}

.cat-pick-pill {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.22rem 0.65rem;
  border-radius: 99px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  font-size: 0.76rem; font-weight: 500;
  color: #6b7280; cursor: pointer;
  transition: all 0.12s;
}
.cat-pick-pill.active {
  background: #111827; color: #fff; border-color: #111827;
}

/* ─── Category manager ─────────────────────────────────── */
.cat-list { display: flex; flex-direction: column; gap: 0.4rem; }

.cat-list-row {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.4rem 0.5rem;
  border-radius: 8px;
  border: 1px solid #f3f4f6;
}

.cat-list-preview {
  width: 30px; height: 30px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; flex-shrink: 0;
}

.cat-list-name {
  flex: 1; font-size: 0.85rem; color: #374151; font-weight: 500;
}

.cat-edit-inline { flex: 1; }

.cat-list-actions { display: flex; gap: 0.2rem; }

.cat-add-section {
  border: 1px dashed #e5e7eb;
  border-radius: 10px;
  padding: 0.9rem;
}

/* ─── Color + icon pickers ─────────────────────────────── */
.color-picker-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.color-swatch {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2.5px solid transparent; cursor: pointer;
  transition: transform 0.1s, border-color 0.1s;
}
.color-swatch:hover { transform: scale(1.15); }
.color-swatch-active { border-color: #111827; transform: scale(1.15); }

.icon-picker-row { display: flex; flex-wrap: wrap; gap: 0.35rem; }

.icon-swatch {
  width: 30px; height: 30px; border-radius: 6px;
  border: 1.5px solid #e5e7eb;
  background: #f9fafb;
  color: #6b7280;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.85rem; cursor: pointer;
  transition: all 0.1s;
}
.icon-swatch:hover { border-color: #6366f1; color: #6366f1; }
.icon-swatch-active { border-color: transparent; }
</style>
