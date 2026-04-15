<template>
  <button class="fab font-display" title="发布任务">
    <span class="fab-icon">+</span>
    <span class="fab-label">发布任务</span>
  </button>
</template>

<style scoped>
.fab {
  position: fixed;
  left: 18px;
  bottom: 18px;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 22px;
  border: 2px solid #1f2230;
  border-radius: 999px;
  background: #f0c94a;
  color: #1f2230;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 6px 6px 0 rgba(31, 34, 48, 0.18);
  transition: all 200ms ease;
  animation: fab-float 3s ease-in-out infinite;
}

.fab:hover {
  transform: translateY(-2px);
  box-shadow: 8px 8px 0 rgba(31, 34, 48, 0.22);
}

.fab:active {
  transform: translateY(0);
  box-shadow: 4px 4px 0 rgba(31, 34, 48, 0.18);
}

.fab-icon {
  font-size: 20px;
  line-height: 1;
}

@keyframes fab-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.fab:hover {
  animation: none;
  transform: translateY(-2px);
}

@media (max-width: 1180px) {
  .fab {
    left: auto;
    right: 18px;
    bottom: 88px;
  }
}
</style>
