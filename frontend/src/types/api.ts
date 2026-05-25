// ===== 枚举 =====
export type Role = "USER" | "ADMIN";

export type TaskStatus =
  | "PENDING"
  | "IN_PROGRESS"
  | "PENDING_REVIEW"
  | "COMPLETED"
  | "DISPUTED"
  | "CANCELLED"
  | "EXPIRED"
  | "CLOSED_BY_ADMIN";

export type TaskCategory = "package" | "food" | "move" | "other";

export type TransactionType =
  | "TOP_UP"
  | "WITHDRAW"
  | "FREEZE"
  | "UNFREEZE"
  | "SETTLE_OUT"
  | "SETTLE_IN"
  | "SETTLE_SPLIT";

export type ModerationResult = "ALLOW" | "REVIEW" | "BLOCK";

export type AdminReviewStatus = "PENDING" | "APPROVED" | "REJECTED";

export type HomepageBlockType = "ANNOUNCEMENT" | "BANNER" | "RECOMMEND_SLOT";

export type NotificationType =
  | "TASK_ACCEPTED"
  | "TASK_SUBMITTED"
  | "TASK_CONFIRMED"
  | "TASK_REJECTED"
  | "TASK_CANCELLED"
  | "TASK_DISPUTED"
  | "DISPUTE_RESOLVED"
  | "CHAT_MESSAGE"
  | "CHAT_READ"
  | "SYSTEM_NOTICE"
  | "MODERATION_REVIEW";

export type ChatMessageType = "TEXT";

// ===== 通用响应 =====
export interface SuccessResponse<T> {
  success: true;
  data: T;
  meta?: PaginationMeta | null;
}

export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  };
}

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  unreadCount?: number;
}

// ===== 认证相关 =====
export interface AuthRegisterRequest {
  studentEmail: string;
  password: string;
  nickname: string;
}

export interface AuthLoginRequest {
  studentEmail: string;
  password: string;
}

export interface TokenRefreshRequest {
  refreshToken: string;
}

export interface AuthPayload {
  accessToken: string;
  refreshToken: string;
  user: User;
}

export interface User {
  id: string;
  studentEmail: string;
  nickname: string;
  role: Role;
  phone?: string | null;
  requesterCreditScore: number;
  helperCreditScore: number;
  overallCreditScore: number;
  isActive?: boolean;
  avatarUrl?: string | null;
  defaultBuildingCode?: string | null;
}

export interface UserUpdateRequest {
  nickname?: string;
  phone?: string | null;
  avatarUrl?: string | null;
  defaultBuildingCode?: string | null;
}

export interface UserSummary {
  id: string;
  nickname: string;
  overallCreditScore: number;
}

export interface UserPublicProfile {
  id: string;
  nickname: string;
  role: Role;
  phone?: string | null;
  avatarUrl?: string | null;
  requesterCreditScore: number;
  helperCreditScore: number;
  overallCreditScore: number;
}

// ===== 任务相关 =====
export interface CreateTaskRequest {
  title: string;
  description: string;
  category: TaskCategory;
  reward: string;
  deadline: string;
  buildingCode?: string;
  latitude?: number;
  longitude?: number;
  locationDetail?: string;
  imageUrls?: string[];
}

export interface SubmitTaskProofRequest {
  proofNote?: string;
  proofImageUrls?: string[];
}

export interface RejectTaskRequest {
  reason: string;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  category: TaskCategory;
  reward: string;
  status: TaskStatus;
  buildingCode: string;
  latitude?: number | null;
  longitude?: number | null;
  locationDetail?: string | null;
  deadline: string;
  imageUrls: string[];
  requester: UserSummary;
  helper?: UserSummary | null;
  moderationResult: ModerationResult;
  needsAdminReview: boolean;
  createdAt: string;
}

export interface TaskLog {
  id: string;
  fromStatus: TaskStatus;
  toStatus: TaskStatus;
  actorId: string;
  remark?: string | null;
  createdAt: string;
}

export interface TaskDetail extends Task {
  proofNote?: string | null;
  proofImageUrls: string[];
  logs: TaskLog[];
}

export interface TaskListParams {
  page?: number;
  limit?: number;
  category?: TaskCategory;
  keyword?: string;
  buildingCode?: string;
  nearBuildingCode?: string;
  sortBy?: "newest" | "rewardDesc" | "rewardAsc" | "deadlineAsc" | "distanceAsc";
}

// ===== 信用与评价 =====
export interface RateTaskPartnerRequest {
  score: number;
  comment?: string;
}

export interface Rating {
  id: string;
  taskId: string;
  fromUserId: string;
  toUserId: string;
  score: number;
  comment?: string | null;
  createdAt: string;
}

export interface CreditProfile {
  requesterCreditScore: number;
  helperCreditScore: number;
  overallCreditScore: number;
  ratingCount: number;
  averageRating: number;
}

// ===== 钱包相关 =====
export interface TopUpRequest {
  amount: string;
}

export interface WithdrawRequest {
  amount: string;
}

export interface Wallet {
  available: string;
  frozen: string;
  total: string;
}

export interface Transaction {
  id: string;
  type: TransactionType;
  amount: string;
  balanceAfter: string;
  relatedTaskId?: string | null;
  description: string;
  createdAt: string;
}

// ===== 通知相关 =====
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  relatedTaskId?: string | null;
  isRead: boolean;
  createdAt: string;
}

// ===== 聊天相关 =====
export interface ChatConversation {
  id: string;
  taskId: string;
  unreadCount: number;
  taskStatus?: string | null;
  latestMessage?: ChatMessage | null;
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  taskId: string;
  senderId: string;
  content: string;
  createdAt: string;
}

export interface SendChatMessageRequest {
  clientMessageId?: string;
  content: string;
}

export interface MarkConversationReadRequest {
  lastReadMessageId?: string;
}

// ===== 地图相关 =====
export interface CampusBuilding {
  code: string;
  osmType?: string | null;
  osmId?: string | null;
  name: string;
  campusZone: string | null;
  latitude: number;
  longitude: number;
  polygon?: number[][] | number[][][] | null;
}

export interface NearbyTask extends Task {
  distanceScore: number;
}

// ===== 推荐相关 =====
export interface RecommendationItem {
  task: Task;
  scoreTotal: number;
  scoreCategory: number;
  scoreDistance: number;
  scoreSuccessRate: number;
  scoreActiveTime: number;
}

// ===== 审核相关 =====
export interface ModerationRecord {
  id: string;
  taskId?: string | null;
  userId: string;
  provider: string;
  riskLevel: ModerationResult;
  hitTags: string[];
  adminReviewStatus: AdminReviewStatus;
  adminReviewNote?: string | null;
  createdAt: string;
}

// ===== 管理后台 =====
export interface AdminUpdateUserRequest {
  isActive?: boolean;
  requesterCreditScore?: number;
  helperCreditScore?: number;
}

export interface AdminResolveDisputeRequest {
  resolution: "refund" | "settle" | "split" | "close";
  splitRatio?: number;
  note: string;
}

export interface AdminReviewModerationRequest {
  decision: "approve" | "reject";
  note?: string;
}

export interface AdminUpdateConfigRequest {
  configValue: Record<string, unknown>;
  configGroup?: string;
  description?: string | null;
}

// ===== 系统配置 =====
export interface ConfigItem {
  configKey: string;
  configGroup: string;
  configValue: Record<string, unknown>;
  description: string;
  updatedAt: string;
}

export interface HomepageBlock {
  id: string;
  blockType: HomepageBlockType;
  title: string;
  content: Record<string, unknown>;
  sortOrder: number;
  isActive: boolean;
  updatedAt: string;
}

export interface HomepageBlockUpsert {
  blockType: HomepageBlockType;
  title: string;
  content: Record<string, unknown>;
  sortOrder?: number;
  isActive?: boolean;
}

// ===== 上传 =====
export interface UploadImageData {
  fileKey: string;
  fileUrl: string;
}
