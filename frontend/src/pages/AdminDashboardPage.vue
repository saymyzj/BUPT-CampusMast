<!--
  运营后台页面。
  运营管理的总入口，管理用户、任务和审核。
  风格：style-1-fresh-academic（校园工坊 / 纸张与印章感）
-->
<template>
  <div class="admin-page">
    <section class="page-container">
      <div class="page-header">
        <h1 class="page-title">运营后台</h1>
        <p class="page-subtitle">平台管理和数据统计</p>
      </div>
      <div class="page-card">
        <p class="placeholder-text">这里将作为后台总入口，继续拆分用户、任务、审核、配置与统计模块。</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
:root {
  --blue-500: #2556a8;
  --blue-600: #1f478c;
  --gray-600: #50493f;
  --gray-800: #202735;
  --bg-gradient-start: #fbf7ef;
  --bg-gradient-end: #efe6d6;
  --shadow-lg: 0 14px 28px rgba(23, 29, 40, 0.1);
  --radius: 16px;
}

.admin-page {
  min-height: 100vh;
  background: linear-gradient(180deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
  background-attachment: fixed;
  position: relative;
}

.admin-page::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: linear-gradient(rgba(37, 86, 168, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 86, 168, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.5;
  pointer-events: none;
}

.page-container {
  position: relative;
  z-index: 1;
  padding: 40px 20px;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--gray-800);
  font-family: 'Nunito', 'Noto Sans SC', sans-serif;
}

.page-subtitle {
  font-size: 15px;
  color: var(--gray-600);
  margin-top: 8px;
}

.page-card {
  background: #faf7f1;
  border: 1px solid rgba(31, 42, 58, 0.04);
  border-radius: var(--radius);
  padding: 32px;
  box-shadow: var(--shadow-lg);
}

.placeholder-text {
  color: var(--gray-600);
  font-size: 14px;
}
</style>
