<template>
  <div class="page-root">
    <section class="page-container">
      <div class="page-header">
        <h1 class="page-title">个人中心</h1>
        <p class="page-subtitle">管理个人资料与查看信用分</p>
      </div>

      <div v-if="!authStore.currentUser" class="state-box">请先登录</div>
      <template v-else>
        <div class="credit-row">
          <div class="credit-card">
            <p class="credit-label">需求方信用</p>
            <p class="credit-value">{{ user.requesterCreditScore }}</p>
          </div>
          <div class="credit-card">
            <p class="credit-label">接单方信用</p>
            <p class="credit-value">{{ user.helperCreditScore }}</p>
          </div>
          <div class="credit-card credit-card-main">
            <p class="credit-label">综合信用</p>
            <p class="credit-value">{{ user.overallCreditScore }}</p>
          </div>
        </div>

        <div class="edit-card">
          <h3 class="section-title">编辑资料</h3>
          <form @submit.prevent="handleSave" class="edit-form">
            <div class="form-group">
              <label class="form-label">邮箱</label>
              <input type="email" class="form-input" :value="user.studentEmail" disabled />
            </div>
            <div class="form-group">
              <label class="form-label">昵称</label>
              <input v-model="edit.nickname" type="text" class="form-input" maxlength="50" />
            </div>
            <div class="form-group">
              <label class="form-label">手机号</label>
              <input v-model="edit.phone" type="text" class="form-input" placeholder="选填" />
            </div>
            <div class="form-group">
              <label class="form-label">常用楼宇</label>
              <select v-model="edit.defaultBuildingCode" class="form-select">
                <option value="">未设置</option>
                <option v-for="b in buildings" :key="b.code" :value="b.code">{{ b.name }}</option>
              </select>
            </div>
            <div v-if="saveError" class="form-error">{{ saveError }}</div>
            <div v-if="saveOk" class="form-success">{{ saveOk }}</div>
            <button type="submit" :disabled="saving" class="btn btn-primary">{{ saving ? '保存中...' : '保存' }}</button>
          </form>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { listCampusBuildings } from "@/api/modules/map";
import type { CampusBuilding } from "@/types/api";

const authStore = useAuthStore();
const user = computed(() => authStore.currentUser!);
const buildings = ref<CampusBuilding[]>([]);
const saving = ref(false); const saveError = ref(""); const saveOk = ref("");

const edit = reactive({ nickname: "", phone: "", defaultBuildingCode: "" });

onMounted(async () => {
  const u = authStore.currentUser;
  if (u) { edit.nickname = u.nickname || ""; edit.defaultBuildingCode = u.defaultBuildingCode || ""; }
  try { buildings.value = await listCampusBuildings(); } catch { /* */ }
});

async function handleSave() {
  saveError.value = ""; saveOk.value = ""; saving.value = true;
  try {
    await authStore.updateCurrentUserProfile({
      nickname: edit.nickname.trim() || undefined,
      phone: edit.phone.trim() || undefined,
      defaultBuildingCode: edit.defaultBuildingCode || undefined,
    } as any);
    saveOk.value = "保存成功";
  } catch (err: any) { saveError.value = err?.response?.data?.error?.message || "保存失败"; } finally { saving.value = false; }
}
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --green-500: #2f7a41;
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
.page-header { margin-bottom: 28px; }
.page-title { font-size: 32px; font-weight: 700; color: var(--gray-800); font-family: 'Nunito','Noto Sans SC',sans-serif; }
.page-subtitle { font-size: 15px; color: var(--gray-600); margin-top: 6px; }
.state-box { text-align: center; padding: 80px 20px; color: var(--gray-600); font-size: 15px; }

.credit-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px; }
@media (max-width: 480px) { .credit-row { grid-template-columns: 1fr; } }
.credit-card { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-sm); text-align: center; }
.credit-card-main { background: var(--blue-50); border-color: rgba(37,86,168,0.12); }
.credit-label { font-size: 13px; color: var(--gray-600); margin-bottom: 8px; }
.credit-value { font-size: 36px; font-weight: 700; color: var(--blue-500); font-family: 'Nunito',sans-serif; }
.credit-card-main .credit-value { color: var(--blue-600); }

.edit-card { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 32px; box-shadow: var(--shadow-lg); }
.section-title { font-size: 16px; font-weight: 600; color: var(--gray-800); margin-bottom: 20px; }
.edit-form { display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 13px; font-weight: 600; color: var(--gray-800); }
.form-input, .form-select { padding: 10px 14px; font-size: 14px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; color: var(--gray-800); transition: border 0.2s; }
.form-select { appearance: none; -webkit-appearance: none; padding-right: 36px; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2350493f' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; cursor: pointer; }
.form-input:focus, .form-select:focus { outline: none; border-color: var(--blue-500); box-shadow: 0 0 0 3px rgba(37,86,168,0.08); }
.form-input:disabled { background: var(--gray-50); color: var(--gray-600); }
.form-error { padding: 10px 14px; font-size: 13px; background: #ffebee; color: var(--red-500); border-radius: var(--radius); }
.form-success { padding: 10px 14px; font-size: 13px; background: #edf8ee; color: var(--green-500); border-radius: var(--radius); border: 1px solid rgba(47,122,65,0.2); }
.btn { padding: 12px 24px; font-size: 14px; font-weight: 600; border-radius: var(--radius); cursor: pointer; border: none; transition: all 0.25s; }
.btn-primary { background: var(--blue-500); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--blue-600); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(37,86,168,0.25); }
.btn-primary:disabled { background: var(--gray-300); cursor: not-allowed; }
</style>
