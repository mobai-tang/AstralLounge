<template>
  <div class="app">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <h1 class="logo">AstralLounge</h1>
        <nav class="nav">
          <router-link to="/" class="nav-link" active-class="active">
            <span class="nav-icon">💬</span>
            <span class="nav-text">对话</span>
          </router-link>
          <router-link to="/group-chat" class="nav-link" active-class="active">
            <span class="nav-icon">👥</span>
            <span class="nav-text">群聊</span>
          </router-link>
          <router-link to="/characters" class="nav-link" active-class="active">
            <span class="nav-icon">🎭</span>
            <span class="nav-text">角色</span>
          </router-link>
          <router-link to="/lorebooks" class="nav-link" active-class="active">
            <span class="nav-icon">📚</span>
            <span class="nav-text">世界</span>
          </router-link>
          <router-link to="/memory" class="nav-link" active-class="active">
            <span class="nav-icon">🧠</span>
            <span class="nav-text">记忆</span>
          </router-link>
          <router-link to="/plugins" class="nav-link" active-class="active">
            <span class="nav-icon">🔌</span>
            <span class="nav-text">插件</span>
          </router-link>
        </nav>
      </div>

      <div class="header-right">
        <!-- 模型选择器 -->
        <div class="model-indicator" :class="modelStatusClass" :title="modelStatusText">
          <span class="model-dot"></span>
          <select v-model="currentModel" @change="onModelChange" class="model-select">
            <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <!-- 语言切换 -->
        <select v-model="currentLang" @change="onLangChange" class="lang-select">
          <option v-for="lang in availableLangs" :key="lang.code" :value="lang.code">
            {{ lang.flag }}
          </option>
        </select>

        <!-- 通知中心 -->
        <button
          @click="showNotifications = !showNotifications"
          class="notification-btn"
          :class="{ 'has-unread': uiStore.notificationCount > 0 }"
          :title="`${uiStore.notificationCount} 条未读通知`"
        >
          <span class="bell-icon">🔔</span>
          <span v-if="uiStore.notificationCount > 0" class="notification-badge">
            {{ uiStore.notificationCount > 99 ? '99+' : uiStore.notificationCount }}
          </span>
        </button>

        <!-- 快捷设置 -->
        <button @click="showSettings = true" class="settings-btn" title="设置">
          <span>&#9881;</span>
        </button>

        <!-- 移动端菜单 -->
        <button @click="showMobileMenu = !showMobileMenu" class="mobile-menu-btn hide-desktop">
          <span>&#9776;</span>
        </button>
      </div>
    </header>

    <!-- 移动端抽屉菜单 -->
    <div v-if="showMobileMenu" class="mobile-menu-overlay" @click="showMobileMenu = false">
      <nav class="mobile-menu" @click.stop>
        <div class="mobile-menu-header">
          <h2>导航</h2>
          <button @click="showMobileMenu = false" class="mobile-menu-close">&#215;</button>
        </div>
        <router-link to="/" class="mobile-nav-link" @click="showMobileMenu = false">💬 对话</router-link>
        <router-link to="/group-chat" class="mobile-nav-link" @click="showMobileMenu = false">👥 群聊</router-link>
        <router-link to="/characters" class="mobile-nav-link" @click="showMobileMenu = false">🎭 角色</router-link>
        <router-link to="/lorebooks" class="mobile-nav-link" @click="showMobileMenu = false">📚 世界</router-link>
        <router-link to="/memory" class="mobile-nav-link" @click="showMobileMenu = false">🧠 记忆</router-link>
        <router-link to="/plugins" class="mobile-nav-link" @click="showMobileMenu = false">🔌 插件</router-link>
        <router-link to="/settings" class="mobile-nav-link" @click="showMobileMenu = false">⚙️ 设置</router-link>
      </nav>
    </div>

    <!-- 通知面板 -->
    <Transition name="slide-down">
      <div v-if="showNotifications" class="notifications-panel">
        <div class="notifications-header">
          <h3>通知</h3>
          <div class="notifications-actions">
            <button @click="uiStore.markAllNotificationsRead()" class="mark-all-btn">全部已读</button>
            <button @click="uiStore.clearNotifications()" class="clear-btn">清空</button>
          </div>
        </div>
        <div class="notifications-body">
          <div
            v-if="uiStore.notifications.length === 0"
            class="notifications-empty"
          >
            <span class="empty-icon">🔔</span>
            <p>暂无通知</p>
          </div>
          <div
            v-for="n in uiStore.notifications"
            :key="n.id"
            :class="['notification-item', { unread: !n.read }]"
            @click="uiStore.markNotificationRead(n.id)"
          >
            <div class="notification-icon" :class="n.type || 'info'">
              {{ getNotificationIcon(n.type) }}
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ n.title }}</div>
              <div class="notification-message">{{ n.message }}</div>
              <div class="notification-time">{{ formatTime(n.timestamp) }}</div>
            </div>
            <div v-if="!n.read" class="unread-dot"></div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 通知遮罩 -->
    <div
      v-if="showNotifications"
      class="notifications-overlay"
      @click="showNotifications = false"
    ></div>

    <!-- 路由视图 -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- 设置弹窗 -->
    <SettingsModal v-if="showSettings" @close="showSettings = false" />

    <!-- 全局 Toast -->
    <TransitionGroup name="fade" tag="div" class="toast-container">
      <div v-for="toast in uiStore.toasts" :key="toast.id" :class="['global-toast', toast.type]">
        {{ toast.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { initI18n, setI18nLanguage, getAvailableLanguages } from '@/plugins/i18n'
import { useUIStore } from '@/stores/ui'
import { useSettingsStore } from '@/stores/settings'
import SettingsModal from '@/components/SettingsModal.vue'

const uiStore = useUIStore()
const settingsStore = useSettingsStore()
const { t } = useI18n()

const showSettings = ref(false)
const showNotifications = ref(false)
const showMobileMenu = ref(false)
const currentModel = ref('')
const availableModels = ref<string[]>([])
const currentLang = ref('zh')
const availableLangs = ref<Array<{ code: string; name: string; native: string; flag: string }>>([])
const modelStatus = ref<'online' | 'offline' | 'loading'>('online')

const modelStatusClass = computed(() => ({
  online: modelStatus.value === 'online',
  offline: modelStatus.value === 'offline',
  loading: modelStatus.value === 'loading',
}))

const modelStatusText = computed(() => {
  switch (modelStatus.value) {
    case 'online': return '模型在线'
    case 'offline': return '模型离线'
    case 'loading': return '模型加载中'
    default: return ''
  }
})

async function loadLanguages() {
  try {
    const langs = await getAvailableLanguages()
    availableLangs.value = langs
    const savedLang = localStorage.getItem('language') || 'zh'
    currentLang.value = langs.find(l => l.code === savedLang) ? savedLang : 'zh'
    await initI18n(currentLang.value)
  } catch (e) {
    availableLangs.value = [
      { code: 'zh', name: '中文', native: '简体中文', flag: '🇨🇳' },
      { code: 'en', name: 'English', native: 'English', flag: '🇺🇸' },
    ]
  }
}

async function loadSettings() {
  try {
    const res = await fetch('/api/config/settings')
    const data = await res.json()
    currentModel.value = data.model?.default_name || 'llama3.2'

    const modelsRes = await fetch('/api/config/models/available')
    if (modelsRes.ok) {
      const modelsData = await modelsRes.json()
      availableModels.value = modelsData.models || []
    }
  } catch (e) {
    console.error('加载设置失败:', e)
  }
}

async function checkModelStatus() {
  modelStatus.value = 'loading'
  try {
    const res = await fetch('/api/health')
    if (res.ok) {
      modelStatus.value = 'online'
    } else {
      modelStatus.value = 'offline'
    }
  } catch (e) {
    modelStatus.value = 'offline'
  }
}

async function onLangChange() {
  await setI18nLanguage(currentLang.value)
  localStorage.setItem('language', currentLang.value)
}

async function onModelChange() {
  try {
    await fetch('/api/config/models/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'ollama', model_name: currentModel.value })
    })
    localStorage.setItem('selectedModel', currentModel.value)
  } catch (e) {
    console.error('切换模型失败:', e)
  }
}

function getNotificationIcon(type: string | undefined): string {
  switch (type) {
    case 'success': return '✓'
    case 'error': return '✗'
    case 'warning': return '⚠'
    default: return 'ℹ'
  }
}

function formatTime(timestamp: number): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return date.toLocaleDateString('zh-CN')
}

// 点击外部关闭通知
function handleClickOutside(e: MouseEvent): void {
  const panel = document.querySelector('.notifications-panel')
  const btn = document.querySelector('.notification-btn')
  if (showNotifications.value && panel && !panel.contains(e.target as Node) && !btn?.contains(e.target as Node)) {
    showNotifications.value = false
  }
}

onMounted(async () => {
  uiStore.init()
  await Promise.all([
    loadLanguages(),
    loadSettings(),
    checkModelStatus(),
  ])
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

/* ===== 顶部导航栏 ===== */
.header {
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(135deg, var(--accent-color) 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
  flex-shrink: 0;
}

.nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
}

.nav-link:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-link.active {
  background: var(--accent-color);
  color: white;
}

.nav-icon { font-size: 1rem; }
.nav-text { }

/* ===== 右侧工具栏 ===== */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 模型状态指示器 */
.model-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.model-indicator.online { border-color: rgba(16, 185, 129, 0.3); }
.model-indicator.offline { border-color: rgba(239, 68, 68, 0.3); }
.model-indicator.loading { border-color: rgba(245, 158, 11, 0.3); }

.model-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
  transition: background 0.2s;
}
.model-indicator.online .model-dot { background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.5); }
.model-indicator.offline .model-dot { background: #ef4444; }
.model-indicator.loading .model-dot { background: #f59e0b; animation: pulse 1.5s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.model-select {
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.85rem;
  max-width: 140px;
}

.lang-select {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 1rem;
  min-width: 50px;
}

/* 通知按钮 */
.notification-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.notification-btn:hover { color: var(--text-primary); }
.notification-btn.has-unread { color: var(--accent-color); }

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.settings-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.settings-btn:hover { color: var(--text-primary); }

/* ===== 移动端菜单按钮 ===== */
.mobile-menu-btn {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 1.3rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== 移动端抽屉菜单 ===== */
.mobile-menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 300;
}

.mobile-menu {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 260px;
  background: var(--bg-secondary);
  z-index: 301;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 4px;
  animation: slideInLeft 0.25s ease;
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

.mobile-menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.mobile-menu-header h2 { margin: 0; font-size: 1.2rem; }
.mobile-menu-close {
  width: 32px; height: 32px; border: none; background: var(--bg-tertiary);
  color: var(--text-secondary); border-radius: 6px; cursor: pointer; font-size: 1.2rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.mobile-nav-link:hover, .mobile-nav-link.router-link-active {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

/* ===== 通知面板 ===== */
.notifications-overlay {
  position: fixed;
  inset: 0;
  z-index: 150;
}

.notifications-panel {
  position: fixed;
  top: 60px;
  right: 20px;
  width: 360px;
  max-height: 500px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  z-index: 151;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.notifications-header h3 { margin: 0; font-size: 1rem; }

.notifications-actions {
  display: flex;
  gap: 8px;
}

.mark-all-btn, .clear-btn {
  padding: 4px 10px;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-all-btn { background: var(--bg-tertiary); color: var(--text-secondary); }
.mark-all-btn:hover { color: var(--text-primary); }

.clear-btn { background: rgba(239,68,68,0.1); color: #ef4444; }
.clear-btn:hover { background: rgba(239,68,68,0.2); }

.notifications-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.notifications-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-secondary);
}

.notifications-empty .empty-icon { font-size: 3rem; margin-bottom: 8px; }

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.notification-item:hover { background: var(--bg-tertiary); }
.notification-item.unread { background: rgba(102,126,234,0.05); }

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.notification-icon.success { background: rgba(16,185,129,0.15); color: #10b981; }
.notification-icon.error { background: rgba(239,68,68,0.15); color: #ef4444; }
.notification-icon.warning { background: rgba(245,158,11,0.15); color: #f59e0b; }
.notification-icon.info { background: rgba(102,126,234,0.15); color: var(--accent-color); }

.notification-content { flex: 1; min-width: 0; }

.notification-title {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 2px;
}

.notification-message {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notification-time {
  font-size: 0.7rem;
  color: var(--text-secondary);
  opacity: 0.7;
  margin-top: 4px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-color);
  flex-shrink: 0;
  margin-top: 4px;
}

/* ===== 路由视图 ===== */
.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ===== 全局 Toast ===== */
.global-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 14px 24px;
  border-radius: 10px;
  font-weight: 500;
  z-index: 9999;
  max-width: 320px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

.global-toast.success { background: #10b981; color: white; }
.global-toast.error { background: #ef4444; color: white; }
.global-toast.warning { background: #f59e0b; color: white; }
.global-toast.info { background: var(--accent-color); color: white; }

/* ===== 过渡动画 ===== */
.slide-down-enter-active, .slide-down-leave-active {
  transition: all 0.25s ease;
}
.slide-down-enter-from { opacity: 0; transform: translateY(-10px); }
.slide-down-leave-to { opacity: 0; transform: translateY(-10px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ===== 响应式 ===== */
@media screen and (max-width: 640px) {
  .header { height: 50px; padding: 0 12px; }

  .logo { font-size: 1.1rem; }

  .nav { display: none; }

  .model-select { max-width: 100px; font-size: 0.8rem; }

  .notifications-panel { width: calc(100vw - 32px); right: 16px; }
}

@media screen and (max-width: 900px) {
  .nav-text { display: none; }
  .nav-link { padding: 8px 12px; }
}

@media screen and (min-width: 641px) {
  .mobile-menu-btn { display: none !important; }
}
</style>
