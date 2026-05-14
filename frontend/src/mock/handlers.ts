/**
 * 文件说明：
 * 这是前端 Mock 启动入口。
 * 目前只保留一个可开关的占位实现，避免 A 同学在后端未完成前被阻塞。
 * 真正的 handler 细节后续按冻结 API 规范补齐。
 */
import { appEnv } from "@/utils/env";

export async function maybeEnableMocking() {
  if (!appEnv.enableMsw) return;
  // 这里先占位，后续由 A 同学补充 worker 与 handlers 细节。
}

