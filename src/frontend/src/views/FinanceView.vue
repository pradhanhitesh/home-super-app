<template>
  <div>
    <!-- Header -->
    <div class="page-header d-flex align-items-center justify-content-between">
      <div>
        <h1 class="page-title"><i class="bi bi-wallet2 me-2 text-primary"></i>Finance</h1>
        <p class="page-subtitle">Shared expenses, budgets & settlements</p>
      </div>
      <div class="d-flex align-items-center gap-2">
        <RouterLink
          v-if="financeStore.settings?.is_admin"
          :to="{ name: 'FinanceSettings' }"
          class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
        >
          <i class="bi bi-gear"></i>
          <span class="d-none d-md-inline">Settings</span>
        </RouterLink>
        <button class="btn btn-sm btn-outline-danger d-flex align-items-center gap-1" @click="resetConfirm = true">
          <i class="bi bi-trash"></i>
          <span class="d-none d-md-inline">Reset</span>
        </button>
        <button class="btn btn-primary btn-sm d-flex align-items-center gap-1" @click="openCreate">
          <i class="bi bi-plus-lg"></i>
          <span class="d-none d-sm-inline">Add Expense</span>
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-5 text-muted">
      <div class="spinner-border spinner-border-sm me-2"></div> Loading…
    </div>

    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <template v-else>
      <!-- Month picker + balance chip -->
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-outline-secondary px-2" @click="shiftMonth(-1)">
            <i class="bi bi-chevron-left"></i>
          </button>
          <span class="month-label">{{ monthLabel }}</span>
          <button
            class="btn btn-sm btn-outline-secondary px-2"
            @click="shiftMonth(1)"
          >
            <i class="bi bi-chevron-right"></i>
          </button>
        </div>
        <div class="d-flex align-items-center gap-2">
          <div v-if="summary?.balance" class="balance-chip" :class="isDebtor ? 'balance-owe' : 'balance-owed'">
            <i class="bi bi-arrow-left-right me-1 flex-shrink-0"></i>
            <span class="balance-text">
              <span v-if="isDebtor">You owe {{ summary.balance.creditor_name.split(' ')[0] }} <strong>₹{{ fmt(summary.balance.amount) }}</strong></span>
              <span v-else><strong>{{ summary.balance.debtor_name.split(' ')[0] }}</strong> owes you <strong>₹{{ fmt(summary.balance.amount) }}</strong></span>
              <span class="balance-net-tag">net</span>
            </span>
          </div>
          <button
            v-if="summary?.balance && isCurrentMonth"
            class="btn btn-sm btn-outline-success"
            @click="openSettle"
          >
            Settle up
          </button>
          <div v-if="!summary?.balance && summary" class="balance-chip balance-clear">
            <i class="bi bi-check2-circle me-1"></i> All settled
          </div>
          <button
            v-if="summary"
            class="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
            @click="openLedger"
            title="View full balance ledger"
          >
            <i class="bi bi-journal-text"></i>
            <span class="d-none d-sm-inline">Ledger</span>
          </button>
        </div>
      </div>

      <!-- Budget overview cards — own spending only -->
      <div class="budget-grid mb-4" v-if="summary?.users?.length">
        <div class="budget-card" v-for="u in summary.users.filter(u => u.user_id === currentUserId)" :key="u.user_id">
          <div class="budget-card-header">
            <span class="budget-user">{{ u.user_name }}</span>
            <span class="budget-amounts">
              <span class="budget-spent">₹{{ fmt(u.total_spent) }}</span>
              <span v-if="u.total_budget" class="budget-limit"> / ₹{{ fmt(u.total_budget) }}</span>
            </span>
          </div>
          <div v-if="u.total_budget" class="budget-bar-track">
            <div
              class="budget-bar-fill"
              :class="{ 'budget-bar-over': u.total_pct >= 100 }"
              :style="{ width: Math.min(u.total_pct || 0, 100) + '%' }"
            ></div>
          </div>
          <!-- Category rows -->
          <div class="budget-cats">
            <div class="budget-cat-row" v-for="cat in u.categories" :key="cat.category_id">
              <span class="cat-dot" :style="{ background: cat.category_color }"></span>
              <span class="cat-name">{{ cat.category_name }}</span>
              <span class="cat-amounts">
                <span class="cat-spent">₹{{ fmt(cat.spent) }}</span>
                <span v-if="cat.budget" class="cat-limit"> / ₹{{ fmt(cat.budget) }}</span>
              </span>
              <div v-if="cat.budget" class="cat-bar-track">
                <div
                  class="cat-bar-fill"
                  :class="{ 'cat-bar-over': (cat.pct || 0) >= 100 }"
                  :style="{ width: Math.min(cat.pct || 0, 100) + '%', background: cat.category_color }"
                ></div>
              </div>
            </div>
            <div v-if="!u.categories.length" class="budget-cat-empty">No categories assigned yet.</div>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div v-if="myExpenses.length >= 2" class="charts-row mb-4">
        <div class="chart-card">
          <div class="chart-title">Spending by Category</div>
          <div class="chart-wrap chart-wrap-donut">
            <Doughnut :data="categoryChartData" :options="donutOptions" />
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-title">Daily Spending</div>
          <div class="chart-wrap">
            <Bar :data="dailyChartData" :options="barOptions" />
          </div>
        </div>
      </div>

      <!-- Expense list -->
      <div class="expenses-header d-flex align-items-center justify-content-between mb-2">
        <h6 class="mb-0 fw-semibold text-secondary">Expenses — {{ monthLabel }}</h6>
        <span class="text-muted small">{{ filteredExpenses.length }} item{{ filteredExpenses.length !== 1 ? 's' : '' }}</span>
      </div>

      <!-- Category filter pills -->
      <div v-if="categoriesWithExpenses.length > 1" class="filter-pills mb-3">
        <button
          class="pill"
          :class="{ 'pill-active': filterCatId === null }"
          @click="filterCatId = null"
        >All</button>
        <button
          v-for="cat in categoriesWithExpenses"
          :key="cat.id"
          class="pill"
          :class="{ 'pill-active': filterCatId === cat.id }"
          :style="filterCatId === cat.id ? { background: cat.color, color: '#fff', borderColor: cat.color } : {}"
          @click="filterCatId = filterCatId === cat.id ? null : cat.id"
        >
          <i :class="`bi ${cat.icon} me-1`"></i>{{ cat.name }}
        </button>
      </div>

      <div v-if="filteredExpenses.length === 0" class="expenses-empty">
        <i class="bi bi-receipt"></i>
        <p>No expenses this month.</p>
      </div>

      <div v-else-if="filteredExpenses.length > 0" class="expense-list">
        <template v-for="(group, date) in groupedExpenses" :key="date">
          <div class="expense-date-heading">{{ formatDate(date) }}</div>
          <div
            class="expense-item"
            v-for="exp in group"
            :key="exp.id"
          >
            <div class="exp-cat-badge" :style="{ background: exp.category_color + '22', color: exp.category_color }">
              <i :class="`bi ${exp.category_icon}`"></i>
            </div>
            <div class="exp-content">
              <div class="exp-title">
                {{ exp.title }}
                <span v-if="exp.is_subscription" class="badge-sub">sub</span>
              </div>
              <div class="exp-meta">
                <span>{{ exp.category_name }}</span>
                <span class="sep">·</span>
                <span>{{ exp.paid_by_name }} paid</span>
                <span class="sep">·</span>
                <span :class="`split-badge split-${exp.split_type}`">
                  <i class="bi bi-people me-1" v-if="exp.split_type !== 'none'"></i>
                  <i class="bi bi-person me-1" v-else></i>
                  {{ splitLabel(exp) }}
                </span>
                <span class="sep exp-payment-sep">·</span>
                <span class="exp-payment d-flex align-items-center gap-1">
                  <i :class="`bi bi-${exp.payment_method === 'card' ? 'credit-card' : 'cash-coin'}`"></i>
                  {{ exp.payment_method }}
                </span>
              </div>
            </div>
            <div class="exp-right">
              <div class="exp-amount">₹{{ fmt(exp.amount) }}</div>
              <div class="exp-actions">
                <button class="note-btn" @click="openEdit(exp)" title="Edit"><i class="bi bi-pencil"></i></button>
                <button class="note-btn note-btn-danger" @click="confirmDelete(exp)" title="Delete"><i class="bi bi-trash"></i></button>
              </div>
            </div>
          </div>
        </template>
      </div>
    </template>

    <!-- Create / Edit Expense Modal -->
    <div class="modal-backdrop-custom" v-if="modal.open" @click.self="closeModal">
      <div class="modal-card">
        <div class="modal-card-header">
          <span>{{ modal.id ? "Edit Expense" : "New Expense" }}</span>
          <button class="modal-close" @click="closeModal"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <div class="row g-2 mb-3">
            <div class="col-8">
              <label class="form-label form-label-sm">Title <span class="text-danger">*</span></label>
              <input v-model="modal.title" type="text" class="form-control form-control-sm" placeholder="e.g. BigBazaar groceries" maxlength="300" />
            </div>
            <div class="col-4">
              <label class="form-label form-label-sm">Amount (₹) <span class="text-danger">*</span></label>
              <input v-model="modal.amount" type="number" min="1" step="0.01" class="form-control form-control-sm" placeholder="0.00" />
            </div>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label form-label-sm">Category <span class="text-danger">*</span></label>
              <select v-model="modal.category_id" class="form-select form-select-sm">
                <option value="">-- select --</option>
                <option v-for="c in myCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label form-label-sm">Paid by <span class="text-danger">*</span></label>
              <select v-model="modal.paid_by" class="form-select form-select-sm">
                <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.display_name }}</option>
              </select>
            </div>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label form-label-sm">Date</label>
              <input v-model="modal.expense_date" type="date" class="form-control form-control-sm" />
            </div>
            <div class="col-6">
              <label class="form-label form-label-sm">Payment</label>
              <div class="btn-group w-100" role="group">
                <input type="radio" class="btn-check" v-model="modal.payment_method" value="card" id="pm-card" />
                <label class="btn btn-sm btn-outline-secondary" for="pm-card"><i class="bi bi-credit-card me-1"></i>Card</label>
                <input type="radio" class="btn-check" v-model="modal.payment_method" value="cash" id="pm-cash" />
                <label class="btn btn-sm btn-outline-secondary" for="pm-cash"><i class="bi bi-cash-coin me-1"></i>Cash</label>
              </div>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label form-label-sm">Split</label>
            <div class="btn-group w-100" role="group">
              <input type="radio" class="btn-check" v-model="modal.split_type" value="equal" id="st-equal" />
              <label class="btn btn-sm btn-outline-secondary" for="st-equal">50 / 50</label>
              <input type="radio" class="btn-check" v-model="modal.split_type" value="custom" id="st-custom" />
              <label class="btn btn-sm btn-outline-secondary" for="st-custom">Ratio</label>
              <input type="radio" class="btn-check" v-model="modal.split_type" value="amount" id="st-amount" />
              <label class="btn btn-sm btn-outline-secondary" for="st-amount">Custom ₹</label>
              <input type="radio" class="btn-check" v-model="modal.split_type" value="none" id="st-none" />
              <label class="btn btn-sm btn-outline-secondary" for="st-none">No split</label>
            </div>
          </div>

          <!-- Custom ratio inputs -->
          <div v-if="modal.split_type === 'custom'" class="mb-3">
            <label class="form-label form-label-sm">Ratio (e.g. 1 : 2 means first pays ⅓, second pays ⅔)</label>
            <div class="d-flex align-items-center gap-2">
              <div v-for="u in allUsers" :key="u.id" class="flex-1 text-center">
                <div class="small text-muted mb-1">{{ u.display_name }}</div>
                <input
                  type="number"
                  min="0"
                  step="1"
                  class="form-control form-control-sm text-center"
                  :value="modal.split_ratio[u.id] ?? 1"
                  @input="modal.split_ratio[u.id] = parseInt($event.target.value) || 0"
                />
              </div>
            </div>
          </div>

          <!-- Custom amount inputs -->
          <div v-if="modal.split_type === 'amount'" class="mb-3">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <label class="form-label form-label-sm mb-0">Amount per person (₹)</label>
              <span class="small" :class="splitAmountValid ? 'text-success' : 'text-danger'">
                Sum: ₹{{ fmt(splitAmountSum) }} / ₹{{ fmt(modal.amount || 0) }}
              </span>
            </div>
            <div class="d-flex align-items-center gap-2">
              <div v-for="u in allUsers" :key="u.id" class="flex-1 text-center">
                <div class="small text-muted mb-1">{{ u.display_name }}</div>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-control form-control-sm text-center"
                  :class="{ 'is-invalid': modal.split_type === 'amount' && !splitAmountValid && modal.amount }"
                  :value="modal.split_ratio[u.id] ?? 0"
                  @input="modal.split_ratio[u.id] = parseFloat($event.target.value) || 0"
                />
              </div>
            </div>
          </div>

          <div class="row g-2 mb-2">
            <div class="col-12">
              <label class="form-label form-label-sm">Notes</label>
              <textarea v-model="modal.notes" class="form-control form-control-sm" rows="2" placeholder="Optional…"></textarea>
            </div>
          </div>

          <div class="form-check mb-2">
            <input class="form-check-input" type="checkbox" v-model="modal.is_subscription" id="is-sub" />
            <label class="form-check-label small" for="is-sub">This is a recurring subscription</label>
          </div>

          <div v-if="modal.error" class="alert alert-danger py-2 small mt-2">{{ modal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-sm btn-primary" :disabled="modal.saving" @click="saveExpense">
            <span v-if="modal.saving" class="spinner-border spinner-border-sm me-1"></span>
            {{ modal.id ? "Save changes" : "Add Expense" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div class="modal-backdrop-custom" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Delete expense?</span>
          <button class="modal-close" @click="deleteTarget = null"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="mb-0">Delete <strong>{{ deleteTarget?.title }}</strong> (₹{{ fmt(deleteTarget?.amount) }})? Cannot be undone.</p>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="deleteTarget = null">Cancel</button>
          <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteExpense">
            <span v-if="deleting" class="spinner-border spinner-border-sm me-1"></span> Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Settle up modal -->
    <div class="modal-backdrop-custom" v-if="settleModal.open" @click.self="settleModal.open = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Record settlement</span>
          <button class="modal-close" @click="settleModal.open = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="small text-muted mb-3">
            Record a cash/transfer payment to reduce the running balance.
          </p>
          <div class="mb-3">
            <label class="form-label form-label-sm">Amount paid (₹) <span class="text-danger">*</span></label>
            <input v-model="settleModal.amount" type="number" min="1" step="0.01" class="form-control form-control-sm" />
          </div>
          <div class="mb-3">
            <label class="form-label form-label-sm">From → To</label>
            <div class="d-flex align-items-center gap-2">
              <select v-model="settleModal.paid_by" class="form-select form-select-sm">
                <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.display_name }}</option>
              </select>
              <i class="bi bi-arrow-right text-muted"></i>
              <select v-model="settleModal.paid_to" class="form-select form-select-sm">
                <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.display_name }}</option>
              </select>
            </div>
          </div>
          <div class="mb-2">
            <label class="form-label form-label-sm">Note</label>
            <input v-model="settleModal.note" type="text" class="form-control form-control-sm" placeholder="Optional…" />
          </div>
          <div v-if="settleModal.error" class="alert alert-danger py-2 small">{{ settleModal.error }}</div>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="settleModal.open = false">Cancel</button>
          <button class="btn btn-sm btn-success" :disabled="settleModal.saving" @click="recordSettlement">
            <span v-if="settleModal.saving" class="spinner-border spinner-border-sm me-1"></span>
            Record
          </button>
        </div>
      </div>
    </div>
    <!-- Balance Ledger Modal -->
    <div class="modal-backdrop-custom" v-if="ledger.open" @click.self="ledger.open = false">
      <div class="modal-card ledger-modal">
        <div class="modal-card-header">
          <span><i class="bi bi-journal-text me-2"></i>Balance Ledger</span>
          <div class="ledger-header-controls">
            <div class="ledger-month-nav">
              <button class="btn btn-sm btn-outline-secondary px-2" @click="changeLedgerMonth(-1)" :disabled="ledger.loading" title="Previous month"><i class="bi bi-chevron-left"></i></button>
              <span class="ledger-month-pill">{{ ledgerMonthLabel(ledger.month) }}</span>
              <button class="btn btn-sm btn-outline-secondary px-2" @click="changeLedgerMonth(1)" :disabled="ledger.loading" title="Next month"><i class="bi bi-chevron-right"></i></button>
            </div>
            <button class="btn btn-sm btn-outline-primary d-flex align-items-center gap-1" @click="downloadLedgerPDF" :disabled="ledger.loading || !ledger.data" title="Download as PDF">
              <i class="bi bi-file-earmark-arrow-down"></i>
              <span class="d-none d-sm-inline">PDF</span>
            </button>
            <button class="modal-close" @click="ledger.open = false"><i class="bi bi-x-lg"></i></button>
          </div>
        </div>
        <div class="modal-card-body ledger-body">

          <div v-if="ledger.loading" class="text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div> Loading ledger…
          </div>

          <div v-else-if="ledger.error" class="alert alert-danger">{{ ledger.error }}</div>

          <template v-else-if="ledger.data">

            <!-- Net balance summary -->
            <div v-if="ledger.data.balance" class="ledger-summary-card ledger-summary-owe">
              <div class="ledger-summary-icon"><i class="bi bi-arrow-left-right"></i></div>
              <div>
                <div class="ledger-summary-label">Net Balance — All Time (as of last entry)</div>
                <div class="ledger-summary-value">
                  <strong>{{ ledger.data.balance.debtor_name }}</strong> owes
                  <strong>{{ ledger.data.balance.creditor_name }}</strong>
                  <span class="ledger-summary-amount">₹{{ fmt(ledger.data.balance.amount) }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="ledger.data.entries?.length" class="ledger-summary-card ledger-summary-clear">
              <div class="ledger-summary-icon"><i class="bi bi-check2-circle"></i></div>
              <div>
                <div class="ledger-summary-label">All-Time Balance</div>
                <div class="ledger-summary-value">All settled — no outstanding balance</div>
              </div>
            </div>

            <!-- Empty -->
            <div v-if="!ledger.data.entries?.length" class="text-center py-4 text-muted">
              <i class="bi bi-receipt" style="font-size:2rem;display:block;margin-bottom:.5rem;"></i>
              No expenses recorded yet.
            </div>

            <!-- Chronological entries -->
            <div v-else class="ledger-timeline">
              <div class="ledger-timeline-label">{{ ledgerMonthLabel(ledger.month) }} — {{ ledger.data.entries.length }} {{ ledger.data.entries.length === 1 ? 'entry' : 'entries' }}</div>

              <template v-for="entry in ledger.data.entries" :key="entry.id">

                <!-- EXPENSE -->
                <div v-if="entry.type === 'expense'" class="ledger-entry ledger-entry-expense">
                  <div class="ledger-entry-datecol">
                    <div class="ledger-date">{{ new Date(entry.date + 'T00:00:00').toLocaleDateString('en-IN', { day:'numeric', month:'short' }) }}</div>
                    <div class="ledger-year">{{ new Date(entry.date + 'T00:00:00').getFullYear() }}</div>
                  </div>

                  <div class="ledger-entry-main">
                    <div class="ledger-entry-top">
                      <div class="ledger-cat-badge" :style="{ background: entry.category_color + '22', color: entry.category_color }">
                        <i :class="`bi ${entry.category_icon}`"></i>
                      </div>
                      <div class="ledger-entry-info">
                        <div class="ledger-entry-title">{{ entry.title }}</div>
                        <div class="ledger-entry-meta">
                          <span>{{ entry.category_name }}</span>
                          <span class="sep">·</span>
                          <span>Paid by <strong>{{ entry.paid_by_name }}</strong></span>
                          <span class="sep">·</span>
                          <span>{{ ledgerSplitDesc(entry) }}</span>
                        </div>
                      </div>
                      <div class="ledger-entry-amount">₹{{ fmt(entry.amount) }}</div>
                    </div>

                    <!-- Share breakdown per user -->
                    <div class="ledger-shares">
                      <div class="ledger-shares-row" v-for="u in ledger.data.users" :key="u.id">
                        <span class="ledger-share-name" :title="u.name">{{ u.name.split(' ')[0] }}</span>
                        <div class="ledger-share-bar-wrap">
                          <div
                            class="ledger-share-bar"
                            :style="{ width: entry.amount > 0 ? Math.round((entry.shares[u.id] || 0) / entry.amount * 100) + '%' : '0%', background: entry.category_color }"
                          ></div>
                        </div>
                        <span class="ledger-share-amount">₹{{ fmt(entry.shares[u.id] || 0) }}</span>
                        <span class="ledger-share-pct">{{ entry.amount > 0 ? Math.round((entry.shares[u.id] || 0) / entry.amount * 100) : 0 }}%</span>
                        <span v-if="u.id !== entry.paid_by && (entry.shares[u.id] || 0) > 0.005" class="ledger-owes-tag">owes {{ entry.paid_by_name.split(' ')[0] }}</span>
                        <span v-else-if="u.id === entry.paid_by" class="ledger-paid-tag">paid</span>
                        <span v-else class="ledger-noowe-tag">no obligation</span>
                      </div>
                    </div>

                    <!-- Net effect from this expense -->
                    <div v-if="entry.net_amount > 0" class="ledger-net-effect">
                      <i class="bi bi-arrow-right-circle me-1"></i>
                      From this: <strong>{{ ledgerUserName(entry.net_debtor) }}</strong> owes
                      <strong>{{ ledgerUserName(entry.net_creditor) }}</strong>
                      <span class="ledger-net-amount">₹{{ fmt(entry.net_amount) }}</span>
                    </div>
                    <div v-else class="ledger-net-effect ledger-net-none">
                      <i class="bi bi-person-check me-1"></i>
                      <strong>{{ entry.paid_by_name }}</strong> bears this cost entirely — no transfer
                    </div>

                    <!-- Running balance after this entry -->
                    <div class="ledger-running" :class="entry.running_amount > 0 ? 'ledger-running-owe' : 'ledger-running-clear'">
                      <i class="bi bi-arrow-return-right me-1"></i>
                      <span v-if="entry.running_amount > 0">
                        Running balance: <strong>{{ ledgerUserName(entry.running_debtor) }}</strong> owes
                        <strong>{{ ledgerUserName(entry.running_creditor) }}</strong>
                        <strong class="ledger-running-val">₹{{ fmt(entry.running_amount) }}</strong>
                      </span>
                      <span v-else>Running balance: <strong class="text-success">All settled ✓</strong></span>
                    </div>
                  </div>
                </div>

                <!-- SETTLEMENT -->
                <div v-else class="ledger-entry ledger-entry-settlement">
                  <div class="ledger-entry-datecol">
                    <div class="ledger-date">{{ new Date(entry.date + 'T00:00:00').toLocaleDateString('en-IN', { day:'numeric', month:'short' }) }}</div>
                    <div class="ledger-year">{{ new Date(entry.date + 'T00:00:00').getFullYear() }}</div>
                  </div>

                  <div class="ledger-entry-main">
                    <div class="ledger-entry-top">
                      <div class="ledger-settle-badge">
                        <i class="bi bi-check2-circle"></i>
                      </div>
                      <div class="ledger-entry-info">
                        <div class="ledger-entry-title">Settlement</div>
                        <div class="ledger-entry-meta">
                          <strong>{{ entry.paid_by_name }}</strong>
                          <span>paid</span>
                          <strong>{{ entry.paid_to_name }}</strong>
                          <span v-if="entry.note" class="sep">·</span>
                          <span v-if="entry.note">"{{ entry.note }}"</span>
                        </div>
                      </div>
                      <div class="ledger-entry-amount ledger-settle-amount">−₹{{ fmt(entry.amount) }}</div>
                    </div>

                    <div class="ledger-net-effect ledger-net-settle">
                      <i class="bi bi-arrow-down-circle me-1"></i>
                      Debt reduced by ₹{{ fmt(entry.amount) }} —
                      <strong>{{ entry.paid_by_name }}</strong> paid <strong>{{ entry.paid_to_name }}</strong> in full/partial settlement
                    </div>

                    <div class="ledger-running" :class="entry.running_amount > 0 ? 'ledger-running-owe' : 'ledger-running-clear'">
                      <i class="bi bi-arrow-return-right me-1"></i>
                      <span v-if="entry.running_amount > 0">
                        Running balance: <strong>{{ ledgerUserName(entry.running_debtor) }}</strong> owes
                        <strong>{{ ledgerUserName(entry.running_creditor) }}</strong>
                        <strong class="ledger-running-val">₹{{ fmt(entry.running_amount) }}</strong>
                      </span>
                      <span v-else>Running balance: <strong class="text-success">All settled ✓</strong></span>
                    </div>
                  </div>
                </div>

              </template>
            </div>
          </template>

        </div>
      </div>
    </div>

    <!-- Reset month confirm -->
    <div class="modal-backdrop-custom" v-if="resetConfirm" @click.self="resetConfirm = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-card-header">
          <span>Reset {{ monthLabel }}?</span>
          <button class="modal-close" @click="resetConfirm = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-card-body">
          <p class="mb-0">This will permanently delete <strong>all expenses</strong> for <strong>{{ monthLabel }}</strong>. Cannot be undone.</p>
        </div>
        <div class="modal-card-footer">
          <button class="btn btn-sm btn-outline-secondary" @click="resetConfirm = false">Cancel</button>
          <button class="btn btn-sm btn-danger" :disabled="resetting" @click="resetMonth">
            <span v-if="resetting" class="spinner-border spinner-border-sm me-1"></span> Delete all
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { RouterLink } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useFinanceStore } from "@/stores/finance";
import { Doughnut, Bar } from "vue-chartjs";
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const authStore = useAuthStore();
const financeStore = useFinanceStore();

const loading = ref(true);
const error = ref(null);
const expenses = ref([]);
const summary = computed(() => financeStore.summary);

// Month state
const today = new Date();
const selectedYear = ref(today.getFullYear());
const selectedMonth = ref(today.getMonth() + 1); // 1-12

const isCurrentMonth = computed(() =>
  selectedYear.value === today.getFullYear() && selectedMonth.value === today.getMonth() + 1
);

const monthKey = computed(() =>
  `${selectedYear.value}-${String(selectedMonth.value).padStart(2, "0")}`
);

const monthLabel = computed(() => {
  const d = new Date(selectedYear.value, selectedMonth.value - 1, 1);
  return d.toLocaleString("en-IN", { month: "long", year: "numeric" });
});

function shiftMonth(delta) {
  let m = selectedMonth.value + delta;
  let y = selectedYear.value;
  if (m > 12) { m = 1; y++; }
  if (m < 1) { m = 12; y--; }
  selectedMonth.value = m;
  selectedYear.value = y;
}

watch(monthKey, () => {
  filterCatId.value = null;
  loadData();
});

// All users + categories
const allUsers = computed(() => financeStore.settings?.users ?? []);
const currentUserId = computed(() => financeStore.settings?.current_user_id ?? "");
const myCategories = computed(() => {
  if (!financeStore.settings) return [];
  const { categories, assignments, current_user_id } = financeStore.settings;
  const ids = new Set(assignments.filter((a) => a.user_id === current_user_id).map((a) => a.category_id));
  return categories.filter((c) => ids.has(c.id));
});

// Balance
const isDebtor = computed(() =>
  summary.value?.balance?.debtor_id === currentUserId.value
);

// Privacy filter — own expenses + shared-category expenses
const sharedCategoryIds = computed(() => {
  const cats = financeStore.settings?.categories ?? [];
  return new Set(cats.filter((c) => c.is_shared).map((c) => c.id));
});

const myExpenses = computed(() =>
  expenses.value.filter(
    (e) => e.paid_by === currentUserId.value || sharedCategoryIds.value.has(e.category_id)
  )
);

// Category filter
const filterCatId = ref(null);

const categoriesWithExpenses = computed(() => {
  const seen = new Set(myExpenses.value.map((e) => e.category_id).filter(Boolean));
  return (financeStore.settings?.categories ?? []).filter((c) => seen.has(c.id));
});

const filteredExpenses = computed(() =>
  filterCatId.value
    ? myExpenses.value.filter((e) => e.category_id === filterCatId.value)
    : myExpenses.value
);

// Grouped expenses by date
const groupedExpenses = computed(() => {
  const groups = {};
  for (const exp of filteredExpenses.value) {
    if (!groups[exp.expense_date]) groups[exp.expense_date] = [];
    groups[exp.expense_date].push(exp);
  }
  return groups;
});

// ── Charts ─────────────────────────────────────────────────────────────────
const categoryChartData = computed(() => {
  const totals = {}, colors = {};
  for (const e of myExpenses.value) {
    const name = e.category_name || "Uncategorized";
    totals[name] = (totals[name] || 0) + e.amount;
    colors[name] = e.category_color || "#9ca3af";
  }
  const labels = Object.keys(totals);
  return {
    labels,
    datasets: [{ data: labels.map((l) => totals[l]), backgroundColor: labels.map((l) => colors[l]), borderWidth: 0 }],
  };
});

const dailyChartData = computed(() => {
  const totals = {};
  for (const e of myExpenses.value) {
    totals[e.expense_date] = (totals[e.expense_date] || 0) + e.amount;
  }
  const days = Object.keys(totals).sort();
  return {
    labels: days.map((d) => new Date(d + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short" })),
    datasets: [{
      label: "Spent",
      data: days.map((d) => totals[d]),
      backgroundColor: "#0d6efd33",
      borderColor: "#0d6efd",
      borderWidth: 2,
      borderRadius: 6,
    }],
  };
});

const fmtInr = (v) => "₹" + Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 });

const donutOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { position: "right", labels: { boxWidth: 10, font: { size: 11 }, padding: 8 } },
    tooltip: { callbacks: { label: (ctx) => " " + fmtInr(ctx.raw) } },
  },
  cutout: "62%",
};

const barOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (ctx) => " " + fmtInr(ctx.raw) } },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
    y: { grid: { color: "#f3f4f6" }, ticks: { font: { size: 10 }, callback: (v) => "₹" + v } },
  },
};

function fmt(n) {
  if (n == null) return "0";
  return Number(n).toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", {
    day: "numeric", month: "short", weekday: "short",
  });
}

function splitLabel(exp) {
  if (exp.split_type === "none") return "No split";
  if (exp.split_type === "equal") return "50/50";
  if (exp.split_type === "amount") return "Custom ₹";
  return "Ratio";
}

const splitAmountSum = computed(() => {
  if (modal.value.split_type !== "amount") return 0;
  return Object.values(modal.value.split_ratio).reduce((s, v) => s + (parseFloat(v) || 0), 0);
});

const splitAmountValid = computed(() => {
  if (modal.value.split_type !== "amount") return true;
  const total = parseFloat(modal.value.amount) || 0;
  return total > 0 && Math.abs(splitAmountSum.value - total) <= 0.01;
});

// ── Modal ──────────────────────────────────────────────────────────────────

const blankModal = () => ({
  open: false, id: null,
  title: "", amount: "", category_id: "",
  paid_by: currentUserId.value,
  expense_date: new Date().toISOString().slice(0, 10),
  split_type: "equal",
  split_ratio: {},
  payment_method: "card",
  notes: "", is_subscription: false,
  saving: false, error: "",
});

const modal = ref(blankModal());
const deleteTarget = ref(null);
const deleting = ref(false);
const resetConfirm = ref(false);
const resetting = ref(false);

function openCreate() {
  const m = blankModal();
  m.open = true;
  m.paid_by = currentUserId.value;
  // init split_ratio with 1 for each user
  for (const u of allUsers.value) m.split_ratio[u.id] = 1;
  modal.value = m;
}

function openEdit(exp) {
  const ratioInit = {};
  for (const u of allUsers.value) ratioInit[u.id] = exp.split_ratio?.[u.id] ?? 1;
  modal.value = {
    open: true, id: exp.id,
    title: exp.title,
    amount: exp.amount,
    category_id: exp.category_id,
    paid_by: exp.paid_by,
    expense_date: exp.expense_date,
    split_type: exp.split_type,
    split_ratio: ratioInit,
    payment_method: exp.payment_method,
    notes: exp.notes ?? "",
    is_subscription: exp.is_subscription,
    saving: false, error: "",
  };
}

function closeModal() { modal.value.open = false; }

async function saveExpense() {
  const m = modal.value;
  m.error = "";
  if (!m.title.trim()) { m.error = "Title required."; return; }
  if (!m.amount || parseFloat(m.amount) <= 0) { m.error = "Valid amount required."; return; }
  if (!m.category_id) { m.error = "Category required."; return; }
  if (m.split_type === "amount" && !splitAmountValid.value) {
    m.error = `Split amounts must sum to ₹${fmt(m.amount)} (currently ₹${fmt(splitAmountSum.value)}).`;
    return;
  }
  m.saving = true;

  const payload = {
    title: m.title.trim(),
    amount: parseFloat(m.amount),
    category_id: m.category_id,
    paid_by: m.paid_by,
    expense_date: m.expense_date,
    split_type: m.split_type,
    split_ratio: (m.split_type === "custom" || m.split_type === "amount") ? m.split_ratio : null,
    payment_method: m.payment_method,
    notes: m.notes || null,
    is_subscription: m.is_subscription,
  };

  try {
    const res = await authStore.apiFetch(
      m.id ? `/api/finance/expenses/${m.id}` : "/api/finance/expenses",
      { method: m.id ? "PUT" : "POST", body: JSON.stringify(payload) }
    );
    if (!res.ok) {
      const d = await res.json();
      m.error = d.error || "Save failed.";
      return;
    }
    closeModal();
    await loadData();
  } catch {
    m.error = "Network error.";
  } finally {
    m.saving = false;
  }
}

function confirmDelete(exp) { deleteTarget.value = exp; }

async function deleteExpense() {
  deleting.value = true;
  try {
    const res = await authStore.apiFetch(`/api/finance/expenses/${deleteTarget.value.id}`, { method: "DELETE" });
    if (res.ok) {
      deleteTarget.value = null;
      await loadData();
    }
  } finally {
    deleting.value = false;
  }
}

async function resetMonth() {
  resetting.value = true;
  try {
    const res = await authStore.apiFetch(`/api/finance/expenses?month=${monthKey.value}`, { method: "DELETE" });
    if (res.ok) {
      resetConfirm.value = false;
      await loadData();
    }
  } finally {
    resetting.value = false;
  }
}

// ── Settle modal ───────────────────────────────────────────────────────────

const settleModal = ref({ open: false, paid_by: "", paid_to: "", amount: "", note: "", saving: false, error: "" });

function openSettle() {
  const bal = summary.value?.balance;
  settleModal.value = {
    open: true,
    paid_by: bal?.debtor_id ?? currentUserId.value,
    paid_to: bal?.creditor_id ?? "",
    amount: bal?.amount ?? "",
    note: "",
    saving: false,
    error: "",
  };
}

async function recordSettlement() {
  const s = settleModal.value;
  s.error = "";
  if (!s.amount || parseFloat(s.amount) <= 0) { s.error = "Valid amount required."; return; }
  if (s.paid_by === s.paid_to) { s.error = "Payer and recipient must differ."; return; }
  s.saving = true;
  try {
    const res = await authStore.apiFetch("/api/finance/settlements", {
      method: "POST",
      body: JSON.stringify({ paid_by: s.paid_by, paid_to: s.paid_to, amount: parseFloat(s.amount), note: s.note || null }),
    });
    if (!res.ok) {
      const d = await res.json();
      s.error = d.error || "Failed.";
      return;
    }
    settleModal.value.open = false;
    await financeStore.fetchSummary(monthKey.value);
  } catch {
    s.error = "Network error.";
  } finally {
    s.saving = false;
  }
}

// ── Balance Ledger ─────────────────────────────────────────────────────────

const ledger = ref({ open: false, loading: false, error: null, data: null, month: null });

async function openLedger() {
  ledger.value = { open: true, loading: true, error: null, data: null, month: monthKey.value };
  await _fetchLedger(monthKey.value);
}

async function _fetchLedger(month) {
  ledger.value.loading = true;
  ledger.value.error = null;
  ledger.value.data = null;
  try {
    const q = month ? `?month=${month}` : "";
    const res = await authStore.apiFetch(`/api/finance/balance/breakdown${q}`);
    if (!res.ok) throw new Error("Failed to load balance breakdown");
    ledger.value.data = await res.json();
  } catch (e) {
    ledger.value.error = e.message || "Failed to load ledger";
  } finally {
    ledger.value.loading = false;
  }
}

async function changeLedgerMonth(delta) {
  const [y, m] = ledger.value.month.split("-").map(Number);
  let nm = m + delta, ny = y;
  if (nm > 12) { nm = 1; ny++; }
  if (nm < 1) { nm = 12; ny--; }
  ledger.value.month = `${ny}-${String(nm).padStart(2, "0")}`;
  await _fetchLedger(ledger.value.month);
}

function ledgerMonthLabel(ym) {
  if (!ym) return "All Time";
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleString("en-IN", { month: "long", year: "numeric" });
}

function ledgerUserName(uid) {
  return ledger.value.data?.users?.find(u => u.id === uid)?.name ?? "Unknown";
}

function ledgerSplitDesc(entry) {
  switch (entry.split_type) {
    case "equal": return "Split equally (50/50)";
    case "none": return `${entry.paid_by_name} pays fully — no split`;
    case "amount": return "Custom ₹ amounts";
    case "custom": return "Custom ratio split";
    default: return "";
  }
}

function downloadLedgerPDF() {
  const d = ledger.value.data;
  if (!d) return;
  const monthLabel = ledgerMonthLabel(ledger.value.month);
  const users = d.users ?? [];

  const fmtAmt = (n) => "₹" + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const balanceLine = d.balance
    ? `<p class="bal-owe"><strong>${d.balance.debtor_name}</strong> owes <strong>${d.balance.creditor_name}</strong> ${fmtAmt(d.balance.amount)}</p>`
    : `<p class="bal-clear">All settled — no outstanding balance</p>`;

  const rows = (d.entries ?? []).map(e => {
    if (e.type === "expense") {
      const sharesHtml = users.map(u => {
        const sh = e.shares?.[u.id] ?? 0;
        const tag = u.id !== e.paid_by && sh > 0.005 ? " (owes)"
          : u.id === e.paid_by ? " (paid)" : " (—)";
        return `${u.name.split(" ")[0]}: ${fmtAmt(sh)}${tag}`;
      }).join(" &nbsp;|&nbsp; ");
      const netLine = e.net_amount > 0
        ? `Net: ${ledgerUserName(e.net_debtor)} owes ${ledgerUserName(e.net_creditor)} ${fmtAmt(e.net_amount)}`
        : `No obligation transfer`;
      const runLine = e.running_amount > 0
        ? `Running: ${ledgerUserName(e.running_debtor)} owes ${ledgerUserName(e.running_creditor)} ${fmtAmt(e.running_amount)}`
        : `Running: All settled`;
      return `<tr>
        <td>${e.date}</td>
        <td>${e.title}<br><small class="meta">${e.category_name} · ${e.paid_by_name} paid ${fmtAmt(e.amount)} · ${ledgerSplitDesc(e)}</small></td>
        <td><small>${sharesHtml}</small><br><small class="net">${netLine}</small></td>
        <td class="run">${runLine}</td>
      </tr>`;
    } else {
      return `<tr class="settle-row">
        <td>${e.date}</td>
        <td colspan="2">Settlement: <strong>${e.paid_by_name}</strong> paid <strong>${e.paid_to_name}</strong> ${fmtAmt(e.amount)}${e.note ? " — " + e.note : ""}</td>
        <td class="run">${e.running_amount > 0 ? `Running: ${ledgerUserName(e.running_debtor)} owes ${ledgerUserName(e.running_creditor)} ${fmtAmt(e.running_amount)}` : "Running: All settled"}</td>
      </tr>`;
    }
  }).join("");

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Balance Ledger — ${monthLabel}</title>
<style>
  body { font-family: Arial, sans-serif; font-size: 11px; color: #111; margin: 24px; }
  h1 { font-size: 16px; margin-bottom: 4px; }
  .subtitle { color: #555; font-size: 12px; margin-bottom: 12px; }
  .bal-owe { background: #fff3cd; padding: 8px 12px; border-radius: 6px; font-size: 13px; display: inline-block; }
  .bal-clear { background: #d1fae5; padding: 8px 12px; border-radius: 6px; font-size: 13px; display: inline-block; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; }
  th { background: #f3f4f6; text-align: left; padding: 6px 8px; font-size: 11px; border-bottom: 2px solid #ddd; }
  td { padding: 6px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
  .settle-row td { background: #f0fdf4; }
  .meta { color: #666; }
  .net { color: #92400e; }
  .run { color: #1d4ed8; font-size: 10px; }
  @page { size: A4 landscape; margin: 15mm; }
</style></head><body>
<h1>Balance Ledger — ${monthLabel}</h1>
<div class="subtitle">H&amp;M Home Finance · Generated ${new Date().toLocaleDateString("en-IN", { day:"numeric", month:"long", year:"numeric" })}</div>
${balanceLine}
<table>
  <thead><tr><th>Date</th><th>Description</th><th>Split Breakdown</th><th>Running Balance</th></tr></thead>
  <tbody>${rows}</tbody>
</table>
</body></html>`;

  const win = window.open("", "_blank");
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); }, 400);
}

// ── Load ───────────────────────────────────────────────────────────────────

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    await Promise.all([
      financeStore.fetchSettings(),
      financeStore.fetchSummary(monthKey.value),
    ]);
    const res = await authStore.apiFetch(`/api/finance/expenses?month=${monthKey.value}`);
    if (!res.ok) throw new Error("Failed to load expenses");
    expenses.value = await res.json();
  } catch (e) {
    error.value = e.message || "Failed to load finance data.";
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.month-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  min-width: 120px;
  text-align: center;
}

/* Balance chip */
.balance-chip {
  display: inline-flex;
  align-items: center;
  font-size: 0.82rem;
  padding: 0.3rem 0.75rem;
  border-radius: 99px;
  font-weight: 500;
  max-width: 260px;
  overflow: hidden;
}
.balance-text {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.balance-net-tag {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.6;
  flex-shrink: 0;
}
.balance-owe { background: #fef9c3; color: #854d0e; }
.balance-owed { background: #dcfce7; color: #166534; }
.balance-clear { background: #f0fdf4; color: #166534; }

/* Budget cards */
.budget-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.budget-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #f3f4f6;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  padding: 1rem 1.25rem 0.75rem;
}

.budget-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.budget-user {
  font-weight: 700;
  font-size: 0.9rem;
  color: #111827;
}

.budget-amounts {
  font-size: 0.83rem;
}

.budget-spent { font-weight: 700; color: #111827; }
.budget-limit { color: #9ca3af; }

.budget-bar-track {
  height: 6px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}
.budget-bar-fill {
  height: 100%;
  background: #0d6efd;
  border-radius: 99px;
  transition: width 0.4s ease;
}
.budget-bar-over { background: #dc2626; }

.budget-cats {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.budget-cat-row {
  display: grid;
  grid-template-columns: 8px 1fr auto;
  grid-template-rows: auto 4px;
  column-gap: 0.5rem;
  row-gap: 0.2rem;
  align-items: center;
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  grid-row: 1;
}

.cat-name {
  font-size: 0.8rem;
  color: #374151;
  grid-row: 1;
}

.cat-amounts {
  font-size: 0.78rem;
  grid-row: 1;
  text-align: right;
}
.cat-spent { font-weight: 600; color: #111827; }
.cat-limit { color: #9ca3af; }

.cat-bar-track {
  height: 4px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
  grid-column: 1 / -1;
  grid-row: 2;
}
.cat-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;
  opacity: 0.75;
}
.cat-bar-over { filter: brightness(0.8); }

.budget-cat-empty {
  font-size: 0.78rem;
  color: #9ca3af;
  text-align: center;
  padding: 0.5rem 0;
}

/* Expense list */
.expenses-empty {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #f3f4f6;
  padding: 3rem 2rem;
  text-align: center;
  color: #9ca3af;
}
.expenses-empty i {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.75rem;
}

.expense-date-heading {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  padding: 0.6rem 0 0.3rem;
}

.expense-list {
  display: flex;
  flex-direction: column;
}

.expense-item {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f3f4f6;
  padding: 0.7rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 0.45rem;
  transition: box-shadow 0.12s;
}
.expense-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); }

.exp-cat-badge {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.exp-content { flex: 1; min-width: 0; }

.exp-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.badge-sub {
  font-size: 0.65rem;
  background: #ede9fe;
  color: #7c3aed;
  padding: 0.05rem 0.4rem;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.exp-meta {
  font-size: 0.75rem;
  color: #9ca3af;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem;
  margin-top: 0.2rem;
}

.sep { color: #d1d5db; }

.split-badge {
  padding: 0.05rem 0.4rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}
.split-equal { background: #dbeafe; color: #1d4ed8; }
.split-custom { background: #fce7f3; color: #be185d; }
.split-amount { background: #fef3c7; color: #92400e; }
.split-none { background: #f3f4f6; color: #6b7280; }

.exp-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.2rem;
  flex-shrink: 0;
}

.exp-amount {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
}

.exp-actions {
  display: flex;
  gap: 0.15rem;
}

/* Shared button / modal styles (same as Notes/Reminders) */
.note-btn {
  background: none;
  border: none;
  color: #9ca3af;
  padding: 0.2rem 0.3rem;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.8rem;
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
  max-width: 540px;
  max-height: 90vh;
  overflow-y: auto;
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
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 1;
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
  position: sticky;
  bottom: 0;
  background: #fff;
}

.flex-1 { flex: 1; }

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
.chart-wrap-donut { height: 200px; }

/* Category filter pills */
.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.78rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #6b7280;
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
  white-space: nowrap;
}
.pill:hover { background: #f3f4f6; color: #374151; border-color: #d1d5db; }
.pill-active { background: #111827; color: #fff; border-color: #111827; }

/* ─── Balance Ledger ─────────────────────────── */
.ledger-modal { max-width: 720px; }
.ledger-body { padding: 1rem 1.25rem; }

.ledger-header-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.ledger-month-nav {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.ledger-month-pill {
  font-size: 0.78rem;
  font-weight: 600;
  color: #374151;
  min-width: 90px;
  text-align: center;
  white-space: nowrap;
}

.ledger-summary-card {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.25rem;
}
.ledger-summary-owe { background: #fef9c3; border: 1px solid #fde68a; }
.ledger-summary-clear { background: #f0fdf4; border: 1px solid #bbf7d0; }
.ledger-summary-icon { font-size: 1.4rem; color: #92400e; line-height: 1; margin-top: 0.1rem; }
.ledger-summary-clear .ledger-summary-icon { color: #166534; }
.ledger-summary-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #92400e;
  margin-bottom: 0.25rem;
}
.ledger-summary-clear .ledger-summary-label { color: #166534; }
.ledger-summary-value { font-size: 0.95rem; color: #111827; }
.ledger-summary-amount { font-weight: 700; font-size: 1.1rem; color: #92400e; margin-left: 0.35rem; }

.ledger-timeline-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  margin-bottom: 0.75rem;
}

.ledger-timeline { display: flex; flex-direction: column; }

.ledger-entry {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.ledger-entry-datecol {
  width: 44px;
  flex-shrink: 0;
  text-align: center;
  padding-top: 0.75rem;
}
.ledger-date { font-size: 0.72rem; font-weight: 700; color: #374151; line-height: 1.2; }
.ledger-year { font-size: 0.65rem; color: #9ca3af; }

.ledger-entry-main {
  flex: 1;
  background: #fff;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  min-width: 0;
}
.ledger-entry-settlement .ledger-entry-main { background: #f0fdf4; border-color: #bbf7d0; }

.ledger-entry-top {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
}
.ledger-cat-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}
.ledger-settle-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
  background: #dcfce7;
  color: #16a34a;
}
.ledger-entry-info { flex: 1; min-width: 0; }
.ledger-entry-title { font-size: 0.88rem; font-weight: 600; color: #111827; }
.ledger-entry-meta {
  font-size: 0.73rem;
  color: #9ca3af;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.2rem;
  margin-top: 0.15rem;
}
.ledger-entry-amount { font-size: 0.95rem; font-weight: 700; color: #111827; flex-shrink: 0; }
.ledger-settle-amount { color: #16a34a; }

.ledger-shares {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  background: #f9fafb;
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  margin-bottom: 0.5rem;
}
.ledger-shares-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
}
.ledger-share-name {
  width: 72px;
  flex-shrink: 0;
  font-weight: 500;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ledger-share-bar-wrap { flex: 1; height: 6px; background: #e5e7eb; border-radius: 99px; overflow: hidden; }
.ledger-share-bar { height: 100%; border-radius: 99px; transition: width 0.3s ease; opacity: 0.75; }
.ledger-share-amount { width: 60px; text-align: right; font-weight: 600; color: #111827; flex-shrink: 0; }
.ledger-share-pct { width: 34px; text-align: right; font-size: 0.7rem; color: #9ca3af; flex-shrink: 0; }

.ledger-owes-tag {
  font-size: 0.68rem; padding: 0.05rem 0.4rem; border-radius: 4px;
  background: #fef3c7; color: #92400e; font-weight: 500; flex-shrink: 0; white-space: nowrap;
}
.ledger-paid-tag {
  font-size: 0.68rem; padding: 0.05rem 0.4rem; border-radius: 4px;
  background: #dbeafe; color: #1d4ed8; font-weight: 500; flex-shrink: 0;
}
.ledger-noowe-tag {
  font-size: 0.68rem; padding: 0.05rem 0.4rem; border-radius: 4px;
  background: #f3f4f6; color: #6b7280; font-weight: 500; flex-shrink: 0;
}

.ledger-net-effect {
  font-size: 0.78rem;
  color: #374151;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  background: #fefce8;
  border-left: 3px solid #facc15;
  margin-bottom: 0.5rem;
}
.ledger-net-none { background: #f9fafb; border-left-color: #d1d5db; color: #6b7280; }
.ledger-net-settle { background: #f0fdf4; border-left-color: #4ade80; color: #166534; }
.ledger-net-amount { font-weight: 700; color: #92400e; margin-left: 0.2rem; }

.ledger-running {
  font-size: 0.75rem;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
}
.ledger-running-owe { background: #fef9c3; color: #854d0e; }
.ledger-running-clear { background: #f0fdf4; color: #166534; }
.ledger-running-val { font-size: 0.85rem; margin-left: 0.25rem; }

/* ─── Mobile ─────────────────────────────────── */
@media (max-width: 480px) {
  .page-header { flex-wrap: wrap; gap: 0.5rem; }

  .budget-card { padding: 0.75rem 1rem 0.6rem; }

  .expense-item { padding: 0.55rem 0.75rem; gap: 0.6rem; }
  .exp-cat-badge { width: 30px; height: 30px; font-size: 0.85rem; }
  .exp-amount { font-size: 0.85rem; }
  .exp-meta { font-size: 0.7rem; gap: 0.15rem; }

  /* hide payment method on tiny screens — least useful meta field */
  .exp-meta .exp-payment { display: none; }
  .exp-meta .exp-payment-sep { display: none; }

  .balance-chip { max-width: 200px; font-size: 0.76rem; padding: 0.25rem 0.6rem; }

  .month-label { font-size: 0.82rem; min-width: 90px; }

  .modal-card-body { padding: 0.75rem 1rem; }
  .modal-card-footer { padding: 0.6rem 1rem 0.75rem; }

  .ledger-entry-datecol { width: 34px; }
  .ledger-share-name { width: 54px; }
  .ledger-share-amount { width: 48px; }
  .ledger-share-pct { display: none; }
  .ledger-owes-tag, .ledger-paid-tag, .ledger-noowe-tag { display: none; }
}
</style>
