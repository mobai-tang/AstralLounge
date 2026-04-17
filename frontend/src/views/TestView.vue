<template>
  <div class="test-view">
    <div class="test-container">
      <h1>测试页面</h1>
      <p>这是一个用于调试和测试的页面。</p>

      <div class="test-section">
        <h2>UI 组件测试</h2>
        <div class="test-buttons">
          <button class="btn btn-primary">Primary</button>
          <button class="btn btn-secondary">Secondary</button>
          <button class="btn btn-ghost">Ghost</button>
          <button class="btn btn-danger">Danger</button>
          <button class="btn btn-success">Success</button>
        </div>
      </div>

      <div class="test-section">
        <h2>输入组件</h2>
        <input class="input" placeholder="普通输入框" />
        <textarea class="input textarea" placeholder="文本域"></textarea>
        <select class="select">
          <option>选项 1</option>
          <option>选项 2</option>
        </select>
      </div>

      <div class="test-section">
        <h2>通知测试</h2>
        <div class="test-buttons">
          <button class="btn btn-primary" @click="showSuccessToast">成功通知</button>
          <button class="btn btn-danger" @click="showErrorToast">错误通知</button>
          <button class="btn btn-secondary" @click="showWarningToast">警告通知</button>
          <button class="btn btn-ghost" @click="showInfoToast">信息通知</button>
        </div>
      </div>

      <div class="test-section">
        <h2>标签测试</h2>
        <div class="test-tags">
          <span class="tag">标签 1</span>
          <span class="tag">标签 2</span>
          <span class="badge badge-success">徽章成功</span>
          <span class="badge badge-error">徽章错误</span>
          <span class="badge badge-warning">徽章警告</span>
          <span class="badge badge-info">徽章信息</span>
        </div>
      </div>

      <div class="test-section">
        <h2>开关测试</h2>
        <div class="toggle-row">
          <div :class="['toggle', { active: toggle1 }]" @click="toggle1 = !toggle1"></div>
          <span>开关 1: {{ toggle1 ? 'ON' : 'OFF' }}</span>
        </div>
        <div class="toggle-row">
          <div :class="['toggle', { active: toggle2 }]" @click="toggle2 = !toggle2"></div>
          <span>开关 2: {{ toggle2 ? 'ON' : 'OFF' }}</span>
        </div>
      </div>

      <div class="test-section">
        <h2>加载状态</h2>
        <div class="loading-spinner"></div>
        <div class="test-buttons">
          <button class="btn btn-primary" disabled>
            <span class="loading-spinner"></span>
            加载中...
          </button>
        </div>
      </div>

      <div class="test-section">
        <h2>API 连接测试</h2>
        <div class="test-buttons">
          <button class="btn btn-secondary" @click="testHealth">健康检查</button>
          <button class="btn btn-secondary" @click="testCharacters">获取角色列表</button>
          <button class="btn btn-secondary" @click="testChat">发送测试消息</button>
        </div>
        <div v-if="apiResult" class="api-result">
          <pre>{{ JSON.stringify(apiResult, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()

const toggle1 = ref(false)
const toggle2 = ref(true)
const apiResult = ref<unknown>(null)

function showSuccessToast() { uiStore.showSuccess('这是一条成功通知！') }
function showErrorToast() { uiStore.showError('这是一条错误通知！') }
function showWarningToast() { uiStore.showWarning('这是一条警告通知！') }
function showInfoToast() { uiStore.showInfo('这是一条信息通知！') }

async function testHealth() {
  try {
    const res = await fetch('/api/health')
    apiResult.value = { status: res.status, ok: res.ok }
  } catch (e) {
    apiResult.value = { error: String(e) }
  }
}

async function testCharacters() {
  try {
    const res = await fetch('/api/characters')
    const data = await res.json()
    apiResult.value = { count: Array.isArray(data) ? data.length : 'N/A', data }
  } catch (e) {
    apiResult.value = { error: String(e) }
  }
}

async function testChat() {
  try {
    const res = await fetch('/api/chat/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: '测试会话' }) })
    apiResult.value = { status: res.status, data: await res.json() }
  } catch (e) {
    apiResult.value = { error: String(e) }
  }
}
</script>

<style scoped>
.test-view {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.test-container {
  max-width: 800px;
  margin: 0 auto;
}

h1 { margin-bottom: 8px; }
h2 { font-size: 1.1rem; margin-bottom: 12px; color: var(--text-secondary); }

.test-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 16px;
}

.test-buttons { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }

.input, .select { margin-top: 8px; width: 100%; }
.textarea { min-height: 80px; }

.test-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }

.toggle-row { display: flex; align-items: center; gap: 10px; margin-top: 8px; }

.api-result {
  margin-top: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 12px;
  max-height: 300px;
  overflow: auto;
}

.api-result pre {
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-secondary);
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  margin-right: 4px;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
