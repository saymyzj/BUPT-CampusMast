<template>
  <div class="auth-page">
    <section class="intro-panel">
      <RouterLink to="/tasks" class="auth-brand">
        <span class="brand-mark"><span></span><span></span><span></span></span>
        <strong>CampusMast</strong>
      </RouterLink>

      <div class="campus-photo" aria-hidden="true">
        <div class="photo-building">
          <span class="tower"></span>
          <span class="wall"></span>
          <strong>北京邮电大学</strong>
          <small>Beijing University of Posts and Telecommunications</small>
        </div>
      </div>

      <div class="intro-copy">
        <h1>欢迎回到 CampusMast，<br />继续让校园生活更高效</h1>
        <p>登录后查看任务大厅、校园地图和消息通知，继续完成你在北邮校园内的互助任务。</p>
      </div>

      <div class="metric-row">
        <div class="metric">
          <span class="metric-icon">👥</span>
          <strong>2,400+</strong>
          <small>在校用户</small>
        </div>
        <div class="metric">
          <span class="metric-icon">✓</span>
          <strong>98.6%</strong>
          <small>好评率</small>
        </div>
        <div class="metric">
          <span class="metric-icon">▣</span>
          <strong>15,000+</strong>
          <small>完成任务</small>
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
            <i>✉</i>
            <input v-model.trim="form.studentEmail" type="email" required placeholder="xxx@bupt.edu.cn" />
          </div>
        </label>

        <label class="field">
          <span>密码</span>
          <div class="control">
            <i>▣</i>
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              required
              placeholder="请输入密码"
            />
            <button type="button" class="ghost-icon" @click="showPassword = !showPassword">⌕</button>
          </div>
        </label>

        <div class="login-options">
          <label><input type="checkbox" checked /> 记住登录状态</label>
          <RouterLink to="/register">忘记密码？</RouterLink>
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
import { useAuthStore } from "@/stores/auth";

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
    await authStore.loginUser(form);
    await router.push((route.query.redirect as string) || "/tasks");
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

.message.success {
  background: #edf5ea;
  color: #627c52;
}
</style>
