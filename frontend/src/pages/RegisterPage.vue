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
        <h1>加入 CampusMast，<br />让校园生活更高效、更有温度</h1>
        <p>在北邮校园内，发布或接受代取快递、代买餐食等任务，通过安全托管与信用体系保障每一次互助体验。</p>
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
      <form class="auth-card" @submit.prevent="handleRegister">
        <header>
          <h2>注册账户</h2>
          <p>创建您的 CampusMast 账户，开启互助之旅</p>
        </header>

        <label class="field">
          <span>学校邮箱</span>
          <div class="control">
            <i>✉</i>
            <input v-model.trim="form.studentEmail" type="email" required placeholder="xxx@bupt.edu.cn" />
          </div>
        </label>

        <label class="field">
          <span>昵称</span>
          <div class="control">
            <i>♙</i>
            <input v-model.trim="form.nickname" type="text" required maxlength="30" placeholder="请输入昵称" />
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
              minlength="6"
              placeholder="至少 6 位，包含字母和数字"
            />
            <button type="button" class="ghost-icon" @click="showPassword = !showPassword">⌕</button>
          </div>
        </label>

        <label class="field">
          <span>确认密码</span>
          <div class="control">
            <i>▣</i>
            <input
              v-model="confirmPassword"
              :type="showConfirm ? 'text' : 'password'"
              required
              minlength="6"
              placeholder="请再次输入密码"
            />
            <button type="button" class="ghost-icon" @click="showConfirm = !showConfirm">⌕</button>
          </div>
        </label>

        <label class="field">
          <span>验证码</span>
          <div class="verify-row">
            <div class="control">
              <i>◇</i>
              <input v-model.trim="verificationCode" type="text" placeholder="请输入验证码" />
            </div>
            <button type="button" class="verify-btn">发送验证码</button>
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
        <span>▤ 注册成功后将自动为您创建校园钱包</span>
        <b></b>
        <span>✦ 初始信用分为 600 分</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const loading = ref(false);
const error = ref("");
const showPassword = ref(false);
const showConfirm = ref(false);
const confirmPassword = ref("");
const verificationCode = ref("");
const agreed = ref(true);

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
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.02fr 1fr;
  background: linear-gradient(90deg, #fbfaf7 0%, #fbfaf7 49.8%, #f4f2ee 49.8%, #f7f6f3 100%);
  color: #2b2d29;
  font-family: "Inter", "Noto Sans SC", "Microsoft YaHei", sans-serif;
}

.intro-panel,
.form-panel {
  position: relative;
  min-height: 100vh;
  padding: 34px 66px;
}

.intro-panel {
  display: flex;
  flex-direction: column;
}

.auth-brand {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  color: inherit;
  text-decoration: none;
}

.auth-brand strong {
  font-size: 26px;
  font-weight: 900;
}

.brand-mark {
  position: relative;
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(145deg, #718563, #536d49);
}

.brand-mark span {
  position: absolute;
  width: 20px;
  height: 11px;
  border: 2px solid #fff;
  border-top: 0;
  border-radius: 2px;
  transform: rotate(30deg) skewX(-18deg);
}

.brand-mark span:nth-child(1) { margin-top: -10px; opacity: 0.92; }
.brand-mark span:nth-child(2) { opacity: 0.84; }
.brand-mark span:nth-child(3) { margin-top: 10px; opacity: 0.76; }

.campus-photo {
  height: 300px;
  margin-top: 48px;
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(circle at 10% 80%, rgba(91, 124, 67, 0.48), transparent 28%),
    linear-gradient(90deg, rgba(250, 253, 255, 0.94), rgba(250, 253, 255, 0.25) 42%, rgba(155, 111, 82, 0.18) 43%),
    linear-gradient(15deg, #ced8df 0 38%, #d9c4ac 38% 100%);
  box-shadow: 0 22px 50px rgba(64, 54, 41, 0.12);
}

.photo-building {
  position: relative;
  height: 100%;
}

.tower {
  position: absolute;
  left: 255px;
  top: 44px;
  width: 66px;
  height: 142px;
  border-radius: 40px 40px 2px 2px;
  background: linear-gradient(#f6f3ed, #cbd1d2);
  box-shadow: inset 0 0 0 8px rgba(255, 255, 255, 0.32);
}

.wall {
  position: absolute;
  left: 240px;
  right: 0;
  bottom: 0;
  height: 210px;
  background:
    radial-gradient(circle at 78% 32%, rgba(255, 255, 255, 0.42) 0 42px, transparent 43px),
    linear-gradient(90deg, #efeee8 0 42%, #8c6048 42% 100%);
}

.photo-building strong,
.photo-building small {
  position: absolute;
  left: 310px;
  z-index: 2;
  color: #1f211e;
}

.photo-building strong {
  top: 155px;
  font-size: 25px;
  letter-spacing: 3px;
}

.photo-building small {
  top: 190px;
  font-size: 8px;
  letter-spacing: 0.2px;
}

.intro-copy {
  margin-top: 42px;
}

.intro-copy h1 {
  margin: 0;
  font-size: 39px;
  line-height: 1.48;
  letter-spacing: 0;
  font-weight: 900;
}

.intro-copy p {
  max-width: 760px;
  margin: 16px 0 0;
  color: #60625e;
  font-size: 18px;
  line-height: 1.75;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 64px;
  margin-top: 52px;
  max-width: 700px;
}

.metric {
  display: grid;
  grid-template-columns: 66px 1fr;
  column-gap: 18px;
  align-items: center;
}

.metric-icon {
  grid-row: span 2;
  width: 66px;
  height: 66px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: #f1f1ee;
  color: #6f835f;
  font-size: 26px;
}

.metric strong {
  color: #6f835f;
  font-size: 24px;
  line-height: 1.1;
}

.metric small {
  color: #5f625b;
  font-size: 15px;
}

.intro-panel footer {
  margin-top: auto;
  color: #9b9d99;
  font-size: 14px;
}

.form-panel {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 32px;
}

.auth-card {
  width: min(560px, 100%);
  padding: 54px 46px 38px;
  border: 1px solid #e8e6df;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 22px 62px rgba(67, 58, 45, 0.12);
  backdrop-filter: blur(18px);
}

.auth-card header h2 {
  margin: 0;
  font-size: 31px;
  font-weight: 900;
}

.auth-card header p {
  margin: 10px 0 26px;
  color: #9a9c98;
  font-size: 15px;
}

.field {
  display: grid;
  gap: 9px;
  margin-top: 17px;
}

.field > span {
  font-size: 14px;
  font-weight: 800;
}

.control {
  height: 52px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  border: 1px solid #e5e3dc;
  border-radius: 9px;
  background: #f8f8f6;
}

.control i {
  color: #9c9f9a;
  font-style: normal;
}

.control input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: #2c2d29;
  font: inherit;
}

.ghost-icon {
  border: 0;
  background: transparent;
  color: #9c9f9a;
  cursor: pointer;
}

.verify-row {
  display: grid;
  grid-template-columns: 1fr 124px;
  gap: 14px;
}

.verify-btn {
  border: 1px solid #ccd4c4;
  border-radius: 9px;
  background: #fff;
  color: #778867;
  cursor: pointer;
  font-weight: 800;
}

.agree {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px 0 20px;
  color: #74766f;
  font-size: 13px;
}

.agree input {
  accent-color: #6f835f;
}

.message {
  margin: 0 0 14px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.message.error {
  background: #fff0ee;
  color: #b24a3a;
}

.submit-btn {
  width: 100%;
  height: 54px;
  border: 0;
  border-radius: 9px;
  background: linear-gradient(90deg, #788e67, #657b55);
  color: #fff;
  cursor: pointer;
  font-size: 17px;
  font-weight: 900;
  box-shadow: 0 9px 18px rgba(82, 108, 71, 0.22);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.switch-link {
  margin: 24px 0 0;
  text-align: center;
  color: #8d8f89;
  font-size: 15px;
}

.switch-link a {
  color: #6f835f;
  font-weight: 900;
  text-decoration: none;
}

.form-notes {
  display: flex;
  align-items: center;
  gap: 26px;
  color: #7d8e70;
  font-size: 14px;
}

.form-notes b {
  width: 1px;
  height: 14px;
  background: #a8a99f;
}

@media (max-width: 980px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .intro-panel,
  .form-panel {
    min-height: auto;
    padding: 28px;
  }

  .intro-panel footer {
    margin-top: 40px;
  }
}
</style>
