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
        <h1>加入 CampusMast，<br />让校园生活更高效、更有温度</h1>
        <p>发布或领取校内互助任务，通过资金托管与信用体系保障每一次互助体验。</p>
      </div>

      <div class="metric-row">
        <div class="metric">
          <span class="metric-icon"><AppIcon name="wallet" /></span>
          <strong>校园钱包</strong>
          <small>注册后自动创建余额账户</small>
        </div>
        <div class="metric">
          <span class="metric-icon"><AppIcon name="shield" /></span>
          <strong>信用起步</strong>
          <small>初始信用分为 {{ initialCreditScore }} 分</small>
        </div>
        <div class="metric">
          <span class="metric-icon"><AppIcon name="bell" /></span>
          <strong>实时通知</strong>
          <small>任务进展及时同步</small>
        </div>
      </div>

      <footer>© 2026 CampusMast · 北京邮电大学</footer>
    </section>

    <section class="form-panel">
      <form class="auth-card register-card" @submit.prevent="handleRegister">
        <header>
          <h2>注册账户</h2>
          <p>创建您的 CampusMast 账户，开启校园互助之旅</p>
        </header>

        <label class="field">
          <span>学校邮箱</span>
          <div class="control">
            <AppIcon name="message" />
            <input v-model.trim="form.studentEmail" type="email" required placeholder="xxx@bupt.edu.cn" />
          </div>
        </label>

        <label class="field">
          <span>昵称</span>
          <div class="control">
            <AppIcon name="user" />
            <input v-model.trim="form.nickname" type="text" required maxlength="30" placeholder="请输入昵称" />
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
              minlength="6"
              placeholder="至少 6 位"
            />
            <button type="button" class="ghost-icon" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">
              <AppIcon name="eye" />
            </button>
          </div>
        </label>

        <label class="field">
          <span>确认密码</span>
          <div class="control">
            <AppIcon name="lock" />
            <input
              v-model="confirmPassword"
              :type="showConfirm ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="请再次输入密码"
            />
            <button type="button" class="ghost-icon" :aria-label="showConfirm ? '隐藏密码' : '显示密码'" @click="showConfirm = !showConfirm">
              <AppIcon name="eye" />
            </button>
          </div>
        </label>

        <label class="agree">
          <input v-model="agreed" type="checkbox" />
          <span>我已阅读并同意《用户协议》和《隐私政策》</span>
        </label>

        <p v-if="error" class="message error">{{ error }}</p>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? "注册中..." : "注册并创建账户" }}
        </button>

        <p class="switch-link">已有账号？ <RouterLink to="/login">立即登录</RouterLink></p>
      </form>

      <div class="form-notes">
        <span><AppIcon name="wallet" /> 注册成功后将自动为您创建校园钱包</span>
        <b></b>
        <span><AppIcon name="shield" /> 初始信用分为 {{ initialCreditScore }} 分</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import AppIcon from "@/components/ui/AppIcon.vue";
import { useAuthStore } from "@/stores/auth";
import loginHeroUrl from "../../ui-static/assets/loginpage.jpg";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const showPassword = ref(false);
const showConfirm = ref(false);
const confirmPassword = ref("");
const agreed = ref(true);
const initialCreditScore = 100;

const form = reactive({
  nickname: "",
  studentEmail: "",
  password: "",
});

async function handleRegister() {
  error.value = "";
  if (form.password !== confirmPassword.value) {
    error.value = "两次输入的密码不一致";
    return;
  }
  if (!agreed.value) {
    error.value = "请先同意用户协议和隐私政策";
    return;
  }

  loading.value = true;
  try {
    await authStore.registerUser(form);
    await router.push("/tasks");
  } catch {
    error.value = authStore.error || "注册失败，请检查输入信息";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
@import "./auth-shared.css";

.register-card {
  padding-top: 44px;
}

.metric strong {
  font-size: 19px;
}

.metric small {
  font-size: 13px;
  line-height: 1.45;
}
</style>
