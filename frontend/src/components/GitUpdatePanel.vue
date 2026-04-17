<template>
  <div class="git-panel">
    <div class="panel-header">
      <h2>Git 更新管理</h2>
      <button class="btn btn-secondary" @click="checkUpdates" :disabled="checking">
        {{ checking ? '检查中...' : '🔄 检查更新' }}
      </button>
    </div>

    <div v-if="updateInfo" class="update-info">
      <div class="update-badge">
        <span v-if="updateInfo.hasUpdate" class="badge badge-warning">有新版本</span>
        <span v-else class="badge badge-success">已是最新</span>
      </div>
      <div v-if="updateInfo.hasUpdate" class="update-details">
        <div class="version-info">
          <span class="label">当前版本:</span> <span class="value">{{ updateInfo.currentVersion }}</span>
          <span class="label">最新版本:</span> <span class="value highlight">{{ updateInfo.latestVersion }}</span>
        </div>
        <div v-if="updateInfo.releaseNotes" class="release-notes">
          <div class="notes-title">更新内容:</div>
          <div class="notes-content">{{ updateInfo.releaseNotes }}</div>
        </div>
        <div class="update-actions">
          <button class="btn btn-primary" @click="pullUpdate" :disabled="pulling">
            {{ pulling ? '更新中...' : '⬇️ 拉取更新' }}
          </button>
        </div>
      </div>
      <div v-else class="no-update">
        <div class="version-info">
          <span class="label">版本:</span> <span class="value">{{ updateInfo.currentVersion }}</span>
        </div>
      </div>
    </div>

    <div class="git-actions">
      <h3>仓库状态</h3>
      <div class="git-info">
        <div class="git-branch">
          <span class="label">分支:</span>
          <span class="value">{{ gitInfo.branch }}</span>
        </div>
        <div class="git-status">
          <span class="label">状态:</span>
          <span :class="['status-text', gitInfo.isClean ? 'clean' : 'dirty']">
            {{ gitInfo.isClean ? '✅ 干净' : '⚠️ 有未提交更改' }}
          </span>
        </div>
        <div v-if="gitInfo.lastCommit" class="git-commit">
          <span class="label">最近提交:</span>
          <span class="value commit-hash">{{ gitInfo.lastCommit.hash?.slice(0, 7) }}</span>
          <span class="value">{{ gitInfo.lastCommit.message }}</span>
        </div>
      </div>
      <div class="action-row">
        <button class="btn btn-secondary" @click="gitStatus">📋 Git 状态</button>
        <button class="btn btn-secondary" @click="gitPull">⬇️ Git Pull</button>
        <button class="btn btn-secondary" @click="gitLog">📜 提交历史</button>
      </div>
    </div>

    <div v-if="gitLogs.length > 0" class="git-logs">
      <h3>最近提交</h3>
      <div v-for="log in gitLogs" :key="log.hash" class="log-item">
        <span class="log-hash">{{ log.hash.slice(0, 7) }}</span>
        <span class="log-message">{{ log.message }}</span>
        <span class="log-date">{{ formatDate(log.date) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'

const { t } = useI18n()
const uiStore = useUIStore()

const checking = ref(false)
const pulling = ref(false)
const updateInfo = ref<{ hasUpdate: boolean; currentVersion: string; latestVersion: string; releaseNotes?: string } | null>(null)
const gitInfo = reactive({
  branch: 'main',
  isClean: true,
  lastCommit: null as { hash?: string; message?: string } | null
})
const gitLogs = ref<Array<{ hash: string; message: string; date: string }>>([])

async function checkUpdates() {
  checking.value = true
  try {
    const res = await fetch('/api/git/check-update')
    if (res.ok) {
      updateInfo.value = await res.json()
      uiStore.showInfo(updateInfo.value.hasUpdate ? '发现新版本' : '已是最新版本')
    }
  } catch {
    uiStore.showError('检查更新失败')
  } finally {
    checking.value = false
  }
}

async function pullUpdate() {
  pulling.value = true
  try {
    const res = await fetch('/api/git/pull', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      uiStore.showSuccess('更新成功！可能需要重启服务')
      if (data.version) updateInfo.value!.currentVersion = data.version
    }
  } catch {
    uiStore.showError('更新失败')
  } finally {
    pulling.value = false
  }
}

async function gitStatus() {
  try {
    const res = await fetch('/api/git/status')
    if (res.ok) {
      const data = await res.json()
      Object.assign(gitInfo, data)
      uiStore.showInfo(data.isClean ? '工作区干净' : `工作区有 ${data.untracked || 0} 个未跟踪文件`)
    }
  } catch {
    uiStore.showError('获取状态失败')
  }
}

async function gitPull() {
  try {
    const res = await fetch('/api/git/pull', { method: 'POST' })
    if (res.ok) {
      uiStore.showSuccess('Pull 成功')
      await gitStatus()
    }
  } catch {
    uiStore.showError('Pull 失败')
  }
}

async function gitLog() {
  try {
    const res = await fetch('/api/git/log')
    if (res.ok) {
      gitLogs.value = await res.json()
    }
  } catch {
    uiStore.showError('获取日志失败')
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN')
}

onMounted(async () => {
  await gitStatus()
})
</script>

<style scoped>
.git-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h2 { margin: 0; font-size: 1.2rem; }

.update-info, .git-actions, .git-logs {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.update-badge { margin-bottom: 12px; }

.update-details { display: flex; flex-direction: column; gap: 12px; }

.version-info { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.version-info .label { color: var(--text-secondary); font-size: 0.85rem; }
.version-info .value { font-weight: 500; }
.version-info .highlight { color: var(--accent-color); }

.release-notes {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.notes-title { font-weight: 600; font-size: 0.85rem; margin-bottom: 6px; }
.notes-content { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap; }

.update-actions { display: flex; gap: 8px; }

.git-actions h3, .git-logs h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.git-info { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.git-branch, .git-status, .git-commit { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.git-commit { flex-direction: column; align-items: flex-start; }
.label { color: var(--text-secondary); font-size: 0.85rem; }
.value { font-weight: 500; }
.commit-hash { color: var(--accent-color); font-family: monospace; }
.status-text.clean { color: #10b981; }
.status-text.dirty { color: #f59e0b; }

.action-row { display: flex; gap: 8px; flex-wrap: wrap; }

.git-logs {
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  border-bottom: 1px solid var(--border-color);
}

.log-item:last-child { border-bottom: none; }
.log-hash { color: var(--accent-color); font-family: monospace; font-size: 0.8rem; }
.log-message { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-date { color: var(--text-secondary); font-size: 0.75rem; flex-shrink: 0; }
</style>
