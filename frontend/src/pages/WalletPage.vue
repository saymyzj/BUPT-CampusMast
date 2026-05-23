<template>
  <div class="page-root">
    <section class="page-container">
      <div class="page-header">
        <h1 class="page-title">钱包</h1>
        <p class="page-subtitle">管理余额与查看资金流水</p>
      </div>

      <div v-if="loading" class="state-box">加载中...</div>
      <div v-else-if="error" class="state-box state-error">{{ error }}</div>
      <template v-else>
        <div class="balance-row">
          <div class="balance-card">
            <p class="balance-label">可用余额</p>
            <p class="balance-value">{{ wallet.available }}</p>
            <p class="balance-unit">元</p>
          </div>
          <div class="balance-card">
            <p class="balance-label">冻结余额</p>
            <p class="balance-value balance-frozen">{{ wallet.frozen }}</p>
            <p class="balance-unit">元</p>
          </div>
          <div class="balance-card">
            <p class="balance-label">总余额</p>
            <p class="balance-value balance-total">{{ wallet.total }}</p>
            <p class="balance-unit">元</p>
          </div>
        </div>

        <div class="action-row">
          <div class="action-card">
            <input v-model="topUpAmount" type="number" class="form-input" placeholder="充值金额" min="0.01" step="0.01" />
            <button class="btn btn-primary" :disabled="topUpLoading" @click="handleTopUp">{{ topUpLoading ? '处理中...' : '模拟充值' }}</button>
            <p v-if="actionMsg" class="action-msg">{{ actionMsg }}</p>
          </div>
          <div class="action-card">
            <input v-model="withdrawAmount" type="number" class="form-input" placeholder="提现金额" min="0.01" step="0.01" />
            <button class="btn btn-secondary" :disabled="withdrawLoading" @click="handleWithdraw">{{ withdrawLoading ? '处理中...' : '模拟提现' }}</button>
          </div>
        </div>

        <div class="tx-section">
          <h3 class="section-title">资金流水</h3>
          <div v-if="txLoading" class="state-box">加载中...</div>
          <div v-else-if="transactions.length === 0" class="state-box">暂无流水</div>
          <div v-else class="tx-list">
            <div v-for="tx in transactions" :key="tx.id" class="tx-item">
              <div>
                <span class="tx-type" :class="`tx-${txTypeClass(tx.type)}`">{{ txTypeLabel(tx.type) }}</span>
                <span class="tx-desc">{{ tx.description }}</span>
              </div>
              <div class="tx-right">
                <span class="tx-amount">{{ tx.amount }}</span>
                <span class="tx-time">{{ formatTime(tx.createdAt) }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getWalletBalance, listWalletTransactions, topUpWallet, withdrawWallet } from "@/api/modules/wallet";
import type { Wallet, Transaction, TransactionType } from "@/types/api";

const wallet = ref<Wallet>({ available: "--", frozen: "--", total: "--" });
const transactions = ref<Transaction[]>([]);
const loading = ref(false); const error = ref(""); const txLoading = ref(false);
const topUpAmount = ref(""); const withdrawAmount = ref("");
const topUpLoading = ref(false); const withdrawLoading = ref(false);
const actionMsg = ref("");

const L: Record<string, string> = { TOP_UP: "充值", WITHDRAW: "提现", FREEZE: "冻结", UNFREEZE: "解冻", SETTLE_OUT: "支出", SETTLE_IN: "收入", SETTLE_SPLIT: "拆分" };
function txTypeLabel(t: TransactionType) { return L[t] ?? t; }
function txTypeClass(t: TransactionType) { if (t === "TOP_UP" || t === "UNFREEZE" || t === "SETTLE_IN") return "in"; if (t === "SETTLE_SPLIT") return "split"; return "out"; }
function formatTime(iso: string) { return new Date(iso).toLocaleString("zh-CN"); }

async function loadData() {
  loading.value = true; error.value = "";
  try { wallet.value = await getWalletBalance(); } catch (err: any) { error.value = "加载钱包失败"; return; } finally { loading.value = false; }
  await loadTx();
}
async function loadTx() {
  txLoading.value = true;
  try { transactions.value = (await listWalletTransactions({ page: 1, limit: 20 })).data; } catch { /* */ } finally { txLoading.value = false; }
}
async function handleTopUp() {
  if (!topUpAmount.value) return; topUpLoading.value = true; actionMsg.value = "";
  try { wallet.value = await topUpWallet({ amount: parseFloat(topUpAmount.value).toFixed(2) }); actionMsg.value = "充值成功"; topUpAmount.value = ""; await loadTx(); } catch (err: any) { actionMsg.value = err?.response?.data?.error?.message || "充值失败"; } finally { topUpLoading.value = false; }
}
async function handleWithdraw() {
  if (!withdrawAmount.value) return; withdrawLoading.value = true; actionMsg.value = "";
  try { wallet.value = await withdrawWallet({ amount: parseFloat(withdrawAmount.value).toFixed(2) }); actionMsg.value = "提现成功"; withdrawAmount.value = ""; await loadTx(); } catch (err: any) { actionMsg.value = err?.response?.data?.error?.message || "提现失败"; } finally { withdrawLoading.value = false; }
}
onMounted(loadData);
</script>

<style scoped>
.page-root {
  --blue-500: #2556a8; --blue-600: #1f478c; --blue-50: #edf3fb;
  --red-500: #b24a3a; --green-500: #2f7a41; --orange-500: #c67f2f; --purple-500: #7c3aed;
  --gray-50: #f6f1e6; --gray-100: #ece3d2; --gray-300: #b9ad95; --gray-600: #50493f; --gray-800: #202735;
  --bg-start: #fbf7ef; --bg-end: #efe6d6;
  --shadow-sm: 0 2px 6px rgba(23,29,40,0.04); --shadow-md: 0 8px 20px rgba(23,29,40,0.07);
  --shadow-lg: 0 14px 32px rgba(23,29,40,0.10);
  --radius-sm: 6px; --radius: 10px; --radius-lg: 16px;
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
.page-container { position: relative; z-index: 1; padding: 40px 20px; max-width: 860px; margin: 0 auto; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 32px; font-weight: 700; color: var(--gray-800); font-family: 'Nunito','Noto Sans SC',sans-serif; }
.page-subtitle { font-size: 15px; color: var(--gray-600); margin-top: 6px; }
.state-box { text-align: center; padding: 80px 20px; color: var(--gray-600); font-size: 15px; }
.state-error { color: var(--red-500); background: #fff5f5; border-radius: var(--radius-lg); }

.balance-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px; }
@media (max-width: 540px) { .balance-row { grid-template-columns: 1fr; } }
.balance-card { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-sm); text-align: center; }
.balance-label { font-size: 13px; color: var(--gray-600); margin-bottom: 8px; }
.balance-value { font-size: 36px; font-weight: 700; color: var(--blue-500); font-family: 'Nunito',sans-serif; }
.balance-frozen { color: var(--orange-500); }
.balance-total { color: var(--blue-600); }
.balance-unit { font-size: 13px; color: var(--gray-600); margin-top: 2px; }

.action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 32px; }
@media (max-width: 540px) { .action-row { grid-template-columns: 1fr; } }
.action-card { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-sm); display: flex; flex-direction: column; gap: 10px; }
.form-input { padding: 10px 14px; font-size: 14px; border: 1px solid var(--gray-100); border-radius: var(--radius); background: #fff; color: var(--gray-800); }
.form-input:focus { outline: none; border-color: var(--blue-500); }
.btn { padding: 10px 20px; font-size: 14px; font-weight: 600; border-radius: var(--radius); cursor: pointer; border: none; transition: all 0.25s; }
.btn:hover { transform: translateY(-1px); }
.btn-primary { background: var(--blue-500); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--blue-600); box-shadow: 0 6px 16px rgba(37,86,168,0.25); }
.btn-primary:disabled { background: var(--gray-300); cursor: not-allowed; }
.btn-secondary { background: #fff; color: var(--blue-500); border: 1px solid var(--blue-500); }
.btn-secondary:hover:not(:disabled) { background: var(--blue-50); box-shadow: 0 6px 16px rgba(37,86,168,0.1); }
.btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
.action-msg { font-size: 13px; color: var(--green-500); }

.tx-section { background: #faf7f1; border: 1px solid rgba(31,42,58,0.04); border-radius: var(--radius-lg); padding: 24px; box-shadow: var(--shadow-md); }
.section-title { font-size: 16px; font-weight: 600; color: var(--gray-800); margin-bottom: 16px; }
.tx-list { display: flex; flex-direction: column; }
.tx-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--gray-100); font-size: 13px; }
.tx-item:last-child { border-bottom: none; }
.tx-type { padding: 2px 8px; border-radius: var(--radius-sm); font-size: 11px; font-weight: 600; margin-right: 8px; }
.tx-in { background: #dbeafe; color: #1e40af; }
.tx-out { background: #fee2e2; color: #991b1b; }
.tx-split { background: #ede9fe; color: #6b21a8; }
.tx-desc { color: var(--gray-600); }
.tx-right { text-align: right; }
.tx-amount { font-weight: 600; display: block; color: var(--gray-800); }
.tx-time { font-size: 11px; color: var(--gray-600); }
</style>
