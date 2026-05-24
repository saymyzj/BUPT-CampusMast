<template>
  <svg class="app-icon" viewBox="0 0 24 24" aria-hidden="true">
    <template v-if="name === 'search'">
      <circle cx="10.8" cy="10.8" r="6.2" />
      <path d="m16 16 4.2 4.2" />
    </template>
    <template v-else-if="name === 'zoom-in'">
      <circle cx="10.8" cy="10.8" r="6.2" />
      <path d="M10.8 8.2v5.2M8.2 10.8h5.2M16 16l4.2 4.2" />
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
    <template v-else-if="name === 'hand'">
      <path d="M7.2 12.4V7.2a1.3 1.3 0 0 1 2.6 0v4.4" />
      <path d="M9.8 11V5.4a1.3 1.3 0 0 1 2.6 0v5.4" />
      <path d="M12.4 10.8V6.4a1.3 1.3 0 0 1 2.6 0v5" />
      <path d="M15 11.4V8.2a1.3 1.3 0 0 1 2.6 0v5.5c0 4-2.3 6.5-6.2 6.5h-.8c-2.4 0-3.7-.8-5.1-2.6l-2-2.7a1.45 1.45 0 0 1 2.2-1.9l1.5 1.5" />
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
    <template v-else-if="name === 'message'">
      <path d="M5 5.5h14A1.5 1.5 0 0 1 20.5 7v8.2a1.5 1.5 0 0 1-1.5 1.5h-6.1L8 20v-3.3H5A1.5 1.5 0 0 1 3.5 15.2V7A1.5 1.5 0 0 1 5 5.5Z" />
      <path d="M7.5 9.5h9M7.5 12.5h5.8" />
    </template>
    <template v-else-if="name === 'check-circle'">
      <circle cx="12" cy="12" r="8.5" />
      <path d="m8.5 12.1 2.2 2.2 4.8-5" />
    </template>
    <template v-else-if="name === 'upload'">
      <path d="M12 16V4.5M7.5 9 12 4.5 16.5 9" />
      <path d="M5 14.5v3.2A1.8 1.8 0 0 0 6.8 19.5h10.4a1.8 1.8 0 0 0 1.8-1.8v-3.2" />
    </template>
    <template v-else-if="name === 'more'">
      <circle cx="12" cy="5.8" r="1.1" />
      <circle cx="12" cy="12" r="1.1" />
      <circle cx="12" cy="18.2" r="1.1" />
    </template>
    <template v-else-if="name === 'smile'">
      <circle cx="12" cy="12" r="8.5" />
      <path d="M8.8 10h.01M15.2 10h.01M8.8 14.3c1.8 1.7 4.6 1.7 6.4 0" />
    </template>
    <template v-else-if="name === 'star'">
      <path d="m12 4.2 2.2 4.5 5 .7-3.6 3.5.8 5-4.4-2.4-4.4 2.4.8-5-3.6-3.5 5-.7L12 4.2Z" />
    </template>
    <template v-else-if="name === 'heart'">
      <path d="M12 19.2s-6.7-4-7.9-8.3C3.4 8.2 5 6 7.5 6c1.5 0 2.8.8 3.5 2 .7-1.2 2-2 3.5-2C17 6 18.6 8.2 17.9 10.9 16.7 15.2 12 19.2 12 19.2Z" />
    </template>
    <template v-else-if="name === 'calendar'">
      <path d="M7 3.5v3M17 3.5v3" />
      <path d="M5.5 5.5h13A1.5 1.5 0 0 1 20 7v11a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18V7a1.5 1.5 0 0 1 1.5-1.5Z" />
      <path d="M4 9.5h16" />
    </template>
    <template v-else-if="name === 'wallet'">
      <path d="M4 7.5h14.5A1.5 1.5 0 0 1 20 9v8a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17V7.5Z" />
      <path d="M4 7.5 15.5 5A1.2 1.2 0 0 1 17 6.2v1.3" />
      <path d="M16 12.2h4v3.2h-4a1.6 1.6 0 1 1 0-3.2Z" />
    </template>
    <template v-else-if="name === 'alert'">
      <path d="M12 3.7 20.2 18a1.4 1.4 0 0 1-1.2 2H5a1.4 1.4 0 0 1-1.2-2L12 3.7Z" />
      <path d="M12 9v4M12 16.5h.01" />
    </template>
    <template v-else-if="name === 'save'">
      <path d="M5 4h11l3 3v13H5V4Z" />
      <path d="M8 4v6h8V4M8 20v-6h8v6" />
    </template>
    <template v-else-if="name === 'send'">
      <path d="M21 4 10 15" />
      <path d="M21 4 14 20l-4-5-6-2 17-9Z" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M3.5 12s3-5.5 8.5-5.5 8.5 5.5 8.5 5.5-3 5.5-8.5 5.5S3.5 12 3.5 12Z" />
      <circle cx="12" cy="12" r="2.4" />
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
