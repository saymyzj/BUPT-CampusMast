<template>
  <div class="public-profile-page">
    <section class="profile-shell">
      <button class="back-link" type="button" @click="router.back()">
        <AppIcon name="arrow-right" />
        返回上一页
      </button>

      <div v-if="loading" class="state-card">个人资料加载中...</div>
      <div v-else-if="loadError" class="state-card error">{{ loadError }}</div>

      <template v-else-if="profile">
        <section class="hero-card">
          <div class="avatar-wrap">
            <img v-if="profile.avatarUrl" :src="profile.avatarUrl" alt="" />
            <span v-else>{{ initial }}</span>
          </div>

          <div class="hero-copy">
            <span class="role-pill">{{ roleLabel }}</span>
            <h1>{{ profile.nickname }}</h1>
            <p>北邮校园互助平台用户</p>
          </div>

          <div class="credit-badge">
            <small>综合信用分</small>
            <strong>{{ profile.overallCreditScore }}</strong>
          </div>
        </section>

        <section class="metric-grid">
          <article class="metric-card">
            <span><AppIcon name="shield" /></span>
            <small>综合信用分</small>
            <strong>{{ profile.overallCreditScore }}</strong>
          </article>
          <article class="metric-card">
            <span><AppIcon name="clipboard" /></span>
            <small>发布侧信用</small>
            <strong>{{ profile.requesterCreditScore }}</strong>
          </article>
          <article class="metric-card">
            <span><AppIcon name="users" /></span>
            <small>接单侧信用</small>
            <strong>{{ profile.helperCreditScore }}</strong>
          </article>
        </section>

        <section class="info-grid">
          <article class="info-card">
            <h2>公开资料</h2>
            <div>
              <span>昵称</span>
              <strong>{{ profile.nickname }}</strong>
            </div>
            <div>
              <span>身份</span>
              <strong>{{ roleLabel }}</strong>
            </div>
            <div>
              <span>绑定手机</span>
              <strong>{{ profile.phone || "未绑定" }}</strong>
            </div>
          </article>

          <article class="info-card">
            <h2>信用说明</h2>
            <p>信用分来自平台当前真实用户数据，发布任务和接取任务两侧分别统计，综合分用于页面统一展示。</p>
          </article>
        </section>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getUserPublicProfile } from "@/api/modules/auth";
import AppIcon from "@/components/ui/AppIcon.vue";
import type { UserPublicProfile } from "@/types/api";

const route = useRoute();
const router = useRouter();
const profile = ref<UserPublicProfile | null>(null);
const loading = ref(false);
const loadError = ref("");

const initial = computed(() => profile.value?.nickname?.slice(0, 1) || "用");
const roleLabel = computed(() => (profile.value?.role === "ADMIN" ? "管理员" : "普通用户"));

async function loadProfile() {
  const id = String(route.params.id || "");
  if (!id) return;
  loading.value = true;
  loadError.value = "";
  try {
    profile.value = await getUserPublicProfile(id);
  } catch (err: any) {
    profile.value = null;
    loadError.value = err?.response?.data?.error?.message || "个人资料加载失败";
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.id, loadProfile);
onMounted(loadProfile);
</script>

<style scoped>
.public-profile-page {
  min-height: calc(100dvh - 86px);
  padding: clamp(18px, 2.4vw, 30px);
  background: #f7f5ef;
  color: #252720;
}

.profile-shell {
  width: min(100%, 1120px);
  margin: 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  border: 0;
  background: transparent;
  color: #6f835f;
  cursor: pointer;
  font-size: 14px;
  font-weight: 850;
}

.back-link .app-icon {
  transform: rotate(180deg);
}

.state-card,
.hero-card,
.metric-card,
.info-card {
  border: 1px solid #ebe7df;
  border-radius: 12px;
  background: rgba(255, 254, 251, 0.94);
  box-shadow: 0 16px 38px rgba(60, 52, 42, 0.06);
}

.state-card {
  display: grid;
  place-items: center;
  min-height: 240px;
  color: #7e8178;
}

.state-card.error {
  color: #b8544a;
}

.hero-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: clamp(16px, 2.5vw, 28px);
  padding: clamp(22px, 3vw, 34px);
}

.avatar-wrap {
  width: clamp(76px, 8vw, 104px);
  aspect-ratio: 1;
  display: grid;
  place-items: center;
  overflow: hidden;
  border-radius: 28px;
  background: linear-gradient(145deg, #768a66, #c4c8a9);
  color: #fff;
  font-size: clamp(30px, 4vw, 46px);
  font-weight: 950;
}

.avatar-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-copy {
  min-width: 0;
}

.role-pill {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: #eef1e8;
  color: #6f835f;
  font-size: 12px;
  font-weight: 900;
}

.hero-copy h1 {
  margin: 12px 0 6px;
  overflow: hidden;
  color: #191b17;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 950;
}

.hero-copy p {
  margin: 0;
  color: #7e8178;
}

.credit-badge {
  min-width: 132px;
  padding: 18px;
  border-radius: 12px;
  background: linear-gradient(145deg, #eef1e8, #fffaf1);
  text-align: center;
}

.credit-badge small {
  display: block;
  color: #7e8178;
  font-size: 12px;
  font-weight: 800;
}

.credit-badge strong {
  display: block;
  margin-top: 4px;
  color: #6f835f;
  font-size: 34px;
  font-weight: 950;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.metric-card {
  min-width: 0;
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  gap: 6px 12px;
  padding: 18px;
}

.metric-card span {
  grid-row: span 2;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: #eef1e8;
  color: #6f835f;
  font-size: 22px;
}

.metric-card small {
  color: #7e8178;
  font-weight: 800;
}

.metric-card strong {
  min-width: 0;
  overflow: hidden;
  color: #252720;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 26px;
  font-weight: 950;
}

.info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.7fr);
  gap: 16px;
  margin-top: 16px;
}

.info-card {
  min-width: 0;
  padding: 20px;
}

.info-card h2 {
  margin: 0 0 14px;
  font-size: 18px;
  font-weight: 950;
}

.info-card div {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid #eee9df;
}

.info-card span {
  color: #7e8178;
}

.info-card strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.info-card p {
  margin: 0;
  color: #5f635a;
  line-height: 1.8;
}

@media (max-width: 760px) {
  .hero-card,
  .info-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .credit-badge {
    text-align: left;
  }
}
</style>
