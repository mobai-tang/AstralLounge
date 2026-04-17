# Bug 记录

本文档记录当前项目中已确认的 bug，来源于一次针对前后端联调、类型检查与运行路径的排查。

## 1. ChatView 置顶按钮运行时报错

- 严重级别: `P1`
- 文件: `frontend/src/views/ChatView.vue:347-348`
- 问题说明:
  `togglePin()` 中调用的是 `_togglePinSession`，但 store 解构出来的实际名称是 `_togglePin`。点击置顶按钮时会触发 `ReferenceError`，导致置顶功能失效。
- 影响:
  会话置顶/取消置顶无法正常使用。

## 2. 群聊前后端响应格式不一致

- 严重级别: `P1`
- 文件: `frontend/src/views/GroupChatView.vue:509-523`
- 问题说明:
  前端向 `/api/group-chat/{id}/messages` 发送请求后，直接用 `await res.json()` 读取并期望得到 `CharacterMessage[]`。但后端实际返回的是 `StreamingResponse`，内容是类似 `[角色]:内容` 的纯文本流。
- 影响:
  群聊消息解析失败，角色回复无法正常显示。

## 3. Lorebook 保存字段名与后端接口不匹配

- 严重级别: `P1`
- 文件: `frontend/src/components/LorebookManager.vue:264-289`
- 问题说明:
  前端提交的是 `scanDepth`、`contextLength`、`insertMode`、`maxRecursion`，而后端 Pydantic 模型接受的是 `scan_depth`、`context_length`、`insert_mode`、`max_recursion`。
- 影响:
  世界书相关设置在保存时会被忽略、重置或部分失效。

## 4. 后端创建 Lorebook 时未持久化 `max_recursion`

- 严重级别: `P1`
- 文件: `backend/api/routes/lorebooks.py:115-126`
- 问题说明:
  `create_lorebook()` 虽然接收 `max_recursion`，但在创建 `LorebookModel(...)` 时没有传入该字段。
- 影响:
  新建世界书时递归深度配置会丢失，前端看起来可编辑，但保存后不生效。

## 5. Memory 类型定义与页面/接口契约脱节

- 严重级别: `P1`
- 文件: `frontend/src/types/index.ts:83-95`
- 问题说明:
  `Memory.source` 目前只允许 `'auto' | 'manual'`，但页面逻辑已经在处理 `'summarized'`。同时类型中也缺少 `relatedMemories`，而记忆详情弹窗已经在读取该字段。
- 影响:
  记忆页面、类型系统与后端接口出现漂移，容易引发构建失败、运行时判断错误或 UI 显示异常。

## 6. API helper 调用 `request()` 参数顺序错误

- 严重级别: `P2`
- 文件: `frontend/src/utils/api.ts:156-158`
- 问题说明:
  `request()` 的签名是 `(method, path, options)`，但 `getGroupChatMessages()` 只传入了路径字符串，导致调用方式错误。
- 影响:
  该 helper 无法正确工作，也会直接引发 TypeScript 报错。

## 7. i18n 初始化使用了当前版本未导出的类型

- 严重级别: `P2`
- 文件: `frontend/src/plugins/i18n.ts:5-12`
- 问题说明:
  当前安装的 `vue-i18n` 版本并没有从包根导出 `MessageSchema`，但代码中直接进行了导入。
- 影响:
  `vue-tsc` 和前端构建会失败，属于明确的编译阻塞问题。

## 8. 其他已发现的类型检查报错

以下问题来自 `frontend` 目录下执行 `npm run type-check` 的结果。这些报错未必都已经单独定位为业务 bug，但目前都属于待修复项，会影响构建、联调或后续开发。

### 8.1 GitUpdatePanel 空值判断不充分

- 文件: `frontend/src/components/GitUpdatePanel.vue:98`
- 报错:
  `TS18047: 'updateInfo.value' is possibly 'null'.`
- 说明:
  更新提示逻辑里直接读取了 `updateInfo.value.hasUpdate`，但 TS 认为这里仍可能为空。

### 8.2 LorebookManager 表单类型过窄

- 文件: `frontend/src/components/LorebookManager.vue:264-275`
- 报错:
  - `TS2322: Property 'maxRecursion' is missing ...`
  - `TS2322: Type '"append" | "insert" | "prioritize"' is not assignable to type '"append"'`
- 说明:
  当前 `bookForm` 推断出的类型过于收窄，导致编辑态和新建态之间的字段结构不一致。

### 8.3 SettingsModal 安全词数组可能为 `undefined`

- 文件: `frontend/src/components/SettingsModal.vue:258-266`
- 报错:
  - `TS2532: Object is possibly 'undefined'.`
- 说明:
  `settings.safety[type]` 在添加、删除词条时被认为可能不存在，说明初始化类型和使用方式没有完全对齐。

### 8.4 ChatView 中 ref/computed 使用方式混乱

- 文件: `frontend/src/views/ChatView.vue:301-306`
- 报错:
  - `TS2769: No overload matches this call.`
  - `TS18047: 'ghostPendingMessage' is possibly 'null'.`
  - `TS2551: Property 'value' does not exist on type 'string'.`
- 说明:
  `watch(ghostPendingMessage, ...)` 和回调里的访问方式混用了 ref 值与解包后的值，导致监听逻辑类型不一致。

### 8.5 ChatView 中 `currentSession` 被当成 ref 使用

- 文件: `frontend/src/views/ChatView.vue:366-384`
- 报错:
  - `TS18047: 'currentSession' is possibly 'null'.`
  - `TS2339: Property 'value' does not exist on type ...`
- 说明:
  从 Pinia store 解构出来的 `currentSession` 是自动解包后的响应式值，但组件里仍按 `currentSession.value` 访问，造成多处类型错误，也说明这里的状态访问方式需要统一。

### 8.6 GroupChatView 消息类型缺少 `characterName`

- 文件: `frontend/src/views/GroupChatView.vue:106`
- 报错:
  `TS2339: Property 'characterName' does not exist on type ...`
- 说明:
  模板中显示了 `msg.characterName`，但共享消息类型 `CharacterMessage` 没有该字段定义。

### 8.7 GroupChatView 模板里 `selectedGroup` 可能为空

- 文件: `frontend/src/views/GroupChatView.vue:313, 323`
- 报错:
  - `TS18047: '__VLS_ctx.selectedGroup' is possibly 'null'.`
- 说明:
  统计弹窗中直接读取 `selectedGroup.members`，但模板类型系统认为这里仍可能为空。

### 8.8 MemoryView 中 `summarized` 与现有类型不兼容

- 文件: `frontend/src/views/MemoryView.vue:121, 422, 467`
- 报错:
  - `TS2367: This comparison appears to be unintentional because the types '"manual" | undefined' and '"summarized"' have no overlap.`
  - `TS2367: This comparison appears to be unintentional because the types '"auto" | "manual" | undefined' and '"summarized"' have no overlap.`
- 说明:
  页面已经处理 `summarized`，但 `Memory.source` 类型没更新，和第 5 条属于同一问题链。

### 8.9 MemoryView 访问了未声明的 `relatedMemories`

- 文件: `frontend/src/views/MemoryView.vue:226, 229`
- 报错:
  - `TS2339: Property 'relatedMemories' does not exist on type ...`
- 说明:
  详情弹窗中展示关联记忆，但基础类型未包含该字段。

### 8.10 MemoryView 将可能为 `null` 的对象传入详情编辑流程

- 文件: `frontend/src/views/MemoryView.vue:238`
- 报错:
  `TS2345: Argument of type ... is not assignable to parameter of type 'Memory'. Type 'null' is not assignable to type 'Memory'.`
- 说明:
  说明 `viewingMemory` 的空值分支没有被完全收窄。

### 8.11 MemoryView 中布尔值存在 `undefined` 风险

- 文件: `frontend/src/views/MemoryView.vue:515`
- 报错:
  `TS2322: Type 'boolean | undefined' is not assignable to type 'boolean'.`
- 说明:
  某个布尔状态或组件绑定值没有做默认值兜底。

## 9. 当前检查结果摘要

- 已重新执行命令: `frontend/npm run type-check`
- 当前结果:
  前端类型检查仍失败，除上面 7 个已重点确认的问题外，还存在一批空值处理、类型定义漂移、Pinia 解构使用方式不一致等问题。
- 建议:
  可以先优先修复 `ChatView`、`GroupChatView`、`LorebookManager`、`Memory` 类型定义这几块，它们既能消掉报错，也最可能对应真实功能异常。

## 备注

- 当前这些问题中，`P1` 优先级更高，建议优先修复会直接影响功能或数据保存的项。
- `P2` 问题虽然相对次一级，但会影响构建稳定性和后续开发效率，也建议尽快处理。
