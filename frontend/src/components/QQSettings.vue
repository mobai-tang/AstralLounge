<template>
  <div class="qq-settings">
    <div class="qq-header">
      <h2>QQ 机器人设置</h2>
      <div :class="['status-indicator', connectionStatus]">
        <span class="status-dot"></span>
        {{ statusText }}
      </div>
    </div>

    <div class="settings-section">
      <h3>连接配置</h3>
      <div class="form-group">
        <label class="form-label">Bot QQ 号</label>
        <input v-model="settings.botUin" class="input" placeholder="123456789" />
      </div>
      <div class="form-group">
        <label class="form-label">反向 WS 地址</label>
        <input v-model="settings.wsUrl" class="input" placeholder="ws://localhost:8080/ws" />
      </div>
      <div class="form-row">
        <button class="btn btn-primary" @click="connect" :disabled="connecting">
          {{ connecting ? '连接中...' : '连接' }}
        </button>
        <button class="btn btn-secondary" @click="disconnect" :disabled="!connected">断开</button>
        <button class="btn btn-secondary" @click="refreshFriends">🔄 刷新好友</button>
      </div>
    </div>

    <div class="settings-section">
      <h3>好友白名单</h3>
      <div class="friends-list">
        <div v-if="friends.length === 0" class="empty-hint">暂无好友列表</div>
        <div v-for="friend in friends" :key="friend.uin" class="friend-item">
          <div class="friend-avatar">
            <img v-if="friend.avatar" :src="friend.avatar" />
            <span v-else>{{ friend.nickname?.charAt(0) || '?' }}</span>
          </div>
          <div class="friend-info">
            <div class="friend-name">{{ friend.nickname || friend.uin }}</div>
            <div class="friend-uin">QQ: {{ friend.uin }}</div>
          </div>
          <div :class="['toggle', { active: isWhitelisted(friend.uin) }]" @click="toggleWhitelist(friend.uin)"></div>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3>群组配置</h3>
      <div class="form-group">
        <label class="toggle-label">
          <div :class="['toggle', { active: settings.groupEnabled }]" @click="settings.groupEnabled = !settings.groupEnabled"></div>
          启用群聊功能
        </label>
      </div>
      <div class="groups-list">
        <div v-if="groups.length === 0" class="empty-hint">暂无群组</div>
        <div v-for="group in groups" :key="group.groupId" class="group-item">
          <div class="group-info">
            <div class="group-name">{{ group.groupName || group.groupId }}</div>
            <div class="group-id">群号: {{ group.groupId }}</div>
          </div>
          <div :class="['toggle', { active: isGroupEnabled(group.groupId) }]" @click="toggleGroupEnabled(group.groupId)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'

const { t } = useI18n()
const uiStore = useUIStore()

interface Friend { uin: string; nickname?: string; avatar?: string }
interface Group { groupId: string; groupName?: string }

const settings = reactive({
  botUin: '',
  wsUrl: 'ws://localhost:8080/ws',
  groupEnabled: true,
  whitelistedFriends: [] as string[],
  enabledGroups: [] as string[]
})

const connectionStatus = ref<'connected' | 'disconnected' | 'connecting'>('disconnected')
const connecting = ref(false)
const friends = ref<Friend[]>([])
const groups = ref<Group[]>([])

const connected = computed(() => connectionStatus.value === 'connected')
const statusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected': return '已连接'
    case 'connecting': return '连接中...'
    default: return '未连接'
  }
})

function isWhitelisted(uin: string) {
  return settings.whitelistedFriends.includes(uin)
}

function toggleWhitelist(uin: string) {
  const idx = settings.whitelistedFriends.indexOf(uin)
  if (idx >= 0) settings.whitelistedFriends.splice(idx, 1)
  else settings.whitelistedFriends.push(uin)
}

function isGroupEnabled(groupId: string) {
  return settings.enabledGroups.includes(groupId)
}

function toggleGroupEnabled(groupId: string) {
  const idx = settings.enabledGroups.indexOf(groupId)
  if (idx >= 0) settings.enabledGroups.splice(idx, 1)
  else settings.enabledGroups.push(groupId)
}

async function connect() {
  connecting.value = true
  connectionStatus.value = 'connecting'
  try {
    const res = await fetch('/api/qq/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bot_uin: settings.botUin, ws_url: settings.wsUrl })
    })
    if (res.ok) {
      connectionStatus.value = 'connected'
      uiStore.showSuccess('连接成功')
      await refreshFriends()
      await refreshGroups()
    } else {
      connectionStatus.value = 'disconnected'
      uiStore.showError('连接失败')
    }
  } catch {
    connectionStatus.value = 'disconnected'
    uiStore.showError('连接失败')
  } finally {
    connecting.value = false
  }
}

async function disconnect() {
  try {
    await fetch('/api/qq/disconnect', { method: 'POST' })
    connectionStatus.value = 'disconnected'
    uiStore.showInfo('已断开')
  } catch {
    uiStore.showError('断开失败')
  }
}

async function refreshFriends() {
  try {
    const res = await fetch('/api/qq/friends')
    if (res.ok) friends.value = await res.json()
  } catch {
    console.error('刷新好友失败')
  }
}

async function refreshGroups() {
  try {
    const res = await fetch('/api/qq/groups')
    if (res.ok) groups.value = await res.json()
  } catch {
    console.error('刷新群组失败')
  }
}

async function loadSettings() {
  try {
    const res = await fetch('/api/qq/settings')
    if (res.ok) {
      const data = await res.json()
      Object.assign(settings, data)
      if (data.status === 'connected') connectionStatus.value = 'connected'
    }
  } catch {
    console.error('加载设置失败')
  }
}

onMounted(async () => {
  await loadSettings()
  if (connected.value) {
    await Promise.all([refreshFriends(), refreshGroups()])
  }
})
</script>

<style scoped>
.qq-settings {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.qq-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.qq-header h2 { margin: 0; font-size: 1.2rem; }

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 500;
}

.status-indicator.disconnected { background: rgba(239,68,68,0.15); color: #ef4444; }
.status-indicator.connecting { background: rgba(245,158,11,0.15); color: #f59e0b; }
.status-indicator.connected { background: rgba(16,185,129,0.15); color: #10b981; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.settings-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.settings-section h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.form-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.friends-list, .groups-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow-y: auto;
}

.empty-hint { text-align: center; color: var(--text-muted); padding: 20px; font-size: 0.85rem; }

.friend-item, .group-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
  transition: background var(--transition-fast);
}

.friend-item:hover, .group-item:hover { background: var(--bg-elevated); }

.friend-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.friend-avatar img { width: 100%; height: 100%; object-fit: cover; }

.friend-info, .group-info { flex: 1; min-width: 0; }
.friend-name, .group-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.friend-uin, .group-id { font-size: 0.75rem; color: var(--text-secondary); }
</style>
