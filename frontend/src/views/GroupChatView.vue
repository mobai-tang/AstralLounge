<template>
  <div class="group-chat-view">
    <div class="group-layout">
      <!-- 左侧：群聊列表 -->
      <aside class="groups-sidebar">
        <div class="sidebar-header">
          <h3>{{ $t('groupChat.title') }}</h3>
          <button class="btn btn-primary btn-sm" @click="showCreateGroup = true">
            <span>+</span> {{ $t('groupChat.create') }}
          </button>
        </div>

        <div class="groups-list">
          <div
            v-for="group in groups"
            :key="group.id"
            :class="['group-item', { active: selectedGroupId === group.id }]"
            @click="selectGroup(group.id)"
          >
            <div class="group-avatar">
              <img v-if="group.members && group.members.length > 0" :src="group.members[0].avatar" />
              <span v-else>👥</span>
            </div>
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-meta">{{ group.members?.length || 0 }} {{ $t('groupChat.members') }}</div>
            </div>
          </div>
          <div v-if="groups.length === 0" class="empty-groups">
            {{ $t('groupChat.noGroups') }}
          </div>
        </div>
      </aside>

      <!-- 中间：群聊主区域 -->
      <main class="chat-main">
        <div v-if="!selectedGroup" class="empty-state">
          <div class="empty-icon">👥</div>
          <div class="empty-title">{{ $t('groupChat.selectSession') }}</div>
        </div>

        <template v-else>
          <div class="chat-header">
            <div class="chat-info">
              <div class="chat-name">{{ selectedGroup.name }}</div>
              <div class="chat-mode">
                <select v-model="chatMode" class="select">
                  <option value="rotation">{{ $t('groupChat.rotation') }}</option>
                  <option value="orchestrator">{{ $t('groupChat.orchestrator') }}</option>
                </select>
              </div>
            </div>
            <div class="chat-actions">
              <button class="btn btn-ghost btn-sm" @click="showGroupSettings = true" title="群聊设置">
                ⚙️
              </button>
              <button class="btn btn-ghost btn-sm" @click="showGroupStats = true" title="统计">
                📊
              </button>
            </div>
            <div class="chat-members-avatars">
              <img
                v-for="m in selectedGroup.members?.slice(0, 5)"
                :key="m.id"
                :src="m.avatar"
                :title="m.name"
                class="member-avatar"
              />
              <span v-if="(selectedGroup.members?.length || 0) > 5" class="more-members">
                +{{ (selectedGroup.members?.length || 0) - 5 }}
              </span>
            </div>
          </div>

          <!-- 群聊模式提示 -->
          <div v-if="chatMode === 'orchestrator'" class="mode-banner orchestrator">
            <span class="mode-icon">🎭</span>
            <span>{{ $t('groupChat.orchestratorHint') }}</span>
            <select v-if="selectedGroup.orchestrator" v-model="currentOrchestrator" class="orchestrator-select">
              <option v-for="m in selectedGroup.members" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>

          <!-- 当前发言者指示器 -->
          <div v-if="currentSpeaker" class="speaker-indicator">
            <span class="speaker-label">{{ $t('groupChat.currentSpeaker') }}:</span>
            <img v-if="getMemberAvatar(currentSpeaker)" :src="getMemberAvatar(currentSpeaker)" class="speaker-avatar" />
            <span class="speaker-name">{{ getMemberName(currentSpeaker) }}</span>
            <div class="speaker-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>

          <div ref="messagesContainer" class="messages-container">
            <div v-if="messages.length === 0" class="welcome">
              {{ $t('groupChat.groupReady') }}
            </div>
            <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role, { highlight: isNewMessage(idx) }]">
              <div class="message-avatar">
                <img v-if="msg.characterId && getCharacterAvatar(msg.characterId)" :src="getCharacterAvatar(msg.characterId)" />
                <span v-else>{{ msg.role === 'user' ? '👤' : '🎭' }}</span>
              </div>
              <div class="message-content">
                <div class="message-sender">{{ msg.characterName }}</div>
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time" v-if="msg.timestamp">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>
          </div>

          <div class="input-area">
            <div class="input-row">
              <input v-model="inputText" class="input" :placeholder="$t('chat.typeMessage')" @keyup.enter="sendMessage" />
              <button class="btn btn-primary" @click="sendMessage" :disabled="!inputText.trim() || sending">
                {{ $t('chat.send') }}
              </button>
            </div>
            <div class="input-tools">
              <button class="btn btn-ghost btn-sm" @click="showQuickResponses = !showQuickResponses">
                ⚡ {{ $t('groupChat.quickResponse') }}
              </button>
              <button class="btn btn-ghost btn-sm" @click="showCharacterInfo = !showCharacterInfo">
                ℹ️ {{ $t('groupChat.charInfo') }}
              </button>
            </div>
          </div>

          <!-- 快速回复 -->
          <div v-if="showQuickResponses" class="quick-responses">
            <div class="quick-response" v-for="resp in quickResponses" :key="resp" @click="useQuickResponse(resp)">
              {{ resp }}
            </div>
          </div>
        </template>
      </main>

      <!-- 右侧：成员管理 -->
      <aside v-if="selectedGroup" class="members-sidebar">
        <div class="sidebar-header">
          <h4>{{ $t('groupChat.members') }}</h4>
          <button class="btn btn-sm btn-secondary" @click="showAddCharacter = true">
            + {{ $t('groupChat.addCharacter') }}
          </button>
        </div>
        <div class="members-list">
          <div
            v-for="m in selectedGroup.members"
            :key="m.id"
            :class="['member-item', { active: currentSpeaker === m.id, speaking: isSpeaking(m.id) }]"
          >
            <img :src="m.avatar" class="member-avatar-sm" />
            <span class="member-name">{{ m.name }}</span>
            <div class="member-status">
              <span v-if="currentSpeaker === m.id" class="speaking-indicator">🔊</span>
              <button class="btn btn-ghost btn-xs" @click="removeMember(m.id)">×</button>
            </div>
          </div>
          <div v-if="!selectedGroup.members?.length" class="empty-members">
            {{ $t('groupChat.noCharacters') }}
          </div>
        </div>

        <!-- 发言顺序 -->
        <div v-if="chatMode === 'rotation' && selectedGroup.members?.length" class="rotation-panel">
          <div class="panel-header">
            <span>{{ $t('groupChat.speakOrder') }}</span>
          </div>
          <div class="rotation-list">
            <div v-for="(m, idx) in selectedGroup.members" :key="m.id" :class="['rotation-item', { next: idx === nextSpeakerIndex }]">
              <span class="rotation-num">{{ idx + 1 }}</span>
              <img :src="m.avatar" class="rotation-avatar" />
              <span class="rotation-name">{{ m.name }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- 创建群聊弹窗 -->
    <div v-if="showCreateGroup" class="modal-overlay" @click.self="showCreateGroup = false">
      <div class="modal" style="max-width: 360px;">
        <div class="modal-header">
          <h2>{{ $t('groupChat.create') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showCreateGroup = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('groupChat.groupName') }}</label>
            <input v-model="newGroupName" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('groupChat.initialMode') }}</label>
            <select v-model="newGroupMode" class="select">
              <option value="rotation">{{ $t('groupChat.rotation') }}</option>
              <option value="orchestrator">{{ $t('groupChat.orchestrator') }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateGroup = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="doCreateGroup">{{ $t('common.create') }}</button>
        </div>
      </div>
    </div>

    <!-- 群聊设置弹窗 -->
    <div v-if="showGroupSettings" class="modal-overlay" @click.self="showGroupSettings = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('groupChat.groupSettings') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showGroupSettings = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('groupChat.chatMode') }}</label>
            <select v-model="chatMode" class="select">
              <option value="rotation">{{ $t('groupChat.rotation') }}</option>
              <option value="orchestrator">{{ $t('groupChat.orchestrator') }}</option>
            </select>
          </div>

          <div v-if="chatMode === 'rotation'" class="form-group">
            <label class="form-label">{{ $t('groupChat.rotationStrategy') }}</label>
            <select v-model="rotationStrategy" class="select">
              <option value="sequential">{{ $t('groupChat.sequential') }}</option>
              <option value="random">{{ $t('groupChat.random') }}</option>
              <option value="relevance">{{ $t('groupChat.relevance') }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('groupChat.speakDelay') }}: {{ speakDelay }}ms</label>
            <input v-model.number="speakDelay" type="range" min="0" max="5000" step="500" class="range-input" />
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('groupChat.maxTurns') }}</label>
            <input v-model.number="maxTurns" type="number" class="input" min="1" max="20" />
          </div>

          <div class="toggle-row">
            <label class="toggle-label">
              <div :class="['toggle', { active: showCharacterMessages }]" @click="showCharacterMessages = !showCharacterMessages"></div>
              {{ $t('groupChat.showCharacterMessages') }}
            </label>
          </div>

          <div class="toggle-row">
            <label class="toggle-label">
              <div :class="['toggle', { active: autoSummarize }]" @click="autoSummarize = !autoSummarize"></div>
              {{ $t('groupChat.autoSummarize') }}
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showGroupSettings = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveGroupSettings">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>

    <!-- 添加角色弹窗 -->
    <div v-if="showAddCharacter" class="modal-overlay" @click.self="showAddCharacter = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('groupChat.addCharacter') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showAddCharacter = false">×</button>
        </div>
        <div class="modal-body">
          <div class="search-box" style="margin-bottom: 12px;">
            <span class="search-icon">🔍</span>
            <input v-model="charSearch" class="input" :placeholder="$t('groupChat.noResults')" />
          </div>
          <div class="char-list">
            <div
              v-for="c in filteredChars"
              :key="c.id"
              class="char-option"
              @click="addCharacter(c)"
            >
              <img v-if="c.avatar" :src="c.avatar" class="char-avatar" />
              <div class="char-info">
                <span class="char-name">{{ c.name }}</span>
                <span class="char-desc">{{ c.description }}</span>
              </div>
            </div>
            <div v-if="filteredChars.length === 0" class="empty-hint">
              {{ $t('groupChat.noCharsAvailable') }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 群聊统计 -->
    <div v-if="showGroupStats" class="modal-overlay" @click.self="showGroupStats = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('groupChat.stats') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showGroupStats = false">×</button>
        </div>
        <div class="modal-body">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">💬</div>
              <div class="stat-value">{{ messages.length }}</div>
              <div class="stat-label">{{ $t('groupChat.totalMessages') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-value">{{ selectedGroup.members?.length || 0 }}</div>
              <div class="stat-label">{{ $t('groupChat.totalMembers') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🔄</div>
              <div class="stat-value">{{ turnCount }}</div>
              <div class="stat-label">{{ $t('groupChat.turns') }}</div>
            </div>
          </div>
          <div class="member-stats">
            <div class="member-stat" v-for="m in selectedGroup.members" :key="m.id">
              <img :src="m.avatar" class="member-stat-avatar" />
              <span class="member-stat-name">{{ m.name }}</span>
              <div class="member-stat-bar">
                <div class="member-stat-fill" :style="{ width: getMemberMessageRatio(m.id) + '%' }"></div>
              </div>
              <span class="member-stat-count">{{ getMemberMessageCount(m.id) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Character, CharacterMessage } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

interface GroupWithMembers {
  id: string
  name: string
  mode?: string
  orchestrator?: string
  members: Array<{ id: string; name: string; avatar?: string }>
  settings?: GroupSettings
}

interface GroupSettings {
  rotationStrategy: string
  speakDelay: number
  maxTurns: number
  showCharacterMessages: boolean
  autoSummarize: boolean
}

const groups = ref<GroupWithMembers[]>([])
const selectedGroupId = ref<string | null>(null)
const chatMode = ref<'rotation' | 'orchestrator'>('rotation')
const rotationStrategy = ref('sequential')
const speakDelay = ref(1000)
const maxTurns = ref(5)
const showCharacterMessages = ref(true)
const autoSummarize = ref(false)
const messages = ref<CharacterMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const showCreateGroup = ref(false)
const showAddCharacter = ref(false)
const showGroupSettings = ref(false)
const showGroupStats = ref(false)
const showQuickResponses = ref(false)
const showCharacterInfo = ref(false)
const newGroupName = ref('')
const newGroupMode = ref('rotation')
const charSearch = ref('')
const characters = ref<Character[]>([])
const messagesContainer = ref<HTMLElement | null>(null)
const currentSpeaker = ref<string | null>(null)
const currentOrchestrator = ref<string | null>(null)
const turnCount = ref(0)
const nextSpeakerIndex = ref(0)
const speakingMembers = ref<Set<string>>(new Set())
const newMessageIndices = ref<Set<number>>(new Set())

const quickResponses = [
  '你们怎么看？',
  '有道理',
  '继续说',
  '有意思',
  '等等，让我想想',
]

const selectedGroup = computed(() => groups.value.find(g => g.id === selectedGroupId.value) ?? null)

const filteredChars = computed(() => {
  if (!charSearch.value.trim()) return characters.value
  const q = charSearch.value.toLowerCase()
  return characters.value.filter(c => c.name.toLowerCase().includes(q))
})

function getCharacterAvatar(id: string): string | undefined {
  return characters.value.find(c => c.id === id)?.avatar
}

function getMemberAvatar(id: string): string | undefined {
  return selectedGroup.value?.members.find(m => m.id === id)?.avatar
}

function getMemberName(id: string): string {
  return selectedGroup.value?.members.find(m => m.id === id)?.name ?? 'Unknown'
}

function isNewMessage(idx: number): boolean {
  return newMessageIndices.value.has(idx)
}

function isSpeaking(id: string): boolean {
  return speakingMembers.value.has(id)
}

function getMemberMessageCount(id: string): number {
  return messages.value.filter(m => m.characterId === id).length
}

function getMemberMessageRatio(id: string): number {
  if (messages.value.length === 0) return 0
  return Math.round((getMemberMessageCount(id) / messages.value.length) * 100)
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function useQuickResponse(resp: string) {
  inputText.value = resp
  showQuickResponses.value = false
}

function selectGroup(id: string) {
  selectedGroupId.value = id
  const group = groups.value.find(g => g.id === id)
  if (group) {
    chatMode.value = (group.mode as 'rotation' | 'orchestrator') || 'rotation'
    if (group.settings) {
      rotationStrategy.value = group.settings.rotationStrategy || 'sequential'
      speakDelay.value = group.settings.speakDelay || 1000
      maxTurns.value = group.settings.maxTurns || 5
      showCharacterMessages.value = group.settings.showCharacterMessages ?? true
      autoSummarize.value = group.settings.autoSummarize ?? false
    }
    if (group.orchestrator) {
      currentOrchestrator.value = group.orchestrator
    } else if (group.members.length > 0) {
      currentOrchestrator.value = group.members[0].id
    }
  }
  loadMessages(id)
  turnCount.value = 0
  nextSpeakerIndex.value = 0
  currentSpeaker.value = null
}

async function loadMessages(groupId: string) {
  try {
    const res = await fetch(`/api/group-chat/${groupId}/messages`)
    if (res.ok) messages.value = await res.json()
  } catch {}
}

async function sendMessage() {
  if (!inputText.value.trim() || !selectedGroupId.value || sending.value) return
  if (!selectedGroup.value?.members?.length) {
    uiStore.showError(t('groupChat.noCharacters'))
    return
  }

  const content = inputText.value.trim()
  inputText.value = ''
  sending.value = true

  try {
    // 添加用户消息
    const userMsg: CharacterMessage = {
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    messages.value.push(userMsg)
    scrollToBottom()

    // 确定当前发言者
    if (chatMode.value === 'rotation') {
      currentSpeaker.value = selectedGroup.value!.members[nextSpeakerIndex.value].id
    } else {
      currentSpeaker.value = currentOrchestrator.value || selectedGroup.value!.members[0].id
    }

    speakingMembers.value.add(currentSpeaker.value)

    // 模拟群聊响应
    const res = await fetch(`/api/group-chat/${selectedGroupId.value}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        mode: chatMode.value,
        rotationStrategy: rotationStrategy.value,
        orchestrator: currentOrchestrator.value,
      }),
    })

    if (res.ok) {
      const msgs: CharacterMessage[] = await res.json()
      const startIdx = messages.value.length
      msgs.forEach((msg, idx) => {
        msg.timestamp = Date.now() + idx * 100
        messages.value.push(msg)
        newMessageIndices.value.add(startIdx + idx)
      })
      turnCount.value++

      // 更新下一个发言者
      if (chatMode.value === 'rotation') {
        nextSpeakerIndex.value = (nextSpeakerIndex.value + 1) % (selectedGroup.value?.members?.length || 1)
      }

      // 清除新消息标记
      setTimeout(() => {
        newMessageIndices.value.clear()
      }, 2000)

      scrollToBottom()
    }
  } catch {
    uiStore.showError(t('common.error'))
  } finally {
    sending.value = false
    speakingMembers.value.delete(currentSpeaker.value!)
    setTimeout(() => {
      currentSpeaker.value = null
    }, speakDelay.value)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

async function doCreateGroup() {
  if (!newGroupName.value.trim()) return
  try {
    const res = await fetch('/api/group-chat/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newGroupName.value, mode: newGroupMode.value }),
    })
    if (res.ok) {
      const group: GroupWithMembers = await res.json()
      groups.value.push(group)
      selectedGroupId.value = group.id
      showCreateGroup.value = false
      newGroupName.value = ''
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function addCharacter(char: Character) {
  if (!selectedGroupId.value) return
  try {
    const res = await fetch(`/api/group-chat/${selectedGroupId.value}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ characterId: char.id }),
    })
    if (res.ok) {
      const group = groups.value.find(g => g.id === selectedGroupId.value)
      if (group) {
        if (!group.members) group.members = []
        if (!group.members.find(m => m.id === char.id)) {
          group.members.push({ id: char.id, name: char.name, avatar: char.avatar })
        }
      }
      showAddCharacter.value = false
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function removeMember(charId: string) {
  if (!selectedGroupId.value) return
  try {
    await fetch(`/api/group-chat/${selectedGroupId.value}/members/${charId}`, { method: 'DELETE' })
    const group = groups.value.find(g => g.id === selectedGroupId.value)
    if (group) group.members = group.members?.filter(m => m.id !== charId) ?? []
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function saveGroupSettings() {
  if (!selectedGroup.value) return
  selectedGroup.value.mode = chatMode.value
  selectedGroup.value.settings = {
    rotationStrategy: rotationStrategy.value,
    speakDelay: speakDelay.value,
    maxTurns: maxTurns.value,
    showCharacterMessages: showCharacterMessages.value,
    autoSummarize: autoSummarize.value,
  }
  if (chatMode.value === 'orchestrator') {
    selectedGroup.value.orchestrator = currentOrchestrator.value || undefined
  }
  showGroupSettings.value = false
  uiStore.showSuccess(t('common.save'))
}

onMounted(async () => {
  try {
    const res = await fetch('/api/group-chat/groups')
    if (res.ok) groups.value = await res.json()
    const charsRes = await fetch('/api/characters')
    if (charsRes.ok) characters.value = await charsRes.json()
  } catch (e) {
    console.error('加载群聊失败:', e)
  }
})
</script>

<style scoped>
.group-chat-view {
  height: 100%;
  overflow: hidden;
}

.group-layout {
  display: flex;
  height: 100%;
}

.groups-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.members-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h3 { margin: 0; font-size: 1rem; }
.sidebar-header h4 { margin: 0; font-size: 0.9rem; }

.groups-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.group-item:hover { background: var(--bg-tertiary); }
.group-item.active { background: var(--accent-subtle); }

.group-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.group-avatar img { width: 100%; height: 100%; object-fit: cover; }
.group-info { flex: 1; min-width: 0; }
.group-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-meta { font-size: 0.75rem; color: var(--text-secondary); }

.empty-groups { text-align: center; color: var(--text-muted); padding: 20px; font-size: 0.85rem; }

.chat-header {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--bg-secondary);
}

.chat-info { display: flex; flex-direction: column; gap: 4px; }
.chat-name { font-weight: 600; }
.chat-mode .select { padding: 4px 8px; font-size: 0.8rem; }
.chat-actions { display: flex; gap: 4px; margin-left: auto; }

.chat-members-avatars { display: flex; align-items: center; gap: -4px; }
.member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--bg-secondary);
  margin-left: -6px;
}

.more-members { margin-left: 2px; font-size: 0.8rem; color: var(--text-secondary); }

.mode-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: var(--bg-tertiary);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.mode-banner.orchestrator { background: rgba(168, 85, 247, 0.1); }
.mode-icon { font-size: 1rem; }

.orchestrator-select {
  margin-left: auto;
  padding: 4px 8px;
  font-size: 0.8rem;
  border-radius: var(--radius-sm);
}

.speaker-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 20px;
  background: var(--accent-subtle);
  font-size: 0.8rem;
}

.speaker-label { color: var(--text-muted); }
.speaker-avatar { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; }
.speaker-name { font-weight: 500; color: var(--accent-color); }

.speaker-dots { display: flex; gap: 2px; margin-left: auto; }
.dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent-color);
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome { text-align: center; color: var(--text-secondary); padding: 40px; font-size: 1rem; }

.message {
  display: flex;
  gap: 10px;
  max-width: 80%;
  transition: all 0.3s ease;
}

.message.highlight {
  animation: highlightPulse 2s ease;
}

@keyframes highlightPulse {
  0% { background: rgba(102, 126, 234, 0.2); }
  100% { background: transparent; }
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-avatar img { width: 100%; height: 100%; object-fit: cover; }

.message-content { background: var(--bg-secondary); padding: 8px 12px; border-radius: var(--radius-md); }
.message-sender { font-size: 0.8rem; font-weight: 600; color: var(--accent-color); margin-bottom: 2px; }
.message-text { font-size: 0.9rem; line-height: 1.5; }
.message-time { font-size: 0.7rem; color: var(--text-muted); margin-top: 4px; }

.input-area { padding: 12px 20px; border-top: 1px solid var(--border-color); background: var(--bg-secondary); }
.input-row { display: flex; gap: 8px; }
.input-row .input { flex: 1; }

.input-tools { display: flex; gap: 8px; margin-top: 8px; }

.quick-responses {
  padding: 8px 20px;
  background: var(--bg-tertiary);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-response {
  padding: 4px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-response:hover { background: var(--accent-subtle); color: var(--accent-color); }

.members-list { flex: 1; overflow-y: auto; padding: 8px; }

.member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.member-item:hover { background: var(--bg-tertiary); }
.member-item.active { background: var(--accent-subtle); }
.member-item.speaking { border-left: 3px solid var(--accent-color); }

.member-avatar-sm { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.member-name { flex: 1; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.member-status { display: flex; align-items: center; gap: 4px; }
.speaking-indicator { animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.empty-members { text-align: center; color: var(--text-muted); padding: 20px; font-size: 0.85rem; }

.rotation-panel {
  border-top: 1px solid var(--border-color);
  padding: 12px;
}

.panel-header { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px; }

.rotation-list { display: flex; flex-direction: column; gap: 4px; }

.rotation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  opacity: 0.6;
}

.rotation-item.next { opacity: 1; background: var(--accent-subtle); }

.rotation-num { width: 16px; font-weight: 600; color: var(--text-muted); }
.rotation-avatar { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; }
.rotation-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.char-list { display: flex; flex-direction: column; gap: 4px; max-height: 300px; overflow-y: auto; }

.char-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.char-option:hover { background: var(--bg-tertiary); }
.char-avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.char-info { flex: 1; display: flex; flex-direction: column; }
.char-name { font-size: 0.85rem; font-weight: 500; }
.char-desc { font-size: 0.75rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.empty-hint { text-align: center; color: var(--text-muted); padding: 16px; font-size: 0.85rem; }

.search-box { position: relative; }
.search-box .search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-box .input { padding-left: 32px; }

.form-group { margin-bottom: 16px; }
.form-group:last-child { margin-bottom: 0; }
.form-label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 6px; }

.range-input { width: 100%; accent-color: var(--accent-color); }

.toggle-row { display: flex; align-items: center; margin-bottom: 12px; }
.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 0.85rem; }

.toggle {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: var(--bg-tertiary);
  position: relative;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.toggle::after {
  content: '';
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform var(--transition-fast);
}

.toggle.active { background: var(--accent-color); }
.toggle.active::after { transform: translateX(18px); }

.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }

.stat-card {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 16px;
  text-align: center;
}

.stat-icon { font-size: 1.5rem; margin-bottom: 8px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent-color); }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }

.member-stats { display: flex; flex-direction: column; gap: 8px; }

.member-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

.member-stat-avatar { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; }
.member-stat-name { width: 80px; font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.member-stat-bar { flex: 1; height: 6px; background: var(--bg-secondary); border-radius: 3px; overflow: hidden; }
.member-stat-fill { height: 100%; background: var(--accent-color); transition: width 0.3s ease; }
.member-stat-count { width: 30px; font-size: 0.8rem; text-align: right; color: var(--text-muted); }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 { margin: 0; font-size: 1rem; font-weight: 600; }

.modal-body { padding: 20px; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

@media screen and (max-width: 768px) {
  .groups-sidebar { width: 180px; }
  .members-sidebar { display: none; }
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
