<template>
  <div ref="root" class="app-select" :class="[`variant-${variant}`, { open, disabled }]">
    <button
      class="select-trigger"
      type="button"
      :disabled="disabled"
      :aria-expanded="open"
      @click="toggle"
      @keydown.down.prevent="openMenu"
      @keydown.esc.prevent="close"
    >
      <AppIcon v-if="icon" :name="icon" />
      <span class="select-label">{{ selectedLabel }}</span>
      <AppIcon class="select-chevron" name="chevron-down" />
    </button>

    <Transition name="select-pop">
      <div v-if="open" class="select-menu" role="listbox">
        <button
          v-for="option in options"
          :key="option.value"
          class="select-option"
          :class="{ selected: option.value === modelValue }"
          type="button"
          role="option"
          :aria-selected="option.value === modelValue"
          @click="choose(option.value)"
        >
          <span v-if="option.icon || showOptionDot" class="option-dot">
            <AppIcon v-if="option.icon" :name="option.icon" />
          </span>
          <span class="option-text">{{ option.label }}</span>
          <AppIcon v-if="option.value === modelValue" class="option-check" name="check" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import AppIcon from "@/components/ui/AppIcon.vue";

interface AppSelectOption {
  label: string;
  value: string;
  icon?: string;
}

const props = withDefaults(defineProps<{
  modelValue: string;
  options: AppSelectOption[];
  variant?: "pill" | "field";
  icon?: string;
  placeholder?: string;
  disabled?: boolean;
  showOptionDot?: boolean;
}>(), {
  variant: "field",
  icon: "",
  placeholder: "请选择",
  disabled: false,
  showOptionDot: false,
});

const emit = defineEmits<{
  "update:modelValue": [value: string];
  change: [value: string];
}>();

const root = ref<HTMLElement | null>(null);
const open = ref(false);

const selectedLabel = computed(() => {
  return props.options.find((option) => option.value === props.modelValue)?.label || props.placeholder;
});

function toggle() {
  if (props.disabled) return;
  open.value = !open.value;
}

function openMenu() {
  if (!props.disabled) open.value = true;
}

function close() {
  open.value = false;
}

function choose(value: string) {
  emit("update:modelValue", value);
  emit("change", value);
  close();
}

function handleDocumentClick(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) close();
}

onMounted(() => document.addEventListener("click", handleDocumentClick));
onBeforeUnmount(() => document.removeEventListener("click", handleDocumentClick));
</script>

<style scoped>
.app-select {
  position: relative;
  min-width: 0;
  display: inline-block;
  color: #252720;
  font-size: 13px;
}

.select-trigger {
  width: 100%;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid #e5e0d6;
  background: #fffefa;
  color: inherit;
  cursor: pointer;
  font: inherit;
  font-weight: 900;
  white-space: nowrap;
  transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.variant-field .select-trigger {
  height: 38px;
  padding: 0 12px;
  border-radius: 8px;
}

.variant-pill .select-trigger {
  height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  background: #fffefa;
}

.variant-pill.open .select-trigger,
.variant-pill .select-trigger:hover,
.variant-field.open .select-trigger,
.variant-field .select-trigger:hover {
  border-color: #b9c7ad;
  box-shadow: 0 10px 20px rgba(72, 65, 52, 0.08);
}

.select-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.select-trigger > .app-icon:not(.select-chevron) {
  flex: 0 0 auto;
  width: 17px;
  height: 17px;
  color: #6f835f;
}

.select-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-chevron {
  flex: 0 0 auto;
  width: 15px;
  height: 15px;
  color: #85887f;
  transition: transform 0.16s ease;
}

.open .select-chevron {
  transform: rotate(180deg);
}

.select-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 1200;
  box-sizing: border-box;
  width: max-content;
  min-width: 100%;
  max-width: min(320px, calc(100vw - 24px));
  max-height: min(320px, 50vh);
  padding: 6px;
  overflow: auto;
  border: 1px solid #e8e3d9;
  border-radius: 12px;
  background: #fffefa;
  box-shadow: 0 18px 44px rgba(59, 51, 40, 0.16);
}

.select-option {
  width: 100%;
  min-width: 0;
  height: 36px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #3d4039;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 850;
  text-align: left;
}

.select-option:hover {
  background: #f7f5ef;
}

.select-option.selected {
  background: #eef1e8;
  color: #526842;
}

.option-dot {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eef1e8;
  color: #6f835f;
}

.select-option.selected .option-dot {
  background: #dfe8d8;
}

.option-dot:empty::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.option-dot .app-icon {
  width: 13px;
  height: 13px;
}

.option-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.option-check {
  width: 15px;
  height: 15px;
  color: #6f835f;
}

.select-pop-enter-active,
.select-pop-leave-active {
  transition: opacity 0.14s ease, transform 0.14s ease;
}

.select-pop-enter-from,
.select-pop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
