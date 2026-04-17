/**
 * AstralLounge 全局 TypeScript 类型定义
 */

// ============ 角色相关 ============
export interface Character {
  id: string
  name: string
  description?: string
  personality?: string
  scenario?: string
  greeting?: string
  avatar?: string
  tags?: string[]
  examples?: string[]
  createdAt?: number
  updatedAt?: number
}

export interface CharacterMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  characterId?: string
  timestamp?: number
}

// ============ 对话相关 ============
export interface ChatSession {
  id: string
  name: string
  characterId?: string
  characterName?: string
  messages: CharacterMessage[]
  createdAt: number
  updatedAt: number
  pinned?: boolean
  groupId?: string
  model?: string
  temperature?: number
  maxTokens?: number
  tokenCount?: number
}

export interface Group {
  id: string
  name: string
  color?: string
  createdAt: number
}

// ============ 世界设定相关 ============
export interface LorebookEntry {
  id: string
  name: string
  content: string
  keywords: string[]
  priority: number
  enabled: boolean
  createdAt?: number
  updatedAt?: number
}

export interface Lorebook {
  id: string
  name: string
  description?: string
  scanDepth?: number
  contextLength?: number
  insertMode?: 'append' | 'insert' | 'prioritize'
  forceActivation?: boolean
  entries: LorebookEntry[]
  createdAt?: number
  updatedAt?: number
}

// ============ 记忆相关 ============
export interface Memory {
  id: string
  title?: string
  content: string
  category?: string
  tags?: string[]
  importance?: number
  source?: 'auto' | 'manual'
  accessCount?: number
  createdAt?: number
  updatedAt?: number
  lastAccessedAt?: number
}

// ============ 插件相关 ============
export interface Plugin {
  id: string
  name: string
  displayName?: string
  version?: string
  author?: string
  description?: string
  category?: string
  enabled?: boolean
  installed?: boolean
  entry?: string
  settings?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

export interface Skill {
  id: string
  name: string
  description?: string
  enabled?: boolean
  path?: string
}

// ============ 设置相关 ============
export interface ModelSettings {
  provider: string
  model_name: string
  api_url: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  presence_penalty?: number
  frequency_penalty?: number
  stream?: boolean
}

export interface TTSSettings {
  enabled: boolean
  provider?: string
  cosyvoice_url?: string
  gptsovits_url?: string
  default_voice?: string
  speech_speed?: number
}

export interface UISettings {
  theme?: 'dark' | 'light' | 'auto'
  accent_color?: string
  typing_effect?: boolean
  stream_response?: boolean
  compact_mode?: boolean
  language?: string
}

export interface SafetySettings {
  enabled: boolean
  block_enabled?: boolean
  log_enabled?: boolean
  sensitive_action?: 'block' | 'warn' | 'ignore'
  blocked_words?: string[]
  sensitive_words?: string[]
}

// ============ 通知相关 ============
export interface Notification {
  id: string
  title: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'error'
  read?: boolean
  timestamp: number
}

// ============ Toast 相关 ============
export interface Toast {
  id: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  duration?: number
}

// ============ API 响应 ============
export interface ApiResponse<T = unknown> {
  success?: boolean
  data?: T
  error?: string
  message?: string
}

// ============ 组件 Props 类型 ============
export type ComponentSize = 'sm' | 'md' | 'lg'
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
