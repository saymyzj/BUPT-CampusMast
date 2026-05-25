<template>
  <AppShell v-if="usesShellLayout">
    <RouterView />
  </AppShell>
  <RouterView v-else />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import AppShell from "@/components/AppShell.vue";

const route = useRoute();
const usesShellLayout = computed(() => !["auth", "admin"].includes(String(route.meta.layout || "")));
</script>
