<template>
  <svg class="app-icon" viewBox="0 0 24 24" aria-hidden="true">
    <template v-if="name === 'search'">
      <circle cx="10.8" cy="10.8" r="6.2" />
      <path d="m16 16 4.2 4.2" />
    </template>
    <template v-else-if="name === 'plus'">
      <path d="M12 5v14M5 12h14" />
    </template>
    <template v-else-if="name === 'map-pin'">
      <path d="M12 21s6-5.1 6-11a6 6 0 0 0-12 0c0 5.9 6 11 6 11Z" />
      <circle cx="12" cy="10" r="2.2" />
    </template>
    <template v-else-if="name === 'location'">
      <path d="M12 3.5 5 20.5l7-3.2 7 3.2L12 3.5Z" />
    </template>
    <template v-else-if="name === 'arrow-right'">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </template>
    <template v-else-if="name === 'package'">
      <path d="M5 8.4 12 4l7 4.4v7.2L12 20l-7-4.4V8.4Z" />
      <path d="m5.4 8.6 6.6 4 6.6-4M12 12.6V20" />
    </template>
    <template v-else-if="name === 'food'">
      <path d="M6 4v7M9 4v7M6 8.5h3M7.5 11v9" />
      <path d="M16 4c1.8 1.6 2.6 3.6 2.2 5.9-.3 1.8-1.3 3-2.7 3.6V20" />
    </template>
    <template v-else-if="name === 'move'">
      <path d="M4 12h15M14 7l5 5-5 5" />
      <path d="M9 6H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h4" />
    </template>
    <template v-else-if="name === 'other'">
      <path d="M12 3.8 14.2 9l5.5.5-4.2 3.6 1.3 5.4L12 15.6l-4.8 2.9 1.3-5.4-4.2-3.6 5.5-.5L12 3.8Z" />
    </template>
    <template v-else-if="name === 'spark'">
      <path d="M12 3.5 13.8 9l5.7 1.8-5.7 1.8L12 18.5l-1.8-5.9-5.7-1.8L10.2 9 12 3.5Z" />
      <path d="M19 4v4M17 6h4M5 16v3M3.5 17.5h3" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M12 3.5 18.5 6v5.2c0 4.1-2.6 7.8-6.5 9.3-3.9-1.5-6.5-5.2-6.5-9.3V6L12 3.5Z" />
      <path d="m9.2 12 1.8 1.8 3.9-4.1" />
    </template>
    <template v-else-if="name === 'bell'">
      <path d="M18 10.8c0-3.3-2.1-5.8-5.1-6.4V3a.9.9 0 0 0-1.8 0v1.4C8.1 5 6 7.5 6 10.8v3.4l-1.5 2.4h15l-1.5-2.4v-3.4Z" />
      <path d="M9.7 18.4a2.4 2.4 0 0 0 4.6 0" />
    </template>
    <template v-else-if="name === 'star'">
      <path d="m12 4.2 2.2 4.5 5 .7-3.6 3.5.8 5-4.4-2.4-4.4 2.4.8-5-3.6-3.5 5-.7L12 4.2Z" />
    </template>
    <template v-else-if="name === 'heart'">
      <path d="M12 19.2s-6.7-4-7.9-8.3C3.4 8.2 5 6 7.5 6c1.5 0 2.8.8 3.5 2 .7-1.2 2-2 3.5-2C17 6 18.6 8.2 17.9 10.9 16.7 15.2 12 19.2 12 19.2Z" />
    </template>
  </svg>
</template>

<script setup lang="ts">
defineProps<{ name: string }>();
</script>

<style scoped>
.app-icon {
  width: 1em;
  height: 1em;
  display: block;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
