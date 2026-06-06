<template>
  <div class="landing">

    <!-- ── Nav ─────────────────────────────────────────────────────────────── -->
    <nav class="landing-nav">
      <div class="landing-nav-inner">
        <div class="landing-brand">
          <i class="bi bi-house-heart-fill"></i>
          <span>H&M Home</span>
        </div>
        <router-link to="/login" class="landing-login-btn">
          <i class="bi bi-box-arrow-in-right"></i>
          <span>Login</span>
        </router-link>
      </div>
    </nav>

    <!-- ── Hero ─────────────────────────────────────────────────────────────── -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-badge">
          <i class="bi bi-stars"></i>
          Built with AI-assisted development
        </div>
        <h1 class="hero-title">Your household,<br><span class="hero-accent">fully organised.</span></h1>
        <p class="hero-sub">
          H&M Home is a private full-stack household management platform — tracking shared finances,
          budgets, reminders, notes, and health data for two people living together.
        </p>
        <div class="hero-actions">
          <router-link to="/login" class="hero-cta">
            <i class="bi bi-box-arrow-in-right"></i>
            Enter App
          </router-link>
          <a href="#features" class="hero-ghost">See Features</a>
        </div>
        <div class="hero-stack">
          <span class="stack-pill"><i class="bi bi-diagram-3"></i> Vue 3</span>
          <span class="stack-pill"><i class="bi bi-server"></i> Flask</span>
          <span class="stack-pill"><i class="bi bi-database"></i> PostgreSQL</span>
          <span class="stack-pill"><i class="bi bi-fire"></i> Firebase</span>
          <span class="stack-pill"><i class="bi bi-robot"></i> Claude AI</span>
        </div>
      </div>
      <div class="hero-visual">
        <div class="mockup-card">
          <div class="mockup-header">
            <div class="mockup-dots"><span></span><span></span><span></span></div>
            <span class="mockup-title">Finance — June 2026</span>
          </div>
          <div class="mockup-body">
            <div class="mockup-balance">
              <div class="mockup-balance-label">Net Balance</div>
              <div class="mockup-balance-chip">All settled ✓</div>
            </div>
            <div class="mockup-rows">
              <div class="mockup-row" v-for="row in mockRows" :key="row.name">
                <div class="mockup-row-dot" :style="{ background: row.color }"></div>
                <div class="mockup-row-info">
                  <div class="mockup-row-name">{{ row.name }}</div>
                  <div class="mockup-row-bar-wrap">
                    <div class="mockup-row-bar" :style="{ width: row.pct + '%', background: row.color }"></div>
                  </div>
                </div>
                <div class="mockup-row-amt">{{ row.amt }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Features ─────────────────────────────────────────────────────────── -->
    <section class="features" id="features">
      <div class="section-inner">
        <div class="section-label">What's inside</div>
        <h2 class="section-title">Every corner of home life, covered.</h2>
        <div class="features-grid">
          <div class="feature-card" v-for="f in features" :key="f.title">
            <div class="feature-icon" :style="{ background: f.bg, color: f.color }">
              <i :class="f.icon"></i>
            </div>
            <h3 class="feature-title">{{ f.title }}</h3>
            <p class="feature-desc">{{ f.desc }}</p>
            <ul class="feature-list">
              <li v-for="b in f.bullets" :key="b"><i class="bi bi-check2"></i> {{ b }}</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- ── AI Section ────────────────────────────────────────────────────────── -->
    <section class="ai-section">
      <div class="section-inner">
        <div class="ai-card">
          <div class="ai-icon"><i class="bi bi-robot"></i></div>
          <div class="ai-content">
            <div class="section-label" style="text-align:left; margin-bottom:.5rem;">AI-Assisted Development</div>
            <h2 class="ai-title">Built using AI-first engineering workflow</h2>
            <p class="ai-desc">
              This project was developed using <strong>Claude (Anthropic)</strong> as an AI coding partner — not just for boilerplate,
              but for architecture decisions, debugging complex split-logic bugs, designing the balance ledger algorithm,
              and generating the PDF export feature end-to-end.
            </p>
            <div class="ai-pills">
              <span class="ai-pill"><i class="bi bi-braces"></i> Backend API design</span>
              <span class="ai-pill"><i class="bi bi-layout-text-sidebar"></i> UI/UX component work</span>
              <span class="ai-pill"><i class="bi bi-bug"></i> Debt-matrix debugging</span>
              <span class="ai-pill"><i class="bi bi-file-earmark-pdf"></i> PDF export generation</span>
              <span class="ai-pill"><i class="bi bi-arrow-repeat"></i> Iterative feature builds</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Tech Stack ────────────────────────────────────────────────────────── -->
    <section class="tech-section">
      <div class="section-inner">
        <div class="section-label">Tech Stack</div>
        <h2 class="section-title">Production-grade, full-stack.</h2>
        <div class="tech-grid">
          <div class="tech-card" v-for="t in techStack" :key="t.name">
            <div class="tech-icon" :style="{ color: t.color }"><i :class="t.icon"></i></div>
            <div class="tech-name">{{ t.name }}</div>
            <div class="tech-role">{{ t.role }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Private Notice ─────────────────────────────────────────────────────── -->
    <section class="private-section">
      <div class="section-inner">
        <div class="private-card">
          <div class="private-icon"><i class="bi bi-shield-lock-fill"></i></div>
          <h2 class="private-title">Private Application</h2>
          <p class="private-desc">
            H&M Home is a personal project designed for private household use — not open for public registration.
            If you've landed here out of curiosity, thank you genuinely for showing interest.
          </p>
          <p class="private-desc">
            The codebase and architecture are available for discussion as part of my portfolio.
            Authorised users may sign in below.
          </p>
          <router-link to="/login" class="hero-cta" style="display:inline-flex; margin-top:.5rem;">
            <i class="bi bi-box-arrow-in-right"></i>
            Authorised Login
          </router-link>
        </div>
      </div>
    </section>

    <!-- ── Footer ─────────────────────────────────────────────────────────────── -->
    <footer class="landing-footer">
      <div class="section-inner footer-inner">
        <div class="footer-brand">
          <i class="bi bi-house-heart-fill"></i> H&M Home
        </div>
        <div class="footer-note">
          Portfolio project · Built by Hitesh Pradhan · AI-assisted with Claude
        </div>
      </div>
    </footer>

  </div>
</template>

<script setup>
const mockRows = [
  { name: "Rent", pct: 80, color: "#6366f1", amt: "₹12,000" },
  { name: "Groceries", pct: 45, color: "#10b981", amt: "₹3,200" },
  { name: "Dining", pct: 30, color: "#f59e0b", amt: "₹2,100" },
  { name: "Utilities", pct: 20, color: "#3b82f6", amt: "₹1,400" },
];

const features = [
  {
    icon: "bi bi-wallet2",
    title: "Finance Manager",
    bg: "#eff6ff",
    color: "#2563eb",
    desc: "Complete household expense tracking with smart bill splitting between two users.",
    bullets: [
      "Equal, custom-ratio, or exact-amount splits",
      "Monthly budgets per category",
      "Visual spending breakdown charts",
      "Chronological balance ledger with PDF export",
    ],
  },
  {
    icon: "bi bi-arrow-left-right",
    title: "Balance & Settlements",
    bg: "#fefce8",
    color: "#ca8a04",
    desc: "Always-accurate running debt tracking with chronological settlement logic.",
    bullets: [
      "Debt matrix with temporal settlement ordering",
      "Per-transaction running balance",
      "Settlement history with notes",
      "Month-filtered PDF ledger export",
    ],
  },
  {
    icon: "bi bi-bell",
    title: "Reminders",
    bg: "#fdf4ff",
    color: "#9333ea",
    desc: "Push notification reminders for bills, tasks, and recurring household events.",
    bullets: [
      "FCM push notifications (web & PWA)",
      "Recurring reminder support",
      "Targeted per-user delivery",
      "Foreground in-app toast alerts",
    ],
  },
  {
    icon: "bi bi-sticky",
    title: "Shared Notes",
    bg: "#f0fdf4",
    color: "#16a34a",
    desc: "Shared household notepad for lists, ideas, and important information.",
    bullets: [
      "Real-time shared note space",
      "Pinned and categorised notes",
      "Markdown-friendly content",
      "Timestamped edit history",
    ],
  },
  {
    icon: "bi bi-heart-pulse",
    title: "Health Tracking",
    bg: "#fff1f2",
    color: "#e11d48",
    desc: "Log and visualise personal health metrics over time.",
    bullets: [
      "Daily health metric logging",
      "Trend charts over time",
      "Per-user private data",
      "Goal tracking support",
    ],
  },
  {
    icon: "bi bi-gear",
    title: "Household Settings",
    bg: "#f8fafc",
    color: "#475569",
    desc: "Full configuration of categories, budgets, and user assignments.",
    bullets: [
      "Custom expense categories",
      "Per-user category assignments",
      "Monthly budget management",
      "Budget rollover logic",
    ],
  },
];

const techStack = [
  { icon: "bi bi-filetype-vue", name: "Vue 3", role: "Frontend framework (Composition API)", color: "#42b883" },
  { icon: "bi bi-lightning-fill", name: "Vite", role: "Build tool & dev server", color: "#646cff" },
  { icon: "bi bi-shop", name: "Pinia", role: "State management", color: "#f59e0b" },
  { icon: "bi bi-server", name: "Flask", role: "Python REST API backend", color: "#10b981" },
  { icon: "bi bi-database-fill", name: "PostgreSQL", role: "Primary relational database", color: "#336791" },
  { icon: "bi bi-fire", name: "Firebase", role: "Google auth + push notifications", color: "#ef4444" },
  { icon: "bi bi-phone", name: "PWA", role: "Installable progressive web app", color: "#6366f1" },
  { icon: "bi bi-robot", name: "Claude AI", role: "AI-assisted engineering partner", color: "#d97706" },
];
</script>

<style scoped>
/* ── Reset & base ────────────────────────────────────────────────────────── */
.landing {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  background: #0a0f1e;
  color: #f9fafb;
  min-height: 100vh;
}

.section-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* ── Nav ─────────────────────────────────────────────────────────────────── */
.landing-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(10, 15, 30, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.landing-nav-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.9rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.landing-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.05rem;
  color: #f9fafb;
}

.landing-brand i {
  color: #6366f1;
  font-size: 1.2rem;
}

.landing-login-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 1rem;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s;
}

.landing-login-btn:hover {
  background: rgba(99, 102, 241, 0.28);
  border-color: rgba(99, 102, 241, 0.6);
  color: #c7d2fe;
}

/* ── Hero ────────────────────────────────────────────────────────────────── */
.hero {
  display: flex;
  align-items: center;
  gap: 3rem;
  padding: 5rem 1.5rem 4rem;
  max-width: 1100px;
  margin: 0 auto;
}

.hero-inner { flex: 1; min-width: 0; }

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(99, 102, 241, 0.12);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 100px;
  padding: 0.3rem 0.85rem;
  font-size: 0.78rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.hero-title {
  font-size: clamp(2rem, 5vw, 3.25rem);
  font-weight: 800;
  line-height: 1.1;
  color: #f9fafb;
  margin: 0 0 1rem;
  letter-spacing: -0.02em;
}

.hero-accent {
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  color: #9ca3af;
  font-size: 1.05rem;
  line-height: 1.65;
  margin: 0 0 2rem;
  max-width: 500px;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
}

.hero-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.4rem;
  background: #6366f1;
  color: #fff;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.925rem;
  text-decoration: none;
  transition: background 0.15s, box-shadow 0.15s;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
}

.hero-cta:hover {
  background: #4f46e5;
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
  color: #fff;
}

.hero-ghost {
  color: #9ca3af;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.15s;
}

.hero-ghost:hover { color: #f9fafb; }

.hero-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.stack-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 100px;
  padding: 0.25rem 0.7rem;
  font-size: 0.75rem;
  color: #d1d5db;
}

/* ── Mockup ──────────────────────────────────────────────────────────────── */
.hero-visual { flex: 0 0 340px; }

.mockup-card {
  background: #111827;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.mockup-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: #1f2937;
}

.mockup-dots { display: flex; gap: 0.35rem; }
.mockup-dots span {
  width: 10px; height: 10px; border-radius: 50%;
  background: rgba(255,255,255,0.15);
}
.mockup-dots span:first-child { background: #ef4444; }
.mockup-dots span:nth-child(2) { background: #f59e0b; }
.mockup-dots span:nth-child(3) { background: #10b981; }

.mockup-title {
  font-size: 0.78rem;
  color: #9ca3af;
  font-weight: 500;
  flex: 1;
  text-align: center;
  margin-right: 44px;
}

.mockup-body { padding: 1rem; }

.mockup-balance {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.mockup-balance-label { font-size: 0.75rem; color: #6b7280; }

.mockup-balance-chip {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 100px;
  padding: 0.2rem 0.65rem;
  font-size: 0.72rem;
  font-weight: 600;
}

.mockup-rows { display: flex; flex-direction: column; gap: 0.75rem; }

.mockup-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.mockup-row-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}

.mockup-row-info { flex: 1; min-width: 0; }

.mockup-row-name {
  font-size: 0.72rem;
  color: #d1d5db;
  margin-bottom: 0.25rem;
}

.mockup-row-bar-wrap {
  height: 4px;
  background: rgba(255,255,255,0.08);
  border-radius: 100px;
  overflow: hidden;
}

.mockup-row-bar {
  height: 100%;
  border-radius: 100px;
  transition: width 0.6s ease;
}

.mockup-row-amt {
  font-size: 0.72rem;
  color: #9ca3af;
  font-weight: 500;
  white-space: nowrap;
}

/* ── Section common ──────────────────────────────────────────────────────── */
.section-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #6366f1;
  text-align: center;
  margin-bottom: 0.75rem;
}

.section-title {
  font-size: clamp(1.6rem, 3vw, 2.25rem);
  font-weight: 800;
  text-align: center;
  color: #f9fafb;
  margin: 0 0 3rem;
  letter-spacing: -0.01em;
}

/* ── Features ────────────────────────────────────────────────────────────── */
.features {
  padding: 5rem 0;
  background: #0d1117;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.25rem;
}

.feature-card {
  background: #111827;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  padding: 1.5rem;
  transition: border-color 0.2s, transform 0.2s;
}

.feature-card:hover {
  border-color: rgba(99,102,241,0.35);
  transform: translateY(-2px);
}

.feature-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.feature-title {
  font-size: 1rem;
  font-weight: 700;
  color: #f9fafb;
  margin: 0 0 0.5rem;
}

.feature-desc {
  font-size: 0.85rem;
  color: #9ca3af;
  line-height: 1.6;
  margin: 0 0 0.75rem;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.feature-list li {
  font-size: 0.8rem;
  color: #6b7280;
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
}

.feature-list li i {
  color: #10b981;
  font-size: 0.85rem;
  margin-top: 0.05rem;
  flex-shrink: 0;
}

/* ── AI section ──────────────────────────────────────────────────────────── */
.ai-section {
  padding: 5rem 0;
  background: #0a0f1e;
}

.ai-card {
  background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 20px;
  padding: 2.5rem 2rem;
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.ai-icon {
  font-size: 2.5rem;
  color: #818cf8;
  flex-shrink: 0;
  background: rgba(99,102,241,0.12);
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #f9fafb;
  margin: 0 0 0.75rem;
  letter-spacing: -0.01em;
}

.ai-desc {
  color: #9ca3af;
  font-size: 0.925rem;
  line-height: 1.65;
  margin: 0 0 1.25rem;
}

.ai-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.ai-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(99,102,241,0.12);
  color: #a5b4fc;
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 100px;
  padding: 0.3rem 0.75rem;
  font-size: 0.78rem;
  font-weight: 500;
}

/* ── Tech stack ──────────────────────────────────────────────────────────── */
.tech-section {
  padding: 5rem 0;
  background: #0d1117;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.tech-card {
  background: #111827;
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1.25rem 1rem;
  text-align: center;
  transition: border-color 0.2s;
}

.tech-card:hover { border-color: rgba(255,255,255,0.18); }

.tech-icon { font-size: 1.75rem; margin-bottom: 0.6rem; }

.tech-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #f9fafb;
  margin-bottom: 0.25rem;
}

.tech-role {
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.4;
}

/* ── Private section ─────────────────────────────────────────────────────── */
.private-section {
  padding: 5rem 0;
  background: #0a0f1e;
}

.private-card {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  background: #111827;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 3rem 2rem;
}

.private-icon {
  font-size: 2.5rem;
  color: #6366f1;
  margin-bottom: 1rem;
}

.private-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #f9fafb;
  margin: 0 0 1rem;
}

.private-desc {
  font-size: 0.9rem;
  color: #9ca3af;
  line-height: 1.65;
  margin: 0 0 0.75rem;
}

/* ── Footer ──────────────────────────────────────────────────────────────── */
.landing-footer {
  padding: 1.5rem 0;
  border-top: 1px solid rgba(255,255,255,0.06);
  background: #0a0f1e;
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.footer-brand {
  font-weight: 600;
  font-size: 0.875rem;
  color: #6b7280;
}

.footer-brand i { color: #6366f1; margin-right: 0.3rem; }

.footer-note {
  font-size: 0.78rem;
  color: #4b5563;
}

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    padding: 3rem 1.25rem 2.5rem;
    gap: 2rem;
  }
  .hero-visual { width: 100%; flex: none; }
  .ai-card { flex-direction: column; }
  .footer-inner { flex-direction: column; text-align: center; }
}
</style>
