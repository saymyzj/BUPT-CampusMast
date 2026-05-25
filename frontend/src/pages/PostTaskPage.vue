<template>
  <div class="post-page">
    <section class="post-layout">
      <main class="form-card">
        <header class="page-head">
          <h1>发布任务</h1>
          <p>填写任务信息，AI 审核通过后将发布到任务大厅</p>
        </header>

        <form class="post-form" @submit.prevent="handleSubmit">
          <label class="field title-field">
            <span><b>*</b> 标题</span>
            <div class="control with-count">
              <input
                v-model.trim="form.title"
                type="text"
                maxlength="30"
                placeholder="请简明扼要描述任务，如：代取快递、帮忙取餐等（不超过 30 字）"
                required
              />
              <small>{{ form.title.length }}/30</small>
            </div>
          </label>

          <label class="field desc-field">
            <span><b>*</b> 任务描述</span>
            <div class="control with-count">
              <textarea
                v-model.trim="form.description"
                maxlength="300"
                rows="4"
                placeholder="请详细描述任务内容、注意事项、期望完成方式等，便于获得更好帮助（不超过 300 字）"
                required
              ></textarea>
              <small>{{ form.description.length }}/300</small>
            </div>
          </label>

          <div class="field category-field">
            <span><b>*</b> 分类</span>
            <div class="category-list">
              <button
                v-for="item in categoryOptions"
                :key="item.value"
                type="button"
                class="category-btn"
                :class="{ active: form.category === item.value }"
                @click="form.category = item.value"
              >
                <AppIcon :name="item.icon" />
                {{ item.label }}
              </button>
            </div>
          </div>

          <div class="form-grid">
            <label class="field">
              <span><b>*</b> 报酬金额</span>
              <div class="control price-control">
                <strong>¥</strong>
                <input v-model.trim="form.reward" type="number" min="1" step="0.01" placeholder="请输入金额" required />
                <em>元</em>
              </div>
              <small class="hint">建议参考相似任务的市场价格，合理定价更易被接单</small>
            </label>

            <label class="field">
              <span><b>*</b> 截止时间</span>
              <div class="control icon-control">
                <input v-model="form.deadline" type="datetime-local" required />
                <AppIcon name="calendar" />
              </div>
              <small class="hint">任务需在截止时间前完成</small>
            </label>

            <div class="field">
              <span><b>*</b> 任务地点</span>
              <div v-if="hasPickedLocation" class="picked-location">
                <span><AppIcon name="map-pin" /> {{ pickedBuildingDisplay }}</span>
                <button type="button" @click="goPickBuilding">重新选点</button>
              </div>
              <button v-else type="button" class="map-picker" @click="goPickBuilding">
                <AppIcon name="map-pin" />
                前往地图选点
              </button>
              <small class="hint">请在地图上选择任务所在位置</small>
            </div>

            <label class="field">
              <span><b>*</b> 详细地点</span>
              <div class="control">
                <input v-model.trim="form.locationDetail" type="text" maxlength="200" placeholder="如具体教室、宿舍号、取件点等" required />
              </div>
              <small class="hint">补充更详细的地点信息，帮助接单者更快找到位置</small>
            </label>
          </div>

          <section class="image-placeholder">
            <h2>上传图片 <small>选填，最多 3 张</small></h2>
            <input
              ref="fileInputRef"
              class="file-input"
              type="file"
              accept="image/jpeg,image/png"
              multiple
              @change="handleImageChange"
            />
            <div class="upload-row">
              <div
                v-for="image in uploadedImages"
                :key="image.id"
                class="upload-box preview"
                :class="{ pending: image.uploading, failed: Boolean(image.error) }"
              >
                <img :src="image.previewUrl || image.url" :alt="image.name" />
                <span v-if="image.uploading">上传中</span>
                <span v-else-if="image.error">{{ image.error }}</span>
                <button type="button" aria-label="删除图片" @click="removeImage(image.id)">×</button>
              </div>
              <button
                v-if="uploadedImages.length < 3"
                type="button"
                class="upload-box primary"
                :disabled="uploadingImages"
                @click="openFilePicker"
              >
                <AppIcon name="plus" />
                <strong>点击上传</strong>
                <span>支持 JPG / PNG，单张 ≤ 5MB</span>
              </button>
            </div>
            <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>
          </section>

          <div class="info-row">
            <section class="wallet-card" :class="{ insufficient: !balanceEnough }">
              <header>
                <AppIcon name="wallet" />
                <strong>钱包与冻结提示</strong>
              </header>
              <p>发布任务需冻结相应金额，任务完成并确认后将自动解冻结算。</p>
              <div class="wallet-stats">
                <div>
                  <span>冻结金额</span>
                  <strong>{{ freezeAmountText }}</strong>
                  <small>按报酬金额计算</small>
                </div>
                <div>
                  <span>可用余额</span>
                  <strong>¥ {{ wallet.available }}</strong>
                  <small>{{ balanceEnough ? "充足" : "余额不足" }}</small>
                </div>
                <button type="button" @click="router.push('/wallet')">去充值</button>
              </div>
            </section>

            <section class="audit-card">
              <header>
                <AppIcon name="shield" />
                <strong>AI 审核机制</strong>
              </header>
              <div class="audit-grid">
                <div>
                  <AppIcon name="alert" />
                  <strong>高风险拦截</strong>
                  <span>涉及违规内容将被拦截并限制发布。</span>
                </div>
                <div>
                  <AppIcon name="shield" />
                  <strong>低风险审核</strong>
                  <span>内容安全将快速通过并发布。</span>
                </div>
              </div>
            </section>
          </div>

          <div v-if="error" class="form-error">{{ error }}</div>
          <div v-if="moderationNotice" class="form-notice">{{ moderationNotice }}</div>

          <footer class="form-footer">
            <p>发布即表示你已阅读并同意《平台服务协议》与《隐私政策》</p>
            <div>
              <button type="submit" class="submit-action" :disabled="submitting">
                <AppIcon name="send" />
                {{ submitting ? "发布中..." : "发布任务" }}
              </button>
            </div>
          </footer>
        </form>
      </main>

      <aside class="side-panel">
        <section class="side-card">
          <h2><AppIcon name="spark" /> 发布建议</h2>
          <ul>
            <li>标题清晰简洁，描述具体需求</li>
            <li>提供准确的地点和时间信息</li>
            <li>合理的报酬更容易获得接单</li>
            <li>礼貌用语，良好沟通更高效</li>
          </ul>
        </section>

        <section class="side-card safety-card">
          <h2><AppIcon name="shield" /> 安全提示</h2>
          <ul>
            <li>请勿发布涉及违法违规的任务</li>
            <li>避免透露个人隐私信息</li>
            <li>线下交易请注意人身与财产安全</li>
            <li>遇到问题可联系平台客服</li>
          </ul>
        </section>

        <section class="side-card preview-card">
          <h2><AppIcon name="eye" /> 示例预览</h2>
          <article>
            <header>
              <strong>{{ previewTitle }}</strong>
              <span>{{ previewCategory }}</span>
              <b>{{ freezeAmountText }}</b>
            </header>
            <p>{{ previewDescription }}</p>
            <footer>
              <span><AppIcon name="calendar" /> {{ previewDeadline }}</span>
              <span><AppIcon name="map-pin" /> {{ previewLocation }}</span>
            </footer>
          </article>
          <small>这是任务发布后的展示效果示例</small>
        </section>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createTask } from "@/api/modules/task";
import { getUploadSignedUrl } from "@/api/modules/upload";
import { getWalletBalance } from "@/api/modules/wallet";
import AppIcon from "@/components/ui/AppIcon.vue";
import type { TaskCategory, Wallet } from "@/types/api";

interface UploadedImage {
  id: string;
  name: string;
  url: string;
  previewUrl: string;
  uploading: boolean;
  error: string;
}

const route = useRoute();
const router = useRouter();
const submitting = ref(false);
const error = ref("");
const moderationNotice = ref("");
const uploadError = ref("");
const fileInputRef = ref<HTMLInputElement | null>(null);
const uploadedImages = ref<UploadedImage[]>([]);
const wallet = reactive<Wallet>({ available: "--", frozen: "--", total: "--" });

const form = reactive({
  title: "",
  description: "",
  category: "" as "" | TaskCategory,
  reward: "",
  deadline: "",
  locationDetail: "",
});

const pickedLat = ref<number | null>(null);
const pickedLng = ref<number | null>(null);

const categoryOptions: Array<{ value: TaskCategory; label: string; icon: string }> = [
  { value: "package", label: "代取快递", icon: "package" },
  { value: "food", label: "代取餐食", icon: "food" },
  { value: "move", label: "代取代送", icon: "move" },
  { value: "other", label: "其他", icon: "other" },
];

const categoryLabels: Record<TaskCategory, string> = {
  package: "代取快递",
  food: "代取餐食",
  move: "代取代送",
  other: "其他",
};

const rewardAmount = computed(() => Number.parseFloat(form.reward));
const availableAmount = computed(() => Number.parseFloat(wallet.available));
const hasReward = computed(() => Number.isFinite(rewardAmount.value) && rewardAmount.value > 0);
const hasPickedLocation = computed(() => pickedLat.value != null && pickedLng.value != null);
const uploadingImages = computed(() => uploadedImages.value.some((image) => image.uploading));

const freezeAmountText = computed(() => {
  return hasReward.value ? `¥ ${rewardAmount.value.toFixed(2)}` : "¥ --";
});

const balanceEnough = computed(() => {
  if (!hasReward.value || !Number.isFinite(availableAmount.value)) return true;
  return availableAmount.value >= rewardAmount.value;
});

const pickedBuildingDisplay = computed(() => {
  if (pickedLat.value != null && pickedLng.value != null) {
    return `已选点 (${pickedLat.value.toFixed(4)}, ${pickedLng.value.toFixed(4)})`;
  }
  return "已选点";
});

const previewTitle = computed(() => form.title || "示例任务标题");
const previewCategory = computed(() => (form.category ? categoryLabels[form.category] : "代取快递"));
const previewDescription = computed(() => form.description || "取快递：菜鸟驿站 3-2-1011");
const previewLocation = computed(() => form.locationDetail || pickedBuildingDisplay.value || "学生公寓楼");
const previewDeadline = computed(() => {
  if (!form.deadline) return "今天 18:00 前";
  const date = new Date(form.deadline);
  if (Number.isNaN(date.getTime())) return "今天 18:00 前";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
});

const DRAFT_KEY = "campusmast.postTaskDraft";

function saveDraft() {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify({
    title: form.title,
    description: form.description,
    category: form.category,
    reward: form.reward,
    deadline: form.deadline,
    locationDetail: form.locationDetail,
    pickedLat: pickedLat.value,
    pickedLng: pickedLng.value,
    images: uploadedImages.value
      .filter((image) => image.url && !image.uploading && !image.error)
      .map((image) => ({ name: image.name, url: image.url })),
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
    form.locationDetail = d.locationDetail || "";
    pickedLat.value = d.pickedLat ?? null;
    pickedLng.value = d.pickedLng ?? null;
    if (Array.isArray(d.images)) {
      uploadedImages.value = d.images.slice(0, 3).map((image: { name?: string; url?: string }, index: number) => ({
        id: `restored-${index}-${image.url || ""}`,
        name: image.name || "已上传图片",
        url: image.url || "",
        previewUrl: image.url || "",
        uploading: false,
        error: "",
      })).filter((image: UploadedImage) => image.url);
    }
  } catch {
    /* ignore invalid draft */
  }
}

function clearDraft() {
  sessionStorage.removeItem(DRAFT_KEY);
}

function goPickBuilding() {
  saveDraft();
  router.push("/map?mode=pick-building");
}

function validateForm() {
  const title = form.title.trim();
  const description = form.description.trim();
  const locationDetail = form.locationDetail.trim();
  const deadline = form.deadline ? new Date(form.deadline) : null;

  if (!title) return "请填写任务标题";
  if (title.length > 30) return "任务标题不能超过 30 字";
  if (!description) return "请填写任务描述";
  if (description.length > 300) return "任务描述不能超过 300 字";
  if (!form.category) return "请选择任务分类";
  if (!hasReward.value) return "请输入有效的报酬金额";
  if (!deadline || Number.isNaN(deadline.getTime())) return "请选择截止时间";
  if (deadline.getTime() <= Date.now()) return "截止时间不能早于当前时间";
  if (!hasPickedLocation.value) return "请前往地图选择任务地点";
  if (!locationDetail) return "请填写详细地点";
  if (!balanceEnough.value) return "可用余额不足，请充值后再发布任务";
  if (uploadingImages.value) return "图片仍在上传中，请稍后再发布";
  if (uploadedImages.value.some((image) => image.error)) return "请删除上传失败的图片后再发布";
  return "";
}

function openFilePicker() {
  uploadError.value = "";
  fileInputRef.value?.click();
}

async function handleImageChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  input.value = "";
  uploadError.value = "";
  if (!files.length) return;

  const remain = 3 - uploadedImages.value.length;
  if (remain <= 0) {
    uploadError.value = "最多上传 3 张图片";
    return;
  }

  const accepted = files.slice(0, remain);
  if (files.length > remain) uploadError.value = "最多上传 3 张图片，已自动忽略多余文件";

  for (const file of accepted) {
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      uploadError.value = "仅支持 JPG / PNG 图片";
      continue;
    }
    if (file.size > 5 * 1024 * 1024) {
      uploadError.value = "单张图片不能超过 5MB";
      continue;
    }
    void uploadImage(file);
  }
}

async function uploadImage(file: File) {
  const previewUrl = URL.createObjectURL(file);
  const image: UploadedImage = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name: file.name,
    url: "",
    previewUrl,
    uploading: true,
    error: "",
  };
  uploadedImages.value.push(image);

  try {
    const signed = await getUploadSignedUrl({ filename: file.name, contentType: file.type });
    const isMockUpload = signed.uploadUrl.includes("example.com/mock-upload/") || signed.uploadUrl.includes("replace-me");
    if (!isMockUpload) {
      const response = await fetch(signed.uploadUrl, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });
      if (!response.ok) throw new Error(`upload failed: ${response.status}`);
    }
    image.url = signed.fileUrl;
  } catch {
    image.error = "上传失败";
    uploadError.value = "图片上传失败，请删除后重试";
  } finally {
    image.uploading = false;
  }
}

function removeImage(id: string) {
  const image = uploadedImages.value.find((item) => item.id === id);
  if (image?.previewUrl?.startsWith("blob:")) URL.revokeObjectURL(image.previewUrl);
  uploadedImages.value = uploadedImages.value.filter((item) => item.id !== id);
  uploadError.value = "";
}

onMounted(async () => {
  try {
    const balance = await getWalletBalance();
    wallet.available = balance.available;
    wallet.frozen = balance.frozen;
    wallet.total = balance.total;
  } catch {
    /* wallet card keeps placeholder values */
  }

  if (route.query.lat) {
    loadDraft();
  }
  if (route.query.lat && route.query.lng) {
    pickedLat.value = Number.parseFloat(route.query.lat as string);
    pickedLng.value = Number.parseFloat(route.query.lng as string);
  }
  if (!form.title && !route.query.lat) {
    loadDraft();
  }
});

onBeforeUnmount(() => {
  for (const image of uploadedImages.value) {
    if (image.previewUrl.startsWith("blob:")) URL.revokeObjectURL(image.previewUrl);
  }
});

async function handleSubmit() {
  error.value = "";
  moderationNotice.value = "";

  const validationError = validateForm();
  if (validationError) {
    error.value = validationError;
    return;
  }

  submitting.value = true;
  try {
    const result = await createTask({
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category as TaskCategory,
      reward: rewardAmount.value.toFixed(2),
      deadline: new Date(form.deadline).toISOString(),
      latitude: pickedLat.value ?? undefined,
      longitude: pickedLng.value ?? undefined,
      locationDetail: form.locationDetail.trim(),
      imageUrls: uploadedImages.value.filter((image) => image.url && !image.error).map((image) => image.url),
    });
    if (result.needsAdminReview) moderationNotice.value = "任务已发布，部分内容标记为待管理员复审。";
    clearDraft();
    router.push(`/tasks/${result.id}`);
  } catch (err: any) {
    const d = err?.response?.data?.error;
    error.value = d?.code === "MODERATION_BLOCKED" ? "内容命中审核规则，已被系统拦截，请修改后重新提交。" : d?.message || "发布失败";
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.post-page {
  min-height: calc(100dvh - 62px);
  padding: clamp(16px, 2vw, 28px) clamp(16px, 3.4vw, 51px) 32px;
  background: #fbfaf7;
  color: #242622;
}

.post-layout {
  width: min(1440px, 100%);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 0.42fr);
  gap: clamp(14px, 1.5vw, 20px);
  align-items: start;
}

.form-card,
.side-card {
  border: 1px solid #ebe8df;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 16px 36px rgba(60, 54, 45, 0.06);
}

.form-card {
  min-width: 0;
  padding: clamp(18px, 2vw, 27px);
}

.page-head {
  margin-bottom: 25px;
}

.page-head h1 {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 900;
}

.page-head p {
  margin: 10px 0 0;
  color: #656862;
  font-size: 14px;
}

.post-form {
  display: grid;
  gap: 13px;
}

.field {
  display: grid;
  grid-template-columns: minmax(86px, 0.12fr) minmax(0, 1fr);
  align-items: start;
  gap: 14px;
  color: #292b27;
  font-size: 14px;
  font-weight: 800;
}

.field > span {
  min-height: 37px;
  display: flex;
  align-items: center;
}

.field b {
  margin-right: 6px;
  color: #ef4e5b;
}

.control {
  min-height: 37px;
  display: flex;
  align-items: center;
  border: 1px solid #e7e4dc;
  border-radius: 8px;
  background: #fff;
  color: #292b27;
  overflow: hidden;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.control:focus-within {
  border-color: rgba(111, 131, 95, 0.55);
  box-shadow: 0 0 0 4px rgba(111, 131, 95, 0.1);
}

.control input,
.control textarea {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #252621;
  font: inherit;
  font-weight: 500;
}

.control input {
  height: 37px;
  padding: 0 14px;
}

.control textarea {
  min-height: 72px;
  padding: 12px 14px;
  resize: vertical;
}

.control input::placeholder,
.control textarea::placeholder {
  color: #a5a49e;
}

.with-count {
  position: relative;
}

.with-count input,
.with-count textarea {
  padding-right: 56px;
}

.with-count small {
  position: absolute;
  right: 12px;
  bottom: 8px;
  color: #8d8f88;
  font-size: 12px;
  font-weight: 700;
}

.category-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.category-btn {
  min-height: 37px;
  min-width: min(106px, 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 17px;
  border: 1px solid #e7e4dc;
  border-radius: 8px;
  background: #fff;
  color: #2f312d;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.category-btn .app-icon {
  font-size: 16px;
  color: #6f835f;
}

.category-btn.active {
  border-color: #7b8f6c;
  background: #f2f6ed;
  color: #587048;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr));
  gap: 14px 24px;
}

.form-grid .field {
  grid-template-columns: minmax(86px, 0.22fr) minmax(0, 1fr);
}

.hint {
  grid-column: 2;
  margin-top: -4px;
  color: #8a8d86;
  font-size: 12px;
  font-weight: 500;
}

.price-control strong,
.price-control em {
  flex: 0 0 auto;
  color: #627653;
  font-style: normal;
  font-weight: 900;
}

.price-control strong {
  padding-left: 14px;
}

.price-control em {
  padding-right: 14px;
}

.icon-control {
  position: relative;
}

.icon-control input {
  padding-right: 42px;
}

.icon-control .app-icon {
  position: absolute;
  right: 13px;
  color: #8a8d86;
  pointer-events: none;
}

.map-picker,
.picked-location {
  width: 100%;
  min-height: 37px;
  border-radius: 8px;
}

.map-picker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px dashed #8fa47d;
  background: #f5f8f0;
  color: #617651;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 900;
}

.picked-location {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 8px 0 12px;
  border: 1px solid #dfe8d7;
  background: #f5f8f0;
}

.picked-location span {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 7px;
  overflow: hidden;
  color: #536947;
  font-size: 13px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picked-location button {
  flex: 0 0 auto;
  height: 27px;
  padding: 0 12px;
  border: 1px solid #8fa47d;
  border-radius: 7px;
  background: #fff;
  color: #617651;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 800;
}

.image-placeholder {
  margin-top: 5px;
}

.file-input {
  display: none;
}

.image-placeholder h2 {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 800;
}

.image-placeholder small {
  color: #7d8079;
  font-size: 12px;
  font-weight: 500;
}

.upload-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(132px, 100%), 1fr));
  gap: 10px;
}

.upload-box {
  max-height: 88px;
  aspect-ratio: 1.5 / 1;
  border: 1px solid #e7e4dc;
  border-radius: 8px;
  background: #fff;
}

.upload-box.primary {
  display: grid;
  place-items: center;
  gap: 2px;
  border-style: dashed;
  color: #6f835f;
  cursor: not-allowed;
  font: inherit;
}

.upload-box.primary .app-icon {
  font-size: 16px;
}

.upload-box.primary strong {
  color: #292b27;
  font-size: 12px;
}

.upload-box.primary span {
  color: #8a8d86;
  font-size: 11px;
}

.upload-box.preview {
  position: relative;
  overflow: hidden;
  background: #f5f4ef;
}

.upload-box.preview img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.upload-box.preview::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 48%, rgba(0, 0, 0, 0.38));
  pointer-events: none;
}

.upload-box.preview > span {
  position: absolute;
  left: 8px;
  bottom: 7px;
  z-index: 1;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.upload-box.preview > button {
  position: absolute;
  top: 6px;
  right: 6px;
  z-index: 1;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(31, 33, 29, 0.72);
  color: #fff;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.upload-box.preview.pending img,
.upload-box.preview.failed img {
  filter: grayscale(0.25);
}

.upload-box.preview.failed::after,
.upload-box.preview.pending::after {
  background: rgba(31, 33, 29, 0.48);
}

.upload-error {
  margin: 8px 0 0;
  color: #b24a3a;
  font-size: 12px;
  font-weight: 800;
}

.info-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
  gap: 18px;
  margin-top: 10px;
}

.wallet-card,
.audit-card {
  min-height: 124px;
  padding: 14px 16px;
  border-radius: 8px;
}

.wallet-card {
  border: 1px solid #dce8d2;
  background: linear-gradient(135deg, #fbfff7, #f5f8f0);
}

.wallet-card.insufficient {
  border-color: #f0c5bd;
  background: linear-gradient(135deg, #fff9f8, #fdf3f1);
}

.audit-card {
  border: 1px solid #d7e3f5;
  background: linear-gradient(135deg, #fbfdff, #f3f8ff);
}

.wallet-card header,
.audit-card header {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #526947;
  font-size: 15px;
  font-weight: 900;
}

.wallet-card p {
  margin: 10px 0 12px;
  color: #6f716b;
  font-size: 12px;
  line-height: 1.6;
}

.wallet-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)) minmax(92px, auto);
  gap: 10px;
  align-items: end;
}

.wallet-stats div {
  display: grid;
  gap: 4px;
}

.wallet-stats span,
.wallet-stats small {
  color: #7c8078;
  font-size: 12px;
}

.wallet-stats strong {
  color: #627653;
  font-size: 18px;
  font-weight: 900;
}

.wallet-stats button {
  min-width: 92px;
  height: 38px;
  padding: 0 14px;
  border: 1px solid #8fa47d;
  border-radius: 8px;
  background: #fff;
  color: #536947;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.audit-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(170px, 100%), 1fr));
  gap: 14px;
  margin-top: 18px;
}

.audit-grid div {
  display: grid;
  grid-template-columns: 22px 1fr;
  gap: 3px 8px;
}

.audit-grid .app-icon {
  grid-row: span 2;
  color: #5275ad;
}

.audit-grid strong {
  color: #2d332a;
  font-size: 13px;
}

.audit-grid span {
  color: #70736d;
  font-size: 12px;
  line-height: 1.5;
}

.form-error,
.form-notice {
  padding: 11px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
}

.form-error {
  background: #fff0ee;
  color: #b24a3a;
}

.form-notice {
  background: #fff8e9;
  color: #b67824;
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-top: 11px;
}

.form-footer p {
  min-width: 0;
  margin: 0;
  color: #7d8079;
  font-size: 12px;
}

.form-footer div {
  flex: 0 0 auto;
  display: flex;
  gap: 16px;
}

.secondary-action,
.submit-action {
  height: 38px;
  min-width: 112px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 900;
}

.secondary-action {
  border: 1px solid #e1ded6;
  background: #fff;
  color: #2c2d29;
}

.submit-action {
  border: 0;
  background: linear-gradient(145deg, #728766, #536b49);
  color: #fff;
  box-shadow: 0 10px 22px rgba(83, 107, 73, 0.2);
}

.submit-action:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.side-panel {
  display: grid;
  gap: 14px;
  align-content: start;
}

.side-card {
  padding: 22px;
}

.side-card h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 16px;
  color: #262824;
  font-size: 16px;
  font-weight: 900;
}

.side-card h2 .app-icon {
  color: #6f835f;
  font-size: 18px;
}

.side-card ul {
  display: grid;
  gap: 11px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.side-card li {
  position: relative;
  padding-left: 18px;
  color: #5f625c;
  font-size: 13px;
  line-height: 1.6;
}

.side-card li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #6f835f;
}

.safety-card li::before {
  top: 7px;
  width: 12px;
  height: 12px;
  background: #6f835f;
  mask: radial-gradient(circle at 50% 50%, transparent 3px, #000 3.4px);
}

.preview-card article {
  padding: 16px;
  border: 1px solid #ebe8df;
  border-radius: 10px;
  background: #fff;
}

.preview-card header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
}

.preview-card header strong {
  min-width: 0;
  overflow: hidden;
  color: #292b27;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-card header span {
  padding: 3px 8px;
  border-radius: 6px;
  background: #edf3e8;
  color: #617651;
  font-size: 12px;
  font-weight: 800;
}

.preview-card header b {
  color: #627653;
  font-size: 17px;
}

.preview-card p {
  margin: 12px 0;
  color: #686b65;
  font-size: 13px;
  line-height: 1.6;
}

.preview-card footer {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: #7e817a;
  font-size: 12px;
}

.preview-card footer span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.preview-card > small {
  display: block;
  margin-top: 12px;
  color: #8a8d86;
  font-size: 12px;
}

@media (max-width: 1180px) {
  .post-page {
    padding: 20px 24px 32px;
  }

  .post-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
  }
}

@media (max-width: 760px) {
  .post-page {
    padding: 16px;
  }

  .form-card {
    padding: 20px;
  }

  .field,
  .form-grid .field {
    grid-template-columns: 1fr;
    gap: 7px;
  }

  .field > span {
    min-height: auto;
  }

  .hint {
    grid-column: 1;
    margin-top: 0;
  }

  .form-grid,
  .info-row,
  .upload-row,
  .wallet-stats {
    grid-template-columns: 1fr;
  }

  .form-footer,
  .form-footer div {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
