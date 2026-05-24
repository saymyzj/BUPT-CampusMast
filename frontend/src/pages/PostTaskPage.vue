<template>
  <div class="page-root">
    <section class="page-container">
      <div class="page-header">
        <h1 class="page-title">发布任务</h1>
        <p class="page-subtitle">填写信息，冻结赏金后任务即刻上线</p>
      </div>

      <button class="back-link" @click="$router.push('/tasks')">← 返回任务大厅</button>
      <form @submit.prevent="handleSubmit" class="post-form">
        <div class="form-group">
          <label class="form-label">任务标题 <span class="req">*</span></label>
          <input v-model="form.title" type="text" class="form-input" placeholder="例如：帮取中通快递" maxlength="100" required />
        </div>

        <div class="form-group">
          <label class="form-label">任务描述 <span class="req">*</span></label>
          <textarea v-model="form.description" class="form-input form-textarea" placeholder="详细描述需求，10-500字" maxlength="500" rows="4" required></textarea>
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label class="form-label">分类 <span class="req">*</span></label>
            <select v-model="form.category" class="form-select" required>
              <option value="">选择分类</option>
              <option value="package">📦 快递代取</option>
              <option value="food">🍔 代买餐食</option>
              <option value="move">📦 搬运重物</option>
              <option value="other">📌 其他</option>
            </select>
          </div>
          <div class="form-group flex-1">
            <label class="form-label">报酬（元）<span class="req">*</span></label>
            <input v-model="form.reward" type="number" class="form-input" placeholder="最低 1.00" min="1" step="0.01" required />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label class="form-label">截止时间 <span class="req">*</span></label>
            <input v-model="form.deadline" type="datetime-local" class="form-input" required />
          </div>
          <div class="form-group flex-1">
            <label class="form-label">楼宇 <span class="req">*</span></label>
            <div v-if="form.buildingCode" class="building-picked">
              <span class="building-picked-name">📍 {{ pickedBuildingDisplay }}</span>
              <button type="button" class="btn-reselect" @click="goPickBuilding">重新选择</button>
            </div>
            <button v-else type="button" class="btn-pick-map" @click="goPickBuilding">
              前往地图选点
            </button>
            <input type="hidden" v-model="form.buildingCode" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">详细地点</label>
          <input v-model="form.locationDetail" type="text" class="form-input" placeholder="例如：学生10号公寓门口" maxlength="200" />
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>
        <div v-if="moderationNotice" class="form-notice">{{ moderationNotice }}</div>

        <div class="balance-hint">💰 发布后将冻结赏金，当前可用余额 <strong>{{ walletBalance }} 元</strong></div>

        <button type="submit" :disabled="submitting" class="btn-submit">
          {{ submitting ? '发布中...' : '确认发布' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createTask } from "@/api/modules/task";
import { getWalletBalance } from "@/api/modules/wallet";

const route = useRoute();
const router = useRouter();
const submitting = ref(false);
const error = ref("");
const moderationNotice = ref("");
const walletBalance = ref("--");

const form = reactive({
  title: "", description: "", category: "" as string,
  reward: "", deadline: "", buildingCode: "", locationDetail: "",
});

const pickedLat = ref<number | null>(null);
const pickedLng = ref<number | null>(null);

const pickedBuildingDisplay = computed(() => {
  if (pickedLat.value != null && pickedLng.value != null) {
    return `已选点 (${pickedLat.value.toFixed(4)}, ${pickedLng.value.toFixed(4)})`;
  }
  const name = route.query.buildingName as string;
  if (name) return name;
  return form.buildingCode || "已选点";
});

const DRAFT_KEY = "campusmast.postTaskDraft";

function saveDraft() {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify({
    title: form.title, description: form.description, category: form.category,
    reward: form.reward, deadline: form.deadline, buildingCode: form.buildingCode,
    locationDetail: form.locationDetail, pickedLat: pickedLat.value, pickedLng: pickedLng.value,
  }));
}

function loadDraft() {
  const raw = sessionStorage.getItem(DRAFT_KEY);
  if (!raw) return;
  try {
    const d = JSON.parse(raw);
    form.title = d.title || "";
    form.description = d.description || "";
    form.category = d.category || "";
    form.reward = d.reward || "";
    form.deadline = d.deadline || "";
    form.buildingCode = d.buildingCode || "";
    form.locationDetail = d.locationDetail || "";
    pickedLat.value = d.pickedLat ?? null;
    pickedLng.value = d.pickedLng ?? null;
  } catch { /* ignore */ }
}

function clearDraft() {
  sessionStorage.removeItem(DRAFT_KEY);
}

function goPickBuilding() {
  saveDraft();
  router.push("/map?mode=pick-building");
}

onMounted(async () => {
  try { walletBalance.value = (await getWalletBalance()).available; } catch { /* */ }
  // Restore draft first, then query params from map picker override
  if (route.query.lat || route.query.buildingCode) {
    loadDraft();
  }
  if (route.query.lat && route.query.lng) {
    pickedLat.value = parseFloat(route.query.lat as string);
    pickedLng.value = parseFloat(route.query.lng as string);
  }
  if (route.query.buildingCode) {
    form.buildingCode = route.query.buildingCode as string;
  }
  if (!form.title && !route.query.lat && !route.query.buildingCode) {
    loadDraft();
  }
});

async function handleSubmit() {
  error.value = ""; moderationNotice.value = ""; submitting.value = true;
  try {
    const result = await createTask({
      title: form.title.trim(), description: form.description.trim(),
      category: form.category as any, reward: parseFloat(form.reward).toFixed(2),
      deadline: form.deadline ? new Date(form.deadline).toISOString() : "",
      buildingCode: form.buildingCode,
      latitude: pickedLat.value ?? undefined,
      longitude: pickedLng.value ?? undefined,
      locationDetail: form.locationDetail.trim() || undefined,
    });
    if (result.needsAdminReview) moderationNotice.value = "任务已发布，部分内容标记为待管理员复审。";
    clearDraft();
    router.push(`/tasks/${result.id}`);
  } catch (err: any) {
    const d = err?.response?.data?.error;
    error.value = d?.code === "MODERATION_BLOCKED" ? "内容命中审核规则，已被系统拦截，请修改后重新提交。" : d?.message || "发布失败";
  } finally { submitting.value = false; }
}
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --orange-500: #c67f2f; --green-500: #2f7a41;
  --gray-50: #f6f1e6; --gray-100: #ece3d2; --gray-300: #b9ad95; --gray-600: #50493f; --gray-800: #202735;
  --bg-start: #fbf7ef; --bg-end: #efe6d6;
  --shadow-sm: 0 2px 6px rgba(23,29,40,0.04); --shadow-md: 0 8px 20px rgba(23,29,40,0.07);
  --shadow-lg: 0 14px 32px rgba(23,29,40,0.10);
  --radius: 10px; --radius-lg: 16px;
  min-height: 100vh;
  background: linear-gradient(175deg, var(--bg-start) 0%, #f4efe0 50%, var(--bg-end) 100%);
  background-attachment: fixed; position: relative;
}
.page-root::before {
  content: ''; position: fixed; inset: 0; z-index: 0;
  background-image: linear-gradient(rgba(37,86,168,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37,86,168,0.06) 1px, transparent 1px);
  background-size: 32px 32px; opacity: 0.4; pointer-events: none;
}
.page-container { position: relative; z-index: 1; padding: 40px 20px; max-width: 640px; margin: 0 auto; }
.back-link { display: inline-block; margin-bottom: 20px; padding: 6px 0; font-size: 14px; color: var(--blue-500); background: none; border: none; cursor: pointer; font-weight: 500; transition: color 0.2s; }
.back-link:hover { color: var(--blue-600); }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 32px; font-weight: 700; color: var(--gray-800); font-family: 'Nunito','Noto Sans SC',sans-serif; }
.page-subtitle { font-size: 15px; color: var(--gray-600); margin-top: 6px; }
.post-form {
  background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg);
  padding: 36px; box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column; gap: 18px;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--gray-800); }
.req { color: var(--red-500); }
.form-row { display: flex; gap: 16px; }
.flex-1 { flex: 1; }
.form-input, .form-select {
  padding: 10px 14px; font-size: 14px; border: 1px solid var(--gray-100);
  border-radius: var(--radius); background: #fff; color: var(--gray-800);
  transition: border 0.2s; font-family: inherit;
}
.form-select { appearance: none; -webkit-appearance: none; padding-right: 36px; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2350493f' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; cursor: pointer; }
.form-input:focus, .form-select:focus { outline: none; border-color: var(--blue-500); box-shadow: 0 0 0 3px rgba(37,86,168,0.08); }
.form-textarea { resize: vertical; }
.form-error { padding: 10px 14px; font-size: 13px; background: #ffebee; color: var(--red-500); border-radius: var(--radius); }
.form-notice { padding: 10px 14px; font-size: 13px; background: #fff7e6; color: var(--orange-500); border-radius: var(--radius); }
.balance-hint { font-size: 13px; color: var(--gray-600); padding: 10px 14px; background: var(--blue-50); border-radius: var(--radius); }
.btn-pick-map {
  width: 100%; padding: 12px 16px;
  font-size: 14px; font-weight: 600; color: #2556a8;
  background: #edf3fb; border: 2px dashed #2556a8;
  border-radius: var(--radius); cursor: pointer;
  transition: all 0.25s; font-family: inherit;
}
.btn-pick-map:hover { background: #d5e3f6; border-style: solid; }
.building-picked {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; padding: 10px 14px;
  background: #edf3ee; border: 1px solid #d4e3d5; border-radius: var(--radius);
}
.building-picked-name { font-size: 14px; font-weight: 600; color: #202735; }
.btn-reselect {
  padding: 6px 14px; font-size: 12px; font-weight: 600; color: #2556a8;
  background: transparent; border: 1px solid #2556a8; border-radius: 8px;
  cursor: pointer; transition: all 0.2s; font-family: inherit; white-space: nowrap;
}
.btn-reselect:hover { background: #edf3fb; }
.btn-submit {
  padding: 14px; font-size: 15px; font-weight: 600; background: var(--blue-500); color: #fff;
  border: none; border-radius: var(--radius); cursor: pointer; transition: all 0.25s;
}
.btn-submit:hover:not(:disabled) { background: var(--blue-600); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(37,86,168,0.25); }
.btn-submit:disabled { background: var(--gray-300); cursor: not-allowed; }
@media (max-width: 480px) { .form-row { flex-direction: column; } .post-form { padding: 24px; } }
</style>