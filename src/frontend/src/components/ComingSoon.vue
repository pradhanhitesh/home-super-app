<template>
  <div class="coming-soon">
    <div class="coming-soon-icon">
      <i class="bi bi-rocket-takeoff"></i>
    </div>
    <p class="coming-soon-title">Coming in Phase {{ phase }}</p>
    <p class="coming-soon-sub">This module is being built. Check back soon.</p>
  </div>
</template>

<script setup>
defineProps({ phase: { type: String, required: true } });
</script>

<style scoped>
.coming-soon {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #f3f4f6;
  padding: 3rem 2rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.coming-soon-icon {
  width: 56px;
  height: 56px;
  background: #eff6ff;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  font-size: 1.5rem;
  color: #0d6efd;
}

.coming-soon-title {
  font-weight: 600;
  color: #374151;
  margin: 0;
  font-size: 0.95rem;
}

.coming-soon-sub {
  color: #9ca3af;
  font-size: 0.85rem;
  margin: 0.3rem 0 0;
}
</style>
