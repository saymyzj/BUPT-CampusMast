<template>
  <div class="wallet-page">
    <section class="wallet-shell">
      <header class="page-title">
        <div>
          <h1>钱包与资金流水</h1>
          <p>我的 / 钱包与资金流水</p>
        </div>
      </header>

      <div v-if="loading" class="state-card">
        <AppIcon name="wallet" />
        <span>正在加载钱包信息</span>
      </div>
      <div v-else-if="error" class="state-card state-error">
        <AppIcon name="alert" />
        <span>{{ error }}</span>
      </div>

      <template v-else>
        <section class="balance-grid">
          <article class="balance-card available">
            <span class="balance-icon"><AppIcon name="wallet" /></span>
            <div>
              <p>可用余额</p>
              <strong>¥ {{ money(wallet.available) }}</strong>
              <small>可用于提现、支付任务押金</small>
            </div>
            <button type="button" @click="openAction('topup')">充值</button>
          </article>

          <article class="balance-card frozen">
            <span class="balance-icon"><AppIcon name="shield" /></span>
            <div>
              <p>冻结金额</p>
              <strong>¥ {{ money(wallet.frozen) }}</strong>
              <small>进行中任务的保证金或待结算金额</small>
            </div>
            <button type="button" @click="scrollToTransactions">查看明细</button>
          </article>

          <article class="balance-card total">
            <span class="balance-icon"><AppIcon name="save" /></span>
            <div>
              <p>总余额</p>
              <strong>¥ {{ money(wallet.total) }}</strong>
              <small>可用余额 + 冻结金额</small>
            </div>
            <button type="button" @click="openAction('withdraw')">提现</button>
          </article>
        </section>

        <section v-if="activeAction" class="action-panel">
          <div>
            <strong>{{ activeAction === "topup" ? "充值金额" : "提现金额" }}</strong>
            <span>{{ activeAction === "topup" ? "充值会直接进入可用余额" : "提现金额不能超过当前可用余额" }}</span>
          </div>
          <label>
            <span>¥</span>
            <input v-model="actionAmount" type="number" min="0.01" step="0.01" placeholder="请输入金额" />
          </label>
          <button type="button" :disabled="actionLoading" @click="submitWalletAction">
            {{ actionLoading ? "处理中..." : activeAction === "topup" ? "确认充值" : "确认提现" }}
          </button>
          <button class="ghost" type="button" @click="closeAction">取消</button>
          <p v-if="actionMsg">{{ actionMsg }}</p>
        </section>

        <div class="wallet-layout">
          <main ref="transactionsPanel" class="transactions-card">
            <div class="toolbar">
              <AppSelect
                :model-value="filters.range"
                :options="rangeFilterOptions"
                variant="field"
                icon="calendar"
                @change="handleRangeFilterChange"
              />

              <AppSelect
                :model-value="filters.type"
                :options="typeFilterOptions"
                variant="field"
                icon="filter"
                show-option-dot
                @change="handleTypeFilterChange"
              />

              <AppSelect
                :model-value="filters.status"
                :options="statusFilterOptions"
                variant="field"
                icon="check-circle"
                @change="handleStatusFilterChange"
              />

              <label class="search-box">
                <input v-model.trim="filters.keyword" type="search" placeholder="搜索交易单号或备注" />
                <AppIcon name="search" />
              </label>

              <button class="export-button" type="button" @click="exportCsv">
                <AppIcon name="save" />
                导出流水
              </button>
            </div>

            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>交易时间</th>
                    <th>类型</th>
                    <th>交易对象</th>
                    <th>交易单号</th>
                    <th>金额（元）</th>
                    <th>状态</th>
                    <th>备注</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody v-if="displayTransactions.length > 0">
                  <tr v-for="tx in displayTransactions" :key="tx.id">
                    <td>{{ formatTime(tx.createdAt) }}</td>
                    <td>
                      <span class="type-pill" :class="`tone-${txTone(tx.type)}`">
                        <AppIcon :name="txIcon(tx.type)" />
                        {{ txTypeLabel(tx.type) }}
                      </span>
                    </td>
                    <td class="target">{{ transactionTarget(tx) }}</td>
                    <td>{{ shortId(tx.id) }}</td>
                    <td class="amount" :class="`amount-${txTone(tx.type)}`">{{ signedAmount(tx) }}</td>
                    <td><span class="success-pill">成功</span></td>
                    <td class="note">{{ transactionNote(tx) }}</td>
                    <td><button class="link-button" type="button" @click="viewRelatedTask(tx)">查看</button></td>
                  </tr>
                </tbody>
              </table>
              <div v-if="txLoading" class="table-state">正在加载流水...</div>
              <div v-else-if="displayTransactions.length === 0" class="table-state">暂无资金流水</div>
            </div>

            <footer class="table-footer">
              <span>共 {{ filteredTransactions.length }} 条记录</span>
              <div class="pager">
                <button type="button" :disabled="page <= 1" @click="page -= 1">‹</button>
                <strong>{{ page }}</strong>
                <button type="button" :disabled="page >= totalPages" @click="page += 1">›</button>
              </div>
            </footer>
          </main>

          <aside class="side-column">
            <section class="side-card chart-card">
              <div class="side-head">
                <h2>收支趋势</h2>
                <div class="chart-range" aria-label="收支趋势范围">
                  <button type="button" :class="{ active: chartRange === 6 }" @click="chartRange = 6">近六月</button>
                  <button type="button" :class="{ active: chartRange === 12 }" @click="chartRange = 12">近一年</button>
                </div>
              </div>
              <svg class="trend-chart" viewBox="0 0 340 190" role="img" aria-label="收支趋势">
                <g class="grid-lines">
                  <path v-for="tick in chartYTicks" :key="tick.y" :d="`M42 ${tick.y}H324`" />
                </g>
                <g class="y-labels">
                  <text v-for="tick in chartYTicks" :key="`y-${tick.y}`" x="34" :y="tick.y + 3">{{ tick.label }}</text>
                </g>
                <polyline class="income-line" :points="incomePoints" />
                <polyline class="expense-line" :points="expensePoints" />
                <g>
                  <circle v-for="point in incomeDots" :key="`i-${point.x}`" :cx="point.x" :cy="point.y" r="3.5" class="income-dot" />
                  <circle v-for="point in expenseDots" :key="`e-${point.x}`" :cx="point.x" :cy="point.y" r="3.5" class="expense-dot" />
                </g>
                <g class="x-labels">
                  <text v-for="tick in chartTicks" :key="tick.key" :x="tick.x" y="166">{{ tick.label }}</text>
                </g>
              </svg>
              <div class="chart-total">
                <span>收入 <strong>¥ {{ money(totalIncome) }}</strong></span>
                <span>支出 <strong class="expense">¥ {{ money(totalExpense) }}</strong></span>
              </div>
            </section>

            <section class="side-card">
              <div class="side-head">
                <h2>资金托管规则</h2>
              </div>
              <ul class="info-list">
                <li><AppIcon name="shield" />发布任务时会冻结任务赏金，保障双方权益</li>
                <li><AppIcon name="check-circle" />任务完成且双方确认后，资金自动结算</li>
                <li><AppIcon name="alert" />如发生争议，平台介入处理并保障资金安全</li>
              </ul>
            </section>

            <section class="side-card">
              <div class="side-head">
                <h2>安全提示</h2>
              </div>
              <ul class="info-list quiet">
                <li><AppIcon name="eye" />请勿私下交易，谨防诈骗</li>
                <li><AppIcon name="wallet" />提现仅支持绑定本人银行卡</li>
                <li><AppIcon name="message" />如遇问题，请及时联系平台客服</li>
              </ul>
            </section>
          </aside>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { getTaskById } from "@/api/modules/task";
import { getWalletBalance, listWalletTransactions, topUpWallet, withdrawWallet } from "@/api/modules/wallet";
import AppIcon from "@/components/ui/AppIcon.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import type { Transaction, TransactionType, Wallet } from "@/types/api";

type ActionType = "topup" | "withdraw";
type Tone = "in" | "out" | "freeze" | "split";

const router = useRouter();
const wallet = ref<Wallet>({ available: "--", frozen: "--", total: "--" });
const transactions = ref<Transaction[]>([]);
const taskTitleMap = ref<Record<string, string>>({});
const transactionsPanel = ref<HTMLElement | null>(null);
const loading = ref(false);
const txLoading = ref(false);
const actionLoading = ref(false);
const error = ref("");
const actionMsg = ref("");
const activeAction = ref<ActionType | null>(null);
const actionAmount = ref("");
const chartRange = ref<6 | 12>(6);
const page = ref(1);
const pageSize = 10;
const chartPlot = {
  left: 42,
  right: 324,
  top: 24,
  bottom: 132,
};

const filters = reactive({
  range: "30" as "30" | "90" | "all",
  type: "" as "" | TransactionType,
  status: "",
  keyword: "",
});

const txLabels: Record<TransactionType, string> = {
  TOP_UP: "充值",
  WITHDRAW: "提现",
  FREEZE: "冻结",
  UNFREEZE: "解冻",
  SETTLE_OUT: "结算支出",
  SETTLE_IN: "结算收入",
  SETTLE_SPLIT: "分账",
};

const rangeFilterOptions = [
  { value: "30", label: "最近 30 天", icon: "calendar" },
  { value: "90", label: "最近 90 天", icon: "calendar" },
  { value: "all", label: "全部时间", icon: "clock" },
];

const typeFilterOptions = [
  { value: "", label: "全部类型", icon: "spark" },
  { value: "TOP_UP", label: "充值", icon: "wallet" },
  { value: "WITHDRAW", label: "提现", icon: "download" },
  { value: "FREEZE", label: "冻结", icon: "shield" },
  { value: "UNFREEZE", label: "解冻", icon: "check-circle" },
  { value: "SETTLE_OUT", label: "结算支出", icon: "yen" },
  { value: "SETTLE_IN", label: "结算收入", icon: "yen" },
  { value: "SETTLE_SPLIT", label: "分账", icon: "layers" },
];

const statusFilterOptions = [
  { value: "", label: "全部状态", icon: "spark" },
  { value: "success", label: "成功", icon: "check-circle" },
];

const descriptionLabels: Record<string, string> = {
  "Wallet top-up": "钱包充值",
  "Wallet withdrawal": "钱包提现",
  "Task reward frozen": "任务赏金冻结",
  "Task reward unfrozen": "任务赏金解冻",
  "Task reward settled out to helper": "任务赏金结算给接单人",
  "Task reward settled in from requester": "收到发布者任务赏金",
  "Task expired refund": "任务过期退款",
  "Task expired by system refund": "系统关闭过期任务退款",
  "Task cancelled refund": "任务取消退款",
  "Dispute full refund": "争议处理全额退款",
  "Dispute closed by admin refund": "管理员关闭争议退款",
};

const incomeTypes = new Set<TransactionType>(["TOP_UP", "UNFREEZE", "SETTLE_IN"]);
const expenseTypes = new Set<TransactionType>(["WITHDRAW", "FREEZE", "SETTLE_OUT"]);

const filteredTransactions = computed(() => {
  const keyword = filters.keyword.toLowerCase();
  const startTime = rangeStartTime();
  return transactions.value.filter((tx) => {
    if (filters.type && tx.type !== filters.type) return false;
    if (startTime && new Date(tx.createdAt).getTime() < startTime) return false;
    if (!keyword) return true;
    return [tx.id, transactionTarget(tx), transactionNote(tx)].some((value) => value.toLowerCase().includes(keyword));
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTransactions.value.length / pageSize)));
const displayTransactions = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filteredTransactions.value.slice(start, start + pageSize);
});

const totalIncome = computed(() => sumByTone("in"));
const totalExpense = computed(() => sumByTone("out"));
const chartMonths = computed(() => buildChartMonths());
const chartTicks = computed(() => buildDots("income").map((point, index) => ({ ...point, key: chartMonths.value[index].key, label: chartMonths.value[index].label })));
const chartMax = computed(() => niceChartMax(Math.max(0, ...chartMonths.value.flatMap((row) => [row.income, row.expense]))));
const chartScaleMax = computed(() => chartMax.value || 1);
const chartYTicks = computed(() => {
  const values = [chartMax.value, chartMax.value * (2 / 3), chartMax.value * (1 / 3), 0];
  const ys = [chartPlot.top, chartPlot.top + 36, chartPlot.top + 72, chartPlot.bottom];
  return values.map((value, index) => ({ y: ys[index], label: formatChartAmount(value) }));
});
const incomeDots = computed(() => buildDots("income"));
const expenseDots = computed(() => buildDots("expense"));
const incomePoints = computed(() => incomeDots.value.map((point) => `${point.x},${point.y}`).join(" "));
const expensePoints = computed(() => expenseDots.value.map((point) => `${point.x},${point.y}`).join(" "));

watch(
  () => [filters.range, filters.type, filters.status, filters.keyword],
  () => {
    page.value = 1;
  },
);

function handleRangeFilterChange(value: string) {
  filters.range = value as "30" | "90" | "all";
}

function handleTypeFilterChange(value: string) {
  filters.type = value as "" | TransactionType;
}

function handleStatusFilterChange(value: string) {
  filters.status = value;
}

function money(value: string | number) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "--";
  return numeric.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function amountNumber(tx: Transaction) {
  const amount = Number(tx.amount);
  return Number.isFinite(amount) ? amount : 0;
}

function txTypeLabel(type: TransactionType) {
  return txLabels[type] ?? type;
}

function txTone(type: TransactionType): Tone {
  if (incomeTypes.has(type)) return "in";
  if (expenseTypes.has(type)) return type === "FREEZE" ? "freeze" : "out";
  return "split";
}

function txIcon(type: TransactionType) {
  if (type === "TOP_UP" || type === "UNFREEZE" || type === "SETTLE_IN") return "plus";
  if (type === "FREEZE") return "shield";
  if (type === "SETTLE_SPLIT") return "spark";
  return "wallet";
}

function signedAmount(tx: Transaction) {
  const tone = txTone(tx.type);
  const sign = tone === "in" || tone === "split" ? "+" : "-";
  return `${sign} ${money(tx.amount)}`;
}

function shortId(id: string) {
  if (!id) return "-";
  return id.length > 18 ? `${id.slice(0, 10)}...${id.slice(-4)}` : id;
}

function transactionTarget(tx: Transaction) {
  if (!tx.relatedTaskId) return "钱包账户";
  return taskTitleMap.value[tx.relatedTaskId] || "相关任务";
}

function transactionNote(tx: Transaction) {
  const raw = tx.description?.trim();
  if (!raw) return txTypeLabel(tx.type);
  if (descriptionLabels[raw]) return descriptionLabels[raw];

  const splitFrozen = raw.match(/^Task reward split: frozen consumed ([\d.]+), requester refund ([\d.]+)$/);
  if (splitFrozen) return `任务争议分账：扣除冻结赏金 ${splitFrozen[1]}，发布者退回 ${splitFrozen[2]}`;

  const splitHelper = raw.match(/^Task reward split: helper payout ([\d.]+)$/);
  if (splitHelper) return `任务争议分账：接单人获得 ${splitHelper[1]}`;

  return raw;
}

function formatTime(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function rangeStartTime() {
  if (filters.range === "all") return null;
  return Date.now() - Number(filters.range) * 24 * 60 * 60 * 1000;
}

function sumByTone(tone: "in" | "out") {
  return filteredTransactions.value.reduce((sum, tx) => {
    const currentTone = txTone(tx.type);
    if (tone === "in" && (currentTone === "in" || currentTone === "split")) return sum + amountNumber(tx);
    if (tone === "out" && (currentTone === "out" || currentTone === "freeze")) return sum + amountNumber(tx);
    return sum;
  }, 0);
}

function niceChartMax(value: number) {
  if (!Number.isFinite(value) || value <= 0) return 0;
  const exponent = Math.floor(Math.log10(value));
  const base = 10 ** exponent;
  const normalized = value / base;
  const niceNormalized = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return niceNormalized * base;
}

function formatChartAmount(value: number) {
  if (!value) return "0";
  if (value >= 10000) return `${Number((value / 10000).toFixed(1))}万`;
  if (value >= 1000) return `${Number((value / 1000).toFixed(1))}k`;
  return String(Math.round(value));
}

function buildChartMonths() {
  const now = new Date();
  const months: Array<{ key: string; label: string; income: number; expense: number }> = [];
  for (let i = chartRange.value - 1; i >= 0; i -= 1) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    months.push({ key, label: `${date.getMonth() + 1}月`, income: 0, expense: 0 });
  }
  const lookup = new Map(months.map((item) => [item.key, item]));
  for (const tx of filteredTransactions.value) {
    const date = new Date(tx.createdAt);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const row = lookup.get(key);
    if (!row) continue;
    const tone = txTone(tx.type);
    if (tone === "in" || tone === "split") row.income += amountNumber(tx);
    if (tone === "out" || tone === "freeze") row.expense += amountNumber(tx);
  }
  return months;
}

function buildDots(kind: "income" | "expense") {
  const rows = chartMonths.value;
  return rows.map((row, index) => {
    const value = kind === "income" ? row.income : row.expense;
    const x = chartPlot.left + (index * (chartPlot.right - chartPlot.left)) / Math.max(1, rows.length - 1);
    const y = chartPlot.bottom - (value / chartScaleMax.value) * (chartPlot.bottom - chartPlot.top);
    return { x: Number(x.toFixed(2)), y: Number(y.toFixed(2)) };
  });
}

function openAction(type: ActionType) {
  activeAction.value = type;
  actionAmount.value = "";
  actionMsg.value = "";
}

function closeAction() {
  activeAction.value = null;
  actionAmount.value = "";
  actionMsg.value = "";
}

async function submitWalletAction() {
  if (!activeAction.value || !actionAmount.value) return;
  const amount = Number(actionAmount.value);
  if (!Number.isFinite(amount) || amount <= 0) {
    actionMsg.value = "请输入有效金额";
    return;
  }
  actionLoading.value = true;
  actionMsg.value = "";
  try {
    const payload = { amount: amount.toFixed(2) };
    wallet.value = activeAction.value === "topup" ? await topUpWallet(payload) : await withdrawWallet(payload);
    actionMsg.value = activeAction.value === "topup" ? "充值成功" : "提现成功";
    actionAmount.value = "";
    await loadTransactions();
  } catch (err: any) {
    actionMsg.value = err?.response?.data?.error?.message || (activeAction.value === "topup" ? "充值失败" : "提现失败");
  } finally {
    actionLoading.value = false;
  }
}

async function scrollToTransactions() {
  await nextTick();
  transactionsPanel.value?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function viewRelatedTask(tx: Transaction) {
  if (tx.relatedTaskId) void router.push(`/tasks/${tx.relatedTaskId}`);
}

function exportCsv() {
  const rows = [
    ["交易时间", "类型", "交易对象", "交易单号", "金额", "状态", "备注"],
    ...filteredTransactions.value.map((tx) => [
      formatTime(tx.createdAt),
      txTypeLabel(tx.type),
      transactionTarget(tx),
      tx.id,
      signedAmount(tx),
      "成功",
      transactionNote(tx),
    ]),
  ];
  const csv = rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "campusmast-wallet-transactions.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}

async function loadWallet() {
  wallet.value = await getWalletBalance();
}

async function loadTransactions() {
  txLoading.value = true;
  try {
    const result = await listWalletTransactions({ page: 1, limit: 100 });
    transactions.value = result.data;
    await loadRelatedTaskTitles(result.data);
  } finally {
    txLoading.value = false;
  }
}

async function loadRelatedTaskTitles(rows: Transaction[]) {
  const taskIds = Array.from(new Set(rows.map((tx) => tx.relatedTaskId).filter((id): id is string => Boolean(id))));
  const missingIds = taskIds.filter((id) => !taskTitleMap.value[id]);
  if (missingIds.length === 0) return;

  const pairs = await Promise.all(
    missingIds.map(async (id) => {
      try {
        const task = await getTaskById(id);
        return [id, task.title] as const;
      } catch {
        return [id, "相关任务"] as const;
      }
    }),
  );
  taskTitleMap.value = { ...taskTitleMap.value, ...Object.fromEntries(pairs) };
}

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    await Promise.all([loadWallet(), loadTransactions()]);
  } catch {
    error.value = "加载钱包失败";
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.wallet-page {
  min-height: calc(100dvh - 62px);
  padding: clamp(14px, 2vw, 26px);
  background: #fbfaf7;
  color: #20221d;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
}

.wallet-shell {
  width: min(1380px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 14px;
}

.page-title {
  min-height: 52px;
  display: flex;
  align-items: center;
}

.page-title h1 {
  margin: 0;
  font-size: clamp(20px, 2vw, 26px);
  font-weight: 950;
}

.page-title p {
  margin: 5px 0 0;
  color: #858781;
  font-size: 12px;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.balance-card,
.transactions-card,
.side-card,
.action-panel,
.state-card {
  border: 1px solid #ece8df;
  border-radius: 13px;
  background: rgba(255, 254, 251, 0.96);
  box-shadow: 0 14px 34px rgba(54, 48, 38, 0.06);
}

.balance-card {
  min-width: 0;
  min-height: 156px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 22px;
}

.balance-card .balance-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-size: 21px;
}

.available .balance-icon,
.total .balance-icon {
  background: linear-gradient(135deg, #708461, #566f4d);
}

.frozen .balance-icon {
  background: linear-gradient(135deg, #dd8d35, #c87422);
}

.balance-card p {
  margin: 0;
  color: #55584f;
  font-size: 13px;
  font-weight: 900;
}

.balance-card strong {
  display: block;
  margin-top: 8px;
  color: #6f835f;
  font-size: clamp(25px, 2.6vw, 34px);
  line-height: 1;
  font-weight: 950;
}

.frozen strong {
  color: #df8a2f;
}

.balance-card small {
  display: block;
  margin-top: 9px;
  color: #8a8c84;
  font-size: 12px;
  line-height: 1.45;
}

.balance-card button {
  grid-column: 2;
  width: min(116px, 100%);
  height: 34px;
  margin-top: 8px;
  border: 1px solid #e4dfd5;
  border-radius: 7px;
  background: #fff;
  color: #53644a;
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.available button {
  border: 0;
  background: #6f835f;
  color: #fff;
}

.action-panel {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(170px, 0.7fr) auto auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
}

.action-panel div,
.action-panel p {
  min-width: 0;
}

.action-panel strong {
  display: block;
  font-size: 14px;
  font-weight: 950;
}

.action-panel span,
.action-panel p {
  color: #858781;
  font-size: 12px;
}

.action-panel label {
  height: 38px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid #e5e0d7;
  border-radius: 8px;
  background: #fff;
}

.action-panel input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
}

.action-panel button {
  height: 38px;
  padding: 0 16px;
  border: 0;
  border-radius: 8px;
  background: #6f835f;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
  font-weight: 900;
}

.action-panel button.ghost {
  border: 1px solid #e5e0d7;
  background: #fff;
  color: #666960;
}

.wallet-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 0.32fr);
  gap: 14px;
  align-items: stretch;
}

.transactions-card {
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 14px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(170px, 0.95fr) minmax(120px, 0.7fr) minmax(120px, 0.7fr) minmax(180px, 1.25fr) auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}

.date-filter,
.custom-select,
.search-box,
.export-button {
  height: 38px;
  border: 1px solid #e4dfd5;
  border-radius: 8px;
  background: #fff;
  color: #444740;
  font-size: 12px;
}

.date-filter,
.custom-select,
.search-box {
  min-width: 0;
  position: relative;
  display: flex;
  align-items: center;
}

.date-filter {
  gap: 8px;
  padding-left: 11px;
}

.custom-select::after,
.date-filter::after {
  content: "";
  position: absolute;
  right: 12px;
  top: 50%;
  width: 7px;
  height: 7px;
  border-right: 1.7px solid #7d8179;
  border-bottom: 1.7px solid #7d8179;
  pointer-events: none;
  transform: translateY(-65%) rotate(45deg);
}

.date-filter select,
.custom-select select {
  width: 100%;
  height: 100%;
  min-width: 0;
  padding: 0 30px 0 12px;
  border: 0;
  outline: 0;
  appearance: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}

.date-filter select {
  padding-left: 0;
}

.search-box {
  padding: 0 10px;
  gap: 8px;
}

.search-box input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
}

.search-box .app-icon {
  color: #8f928a;
}

.export-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 14px;
  color: #566d4d;
  cursor: pointer;
  font-weight: 900;
}

.table-wrap {
  flex: 1;
  overflow-x: auto;
  border: 1px solid #eee9df;
  border-radius: 10px;
}

table {
  width: 100%;
  min-width: 840px;
  border-collapse: collapse;
  background: #fff;
  font-size: 12px;
}

th,
td {
  padding: 12px 11px;
  border-bottom: 1px solid #f0ece4;
  text-align: left;
  vertical-align: middle;
}

th {
  color: #63665d;
  font-size: 12px;
  font-weight: 950;
  background: #fffdfa;
}

td {
  color: #50534b;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.type-pill,
.success-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.tone-in {
  background: #edf6eb;
  color: #5f7f50;
}

.tone-out {
  background: #fff0ef;
  color: #b24a3a;
}

.tone-freeze {
  background: #fff4e3;
  color: #bd7628;
}

.tone-split {
  background: #f0edfb;
  color: #7f6dc5;
}

.success-pill {
  background: #edf6eb;
  color: #5f7f50;
}

.amount {
  font-weight: 950;
  white-space: nowrap;
}

.amount-in,
.amount-split {
  color: #d45c4d;
}

.amount-out,
.amount-freeze {
  color: #5f7f50;
}

.target,
.note {
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-button {
  border: 0;
  background: transparent;
  color: #657f55;
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
}

.table-state {
  display: grid;
  place-items: center;
  min-height: 180px;
  color: #858781;
  font-size: 13px;
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  color: #858781;
  font-size: 12px;
}

.pager {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.pager button,
.pager strong {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 1px solid #e4dfd5;
  border-radius: 8px;
  background: #fff;
  color: #697f5b;
  font-weight: 900;
}

.pager strong {
  border-color: #6f835f;
  background: #6f835f;
  color: #fff;
}

.pager button:disabled {
  opacity: 0.42;
}

.side-column {
  min-width: 0;
  display: grid;
  height: 100%;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 14px;
}

.side-card {
  padding: 17px;
}

.side-column .side-card:last-child {
  min-height: 0;
}

.side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.side-head h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 950;
}

.side-head > span {
  color: #7b8d6d;
  font-size: 12px;
  font-weight: 900;
}

.chart-range {
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  padding: 3px;
  border: 1px solid #e8e3d9;
  border-radius: 8px;
  background: #f7f5ef;
}

.chart-range button {
  min-width: 48px;
  height: 24px;
  padding: 0 8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #777a72;
  cursor: pointer;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.chart-range button.active {
  background: #fff;
  color: #6f835f;
  box-shadow: 0 6px 12px rgba(54, 48, 38, 0.08);
}

.trend-chart {
  width: 100%;
  height: auto;
  display: block;
}

.grid-lines path {
  fill: none;
  stroke: #eee9df;
  stroke-width: 1;
}

.income-line,
.expense-line {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.income-line {
  stroke: #d45c4d;
}

.expense-line {
  stroke: #6f835f;
}

.income-dot {
  fill: #d45c4d;
}

.expense-dot {
  fill: #6f835f;
}

.x-labels text {
  fill: #858781;
  font-size: 9px;
  font-weight: 800;
  text-anchor: middle;
}

.y-labels text {
  fill: #858781;
  font-size: 9px;
  font-weight: 800;
  text-anchor: end;
}

.chart-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: #858781;
  font-size: 11px;
}

.chart-total {
  margin-top: 12px;
  font-size: 12px;
}

.chart-total strong {
  color: #d45c4d;
}

.chart-total .expense {
  color: #5f7f50;
}

.info-list {
  display: grid;
  gap: 11px;
  margin: 0;
  padding: 0;
  list-style: none;
  color: #5e6159;
  font-size: 12px;
  line-height: 1.55;
}

.info-list li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
}

.info-list .app-icon {
  margin-top: 3px;
  color: #df8a2f;
}

.info-list.quiet .app-icon {
  color: #6f835f;
}

.state-card {
  min-height: 320px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #777970;
}

.state-card .app-icon {
  width: 34px;
  height: 34px;
  color: #6f835f;
}

.state-error {
  color: #b24a3a;
}

@media (max-width: 1120px) {
  .wallet-layout,
  .balance-grid {
    grid-template-columns: 1fr;
  }

  .side-column {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-template-rows: none;
  }

  .toolbar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .wallet-page {
    padding: 12px;
  }

  .action-panel,
  .toolbar,
  .side-column {
    grid-template-columns: 1fr;
    grid-template-rows: none;
  }

  .balance-card {
    grid-template-columns: auto minmax(0, 1fr);
    padding: 18px;
  }
}
</style>
