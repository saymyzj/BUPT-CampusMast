# 地图页面实现说明（面向成员 A）

> 日期：2026-04-15
> 目标读者：成员 A（前端工程主责）
> 目标：说明当前地图页已经如何实现、为何这样实现、你后续如何接 API 与扩展

---

## 1. 当前实现目标（Route A）

地图页当前是 Route A 基线，核心思路是：

- 底图使用 OSM 瓦片（真实地图）
- 楼宇覆盖层使用经纬度中心点与可选多边形
- 任务点常驻信息收敛成极短标签，详情通过 hover/click popup 展开
- 楼宇详情通过右侧楼层面板展示，不做房间级真实导航

这套方案满足“可联调 + 可扩展 + 可维护”，且与冻结文档口径一致。

---

## 2. 文件结构与职责拆分

### 2.1 页面装配层

- frontend/src/pages/CampusMapPage.vue

职责：

- 固定左右布局（左侧控制面板 + 右侧地图容器）
- 装配楼宇层、任务层、楼宇信息卡
- 监听 Escape 键统一清空选中状态

### 2.2 地图容器与上下文

- frontend/src/components/map/MapContainer.vue
- frontend/src/composables/useLeafletMap.ts

职责：

- 创建 Leaflet map 实例并通过 provide/inject 下发上下文
- 加载 OSM tile layer
- 通过校园边界 + 可视区扩展逻辑控制拖拽边界（防止拖离校园核心区域）
- 提供 toLatLng/projectToViewport 等通用坐标能力

### 2.3 数据层（当前为前端本地基线）

- frontend/src/data/buildings.ts
- frontend/src/data/taskPins.ts
- frontend/src/data/mapConfig.ts
- frontend/src/types/map.ts

职责：

- buildings：楼宇中心点、可选 polygon、楼层信息
- taskPins：任务点经纬度、摘要、奖励、动作文案
- mapConfig：地图缩放级别、校园边界、tile 源
- types：地图域模型、分类颜色、筛选类型

### 2.4 状态层

- frontend/src/stores/map.ts

职责：

- 管理筛选状态 activeFilter
- 管理 activeTaskId / activeBuildingId
- 计算 visiblePins
- 提供 clear/open/close/show 等统一行为

### 2.5 渲染层

- frontend/src/components/map/BuildingLayer.vue
- frontend/src/components/map/TaskBeaconLayer.vue
- frontend/src/components/map/BuildingInfoCard.vue
- frontend/src/components/map/MapHUD.vue
- frontend/src/components/map/MapLegend.vue
- frontend/src/components/map/PostTaskFAB.vue

职责：

- BuildingLayer：楼宇 polygon 或 circleMarker 渲染、hover 高亮、click 打开楼宇面板
- TaskBeaconLayer：任务 pulse + core marker 渲染、常驻短标签、自适应 popup
- BuildingInfoCard：右侧楼层面板、楼层 tab、POI 信息展示
- MapHUD/Legend/FAB：筛选、统计、图例、操作入口

---

## 3. 关键交互实现细节

### 3.1 楼宇交互

在 BuildingLayer 内分两种渲染路径：

- 有 polygon：直接渲染多边形，hover 时提升边框/填充权重
- 无 polygon：回退到中心点圆标记

点击任一楼宇元素后：

- 调用 mapStore.openBuilding(id)
- 关闭任务态，打开楼宇态
- 右侧 BuildingInfoCard 根据 activeBuildingId 渲染楼层内容

### 3.2 任务交互

在 TaskBeaconLayer 中每个任务点由两层组成：

- pulse 圆环：营造“可交互任务点”的动态提醒
- core marker：真实交互节点，绑定 tooltip 和 popup

tooltip：

- 永久显示 shortLabel
- 控制长度避免地图拥挤

popup：

- hover/click 打开
- 内容由 buildPopupHtml 动态生成
- 提供“打开楼宇信息”和“关闭”动作

### 3.3 Popup 自适应方位算法

TaskBeaconLayer 实现了较完整的方位适配：

- 根据 marker 在容器中的坐标判断是否靠近四边/四角
- 给出优先候选方位序列（top/right/bottom/left + 四角）
- 先尝试找到完全不溢出的方位
- 若都溢出，则选择总溢出最小的方位
- 根据最终方位同步 offset 与 tip 形状 class

效果：

- 边缘任务点也能稳定展示 popup
- 减少被裁切或遮挡
- 移动地图/缩放后可重新计算方位，维持可读性

### 3.4 状态互斥规则

当前状态机是“轻互斥”：

- 展开任务详情时清空楼宇态
- 打开楼宇面板时清空任务态
- 点击地图空白或按 Esc 清空全部态

这样能避免信息面板叠加冲突。

---

## 4. 与冻结文档的对齐点

已对齐：

- 地图字段语义：latitude / longitude / polygon
- Route A 底图路线：Leaflet + OSM
- v1 不做真实路径导航，仅做楼宇/任务覆盖层与附近任务表达

这保证了 A 在后续工程化接 API 时不需要改页面交互范式。

---

## 5. 你后续接后端 API 的建议步骤

### 5.1 先替换数据源，不先改 UI

优先把本地静态数据替换为接口数据：

- GET /api/map/buildings -> buildings
- GET /api/map/tasks/nearby -> taskPins（或列表映射）

建议在 map store 新增数据拉取 action：

- loadBuildings()
- loadNearbyTasks(buildingCode?, limit?)

保持组件层只消费 store，减少渲染层改动。

### 5.2 做字段映射适配层

因为现有组件字段较丰富，建议增加 mapper：

- mapApiBuildingToViewModel
- mapApiTaskToPin

把 API 原始字段与 UI 展示字段解耦，避免后端字段微调导致组件大面积改动。

### 5.3 再接真实动作

在 popup 按钮与 FAB 上逐步接入：

- 进入任务详情页
- 发起接单
- 打开发布任务页

当前组件结构已经支持替换按钮行为，不需要重写弹层。

---

## 6. 已知限制与扩展建议

已知限制：

- 当前是单页固定布局，移动端手势与布局尚未专项优化
- taskPins 仍是示例数据，未做大规模点位聚合
- 图书馆等个别楼宇暂时只有中心点，后续可补 polygon

扩展建议：

1. 点位增多后可引入 marker cluster 或网格聚合
2. 将楼层卡片数据从 buildings.ts 抽到独立配置或后端接口
3. 在 store 中加入加载态和错误态，便于联调期间容错
4. 给 popup 增加键盘可达性（可访问性增强）

---

## 7. 对成员 A 的结论

你现在可以把地图页当作“交互框架已稳定、数据源待替换”的状态来推进：

- 页面结构、交互闭环、层级拆分都可继续沿用
- 优先做 store + API 适配层改造
- 组件层保持最小改动即可进入联调

如果后续你希望，我可以再补一版“从本地数据切到 API 的最小改造 PR 清单”，按文件逐个列出改动点。