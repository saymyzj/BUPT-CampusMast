<template>
  <div class="fab-section">
    <button class="fab-btn font-display" title="发布任务">
      <span class="fab-plus">+</span>
      <span>发布任务</span>
    </button>
  </div>
</template>

<style scoped>
.fab-section {
  padding: 12px 16px 16px;
  border-top: 1px solid rgba(31, 42, 58, 0.06);
}

.fab-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 13px;
  border: 2px solid #1f2230;
  border-radius: 14px;
  background: #f0c94a;
  color: #1f2230;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 4px 4px 0 rgba(31, 34, 48, 0.12);
  transition: all 200ms cubic-bezier(0.22, 1, 0.36, 1);
}

.fab-btn:hover {
  transform: translateY(-2px);
  box-shadow: 6px 6px 0 rgba(31, 34, 48, 0.16);
}

.fab-btn:active {
  transform: translateY(0);
  box-shadow: 2px 2px 0 rgba(31, 34, 48, 0.12);
}

.fab-plus {
  font-size: 18px;
  line-height: 1;
}
</style>
