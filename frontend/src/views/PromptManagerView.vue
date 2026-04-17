<template>
  <div class="prompt-manager">
    <div class="toolbar">
      <div class="toolbar-left">
        <h2>Prompt Manager</h2>
        <span class="subtitle">提示词管理器</span>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-ghost btn-sm" @click="importPrompt">📥 导入</button>
        <button class="btn btn-ghost btn-sm" @click="exportPrompt">📤 导出</button>
        <button class="btn btn-ghost btn-sm" @click="resetDefaults">🔄 重置默认</button>
        <button class="btn btn-primary btn-sm" @click="saveAll">💾 保存全部</button>
      </div>
    </div>

    <!-- Token 统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总 Token</span>
        <span class="stat-value">{{ totalTokens }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">上下文限制</span>
        <span class="stat-value">{{ contextLimit }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">使用率</span>
        <span :class="['stat-value', usageClass]">{{ usagePercent }}%</span>
      </div>
      <div class="usage-bar">
        <div class="usage-fill" :style="{ width: Math.min(usagePercent, 100) + '%' }"></div>
      </div>
    </div>

    <div class="pm-layout">
      <!-- 左侧：提示词组件列表 -->
      <aside class="components-panel">
        <div class="panel-title">提示词组件</div>
        <div
          v-for="comp in components"
          :key="comp.id"
          :class="['component-item', { active: selectedId === comp.id, disabled: !comp.enabled }]"
          @click="selectComponent(comp)"
          draggable="true"
          @dragstart="onDragStart($event, comp.id)"
          @dragover.prevent
          @drop="onDrop($event, comp.id)"
        >
          <div class="drag-handle">☰</div>
          <div class="comp-info">
            <div class="comp-name">{{ comp.icon }} {{ comp.name }}</div>
            <div class="comp-meta">{{ comp.tokens }} tokens</div>
          </div>
          <div class="comp-toggle" @click.stop="toggleComponent(comp)">
            <div :class="['toggle', { active: comp.enabled }]"></div>
          </div>
        </div>
      </aside>

      <!-- 右侧：编辑器 -->
      <main class="editor-panel">
        <div v-if="selected" class="editor-content">
          <div class="editor-header">
            <div class="editor-title">
              <span>{{ selected.icon }}</span>
              <span>{{ selected.name }}</span>
            </div>
            <div class="editor-actions">
              <span class="token-badge">{{ selected.tokens }} tokens</span>
              <button class="btn btn-ghost btn-sm" @click="toggleComponent(selected)">
                {{ selected.enabled ? '🔴 禁用' : '🟢 启用' }}
              </button>
            </div>
          </div>
          <textarea
            v-model="selected.content"
            class="editor-textarea"
            :placeholder="selected.placeholder"
            rows="20"
            @input="updateTokens"
          ></textarea>
          <div class="editor-footer">
            <span class="hint">{{ selected.hint }}</span>
            <div class="footer-actions">
              <button class="btn btn-ghost btn-sm" @click="selected.content = selected.defaultContent">↩️ 恢复默认</button>
            </div>
          </div>
        </div>
        <div v-else class="editor-empty">
          <div class="empty-icon">📝</div>
          <p>选择一个组件进行编辑</p>
        </div>
      </main>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>导入提示词配置</h2>
          <button class="btn btn-ghost btn-icon" @click="showImportModal = false">×</button>
        </div>
        <div class="modal-body">
          <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px;">
            从 JSON 文件或剪贴板导入提示词配置
          </p>
          <textarea v-model="importText" class="input textarea" rows="8" placeholder="粘贴 JSON 配置..."></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showImportModal = false">取消</button>
          <button class="btn btn-primary" @click="doImport">导入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()

interface PromptComponent {
  id: string
  name: string
  icon: string
  content: string
  defaultContent: string
  placeholder: string
  hint: string
  enabled: boolean
  tokens: number
  order: number
}

const DEFAULT_COMPONENTS: PromptComponent[] = [
  {
    id: 'system',
    name: '系统提示词',
    icon: '⚙️',
    content: '你是 AstralLounge，一个智能对话助手。请根据上下文进行自然的对话。',
    defaultContent: '你是 AstralLounge，一个智能对话助手。请根据上下文进行自然的对话。',
    placeholder: '定义 AI 的整体行为和角色...',
    hint: '系统级指令，控制 AI 的整体行为',
    enabled: true,
    tokens: 0,
    order: 1,
  },
  {
    id: 'character',
    name: '角色定义',
    icon: '👤',
    content: '',
    defaultContent: '',
    placeholder: '{{char}} 的角色设定会自动填充到这里...',
    hint: '当前角色的描述、性格、场景设定',
    enabled: true,
    tokens: 0,
    order: 2,
  },
  {
    id: 'persona',
    name: '用户人设',
    icon: '🪪',
    content: '',
    defaultContent: '',
    placeholder: '你的用户人设会自动填充到这里...',
    hint: '当前激活的用户人设定义',
    enabled: true,
    tokens: 0,
    order: 3,
  },
  {
    id: 'lorebook',
    name: '世界设定',
    icon: '📚',
    content: '',
    defaultContent: '',
    placeholder: '激活的世界设定条目会自动插入...',
    hint: '来自世界设定（Lorebook）的激活条目',
    enabled: true,
    tokens: 0,
    order: 4,
  },
  {
    id: 'memory',
    name: '记忆系统',
    icon: '🧠',
    content: '',
    defaultContent: '',
    placeholder: '相关的记忆内容会自动插入...',
    hint: '从记忆系统中检索的相关记忆',
    enabled: true,
    tokens: 0,
    order: 5,
  },
  {
    id: 'examples',
    name: '示例对话',
    icon: '💬',
    content: '',
    defaultContent: '',
    placeholder: '示例对话（可提升角色扮演质量）...',
    hint: '定义一些示例对话来引导 AI 的回复风格',
    enabled: false,
    tokens: 0,
    order: 6,
  },
  {
    id: 'authors_note',
    name: "Author's Note",
    icon: '📝',
    content: '',
    defaultContent: '',
    placeholder: '给 AI 的额外提示（通常放在对话末尾）...',
    hint: "Author's Note，深度提示，通常放在对话末尾附近",
    enabled: false,
    tokens: 0,
    order: 7,
  },
  {
    id: 'custom',
    name: '自定义指令',
    icon: '✨',
    content: '',
    defaultContent: '',
    placeholder: '任何自定义的额外指令...',
    hint: '你自己添加的自定义提示词',
    enabled: false,
    tokens: 0,
    order: 8,
  },
]

const components = ref<PromptComponent[]>([...DEFAULT_COMPONENTS.map(c => ({ ...c }))])
const selectedId = ref<string | null>('system')
const showImportModal = ref(false)
const importText = ref('')
const contextLimit = ref(4096)
const dragSourceId = ref<string | null>(null)

const selected = computed(() => components.value.find(c => c.id === selectedId.value) ?? null)

const totalTokens = computed(() => {
  return components.value
    .filter(c => c.enabled)
    .reduce((sum, c) => sum + c.tokens, 0)
})

const usagePercent = computed(() => {
  if (contextLimit.value === 0) return 0
  return Math.round((totalTokens.value / contextLimit.value) * 100)
})

const usageClass = computed(() => {
  if (usagePercent.value > 90) return 'danger'
  if (usagePercent.value > 70) return 'warning'
  return 'normal'
})

function selectComponent(comp: PromptComponent) {
  selectedId.value = comp.id
}

function toggleComponent(comp: PromptComponent) {
  comp.enabled = !comp.enabled
  updateTokens()
}

function updateTokens() {
  for (const comp of components.value) {
    comp.tokens = Math.ceil(comp.content.length / 4)
  }
}

function saveAll() {
  const data = {
    components: components.value.map(c => ({
      id: c.id,
      content: c.content,
      enabled: c.enabled,
      order: c.order,
    })),
  }
  localStorage.setItem('prompt_manager_config', JSON.stringify(data))
  uiStore.showSuccess('保存成功')
}

function resetDefaults() {
  if (!confirm('确定要重置为默认配置吗？')) return
  components.value = DEFAULT_COMPONENTS.map(c => ({ ...c }))
  localStorage.removeItem('prompt_manager_config')
  updateTokens()
  uiStore.showSuccess('已重置为默认')
}

function exportPrompt() {
  const data = {
    components: components.value.map(c => ({
      id: c.id,
      content: c.content,
      enabled: c.enabled,
      order: c.order,
    })),
  }
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'prompt_manager_config.json'
  a.click()
  URL.revokeObjectURL(url)
  uiStore.showSuccess('已导出配置文件')
}

function importPrompt() {
  importText.value = ''
  showImportModal.value = true
}

function doImport() {
  try {
    const data = JSON.parse(importText.value)
    for (const item of data.components ?? []) {
      const comp = components.value.find(c => c.id === item.id)
      if (comp) {
        comp.content = item.content ?? comp.defaultContent
        comp.enabled = item.enabled ?? comp.enabled
        comp.order = item.order ?? comp.order
      }
    }
    components.value.sort((a, b) => a.order - b.order)
    updateTokens()
    showImportModal.value = false
    uiStore.showSuccess('导入成功')
  } catch {
    uiStore.showError('JSON 格式错误')
  }
}

function onDragStart(e: DragEvent, id: string) {
  dragSourceId.value = id
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDrop(e: DragEvent, targetId: string) {
  if (!dragSourceId.value || dragSourceId.value === targetId) return
  const from = components.value.findIndex(c => c.id === dragSourceId.value)
  const to = components.value.findIndex(c => c.id === targetId)
  if (from === -1 || to === -1) return
  const [item] = components.value.splice(from, 1)
  components.value.splice(to, 0, item)
  components.value.forEach((c, i) => { c.order = i + 1 })
  dragSourceId.value = null
}

onMounted(() => {
  const saved = localStorage.getItem('prompt_manager_config')
  if (saved) {
    try {
      const data = JSON.parse(saved)
      for (const item of data.components ?? []) {
        const comp = components.value.find(c => c.id === item.id)
        if (comp) {
          comp.content = item.content ?? comp.defaultContent
          comp.enabled = item.enabled ?? comp.enabled
          comp.order = item.order ?? comp.order
        }
      }
      components.value.sort((a, b) => a.order - b.order)
    } catch {
      console.error('加载 Prompt Manager 配置失败')
    }
  }
  updateTokens()
})
</script>

<style scoped>
.prompt-manager {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 12px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.toolbar-left h2 { margin: 0; font-size: 1.1rem; }
.subtitle { font-size: 0.85rem; color: var(--text-secondary); }
.toolbar-right { display: flex; gap: 6px; }

.stats-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.stat-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.stat-label { font-size: 0.7rem; color: var(--text-muted); }
.stat-value { font-size: 1rem; font-weight: 700; }
.stat-value.danger { color: #ef4444; }
.stat-value.warning { color: #f59e0b; }
.stat-value.normal { color: #10b981; }

.usage-bar {
  flex: 1;
  min-width: 120px;
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}
.usage-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.pm-layout {
  flex: 1;
  display: flex;
  gap: 12px;
  overflow: hidden;
}

.components-panel {
  width: 260px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow-y: auto;
  padding: 8px;
}

.panel-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 8px 8px 4px;
}

.component-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.component-item:hover { background: var(--bg-tertiary); }
.component-item.active { background: var(--accent-subtle); border: 1px solid var(--accent-color); }
.component-item.disabled { opacity: 0.5; }

.drag-handle { color: var(--text-muted); font-size: 0.8rem; cursor: grab; }

.comp-info { flex: 1; min-width: 0; }
.comp-name { font-size: 0.85rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.comp-meta { font-size: 0.7rem; color: var(--text-muted); }

.comp-toggle { flex-shrink: 0; }

.toggle {
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
}
.toggle::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--text-muted);
  transition: all var(--transition-fast);
}
.toggle.active {
  background: var(--accent-color);
  border-color: var(--accent-color);
}
.toggle.active::after {
  left: 18px;
  background: white;
}

.editor-panel {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.editor-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}
.editor-title { display: flex; align-items: center; gap: 8px; font-weight: 600; }
.editor-actions { display: flex; align-items: center; gap: 8px; }

.token-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: var(--bg-primary);
  border-radius: 12px;
  color: var(--text-secondary);
}

.editor-textarea {
  flex: 1;
  padding: 16px;
  background: var(--bg-primary);
  color: var(--text-primary);
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.6;
  min-height: 200px;
}

.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}
.hint { font-size: 0.75rem; color: var(--text-muted); }
.footer-actions { display: flex; gap: 6px; }

.editor-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}
.empty-icon { font-size: 3rem; }

@media screen and (max-width: 768px) {
  .pm-layout { flex-direction: column; }
  .components-panel { width: 100%; max-height: 200px; }
}
</style>
