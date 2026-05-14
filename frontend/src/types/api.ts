/**
 * 文件说明：
 * 这是前端最小 API 类型定义文件。
 * 当前先覆盖公共响应、用户、任务和钱包等基础类型，A 同学后续应继续按冻结
 * OpenAPI 文档补齐聊天、地图、推荐和后台配置类型。
 */
export interface SuccessResponse<T> {
  success: true;
  data: T;
  meta?: Record<string, unknown> | null;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  };
}

export interface UserSummary {
  id: string;
  nickname: string;
  overallCreditScore: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  reward: string;
  buildingCode: string;
  requester: UserSummary;
}

