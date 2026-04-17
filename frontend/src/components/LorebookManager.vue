<template>
  <div class="lorebook-manager">
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input v-model="searchQuery" class="input" :placeholder="$t('common.search')" />
        </div>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-primary" @click="createLorebook">
          <span>+</span> {{ $t('lorebooks.create') }}
        </button>
      </div>
    </div>

    <div v-if="filteredLorebooks.length > 0" class="lorebooks-list">
      <div v-for="book in filteredLorebooks" :key="book.id" class="lorebook-card">
        <div class="lorebook-header" @click="toggleExpand(book.id)">
          <div class="lorebook-info">
            <div class="lorebook-name">{{ book.name }}</div>
            <div class="lorebook-meta">
              {{ book.entries?.length || 0 }} {{ $t('lorebooks.entries') }}
              <span v-if="book.scanDepth"> · {{ $t('lorebooks.scanDepth') }}: {{ book.scanDepth }}</span>
            </div>
          </div>
          <div class="lorebook-actions">
            <button class="btn btn-ghost btn-sm" @click.stop="editLorebook(book)" :title="$t('common.edit')">✏️</button>
            <button class="btn btn-ghost btn-sm" @click.stop="deleteLorebook(book.id)" :title="$t('common.delete')">🗑️</button>
            <span :class="['expand-icon', { expanded: expandedIds.has(book.id) }]">▼</span>
          </div>
        </div>

        <Transition name="slide-up">
          <div v-if="expandedIds.has(book.id)" class="lorebook-body">
            <div v-if="book.description" class="lorebook-desc">{{ book.description }}</div>

            <div class="entries-toolbar">
              <button class="btn btn-sm btn-secondary" @click="addEntry(book)">
                + {{ $t('lorebooks.addEntry') }}
              </button>
            </div>

            <div v-if="book.entries?.length" class="entries-list">
              <div v-for="entry in book.entries" :key="entry.id" class="entry-item">
                <div class="entry-header">
                  <div class="entry-name">{{ entry.name }}</div>
                  <div class="entry-badges">
                    <span v-if="entry.enabled" class="badge badge-success">{{ $t('lorebooks.enabled') }}</span>
                    <span class="badge">{{ $t('lorebooks.priority') }}: {{ entry.priority }}</span>
                  </div>
                </div>
                <div class="entry-content">{{ entry.content }}</div>
                <div v-if="entry.keywords?.length" class="entry-keywords">
                  <span v-for="kw in entry.keywords" :key="kw" class="tag">{{ kw }}</span>
                </div>
                <div class="entry-actions">
                  <button class="btn btn-ghost btn-sm" @click="editEntry(book, entry)">{{ $t('common.edit') }}</button>
                  <button class="btn btn-ghost btn-sm" @click="deleteEntry(book, entry.id)">{{ $t('common.delete') }}</button>
                </div>
              </div>
            </div>
            <div v-else class="entries-empty">
              <p>{{ $t('common.noData') }}</p>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">📚</div>
      <div class="empty-title">{{ $t('lorebooks.noLorebooks') }}</div>
      <button class="btn btn-primary" @click="createLorebook">+ {{ $t('lorebooks.create') }}</button>
    </div>

    <!-- 世界编辑弹窗 -->
    <div v-if="showBookModal" class="modal-overlay" @click.self="showBookModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingBook ? $t('common.edit') : $t('lorebooks.create') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showBookModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('lorebooks.name') }} *</label>
            <input v-model="bookForm.name" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('lorebooks.description') }}</label>
            <textarea v-model="bookForm.description" class="input textarea" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('lorebooks.scanDepth') }}</label>
              <input v-model.number="bookForm.scanDepth" type="number" class="input" min="0" />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('lorebooks.contextLength') }}</label>
              <input v-model.number="bookForm.contextLength" type="number" class="input" min="0" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('lorebooks.insertMode') }}</label>
            <select v-model="bookForm.insertMode" class="select">
              <option value="append">Append</option>
              <option value="insert">Insert</option>
              <option value="prioritize">Prioritize</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showBookModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveLorebook">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>

    <!-- 条目编辑弹窗 -->
    <div v-if="showEntryModal" class="modal-overlay" @click.self="showEntryModal = false">
      <div class="modal" style="max-width: 720px;">
        <div class="modal-header">
          <h2>{{ editingEntry ? $t('lorebooks.editEntry') : $t('lorebooks.addEntry') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showEntryModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('lorebooks.entryName') }} *</label>
              <input v-model="entryForm.name" class="input" />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('lorebooks.priority') }}</label>
              <input v-model.number="entryForm.priority" type="number" class="input" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('lorebooks.entryContent') }}</label>
            <textarea v-model="entryForm.content" class="input textarea" rows="6"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('lorebooks.keywords') }}</label>
            <input v-model="entryForm.keywordsInput" class="input" placeholder="kw1, kw2, kw3" />
          </div>
          <div class="form-group">
            <label class="toggle-label">
              <div :class="['toggle', { active: entryForm.enabled }]" @click="entryForm.enabled = !entryForm.enabled"></div>
              {{ $t('lorebooks.enabled') }}
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEntryModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveEntry">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Lorebook, LorebookEntry } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

const lorebooks = ref<Lorebook[]>([])
const searchQuery = ref('')
const expandedIds = ref(new Set<string>())
const showBookModal = ref(false)
const showEntryModal = ref(false)
const editingBook = ref<Lorebook | null>(null)
const editingEntry = ref<LorebookEntry | null>(null)
const editingBookId = ref<string | null>(null)

const bookForm = ref({ name: '', description: '', scanDepth: 2, contextLength: 2048, insertMode: 'append' as const })
const entryForm = ref({ name: '', content: '', keywordsInput: '', priority: 0, enabled: true })

const filteredLorebooks = computed(() => {
  if (!searchQuery.value.trim()) return lorebooks.value
  const q = searchQuery.value.toLowerCase()
  return lorebooks.value.filter(b =>
    b.name.toLowerCase().includes(q) || b.description?.toLowerCase().includes(q)
  )
})

function toggleExpand(id: string) {
  if (expandedIds.value.has(id)) expandedIds.value.delete(id)
  else expandedIds.value.add(id)
}

function createLorebook() {
  editingBook.value = null
  bookForm.value = { name: '', description: '', scanDepth: 2, contextLength: 2048, insertMode: 'append' }
  showBookModal.value = true
}

function editLorebook(book: Lorebook) {
  editingBook.value = book
  bookForm.value = {
    name: book.name,
    description: book.description ?? '',
    scanDepth: book.scanDepth ?? 2,
    contextLength: book.contextLength ?? 2048,
    insertMode: book.insertMode ?? 'append'
  }
  showBookModal.value = true
}

async function saveLorebook() {
  if (!bookForm.value.name.trim()) return
  try {
    const url = editingBook.value ? `/api/lorebooks/${editingBook.value.id}` : '/api/lorebooks'
    const method = editingBook.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookForm.value)
    })
    if (res.ok) {
      const saved: Lorebook = await res.json()
      if (editingBook.value) {
        const idx = lorebooks.value.findIndex(b => b.id === saved.id)
        if (idx !== -1) lorebooks.value[idx] = saved
      } else {
        lorebooks.value.push(saved)
      }
      showBookModal.value = false
      uiStore.showSuccess(t('lorebooks.saveSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function deleteLorebook(id: string) {
  if (!confirm(t('lorebooks.confirmDeleteBook'))) return
  try {
    const res = await fetch(`/api/lorebooks/${id}`, { method: 'DELETE' })
    if (res.ok) {
      lorebooks.value = lorebooks.value.filter(b => b.id !== id)
      uiStore.showSuccess(t('lorebooks.deleteSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

function addEntry(book: Lorebook) {
  editingEntry.value = null
  editingBookId.value = book.id
  entryForm.value = { name: '', content: '', keywordsInput: '', priority: 0, enabled: true }
  showEntryModal.value = true
}

function editEntry(book: Lorebook, entry: LorebookEntry) {
  editingEntry.value = entry
  editingBookId.value = book.id
  entryForm.value = {
    name: entry.name,
    content: entry.content,
    keywordsInput: entry.keywords?.join(', ') ?? '',
    priority: entry.priority,
    enabled: entry.enabled
  }
  showEntryModal.value = true
}

async function saveEntry() {
  if (!entryForm.value.name.trim() || !editingBookId.value) return
  const data = {
    name: entryForm.value.name,
    content: entryForm.value.content,
    keywords: entryForm.value.keywordsInput.split(',').map(k => k.trim()).filter(Boolean),
    priority: entryForm.value.priority,
    enabled: entryForm.value.enabled
  }
  try {
    const url = editingEntry.value
      ? `/api/lorebooks/${editingBookId.value}/entries/${editingEntry.value.id}`
      : `/api/lorebooks/${editingBookId.value}/entries`
    const method = editingEntry.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res.ok) {
      const saved: LorebookEntry = await res.json()
      const book = lorebooks.value.find(b => b.id === editingBookId.value)
      if (book) {
        if (editingEntry.value) {
          const idx = book.entries.findIndex(e => e.id === saved.id)
          if (idx !== -1) book.entries[idx] = saved
        } else {
          if (!book.entries) book.entries = []
          book.entries.push(saved)
        }
      }
      showEntryModal.value = false
      uiStore.showSuccess(t('lorebooks.saveSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function deleteEntry(book: Lorebook, entryId: string) {
  if (!confirm(t('lorebooks.confirmDelete'))) return
  try {
    const res = await fetch(`/api/lorebooks/${book.id}/entries/${entryId}`, { method: 'DELETE' })
    if (res.ok) {
      book.entries = book.entries.filter(e => e.id !== entryId)
      uiStore.showSuccess(t('lorebooks.deleteSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

onMounted(async () => {
  try {
    const res = await fetch('/api/lorebooks')
    if (res.ok) lorebooks.value = await res.json()
  } catch (e) {
    console.error('加载世界设定失败:', e)
  }
})
</script>

<style scoped>
.lorebook-manager {
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
  gap: 12px;
}

.toolbar-left { flex: 1; max-width: 300px; position: relative; }
.toolbar-left .search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--text-muted); pointer-events: none; }
.toolbar-left .input { padding-left: 32px; }

.lorebooks-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lorebook-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.lorebook-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.lorebook-header:hover { background: var(--bg-tertiary); }

.lorebook-name { font-weight: 600; margin-bottom: 2px; }
.lorebook-meta { font-size: 0.8rem; color: var(--text-secondary); }

.lorebook-actions { display: flex; align-items: center; gap: 6px; }

.expand-icon {
  font-size: 0.7rem;
  color: var(--text-muted);
  transition: transform var(--transition-fast);
}
.expand-icon.expanded { transform: rotate(180deg); }

.lorebook-body { padding: 12px 16px 16px; border-top: 1px solid var(--border-color); }

.lorebook-desc { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px; }

.entries-toolbar { margin-bottom: 12px; }

.entries-list { display: flex; flex-direction: column; gap: 8px; }

.entry-item {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.entry-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.entry-name { font-weight: 600; font-size: 0.9rem; }
.entry-badges { display: flex; gap: 4px; }

.entry-content { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 6px; line-height: 1.5; }

.entry-keywords { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.entry-keywords .tag { font-size: 0.7rem; }

.entry-actions { display: flex; gap: 6px; }

.entries-empty { text-align: center; color: var(--text-muted); padding: 16px; font-size: 0.85rem; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.toggle-label { display: flex; align-items: center; gap: 8px; cursor: pointer; }

@media screen and (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
