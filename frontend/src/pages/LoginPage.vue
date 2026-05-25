<template>
  <div class="auth-page">
    <section class="intro-panel">
      <RouterLink to="/tasks" class="auth-brand">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <strong>CampusMast</strong>
      </RouterLink>

      <div class="campus-photo" aria-hidden="true">
        <img :src="loginHeroUrl" alt="" />
        <div class="photo-caption">
          <strong>北京邮电大学</strong>
          <small>校园任务互助平台</small>
        </div>
      </div>

      <div class="intro-copy">
        <h1>欢迎回到 CampusMast，<br />继续让校园生活更高效</h1>
        <p>登录后查看任务大厅、校园地图和消息通知，继续完成你在北邮校园内的互助任务。</p>
      </div>

      <div class="metric-row">
        <div class="metric">
          <span class="metric-icon"><AppIcon name="clipboard" /></span>
          <strong>任务大厅</strong>
          <small>发现和接取校内互助任务</small>
        </div>
        <div class="metric">
          <span class="metric-icon"><AppIcon name="map-pin" /></span>
          <strong>校园地图</strong>
          <small>按地点查看附近任务</small>
        </div>
        <div class="metric">
          <span class="metric-icon"><AppIcon name="shield" /></span>
          <strong>信用体系</strong>
          <small>用真实履约记录建立信任</small>
        </div>
      </div>

      <footer>© 2026 CampusMast · 北京邮电大学</footer>
    </section>

    <section class="form-panel">
      <form class="auth-card login-card" @submit.prevent="handleLogin">
        <header>
          <h2>登录账户</h2>
          <p>使用您的 CampusMast 账户继续互助之旅</p>
        </header>

        <label class="field">
          <span>学校邮箱</span>
          <div class="control">
            <AppIcon name="message" />
            <input v-model.trim="form.studentEmail" type="text" required placeholder="Admin / user01 / xxx@bupt.edu.cn" />
          </div>
        </label>

        <label class="field">
          <span>密码</span>
          <div class="control">
            <AppIcon name="lock" />
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder="请输入密码"
            />
            <button type="button" class="ghost-icon" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">
              <AppIcon name="eye" />
            </button>
          </div>
        </label>

        <div class="login-options">
          <label><input type="checkbox" checked /> 记住登录状态</label>
        </div>

        <p v-if="logoutNotice" class="message success">{{ logoutNotice }}</p>
        <p v-if="error" class="message error">{{ error }}</p>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? "登录中..." : "登录 CampusMast" }}
        </button>

        <p class="switch-link">还没有账号？ <RouterLink to="/register">立即注册</RouterLink></p>
      </form>

      <div class="form-notes">
        <span>▤ 校内任务实时同步</span>
        <b></b>
        <span>✦ 信用体系保障互助体验</span>
      </div>
    </section>

  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useAuthStore } from "@/stores/auth";
import loginHeroUrl from "@/assets/auth/loginpage.jpg";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const showPassword = ref(false);

const form = reactive({
  studentEmail: "",
  password: "",
});

const logoutNotice = computed(() => (route.query.reason === "logout" ? "你已成功退出登录" : ""));

async function handleLogin() {
  error.value = "";
  loading.value = true;
  try {
    const user = await authStore.loginUser(form);
    await router.push(user.role === "ADMIN" ? "/admin" : "/tasks");
  } catch {
    error.value = authStore.error || "登录失败，请检查邮箱和密码";
  } finally {
    loading.value = false;
  }
}

</script>

<style scoped>
@import "./auth-shared.css";

.login-card {
  padding-top: 62px;
  padding-bottom: 44px;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 16px 0 22px;
  color: #74766f;
  font-size: 13px;
}

.login-options input {
  accent-color: #6f835f;
}

.login-options a {
  color: #6f835f;
  font-weight: 800;
  text-decoration: none;
}

.login-options button {
  border: 0;
  background: transparent;
  color: #6f835f;
  cursor: pointer;
  font: inherit;
  font-weight: 800;
}

.message.success {
  background: #edf5ea;
  color: #627c52;
}

.campus-photo {
  position: relative;
  background: #e7e4db;
}

.campus-photo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.campus-photo::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.02) 62%);
}

.photo-caption {
  position: absolute;
  left: 28px;
  bottom: 24px;
  z-index: 1;
  display: grid;
  gap: 4px;
  color: #fff;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.32);
}

.photo-caption strong {
  font-size: 24px;
  font-weight: 950;
}

.photo-caption small {
  font-size: 13px;
}

.metric strong {
  font-size: 18px;
}

.metric small {
  max-width: 170px;
  line-height: 1.45;
}

.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(31, 33, 29, 0.22);
  backdrop-filter: blur(8px);
}

.reset-dialog {
  width: min(440px, 100%);
  padding: 26px;
  border: 1px solid #e8e6df;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 70px rgba(67, 58, 45, 0.18);
}

.reset-dialog header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.reset-dialog h3 {
  margin: 0;
  font-size: 22px;
  font-weight: 950;
}

.reset-dialog header button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: #f1f1ee;
  cursor: pointer;
  font-size: 20px;
}

.reset-dialog > p {
  margin: 10px 0 18px;
  color: #74766f;
  font-size: 14px;
}

.reset-dialog .submit-btn {
  margin-top: 16px;
}
</style>
