<template>
  <section class="bottom-bar" :class="{ hidden: mapStore.pickerMode }">
    <div class="bar-header">
      <div class="bar-title-row">
        <span class="bar-title">校园互助任务</span>
        <span class="bar-count">待接单 {{ pins.length }} 个</span>
      </div>
      <button class="bar-view-all" @click="router.push('/tasks')">查看全部 ›</button>
    </div>

    <div ref="scrollRef" class="bar-scroll" @wheel.prevent="onWheel">
      <div v-if="pins.length === 0" class="empty-card">
        <span class="empty-title">当前筛选下暂无任务</span>
        <span class="empty-sub">切换任务类型或前往任务大厅查看更多校内互助需求</span>
      </div>
      <button
        v-for="pin in pins"
        :key="pin.id"
        class="task-card"
        :class="{ active: pin.id === mapStore.activeTaskId }"
        @click="selectTask(pin)"
      >
        <span class="card-head">
          <span class="card-type" :style="{ color: CAT_COLORS[pin.category], background: typeBg(pin.category) }">
            <span class="card-icon">{{ CAT_ICONS[pin.category] }}</span>
            {{ CAT_LABELS[pin.category] }}
          </span>
          <span class="card-time">{{ pin.timeLeft }}</span>
        </span>
        <span class="card-title">{{ pin.title }}</span>
        <span class="card-foot">
          <span class="card-summary">{{ pin.summary }}</span>
          <span class="card-reward">{{ pin.reward }}</span>
        </span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useMapStore } from "@/stores/map";
import { CATEGORY_COLORS, CATEGORY_ICONS, CATEGORY_LABELS } from "@/types/map";
import type { CategoryType } from "@/types/map";
import type { MapTaskPin } from "@/stores/map";

interface PinWithDist extends MapTaskPin {
  distanceKm: number | null;
}

defineProps<{ pins: PinWithDist[] }>();

const router = useRouter();
const mapStore = useMapStore();
const scrollRef = ref<HTMLElement | null>(null);

const CAT_COLORS = CATEGORY_COLORS;
const CAT_ICONS = CATEGORY_ICONS;
const CAT_LABELS = CATEGORY_LABELS;

function selectTask(pin: MapTaskPin) {
  mapStore.setFocus(pin.id);
  mapStore.showTask(pin.id);
}

function onWheel(e: WheelEvent) {
  if (!scrollRef.value) return;
  scrollRef.value.scrollLeft += e.deltaY;
}

function typeBg(category: CategoryType) {
  return `${CATEGORY_COLORS[category]}18`;
}
</script>

<style scoped>
.bottom-bar.hidden {
  display: none;
}

.bottom-bar {
  position: relative;
  z-index: 10;
  height: 150px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 10px 18px 12px;
  border-top: 1px solid rgba(31, 36, 48, 0.08);
  background: #fff;
  box-shadow: 0 -8px 24px rgba(31, 36, 48, 0.05);
}

.bar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.bar-title-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.bar-title {
  color: #202633;
  font-size: 15px;
  font-weight: 900;
}

.bar-count {
  color: #9aa1ae;
  font-size: 12px;
  font-weight: 700;
}

.bar-view-all {
  border: none;
  background: transparent;
  color: #6c5ce7;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 900;
}

.bar-scroll {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 3px 0 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.bar-scroll::-webkit-scrollbar {
  display: none;
}

.task-card {
  width: 268px;
  min-width: 268px;
  height: 82px;
  display: grid;
  grid-template-rows: 20px 22px 16px;
  gap: 3px;
  padding: 8px 10px 10px;
  border: 1px solid #eceef3;
  border-radius: 12px;
  box-sizing: border-box;
  background: #fff;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.task-card:hover,
.task-card.active {
  border-color: #7c4dff;
  background: #faf8ff;
  box-shadow: 0 6px 16px rgba(108, 92, 231, 0.1);
}

.card-head,
.card-foot {
  min-width: 0;
  display: flex;
}

.card-head,
.card-foot {
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card-type {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.card-icon {
  font-size: 14px;
  line-height: 1;
}

.card-title {
  min-width: 0;
  overflow: hidden;
  color: #202633;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 22px;
  font-weight: 900;
}

.card-summary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-summary {
  flex: 1;
  color: #7b8495;
  font-size: 11px;
  line-height: 16px;
  font-weight: 700;
}

.card-reward {
  flex-shrink: 0;
  color: #ff4757;
  font-family: "Fredoka", "Noto Sans SC", sans-serif;
  font-size: 15px;
  font-weight: 900;
}

.card-time {
  flex-shrink: 0;
  padding: 2px 6px;
  border-radius: 999px;
  color: #f17b2f;
  background: #fff2e9;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.empty-card {
  width: 268px;
  min-width: 268px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: 1px dashed #d8dce5;
  border-radius: 12px;
  background: #fbfcfe;
}

.empty-title {
  color: #202633;
  font-size: 14px;
  font-weight: 900;
}

.empty-sub {
  color: #7b8495;
  font-size: 12px;
  line-height: 1.45;
}

@media (max-width: 900px) {
  .bottom-bar {
    height: 146px;
    padding: 10px 12px;
  }

  .task-card {
    width: 248px;
    min-width: 248px;
  }
}
</style>
