<!--
  文件说明：
  这是前端应用的根组件。
  当前只负责承载全局布局组件与路由出口，A 同学后续应在 AppShell 中继续填充
  顶部导航、侧栏、未读消息角标等框架级元素。
-->
<template>
  <AppShell>
    <RouterView />
  </AppShell>
</template>

<script setup lang="ts">
/**
 * 根组件仅负责组装应用外壳，不直接承载业务逻辑。
 */
import { RouterView } from "vue-router";
import AppShell from "@/components/AppShell.vue";
</script>

