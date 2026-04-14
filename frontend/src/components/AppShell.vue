<!--
  文件说明：
  这是应用的全局外壳组件。
  负责承载导航、主内容容器和基础布局；A 同学后续可以在这里继续放入用户信息、
  未读角标、全局搜索入口和后台入口。
-->
<template>
  <div class="min-h-screen">
    <header class="border-b border-slate-200 bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div>
          <h1 class="text-xl font-bold text-campus-900">CampusMast</h1>
          <p class="text-sm text-slate-500">校园互助与众包任务平台</p>
        </div>
        <nav class="flex gap-3 text-sm">
          <RouterLink class="btn btn-ghost btn-sm" to="/tasks">任务大厅</RouterLink>
          <RouterLink class="btn btn-ghost btn-sm" to="/map">校园地图</RouterLink>
          <RouterLink class="btn btn-ghost btn-sm" to="/chat">任务聊天</RouterLink>
          <RouterLink class="btn btn-ghost btn-sm" to="/admin">运营后台</RouterLink>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-6 py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
/**
 * 应用外壳本身不放业务状态，保持纯布局职责。
 */
import { RouterLink } from "vue-router";
</script>
