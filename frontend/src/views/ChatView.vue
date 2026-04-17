<template>
  <div class="chat-view">
    <!-- 左侧会话列表 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="btn btn-primary btn-sm" @click="createSession">+ {{ $t('chat.newSession') }}</button>
        <div class="sidebar-actions">
          <button class="btn btn-ghost btn-icon" @click="showGroups = !showGroups" :title="$t('chat.groups')">
            📁
          </button>
        </div>
      </div>

      <!-- 分组选择 -->
      <div v-if="showGroups" class="groups-bar">
        <div class="group-chip" :class="{ active: !selectedGroupId }" @click="selectedGroupId = null">
          {{ $t('chat.allSessions') }}
        </div>
        <div
          v-for="g in groups"
          :key="g.id"
          :class="['group-chip', { active: selectedGroupId === g.id }]"
          @click="selectedGroupId = g.id"
          :style="{ borderColor: g.color || 'var(--border-color)' }"
        >
          {{ g.name }}
        </div>
        <button class="btn btn-ghost btn-sm" @click="showCreateGroup = true">+ {{ $t('chat.createGroup') }}</button>
      </div>

      <!-- 搜索 -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input v-model="searchQuery" class="input" :placeholder="$t('chat.search')" />
      </div>

      <!-- 会话列表 -->
      <div class="sessions-list">
        <div
          v-for="session in filteredSessions"
          :key="session.id"
          :class="['session-item', { active: currentSessionId === session.id, pinned: session.pinned }]"
          @click="switchSession(session.id)"
        >
          <div class="session-avatar">
            <img v-if="session.characterId" :src="`/api/characters/${session.characterId}/avatar`" />
            <span v-else>💬</span>
          </div>
          <div class="session-info">
            <div class="session-name">
              <span v-if="session.pinned" class="pin-icon">📌</span>
              {{ session.name }}
            </div>
            <div class="session-meta">
              {{ session.characterName || $t('chat.noCharacter') }}
              <span v-if="session.tokenCount"> · {{ session.tokenCount }} tokens</span>
            </div>
          </div>
          <div class="session-actions">
            <button class="btn btn-ghost btn-icon btn-sm" @click.stop="togglePin(session.id)" :title="session.pinned ? $t('chat.unpinned') : $t('chat.pinned')">
              {{ session.pinned ? '📌' : '○' }}
            </button>
            <button class="btn btn-ghost btn-icon btn-sm" @click.stop="renameSession(session)" :title="$t('chat.rename')">✏️</button>
            <button class="btn btn-ghost btn-icon btn-sm" @click.stop="deleteSession(session.id)" :title="$t('chat.delete')">🗑️</button>
          </div>
        </div>

        <div v-if="filteredSessions.length === 0" class="empty-sessions">
          <p>{{ $t('chat.noSessions') }}</p>
        </div>
      </div>
    </aside>

    <!-- 主对话区域 -->
    <main class="chat-main">
      <div v-if="!currentSession" class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-title">{{ $t('chat.noSessions') }}</div>
        <button class="btn btn-primary" @click="createSession">{{ $t('chat.newSession') }}</button>
      </div>

      <template v-else>
        <!-- 对话头部 -->
        <div class="chat-header">
          <div class="chat-info">
            <div class="chat-name">{{ currentSession.name }}</div>
            <div class="chat-model">
              <select v-model="currentSession.model" class="select model-select" @change="onModelChange">
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <button
                :class="['btn btn-ghost btn-sm ghost-btn', { active: ghostMode }]"
                @click="ghostMode = !ghostMode"
                :title="$t('chat.ghostMode')"
              >
                👻 {{ ghostMode ? $t('chat.ghostOn') : $t('chat.ghostOff') }}
              </button>
            </div>
          </div>
          <div class="chat-header-actions">
            <div v-if="contextWarning" :class="['context-warning', contextWarning]">
              ⚠️ {{ contextWarning === 'critical' ? $t('chat.contextFull') : $t('chat.contextWarning') }}
            </div>
            <button class="btn btn-ghost btn-sm" @click="exportSession">📤 {{ $t('chat.export') }}</button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div ref="messagesContainer" class="messages-container" @scroll="onScroll">
          <div v-if="currentSession.messages.length === 0" class="welcome-message">
            <div class="welcome-icon">✨</div>
            <div class="welcome-text">
              <span v-if="currentSession.characterName">
                与 {{ currentSession.characterName }} 的对话即将开始...
              </span>
              <span v-else>
                选择一个角色开始对话，或直接发送消息。
              </span>
            </div>
          </div>

          <div v-for="(msg, idx) in currentSession.messages" :key="idx" :class="['message', msg.role]">
            <div class="message-avatar">
              <img v-if="msg.role === 'assistant' && currentSession.characterId" :src="`/api/characters/${currentSession.characterId}/avatar`" />
              <span v-else-if="msg.role === 'user'">👤</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMarkdown(msg.content)"></div>
              <div v-if="isStreaming && idx === currentSession.messages.length - 1 && msg.role === 'assistant'" class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Ghost 模式确认条 -->
        <Transition name="slide-up">
          <div v-if="ghostPendingMessage" class="ghost-confirm-bar">
            <div class="ghost-pending">
              <span class="ghost-icon">👻</span>
              <span>{{ $t('chat.ghostPending') }}: {{ ghostPendingMessage.slice(0, 50) }}{{ ghostPendingMessage.length > 50 ? '...' : '' }}</span>
              <span class="ghost-timer">{{ Math.max(0, Math.ceil(ghostTimeout / 1000)) }}s</span>
            </div>
            <div class="ghost-actions">
              <button class="btn btn-sm btn-ghost" @click="discardGhost">{{ $t('chat.ghostDiscard') }}</button>
              <button class="btn btn-sm btn-primary" @click="confirmGhost">{{ $t('chat.ghostConfirm') }}</button>
            </div>
          </div>
        </Transition>

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-tools">
            <button class="btn btn-ghost btn-icon" @click="showCharacterSelect = !showCharacterSelect" title="选择角色">🎭</button>
            <button class="btn btn-ghost btn-icon" @click="showTTS = !showTTS" title="TTS">🔊</button>
          </div>

          <div v-if="showCharacterSelect" class="character-select-popup">
            <div class="search-box">
              <input v-model="charSearch" class="input" placeholder="搜索角色..." />
            </div>
            <div class="char-list">
              <div
                v-for="c in filteredChars"
                :key="c.id"
                :class="['char-option', { active: currentSession.characterId === c.id }]"
                @click="selectCharacter(c)"
              >
                <img v-if="c.avatar" :src="c.avatar" />
                <span>{{ c.name }}</span>
              </div>
              <div v-if="filteredChars.length === 0" class="no-chars">暂无角色</div>
            </div>
          </div>

          <div v-if="showTTS" class="tts-popup">
            <TTSPlayer />
          </div>

          <div class="input-row">
            <textarea
              ref="inputRef"
              v-model="inputText"
              class="input message-input"
              :placeholder="$t('chat.typeMessage')"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact="inputText += '\n'"
              rows="1"
            ></textarea>
            <button
              class="btn btn-primary send-btn"
              @click="sendMessage"
              :disabled="!inputText.trim() || isSending"
            >
              {{ isSending ? '...' : $t('chat.send') }}
            </button>
          </div>

          <div v-if="isSending" class="sending-indicator">
            {{ $t('chat.thinking') }}
          </div>
        </div>
      </template>
    </main>

    <!-- 创建分组弹窗 -->
    <div v-if="showCreateGroup" class="modal-overlay" @click.self="showCreateGroup = false">
      <div class="modal" style="max-width: 360px;">
        <div class="modal-header">
          <h2>{{ $t('chat.createGroup') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showCreateGroup = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('chat.groupName') }}</label>
            <input v-model="newGroupName" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('chat.groupColor') }}</label>
            <input v-model="newGroupColor" type="color" class="color-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateGroup = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="doCreateGroup">{{ $t('common.create') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useChatStore } from '@/stores/chat'
import { useUIStore } from '@/stores/ui'
import TTSPlayer from '@/components/TTSPlayer.vue'
import type { Character } from '@/types'

const { t } = useI18n()
const chatStore = useChatStore()
const uiStore = useUIStore()

const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)
const charSearch = ref('')
const showCharacterSelect = ref(false)
const showTTS = ref(false)
const showGroups = ref(false)
const showCreateGroup = ref(false)
const newGroupName = ref('')
const newGroupColor = ref('#667eea')
const sidebarCollapsed = ref(false)
const availableModels = ref<string[]>([])
const characters = ref<Character[]>([])

const {
  currentSessionId,
  currentSession,
  filteredSessions,
  groups,
  isSending,
  isStreaming,
  ghostMode,
  ghostPendingMessage,
  contextWarning,
  searchQuery,
  selectedGroupId,
  loadSessions,
  createSession: _createSession,
  deleteSession: _deleteSession,
  renameSession: _renameSession,
  togglePinSession: _togglePin,
  sendMessage: _sendMessage,
  confirmGhostMessage,
  discardGhostMessage,
  switchSession: _switchSession,
  loadGroups,
  createGroup: _createGroup
} = chatStore

const ghostTimeout = ref(0)
let ghostTimer: ReturnType<typeof setInterval> | null = null

const filteredChars = computed(() => {
  if (!charSearch.value.trim()) return characters.value
  const q = charSearch.value.toLowerCase()
  return characters.value.filter(c => c.name.toLowerCase().includes(q))
})

watch(() => currentSession?.messages.length, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

watch(ghostPendingMessage, (val) => {
  if (val) {
    ghostTimeout.value = 5000
    ghostTimer = setInterval(() => {
      ghostTimeout.value -= 100
      if (ghostTimeout.value <= 0 && ghostPendingMessage.value) {
        discardGhostMessage()
        if (ghostTimer) clearInterval(ghostTimer)
        uiStore.showInfo('Ghost 消息已自动放弃')
      }
    }, 100)
  } else if (ghostTimer) {
    clearInterval(ghostTimer)
  }
})

async function sendMessage() {
  if (!inputText.value.trim()) return
  const text = inputText.value.trim()
  inputText.value = ''
  await _sendMessage(text)
}

function confirmGhost() {
  confirmGhostMessage()
  if (ghostTimer) clearInterval(ghostTimer)
}

function discardGhost() {
  discardGhostMessage()
  if (ghostTimer) clearInterval(ghostTimer)
}

async function createSession() {
  await _createSession()
}

function switchSession(id: string) {
  _switchSession(id)
}

async function deleteSession(id: string) {
  if (!confirm(t('chat.deleteConfirm'))) return
  await _deleteSession(id)
}

async function togglePin(id: string) {
  await _togglePinSession(id)
}

function renameSession(session: any) {
  const newName = prompt(t('chat.rename'), session.name)
  if (newName && newName !== session.name) {
    _renameSession(session.id, newName)
  }
}

async function doCreateGroup() {
  if (!newGroupName.value.trim()) return
  await _createGroup(newGroupName.value, newGroupColor.value)
  newGroupName.value = ''
  showCreateGroup.value = false
}

function selectCharacter(char: Character) {
  if (currentSession.value) {
    currentSession.value.characterId = char.id
    currentSession.value.characterName = char.name
    showCharacterSelect.value = false
  }
}

function onModelChange() {
  // 切换模型
}

function exportSession() {
  if (!currentSession.value) return
  const data = JSON.stringify(currentSession.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentSession.value.name}.json`
  a.click()
  URL.revokeObjectURL(url)
  uiStore.showSuccess(t('chat.exportSuccess'))
}

function onScroll() {
  // 处理滚动
}

function formatMarkdown(text: string): string {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

onMounted(async () => {
  await Promise.all([loadSessions(), loadGroups()])
  try {
    const res = await fetch('/api/characters')
    if (res.ok) characters.value = await res.json()
    const modelsRes = await fetch('/api/config/models/available')
    if (modelsRes.ok) {
      const data = await modelsRes.json()
      availableModels.value = data.models || []
    }
  } catch (e) {
    console.error('加载数据失败:', e)
  }
})
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
  overflow: hidden;
}

.sidebar.collapsed { width: 0; border-right: none; }

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-actions { display: flex; gap: 4px; }

.groups-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.group-chip {
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 0.8rem;
  cursor: pointer;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  background: var(--bg-tertiary);
}

.group-chip:hover { border-color: var(--border-hover); color: var(--text-primary); }
.group-chip.active { background: var(--accent-subtle); border-color: var(--accent-color); color: var(--accent-color); }

.search-box {
  position: relative;
  padding: 8px 12px;
}

.search-box .search-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
  font-size: 0.85rem;
}

.search-box .input { padding-left: 30px; }

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 2px;
}

.session-item:hover { background: var(--bg-tertiary); }
.session-item.active { background: var(--accent-subtle); }
.session-item.pinned .session-name { color: var(--accent-color); }

.session-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1rem;
}

.session-avatar img { width: 100%; height: 100%; object-fit: cover; }

.session-info { flex: 1; min-width: 0; }

.session-name {
  font-weight: 500;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pin-icon { font-size: 0.7rem; }

.session-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.session-item:hover .session-actions { opacity: 1; }

.empty-sessions { padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.85rem; }

/* ===== 主对话区 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.chat-name { font-weight: 600; font-size: 1rem; margin-bottom: 2px; }

.chat-model { display: flex; align-items: center; gap: 8px; }
.model-select { padding: 4px 8px; font-size: 0.8rem; min-width: 100px; }

.ghost-btn.active { color: var(--accent-color); }

.chat-header-actions { display: flex; align-items: center; gap: 10px; }

.context-warning {
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
}

.context-warning.warning { background: rgba(245,158,11,0.15); color: #f59e0b; }
.context-warning.critical { background: rgba(239,68,68,0.15); color: #ef4444; }

/* ===== 消息区域 ===== */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

.welcome-icon { font-size: 3rem; }
.welcome-text { font-size: 1rem; }

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1rem;
}

.message-avatar img { width: 100%; height: 100%; object-fit: cover; }

.message-content { flex: 1; min-width: 0; }

.message-text {
  background: var(--bg-secondary);
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  line-height: 1.6;
  font-size: 0.9rem;
  word-break: break-word;
}

.message.user .message-text {
  background: var(--accent-color);
  color: white;
}

.message-text :deep(code) {
  background: rgba(0,0,0,0.2);
  padding: 2px 5px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 0.85em;
}

.message-text :deep(pre) {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) { background: none; padding: 0; }

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* ===== Ghost 确认条 ===== */
.ghost-confirm-bar {
  background: rgba(102,126,234,0.15);
  border-top: 1px solid rgba(102,126,234,0.3);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.ghost-pending {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--accent-color);
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.ghost-icon { font-size: 1.2rem; }
.ghost-pending span:nth-child(2) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.ghost-timer {
  background: var(--accent-color);
  color: white;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.ghost-actions { display: flex; gap: 8px; flex-shrink: 0; }

/* ===== 输入区域 ===== */
.input-area {
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
  position: relative;
  flex-shrink: 0;
}

.input-tools { display: flex; gap: 4px; margin-bottom: 8px; }

.character-select-popup, .tts-popup {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 20px;
  right: 20px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 10;
  max-height: 240px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.char-list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.char-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.char-option:hover { background: var(--bg-tertiary); }
.char-option.active { background: var(--accent-subtle); }

.char-option img {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.no-chars { text-align: center; color: var(--text-muted); padding: 16px; }

.input-row {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  resize: none;
  max-height: 120px;
  line-height: 1.5;
}

.send-btn { flex-shrink: 0; height: 40px; min-width: 60px; }

.sending-indicator {
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 6px;
}

.color-input { width: 60px; height: 36px; border: none; border-radius: var(--radius-md); cursor: pointer; }

@media screen and (max-width: 768px) {
  .sidebar { width: 240px; }
  .message { max-width: 90%; }
}
</style>
