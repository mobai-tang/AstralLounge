<template>
  <div class="memory-view">
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input v-model="searchQuery" class="input" :placeholder="$t('memory.searchPlaceholder')" />
        </div>
        <select v-model="sortBy" class="select">
          <option value="newest">{{ $t('memory.sortBy') }}: {{ $t('memory.newest') }}</option>
          <option value="oldest">{{ $t('memory.oldest') }}</option>
          <option value="importance">{{ $t('memory.byImportance') }}</option>
          <option value="access">{{ $t('memory.byAccess') }}</option>
        </select>
        <select v-model="filterCategory" class="select">
          <option value="">{{ $t('memory.filterByCategory') }}</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="exportMemories">📤 {{ $t('memory.exportMemories') }}</button>
        <button class="btn btn-secondary" @click="showImportModal = true">📥 {{ $t('memory.importMemories') }}</button>
        <button class="btn btn-primary" @click="showAddModal = true">
          <span>+</span> {{ $t('memory.add') }}
        </button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-value">{{ memories.length }}</span>
        <span class="stat-label">{{ $t('memory.stats.total') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ memories.filter(m => m.source === 'auto').length }}</span>
        <span class="stat-label">{{ $t('memory.stats.longTerm') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ categories.length }}</span>
        <span class="stat-label">{{ $t('memory.stats.categories') }}</span>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div v-if="filteredMemories.length > 0" class="memories-grid">
      <div v-for="mem in filteredMemories" :key="mem.id" class="memory-card">
        <div class="memory-header">
          <div class="memory-title">{{ mem.title || $t('memory.title') }}</div>
          <div class="memory-badges">
            <span class="badge" :class="mem.source === 'auto' ? 'badge-info' : ''">
              {{ mem.source === 'auto' ? $t('memory.auto') : $t('memory.manual') }}
            </span>
            <span v-if="mem.importance" class="badge badge-warning">
              ⭐ {{ mem.importance }}
            </span>
          </div>
        </div>
        <div class="memory-content">{{ mem.content }}</div>
        <div v-if="mem.tags?.length" class="memory-tags">
          <span v-for="tag in mem.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
        <div class="memory-footer">
          <span class="memory-meta">
            <span v-if="mem.accessCount">访问 {{ mem.accessCount }} 次</span>
            <span v-if="mem.createdAt"> · {{ formatDate(mem.createdAt) }}</span>
          </span>
          <div class="memory-actions">
            <button class="btn btn-ghost btn-sm" @click="editMemory(mem)">{{ $t('common.edit') }}</button>
            <button class="btn btn-ghost btn-sm" @click="deleteMemory(mem.id)">{{ $t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🧠</div>
      <div class="empty-title">{{ $t('memory.noMemories') }}</div>
      <button class="btn btn-primary" @click="showAddModal = true">+ {{ $t('memory.addFirst') }}</button>
    </div>

    <!-- 添加/编辑记忆弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingMemory ? $t('common.edit') : $t('memory.add') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('memory.titleLabel') }}</label>
            <input v-model="form.title" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('memory.content') }} *</label>
            <textarea v-model="form.content" class="input textarea" rows="5" required></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('memory.category') }}</label>
              <input v-model="form.category" class="input" />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('memory.importance') }}</label>
              <input v-model.number="form.importance" type="number" class="input" min="1" max="10" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('memory.tags') }}</label>
            <input v-model="form.tagsInput" class="input" placeholder="tag1, tag2, tag3" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveMemory">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Memory } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

const memories = ref<Memory[]>([])
const searchQuery = ref('')
const sortBy = ref('newest')
const filterCategory = ref('')
const showAddModal = ref(false)
const showImportModal = ref(false)
const editingMemory = ref<Memory | null>(null)

const form = reactive({
  title: '',
  content: '',
  category: '',
  importance: 5,
  tagsInput: ''
})

const categories = computed(() => {
  const cats = new Set<string>()
  memories.value.forEach(m => m.category && cats.add(m.category))
  return Array.from(cats).sort()
})

const filteredMemories = computed(() => {
  let list = memories.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(m =>
      m.title?.toLowerCase().includes(q) ||
      m.content.toLowerCase().includes(q) ||
      m.tags?.some(tag => tag.toLowerCase().includes(q))
    )
  }
  if (filterCategory.value) {
    list = list.filter(m => m.category === filterCategory.value)
  }

  return [...list].sort((a, b) => {
    switch (sortBy.value) {
      case 'oldest': return (a.createdAt ?? 0) - (b.createdAt ?? 0)
      case 'importance': return (b.importance ?? 0) - (a.importance ?? 0)
      case 'access': return (b.accessCount ?? 0) - (a.accessCount ?? 0)
      default: return (b.createdAt ?? 0) - (a.createdAt ?? 0)
    }
  })
})

function formatDate(ts: number): string {
  return new Date(ts).toLocaleDateString('zh-CN')
}

function editMemory(mem: Memory) {
  editingMemory.value = mem
  Object.assign(form, {
    title: mem.title ?? '',
    content: mem.content,
    category: mem.category ?? '',
    importance: mem.importance ?? 5,
    tagsInput: mem.tags?.join(', ') ?? ''
  })
  showAddModal.value = true
}

async function saveMemory() {
  if (!form.content.trim()) return
  const data = {
    title: form.title,
    content: form.content,
    category: form.category,
    importance: form.importance,
    tags: form.tagsInput.split(',').map(t => t.trim()).filter(Boolean)
  }
  try {
    const url = editingMemory.value ? `/api/memory/${editingMemory.value.id}` : '/api/memory'
    const method = editingMemory.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res.ok) {
      const saved: Memory = await res.json()
      if (editingMemory.value) {
        const idx = memories.value.findIndex(m => m.id === saved.id)
        if (idx !== -1) memories.value[idx] = saved
      } else {
        memories.value.unshift(saved)
      }
      showAddModal.value = false
      editingMemory.value = null
      resetForm()
      uiStore.showSuccess(t('memory.saveSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function deleteMemory(id: string) {
  if (!confirm(t('memory.confirmDelete'))) return
  try {
    const res = await fetch(`/api/memory/${id}`, { method: 'DELETE' })
    if (res.ok) {
      memories.value = memories.value.filter(m => m.id !== id)
      uiStore.showSuccess(t('memory.deleteSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

function exportMemories() {
  const data = JSON.stringify(memories.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'memories.json'
  a.click()
  URL.revokeObjectURL(url)
}

function resetForm() {
  Object.assign(form, { title: '', content: '', category: '', importance: 5, tagsInput: '' })
}

onMounted(async () => {
  try {
    const res = await fetch('/api/memory')
    if (res.ok) memories.value = await res.json()
  } catch (e) {
    console.error('加载记忆失败:', e)
  }
})
</script>

<style scoped>
.memory-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left { display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap; }
.toolbar-left .search-box { position: relative; min-width: 200px; }
.toolbar-left .search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.toolbar-left .input { padding-left: 32px; }

.toolbar-right { display: flex; gap: 8px; }

.stats-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.stat-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: var(--accent-color); }
.stat-label { font-size: 0.75rem; color: var(--text-secondary); }

.memories-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
  padding-bottom: 20px;
}

.memory-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.memory-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.memory-title { font-weight: 600; font-size: 0.95rem; }
.memory-badges { display: flex; gap: 4px; flex-shrink: 0; }

.memory-content {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
}

.memory-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.memory-tags .tag { font-size: 0.7rem; padding: 2px 7px; }

.memory-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.memory-meta { font-size: 0.75rem; color: var(--text-muted); }
.memory-actions { display: flex; gap: 4px; opacity: 0; transition: opacity var(--transition-fast); }
.memory-card:hover .memory-actions { opacity: 1; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

@media screen and (max-width: 640px) {
  .toolbar-left { flex-direction: column; align-items: stretch; }
  .toolbar-left .search-box { min-width: auto; }
  .stats-bar { gap: 12px; }
  .memories-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
