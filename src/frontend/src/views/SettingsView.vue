<template>
  <div>
    <div class="page-header">
      <h1 class="page-title">Settings</h1>
      <p class="page-subtitle">Household preferences and data management</p>
    </div>

    <!-- Export -->
    <div class="settings-card">
      <div class="settings-card-header">
        <i class="bi bi-database-down settings-card-icon"></i>
        <div>
          <div class="settings-card-title">Export Household Data</div>
          <div class="settings-card-desc">
            Download a ZIP of all your data — expenses, notes, reminders, health logs — as CSV and JSON files.
          </div>
        </div>
      </div>

      <div v-if="exportError" class="alert alert-danger py-2 mt-3 mb-0" style="font-size:0.85rem;">
        {{ exportError }}
      </div>

      <button
        class="btn-export mt-3"
        :disabled="exporting"
        @click="downloadExport"
      >
        <span v-if="exporting" class="spinner-border spinner-border-sm me-2" role="status"></span>
        <i v-else class="bi bi-download me-2"></i>
        {{ exporting ? "Preparing download…" : "Download Full Backup" }}
      </button>

      <p class="export-hint">
        Includes: expenses, settlements, transactions, grocery items, reminders, notes, wellbeing, menstrual cycles.
        One <code>.zip</code> with CSVs + <code>dump.json</code>.
      </p>
    </div>

    <!-- Restore -->
    <div class="settings-card mt-3">
      <div class="settings-card-header">
        <i class="bi bi-database-up settings-card-icon"></i>
        <div>
          <div class="settings-card-title">Restore from Backup</div>
          <div class="settings-card-desc">
            Upload a <code>.zip</code> backup file to restore all data into this household. Records are always added — run only on a fresh database to avoid duplicates.
          </div>
        </div>
      </div>

      <div v-if="restoreResult" class="alert alert-success py-2 mt-3 mb-0" style="font-size:0.85rem;">
        Restored: {{ restoreResultSummary }}
      </div>
      <div v-if="restoreError" class="alert alert-danger py-2 mt-3 mb-0" style="font-size:0.85rem;">
        {{ restoreError }}
      </div>

      <input ref="fileInput" type="file" accept=".zip" class="d-none" @change="onFileSelected" />
      <button class="btn-restore mt-3" :disabled="restoring" @click="fileInput.click()">
        <span v-if="restoring" class="spinner-border spinner-border-sm me-2" role="status"></span>
        <i v-else class="bi bi-upload me-2"></i>
        {{ restoring ? "Restoring…" : "Upload Backup ZIP" }}
      </button>
    </div>

    <!-- Household info -->
    <div class="settings-card mt-3">
      <div class="settings-card-header">
        <i class="bi bi-house settings-card-icon"></i>
        <div>
          <div class="settings-card-title">Household</div>
          <div class="settings-card-desc">Signed in as {{ authStore.user?.display_name }} ({{ authStore.user?.email }})</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

// Export
const exporting = ref(false);
const exportError = ref(null);

// Restore
const fileInput = ref(null);
const restoring = ref(false);
const restoreError = ref(null);
const restoreResult = ref(null);

const restoreResultSummary = computed(() => {
  if (!restoreResult.value) return "";
  return Object.entries(restoreResult.value.restored)
    .map(([k, v]) => `${v} ${k}`)
    .join(", ");
});

async function onFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  restoring.value = true;
  restoreError.value = null;
  restoreResult.value = null;
  try {
    const form = new FormData();
    form.append("file", file);
    const res = await authStore.apiFetch("/api/export/restore", {
      method: "POST",
      body: form,
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error ?? `Server error ${res.status}`);
    restoreResult.value = body;
  } catch (err) {
    restoreError.value = err.message;
  } finally {
    restoring.value = false;
    fileInput.value.value = "";
  }
}

async function downloadExport() {
  exporting.value = true;
  exportError.value = null;
  try {
    const res = await authStore.apiFetch("/api/export/full");
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error ?? `Server error ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `home-backup-${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    exportError.value = e.message;
  } finally {
    exporting.value = false;
  }
}
</script>

<style scoped>
.settings-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  max-width: 600px;
}

.settings-card-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.settings-card-icon {
  font-size: 1.5rem;
  color: #6b7280;
  margin-top: 0.1rem;
  flex-shrink: 0;
}

.settings-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
}

.settings-card-desc {
  font-size: 0.82rem;
  color: #6b7280;
  margin-top: 0.2rem;
}

.btn-export {
  display: inline-flex;
  align-items: center;
  background: #0d6efd;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-export:hover:not(:disabled) {
  background: #0b5ed7;
}

.btn-export:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.export-hint {
  font-size: 0.78rem;
  color: #9ca3af;
  margin: 0.6rem 0 0;
}

.btn-restore {
  display: inline-flex;
  align-items: center;
  background: #198754;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1.1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-restore:hover:not(:disabled) {
  background: #157347;
}

.btn-restore:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
