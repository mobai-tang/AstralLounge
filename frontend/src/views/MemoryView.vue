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
          <option value="relevance" v-if="searchQuery">{{ $t('memory.byRelevance') }}</option>
        </select>
        <select v-model="filterCategory" class="select">
          <option value="">{{ $t('memory.filterByCategory') }}</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
        <select v-model="filterSource" class="select">
          <option value="">{{ $t('memory.filterBySource') }}</option>
          <option value="manual">{{ $t('memory.manual') }}</option>
          <option value="auto">{{ $t('memory.auto') }}</option>
          <option value="summarized">{{ $t('memory.summarized') }}</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="showMemoryStats = true" title="记忆统计">
          📊 {{ $t('memory.stats.title') }}
        </button>
        <button class="btn btn-secondary" @click="showAiSuggest = true" title="AI 建议">
          🤖 {{ $t('memory.aiSuggest') }}
        </button>
        <button class="btn btn-secondary" @click="showMemoryGraph = true" title="关系图">
          🕸️ {{ $t('memory.relationGraph') }}
        </button>
        <button class="btn btn-secondary" @click="exportMemories">📤 {{ $t('memory.exportMemories') }}</button>
        <button class="btn btn-secondary" @click="showImportModal = true">📥 {{ $t('memory.importMemories') }}</button>
        <button class="btn btn-primary" @click="showAddModal = true">
          <span>+</span> {{ $t('memory.add') }}
        </button>
      </div>
    </div>

    <!-- 高级搜索栏 -->
    <div v-if="showAdvancedSearch" class="advanced-search">
      <div class="search-row">
        <div class="form-group">
          <label class="form-label">{{ $t('memory.importanceRange') }}</label>
          <div class="range-input-row">
            <input v-model.number="importanceMin" type="number" class="input" min="1" max="10" />
            <span>-</span>
            <input v-model.number="importanceMax" type="number" class="input" min="1" max="10" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('memory.dateRange') }}</label>
          <div class="date-input-row">
            <input v-model="dateFrom" type="date" class="input" />
            <span>-</span>
            <input v-model="dateTo" type="date" class="input" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('memory.tags') }}</label>
          <input v-model="tagFilter" class="input" :placeholder="$t('memory.tagsPlaceholder')" />
        </div>
        <button class="btn btn-ghost btn-sm" @click="showAdvancedSearch = false">{{ $t('common.close') }}</button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <div class="stat-item" :class="{ highlight: stats.total > 0 }">
        <span class="stat-value">{{ stats.total }}</span>
        <span class="stat-label">{{ $t('memory.stats.total') }}</span>
      </div>
      <div class="stat-item" :class="{ highlight: stats.manual > 0 }">
        <span class="stat-value">{{ stats.manual }}</span>
        <span class="stat-label">{{ $t('memory.stats.manual') }}</span>
      </div>
      <div class="stat-item" :class="{ highlight: stats.auto > 0 }">
        <span class="stat-value">{{ stats.auto }}</span>
        <span class="stat-label">{{ $t('memory.stats.longTerm') }}</span>
      </div>
      <div class="stat-item" :class="{ highlight: stats.summarized > 0 }">
        <span class="stat-value">{{ stats.summarized }}</span>
        <span class="stat-label">{{ $t('memory.stats.summarized') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ categories.length }}</span>
        <span class="stat-label">{{ $t('memory.stats.categories') }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ stats.accessRate }}</span>
        <span class="stat-label">{{ $t('memory.stats.accessRate') }}</span>
      </div>
    </div>

    <!-- 记忆衰减指示器 -->
    <div v-if="showDecayIndicator" class="decay-indicator">
      <span class="decay-icon">⏰</span>
      <span class="decay-text">{{ $t('memory.decayInfo') }}: {{ decayInfo }}</span>
      <div class="decay-bar">
        <div class="decay-fill" :style="{ width: decayPercentage + '%' }"></div>
      </div>
    </div>

    <!-- 记忆列表 -->
    <div v-if="filteredMemories.length > 0" class="memories-grid">
      <div
        v-for="mem in filteredMemories"
        :key="mem.id"
        :class="['memory-card', { highlighted: isHighlighted(mem), stale: isStale(mem) }]"
        @click="viewMemoryDetail(mem)"
      >
        <div class="memory-header">
          <div class="memory-title">{{ mem.title || $t('memory.title') }}</div>
          <div class="memory-badges">
            <span class="badge" :class="mem.source === 'auto' ? 'badge-info' : ''">
              {{ mem.source === 'auto' ? $t('memory.auto') : mem.source === 'summarized' ? $t('memory.summarized') : $t('memory.manual') }}
            </span>
            <span v-if="mem.importance" class="badge badge-warning">
              ⭐ {{ mem.importance }}
            </span>
            <span v-if="isStale(mem)" class="badge badge-stale" :title="$t('memory.staleWarning')">
              🕐
            </span>
          </div>
        </div>
        <div class="memory-content">{{ mem.content }}</div>
        <div v-if="mem.tags?.length" class="memory-tags">
          <span v-for="tag in mem.tags" :key="tag" class="tag" @click.stop="filterByTag(tag)">{{ tag }}</span>
        </div>
        <div class="memory-footer">
          <span class="memory-meta">
            <span v-if="mem.accessCount">{{ $t('memory.accessed') }} {{ mem.accessCount }} {{ $t('memory.times') }}</span>
            <span v-if="mem.createdAt"> · {{ formatDate(mem.createdAt) }}</span>
          </span>
          <div class="memory-actions">
            <button class="btn btn-ghost btn-sm" @click.stop="boostMemory(mem)">⬆️</button>
            <button class="btn btn-ghost btn-sm" @click.stop="editMemory(mem)">{{ $t('common.edit') }}</button>
            <button class="btn btn-ghost btn-sm" @click.stop="deleteMemory(mem.id)">{{ $t('common.delete') }}</button>
          </div>
        </div>
        <!-- 衰减进度条 -->
        <div v-if="mem.lastAccessedAt" class="decay-progress">
          <div class="decay-progress-fill" :style="{ width: getDecayProgress(mem) + '%' }"></div>
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
              <input v-model="form.category" class="input" list="categories-list" />
              <datalist id="categories-list">
                <option v-for="cat in categories" :key="cat" :value="cat" />
              </datalist>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('memory.importance') }}</label>
              <div class="importance-slider">
                <input v-model.number="form.importance" type="range" min="1" max="10" step="1" class="range-input" />
                <span class="importance-value">{{ form.importance }}</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('memory.tags') }}</label>
            <input v-model="form.tagsInput" class="input" placeholder="tag1, tag2, tag3" />
          </div>
          <div v-if="editingMemory" class="form-group">
            <label class="form-label">{{ $t('memory.source') }}: {{ editingMemory.source || 'manual' }}</label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveMemory">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>

    <!-- 记忆详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h2>{{ viewingMemory?.title || $t('memory.title') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="memory-detail-meta">
            <span class="badge" :class="viewingMemory?.source === 'auto' ? 'badge-info' : ''">
              {{ viewingMemory?.source || 'manual' }}
            </span>
            <span v-if="viewingMemory?.importance">⭐ {{ viewingMemory.importance }}</span>
            <span>{{ formatDate(viewingMemory?.createdAt || 0) }}</span>
            <span>{{ $t('memory.accessed') }} {{ viewingMemory?.accessCount || 0 }} {{ $t('memory.times') }}</span>
          </div>
          <div class="memory-detail-content">{{ viewingMemory?.content }}</div>
          <div v-if="viewingMemory?.tags?.length" class="memory-detail-tags">
            <span v-for="tag in viewingMemory.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <div v-if="viewingMemory?.relatedMemories?.length" class="related-memories">
            <h4>{{ $t('memory.relatedMemories') }}</h4>
            <div class="related-list">
              <div v-for="rel in viewingMemory.relatedMemories" :key="rel.id" class="related-item" @click="viewMemoryDetail(rel)">
                <span class="related-title">{{ rel.title || rel.content.substring(0, 30) + '...' }}</span>
                <span class="related-score">{{ (rel.similarity * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">{{ $t('common.close') }}</button>
          <button class="btn btn-primary" @click="editMemory(viewingMemory); showDetailModal = false">{{ $t('common.edit') }}</button>
        </div>
      </div>
    </div>

    <!-- 记忆统计弹窗 -->
    <div v-if="showMemoryStats" class="modal-overlay" @click.self="showMemoryStats = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('memory.stats.title') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showMemoryStats = false">×</button>
        </div>
        <div class="modal-body">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">{{ $t('memory.stats.total') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🖊️</div>
              <div class="stat-value">{{ stats.manual }}</div>
              <div class="stat-label">{{ $t('memory.stats.manual') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🤖</div>
              <div class="stat-value">{{ stats.auto }}</div>
              <div class="stat-label">{{ $t('memory.stats.auto') }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">📝</div>
              <div class="stat-value">{{ stats.summarized }}</div>
              <div class="stat-label">{{ $t('memory.stats.summarized') }}</div>
            </div>
          </div>
          <div class="chart-container">
            <h4>{{ $t('memory.stats.distribution') }}</h4>
            <div class="importance-distribution">
              <div v-for="n in 10" :key="n" class="dist-bar">
                <div class="dist-value">{{ getImportanceCount(n) }}</div>
                <div class="dist-bar-fill" :style="{ height: (getImportanceCount(n) / maxImportanceCount * 100) + '%' }"></div>
                <div class="dist-label">{{ n }}</div>
              </div>
            </div>
          </div>
          <div class="chart-container">
            <h4>{{ $t('memory.stats.categoryDist') }}</h4>
            <div class="category-tags">
              <span v-for="cat in categories" :key="cat" class="category-tag">
                {{ cat }} ({{ getCategoryCount(cat) }})
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showMemoryStats = false">{{ $t('common.close') }}</button>
          <button class="btn btn-danger" @click="optimizeMemories">{{ $t('memory.optimize') }}</button>
        </div>
      </div>
    </div>

    <!-- AI 建议弹窗 -->
    <div v-if="showAiSuggest" class="modal-overlay" @click.self="showAiSuggest = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h2>{{ $t('memory.aiSuggest') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showAiSuggest = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="aiSuggestions.length === 0 && !isGeneratingSuggestions" class="suggestions-empty">
            <p>{{ $t('memory.aiSuggestDesc') }}</p>
            <button class="btn btn-primary" @click="generateSuggestions" :disabled="isGeneratingSuggestions">
              {{ isGeneratingSuggestions ? $t('memory.generating') : $t('memory.generateSuggestions') }}
            </button>
          </div>
          <div v-else-if="isGeneratingSuggestions" class="generating">
            <span class="generating-icon">🤖</span>
            <span>{{ $t('memory.generating') }}...</span>
          </div>
          <div v-else class="suggestions-list">
            <div v-for="(sug, idx) in aiSuggestions" :key="idx" class="suggestion-item">
              <div class="suggestion-type">{{ sug.type }}</div>
              <div class="suggestion-content">{{ sug.content }}</div>
              <div class="suggestion-actions">
                <button class="btn btn-primary btn-sm" @click="applySuggestion(sug)">{{ $t('memory.apply') }}</button>
                <button class="btn btn-ghost btn-sm" @click="dismissSuggestion(idx)">{{ $t('memory.dismiss') }}</button>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAiSuggest = false">{{ $t('common.close') }}</button>
        </div>
      </div>
    </div>

    <!-- 关系图弹窗 -->
    <div v-if="showMemoryGraph" class="modal-overlay" @click.self="showMemoryGraph = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h2>{{ $t('memory.relationGraph') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showMemoryGraph = false">×</button>
        </div>
        <div class="modal-body graph-body">
          <div class="graph-container" ref="graphContainer">
            <div class="graph-placeholder">
              <span class="graph-icon">🕸️</span>
              <p>{{ $t('memory.graphDesc') }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showMemoryGraph = false">{{ $t('common.close') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Memory } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

const memories = ref<Memory[]>([])
const searchQuery = ref('')
const sortBy = ref('newest')
const filterCategory = ref('')
const filterSource = ref('')
const showAddModal = ref(false)
const showImportModal = ref(false)
const showDetailModal = ref(false)
const showMemoryStats = ref(false)
const showAiSuggest = ref(false)
const showMemoryGraph = ref(false)
const showAdvancedSearch = ref(false)
const showDecayIndicator = ref(true)
const editingMemory = ref<Memory | null>(null)
const viewingMemory = ref<Memory | null>(null)
const isGeneratingSuggestions = ref(false)

const form = reactive({
  title: '',
  content: '',
  category: '',
  importance: 5,
  tagsInput: ''
})

const advancedFilters = reactive({
  importanceMin: 1,
  importanceMax: 10,
  dateFrom: '',
  dateTo: '',
  tagFilter: ''
})

const importanceMin = ref(1)
const importanceMax = ref(10)
const dateFrom = ref('')
const dateTo = ref('')
const tagFilter = ref('')

const aiSuggestions = ref<Array<{ type: string; content: string; action?: any }>>([])

const graphContainer = ref<HTMLElement | null>(null)

const DECAY_THRESHOLD_DAYS = 30
const DECAY_HALF_LIFE_DAYS = 60

const categories = computed(() => {
  const cats = new Set<string>()
  memories.value.forEach(m => m.category && cats.add(m.category))
  return Array.from(cats).sort()
})

const stats = computed(() => {
  const total = memories.value.length
  const manual = memories.value.filter(m => !m.source || m.source === 'manual').length
  const auto = memories.value.filter(m => m.source === 'auto').length
  const summarized = memories.value.filter(m => m.source === 'summarized').length
  const totalAccess = memories.value.reduce((acc, m) => acc + (m.accessCount || 0), 0)
  const accessRate = total > 0 ? Math.round(totalAccess / total * 10) / 10 : 0
  return { total, manual, auto, summarized, categories: categories.value.length, accessRate }
})

const maxImportanceCount = computed(() => {
  const counts: Record<number, number> = {}
  for (let i = 1; i <= 10; i++) counts[i] = 0
  memories.value.forEach(m => {
    const imp = m.importance || 5
    counts[imp] = (counts[imp] || 0) + 1
  })
  return Math.max(...Object.values(counts), 1)
})

const decayInfo = computed(() => {
  const staleCount = memories.value.filter(m => isStale(m)).length
  return `${staleCount} ${t('memory.staleMemories')}`
})

const decayPercentage = computed(() => {
  if (memories.value.length === 0) return 0
  const staleCount = memories.value.filter(m => isStale(m)).length
  return Math.round((staleCount / memories.value.length) * 100)
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

  if (filterSource.value) {
    list = list.filter(m => {
      if (filterSource.value === 'summarized') return m.source === 'summarized'
      return m.source === filterSource.value
    })
  }

  if (importanceMin.value > 1 || importanceMax.value < 10) {
    list = list.filter(m => {
      const imp = m.importance || 5
      return imp >= importanceMin.value && imp <= importanceMax.value
    })
  }

  if (dateFrom.value) {
    const from = new Date(dateFrom.value).getTime()
    list = list.filter(m => (m.createdAt || 0) >= from)
  }

  if (dateTo.value) {
    const to = new Date(dateTo.value).getTime() + 86400000
    list = list.filter(m => (m.createdAt || 0) <= to)
  }

  if (tagFilter.value.trim()) {
    const tags = tagFilter.value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean)
    if (tags.length) {
      list = list.filter(m => m.tags?.some(tag => tags.includes(tag.toLowerCase())))
    }
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

function isStale(mem: Memory): boolean {
  const lastAccess = mem.lastAccessedAt || mem.createdAt || Date.now()
  const daysSinceAccess = (Date.now() - lastAccess) / 86400000
  return daysSinceAccess > DECAY_THRESHOLD_DAYS
}

function isHighlighted(mem: Memory): boolean {
  if (!searchQuery.value.trim()) return false
  const q = searchQuery.value.toLowerCase()
  return mem.content.toLowerCase().includes(q) || mem.title?.toLowerCase().includes(q)
}

function getDecayProgress(mem: Memory): number {
  const lastAccess = mem.lastAccessedAt || mem.createdAt || Date.now()
  const daysSinceAccess = (Date.now() - lastAccess) / 86400000
  return Math.min(100, Math.max(0, (daysSinceAccess / DECAY_HALF_LIFE_DAYS) * 100))
}

function getImportanceCount(n: number): number {
  return memories.value.filter(m => (m.importance || 5) === n).length
}

function getCategoryCount(cat: string): number {
  return memories.value.filter(m => m.category === cat).length
}

function formatDate(ts: number): string {
  return new Date(ts).toLocaleDateString('zh-CN')
}

function filterByTag(tag: string) {
  tagFilter.value = tag
}

function viewMemoryDetail(mem: Memory) {
  viewingMemory.value = mem
  showDetailModal.value = true

  const idx = memories.value.findIndex(m => m.id === mem.id)
  if (idx !== -1) {
    memories.value[idx].accessCount = (memories.value[idx].accessCount || 0) + 1
    memories.value[idx].lastAccessedAt = Date.now()
  }
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
    tags: form.tagsInput.split(',').map(t => t.trim()).filter(Boolean),
    lastAccessedAt: Date.now()
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

async function boostMemory(mem: Memory) {
  mem.importance = Math.min(10, (mem.importance || 5) + 1)
  mem.lastAccessedAt = Date.now()
  await fetch(`/api/memory/${mem.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mem)
  })
  uiStore.showSuccess(t('memory.boostSuccess'))
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

async function generateSuggestions() {
  isGeneratingSuggestions.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1500))
    aiSuggestions.value = [
      { type: 'merge', content: t('memory.suggestMerge') },
      { type: 'enhance', content: t('memory.suggestEnhance') },
      { type: 'archive', content: t('memory.suggestArchive') },
    ]
  } finally {
    isGeneratingSuggestions.value = false
  }
}

function applySuggestion(sug: any) {
  uiStore.showSuccess(t('memory.suggestionApplied'))
  const idx = aiSuggestions.value.indexOf(sug)
  if (idx !== -1) aiSuggestions.value.splice(idx, 1)
}

function dismissSuggestion(idx: number) {
  aiSuggestions.value.splice(idx, 1)
}

async function optimizeMemories() {
  const staleMemories = memories.value.filter(m => isStale(m))
  if (staleMemories.length === 0) {
    uiStore.showInfo(t('memory.noStaleMemories'))
    return
  }
  if (confirm(t('memory.optimizeConfirm', { count: staleMemories.length }))) {
    memories.value = memories.value.filter(m => !isStale(m) || (m.importance && m.importance >= 8))
    uiStore.showSuccess(t('memory.optimizeSuccess'))
    showMemoryStats.value = false
  }
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

.toolbar-right { display: flex; gap: 8px; flex-wrap: wrap; }

.advanced-search {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.search-row { display: flex; align-items: flex-end; gap: 16px; flex-wrap: wrap; }

.range-input-row, .date-input-row { display: flex; align-items: center; gap: 8px; }

.stats-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.stat-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.stat-item.highlight .stat-value { color: var(--accent-color); }
.stat-value { font-size: 1.3rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: var(--text-secondary); }

.decay-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.decay-icon { font-size: 1rem; }
.decay-text { flex: 1; }
.decay-bar { width: 120px; height: 6px; background: var(--bg-tertiary); border-radius: 3px; overflow: hidden; }
.decay-fill { height: 100%; background: #f59e0b; transition: width 0.3s ease; }

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
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.memory-card:hover { border-color: var(--border-hover); transform: translateY(-2px); }
.memory-card.highlighted { border-color: var(--accent-color); background: var(--accent-subtle); }
.memory-card.stale { opacity: 0.7; }

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
.memory-tags .tag { font-size: 0.7rem; padding: 2px 7px; cursor: pointer; }
.memory-tags .tag:hover { background: var(--accent-subtle); }

.memory-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.memory-meta { font-size: 0.75rem; color: var(--text-muted); }
.memory-actions { display: flex; gap: 4px; opacity: 0; transition: opacity var(--transition-fast); }
.memory-card:hover .memory-actions { opacity: 1; }

.decay-progress { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: var(--bg-tertiary); }
.decay-progress-fill { height: 100%; background: #f59e0b; transition: width 0.3s ease; }

.badge { font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: var(--bg-tertiary); }
.badge-info { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.badge-warning { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.badge-stale { background: rgba(107, 114, 128, 0.2); color: #6b7280; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.importance-slider { display: flex; align-items: center; gap: 8px; }
.importance-slider .range-input { flex: 1; accent-color: var(--accent-color); }
.importance-value { min-width: 24px; text-align: center; font-weight: 600; color: var(--accent-color); }

.memory-detail-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; font-size: 0.85rem; color: var(--text-secondary); }
.memory-detail-content { font-size: 0.95rem; line-height: 1.7; margin-bottom: 16px; white-space: pre-wrap; }
.memory-detail-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }

.related-memories { border-top: 1px solid var(--border-color); padding-top: 12px; }
.related-memories h4 { font-size: 0.9rem; margin-bottom: 8px; color: var(--text-secondary); }
.related-list { display: flex; flex-direction: column; gap: 4px; }
.related-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}
.related-item:hover { background: var(--accent-subtle); }
.related-score { font-size: 0.75rem; color: var(--text-muted); }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: var(--bg-tertiary); border-radius: var(--radius-md); padding: 16px; text-align: center; }
.stat-icon { font-size: 1.5rem; margin-bottom: 8px; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: var(--accent-color); }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }

.chart-container { margin-top: 16px; }
.chart-container h4 { font-size: 0.9rem; margin-bottom: 12px; color: var(--text-secondary); }
.importance-distribution { display: flex; align-items: flex-end; gap: 4px; height: 100px; }
.dist-bar { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dist-value { font-size: 0.7rem; color: var(--text-muted); }
.dist-bar-fill { width: 100%; background: var(--accent-color); border-radius: 2px 2px 0 0; min-height: 2px; transition: height 0.3s ease; }
.dist-label { font-size: 0.7rem; color: var(--text-muted); }

.category-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.category-tag { padding: 4px 10px; background: var(--bg-tertiary); border-radius: var(--radius-sm); font-size: 0.8rem; }

.suggestions-empty { text-align: center; padding: 20px; }
.suggestions-empty p { color: var(--text-secondary); margin-bottom: 16px; }

.generating { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 40px; font-size: 1.1rem; }
.generating-icon { font-size: 2rem; animation: bounce 1s infinite; }

.suggestions-list { display: flex; flex-direction: column; gap: 12px; }
.suggestion-item { background: var(--bg-tertiary); border-radius: var(--radius-md); padding: 14px; }
.suggestion-type { font-size: 0.75rem; color: var(--accent-color); font-weight: 600; margin-bottom: 6px; text-transform: uppercase; }
.suggestion-content { font-size: 0.9rem; margin-bottom: 10px; }
.suggestion-actions { display: flex; gap: 8px; }

.graph-body { min-height: 400px; }
.graph-container { width: 100%; height: 400px; display: flex; align-items: center; justify-content: center; }
.graph-placeholder { text-align: center; color: var(--text-muted); }
.graph-icon { font-size: 3rem; display: block; margin-bottom: 12px; }

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

.modal-lg { max-width: 640px; }

.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.modal-header h2 { margin: 0; font-size: 1rem; font-weight: 600; }
.modal-body { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid var(--border-color); }

.form-group { margin-bottom: 14px; }
.form-group:last-child { margin-bottom: 0; }
.form-label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 6px; }

@media screen and (max-width: 640px) {
  .toolbar-left { flex-direction: column; align-items: stretch; }
  .toolbar-left .search-box { min-width: auto; }
  .stats-bar { gap: 12px; }
  .memories-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
