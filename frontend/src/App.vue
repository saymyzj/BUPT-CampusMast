<template>
  <AppShell v-if="!isMapLayout">
    <RouterView />
  </AppShell>
  <RouterView v-else />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterView, useRoute } from "vue-router";
import AppShell from "@/components/AppShell.vue";

const route = useRoute();
const isMapLayout = computed(() => route.meta.layout === "map");
</script>
