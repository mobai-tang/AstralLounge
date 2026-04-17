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

          <div ref="messagesContainer" class="messages-container">
            <div v-if="messages.length === 0" class="welcome">
              {{ $t('groupChat.groupReady') }}
            </div>
            <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
              <div class="message-avatar">
                <img v-if="msg.characterId && getCharacterAvatar(msg.characterId)" :src="getCharacterAvatar(msg.characterId)" />
                <span v-else>{{ msg.role === 'user' ? '👤' : '🎭' }}</span>
              </div>
              <div class="message-content">
                <div class="message-sender">{{ msg.characterName }}</div>
                <div class="message-text">{{ msg.content }}</div>
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
          <div v-for="m in selectedGroup.members" :key="m.id" class="member-item">
            <img :src="m.avatar" class="member-avatar-sm" />
            <span class="member-name">{{ m.name }}</span>
            <button class="btn btn-ghost btn-sm" @click="removeMember(m.id)">×</button>
          </div>
          <div v-if="!selectedGroup.members?.length" class="empty-members">
            {{ $t('groupChat.noCharacters') }}
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
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateGroup = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="doCreateGroup">{{ $t('common.create') }}</button>
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
              <span>{{ c.name }}</span>
            </div>
            <div v-if="filteredChars.length === 0" class="empty-hint">
              {{ $t('groupChat.noCharsAvailable') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Character, CharacterMessage } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

interface GroupWithMembers {
  id: string
  name: string
  members: Array<{ id: string; name: string; avatar?: string }>
}

const groups = ref<GroupWithMembers[]>([])
const selectedGroupId = ref<string | null>(null)
const chatMode = ref<'rotation' | 'orchestrator'>('rotation')
const messages = ref<CharacterMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const showCreateGroup = ref(false)
const showAddCharacter = ref(false)
const newGroupName = ref('')
const charSearch = ref('')
const characters = ref<Character[]>([])
const messagesContainer = ref<HTMLElement | null>(null)

const selectedGroup = computed(() => groups.value.find(g => g.id === selectedGroupId.value) ?? null)

const filteredChars = computed(() => {
  if (!charSearch.value.trim()) return characters.value
  const q = charSearch.value.toLowerCase()
  return characters.value.filter(c => c.name.toLowerCase().includes(q))
})

function getCharacterAvatar(id: string): string | undefined {
  return characters.value.find(c => c.id === id)?.avatar
}

function selectGroup(id: string) {
  selectedGroupId.value = id
  loadMessages(id)
}

async function loadMessages(groupId: string) {
  try {
    const res = await fetch(`/api/group-chat/${groupId}/messages`)
    if (res.ok) messages.value = await res.json()
  } catch {}
}

async function sendMessage() {
  if (!inputText.value.trim() || !selectedGroupId.value || sending.value) return
  const content = inputText.value.trim()
  inputText.value = ''
  sending.value = true
  try {
    const res = await fetch(`/api/group-chat/${selectedGroupId.value}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, mode: chatMode.value })
    })
    if (res.ok) {
      const msgs: CharacterMessage[] = await res.json()
      messages.value = msgs
    }
  } catch {
    uiStore.showError(t('common.error'))
  } finally {
    sending.value = false
  }
}

async function doCreateGroup() {
  if (!newGroupName.value.trim()) return
  try {
    const res = await fetch('/api/group-chat/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newGroupName.value })
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
      body: JSON.stringify({ characterId: char.id })
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
  justify-content: space-between;
  background: var(--bg-secondary);
}

.chat-name { font-weight: 600; margin-bottom: 2px; }
.chat-mode .select { padding: 4px 8px; font-size: 0.8rem; }

.chat-members-avatars { display: flex; align-items: center; gap: -4px; }
.member-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--bg-secondary);
  margin-left: -6px;
}

.more-members {
  margin-left: 2px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px;
  font-size: 1rem;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 80%;
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

.input-area { padding: 12px 20px; border-top: 1px solid var(--border-color); background: var(--bg-secondary); }
.input-row { display: flex; gap: 8px; }
.input-row .input { flex: 1; }

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

.member-avatar-sm { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.member-name { flex: 1; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.empty-members { text-align: center; color: var(--text-muted); padding: 20px; font-size: 0.85rem; }

.char-list { display: flex; flex-direction: column; gap: 4px; max-height: 300px; overflow-y: auto; }
.char-option { display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: var(--radius-md); cursor: pointer; transition: background var(--transition-fast); }
.char-option:hover { background: var(--bg-tertiary); }
.char-avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.empty-hint { text-align: center; color: var(--text-muted); padding: 16px; font-size: 0.85rem; }

.search-box { position: relative; }
.search-box .search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.search-box .input { padding-left: 32px; }

@media screen and (max-width: 768px) {
  .groups-sidebar { width: 180px; }
  .members-sidebar { display: none; }
}
</style>
