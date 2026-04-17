<template>
  <div class="character-manager">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            class="input"
            :placeholder="$t('characters.searchPlaceholder')"
          />
        </div>
        <select v-model="selectedTag" class="select">
          <option value="">{{ $t('characters.filterByTag') }}</option>
          <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-primary" @click="showCreateModal = true">
          <span>+</span> {{ $t('characters.create') }}
        </button>
        <button class="btn btn-secondary" @click="showImportModal = true">
          {{ $t('characters.import') }}
        </button>
      </div>
    </div>

    <!-- 角色网格 -->
    <div v-if="filteredCharacters.length > 0" class="characters-grid">
      <div
        v-for="char in filteredCharacters"
        :key="char.id"
        :class="['character-card', { selected: selectedId === char.id }]"
        @click="selectCharacter(char.id)"
      >
        <div class="card-avatar">
          <img v-if="char.avatar" :src="char.avatar" :alt="char.name" />
          <span v-else class="avatar-placeholder">{{ char.name?.charAt(0) || '?' }}</span>
        </div>
        <div class="card-body">
          <div class="card-name">{{ char.name }}</div>
          <div v-if="char.description" class="card-desc">{{ char.description }}</div>
          <div v-if="char.tags?.length" class="card-tags">
            <span v-for="tag in char.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="card-actions">
          <button class="btn btn-ghost btn-sm" @click.stop="editCharacter(char)" :title="$t('characters.edit')">✏️</button>
          <button class="btn btn-ghost btn-sm" @click.stop="exportCharacter(char)" :title="$t('characters.export')">📤</button>
          <button class="btn btn-ghost btn-sm" @click.stop="deleteCharacter(char.id)" :title="$t('characters.delete')">🗑️</button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">🎭</div>
      <div class="empty-title">{{ $t('characters.noCharacters') }}</div>
      <div class="empty-desc">{{ $t('characters.createFirst') }}</div>
      <button class="btn btn-primary" @click="showCreateModal = true">+ {{ $t('characters.create') }}</button>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal" style="max-width: 720px;">
        <div class="modal-header">
          <h2>{{ editingCharacter ? $t('characters.edit') : $t('characters.create') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('characters.name') }} *</label>
              <input v-model="form.name" class="input" required />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('characters.tags') }}</label>
              <input v-model="form.tagsInput" class="input" placeholder="tag1, tag2, tag3" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.description') }}</label>
            <textarea v-model="form.description" class="input textarea" rows="2"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.personality') }}</label>
            <textarea v-model="form.personality" class="input textarea" rows="3"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.scenario') }}</label>
            <textarea v-model="form.scenario" class="input textarea" rows="2"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.greeting') }}</label>
            <textarea v-model="form.greeting" class="input textarea" rows="2"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.examples') }}</label>
            <textarea v-model="form.examples" class="input textarea" rows="3" placeholder="User: ...&#10;Character: ..."></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('characters.avatar') }}</label>
            <div class="avatar-upload" @click="avatarInput?.click()">
              <div v-if="form.avatar" class="avatar-preview">
                <img :src="form.avatar" alt="avatar" />
                <button class="remove-avatar" @click.stop="form.avatar = ''">×</button>
              </div>
              <div v-else class="avatar-placeholder-upload">
                <span>{{ $t('characters.uploadAvatar') }}</span>
              </div>
            </div>
            <input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatarChange" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveCharacter">{{ $t('common.save') }}</button>
        </div>
      </div>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('characters.import') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showImportModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="tabs">
            <button :class="['tab', { active: importTab === 'file' }]" @click="importTab = 'file'">{{ $t('characters.fileImport') }}</button>
            <button :class="['tab', { active: importTab === 'paste' }]" @click="importTab = 'paste'">{{ $t('characters.pasteImport') }}</button>
          </div>

          <div v-if="importTab === 'file'" class="drop-zone" @click="importFileInput?.click()" @dragover.prevent="isDragOver = true" @dragleave="isDragOver = false" @drop.prevent="onDrop" :class="{ 'drag-over': isDragOver }">
            <p>{{ $t('characters.dropHere') }}</p>
            <p class="form-hint">{{ $t('characters.importFormats') }}</p>
          </div>
          <input ref="importFileInput" type="file" accept=".json,.png,.jpg,.webp" hidden @change="onImportFile" />

          <div v-if="importTab === 'paste'" class="form-group" style="margin-top: 12px;">
            <textarea v-model="importText" class="input textarea" rows="10" placeholder="粘贴角色卡内容..."></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showImportModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="importCharacter">{{ $t('characters.import') }}</button>
        </div>
      </div>
    </div>

    <!-- 导出弹窗 -->
    <div v-if="showExportModal" class="modal-overlay" @click.self="showExportModal = false">
      <div class="modal" style="max-width: 400px;">
        <div class="modal-header">
          <h2>{{ $t('characters.export') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showExportModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('characters.exportFormat') }}</label>
            <select v-model="exportFormat" class="select" style="width: 100%;">
              <option value="sillytavern">{{ $t('characters.sillytavern') }}</option>
              <option value="tavernai">{{ $t('characters.tavernai') }}</option>
              <option value="ooba">{{ $t('characters.ooba') }}</option>
              <option value="json">{{ $t('characters.json') }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showExportModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="doExport">{{ $t('common.download') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Character } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

const characters = ref<Character[]>([])
const selectedId = ref<string | null>(null)
const searchQuery = ref('')
const selectedTag = ref('')
const showCreateModal = ref(false)
const showImportModal = ref(false)
const showExportModal = ref(false)
const editingCharacter = ref<Character | null>(null)
const importTab = ref<'file' | 'paste'>('file')
const importText = ref('')
const isDragOver = ref(false)
const exportFormat = ref('sillytavern')
const exportingCharacter = ref<Character | null>(null)
const avatarInput = ref<HTMLInputElement | null>(null)
const importFileInput = ref<HTMLInputElement | null>(null)

const form = ref({
  name: '',
  description: '',
  personality: '',
  scenario: '',
  greeting: '',
  examples: '',
  tagsInput: '',
  avatar: ''
})

const allTags = computed(() => {
  const tags = new Set<string>()
  characters.value.forEach(c => c.tags?.forEach(t => tags.add(t)))
  return Array.from(tags).sort()
})

const filteredCharacters = computed(() => {
  let list = characters.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.description?.toLowerCase().includes(q) ||
      c.tags?.some(t => t.toLowerCase().includes(q))
    )
  }
  if (selectedTag.value) {
    list = list.filter(c => c.tags?.includes(selectedTag.value))
  }
  return list.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''))
})

function selectCharacter(id: string) {
  selectedId.value = id
}

function editCharacter(char: Character) {
  editingCharacter.value = char
  form.value = {
    name: char.name,
    description: char.description ?? '',
    personality: char.personality ?? '',
    scenario: char.scenario ?? '',
    greeting: char.greeting ?? '',
    examples: char.examples?.join('\n\n') ?? '',
    tagsInput: char.tags?.join(', ') ?? '',
    avatar: char.avatar ?? ''
  }
  showCreateModal.value = true
}

async function saveCharacter() {
  if (!form.value.name.trim()) return
  const data = {
    name: form.value.name,
    description: form.value.description,
    personality: form.value.personality,
    scenario: form.value.scenario,
    greeting: form.value.greeting,
    examples: form.value.examples.split('\n\n').filter(Boolean),
    tags: form.value.tagsInput.split(',').map(t => t.trim()).filter(Boolean),
    avatar: form.value.avatar
  }

  try {
    const url = editingCharacter.value
      ? `/api/characters/${editingCharacter.value.id}`
      : '/api/characters'
    const method = editingCharacter.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res.ok) {
      const saved: Character = await res.json()
      if (editingCharacter.value) {
        const idx = characters.value.findIndex(c => c.id === saved.id)
        if (idx !== -1) characters.value[idx] = saved
      } else {
        characters.value.push(saved)
      }
      showCreateModal.value = false
      editingCharacter.value = null
      resetForm()
      uiStore.showSuccess(t('characters.saveSuccess'))
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  }
}

async function deleteCharacter(id: string) {
  if (!confirm(t('characters.confirmDelete'))) return
  try {
    const res = await fetch(`/api/characters/${id}`, { method: 'DELETE' })
    if (res.ok) {
      characters.value = characters.value.filter(c => c.id !== id)
      if (selectedId.value === id) selectedId.value = null
      uiStore.showSuccess(t('characters.deleteSuccess'))
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  }
}

function exportCharacter(char: Character) {
  exportingCharacter.value = char
  showExportModal.value = true
}

function doExport() {
  if (!exportingCharacter.value) return
  const char = exportingCharacter.value
  let data: Record<string, unknown>
  if (exportFormat.value === 'json') {
    data = char
  } else if (exportFormat.value === 'ooba') {
    data = {
      name: char.name,
      description: char.description,
      personality: char.personality,
      scenario: char.scenario,
      greeting: char.greeting,
      example_dialogue: char.examples?.join('\n')
    }
  } else {
    data = char
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${char.name}.json`
  a.click()
  URL.revokeObjectURL(url)
  showExportModal.value = false
  uiStore.showSuccess(t('characters.exportSuccess'))
}

async function importCharacter() {
  if (importTab.value === 'paste' && !importText.value.trim()) return
  try {
    const res = await fetch('/api/characters/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: importText.value })
    })
    if (res.ok) {
      const chars: Character[] = await res.json()
      chars.forEach(c => {
        if (!characters.value.find(x => x.id === c.id)) {
          characters.value.push(c)
        }
      })
      showImportModal.value = false
      importText.value = ''
      uiStore.showSuccess(t('characters.importSuccess'))
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  }
}

function onAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    form.value.avatar = ev.target?.result as string
  }
  reader.readAsDataURL(file)
}

function onDrop(e: DragEvent) {
  isDragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) handleImportFile(file)
}

function onImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) handleImportFile(file)
}

async function handleImportFile(file: File) {
  const text = await file.text()
  try {
    const res = await fetch('/api/characters/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: text, filename: file.name })
    })
    if (res.ok) {
      const chars: Character[] = await res.json()
      chars.forEach(c => {
        if (!characters.value.find(x => x.id === c.id)) {
          characters.value.push(c)
        }
      })
      showImportModal.value = false
      uiStore.showSuccess(t('characters.importSuccess'))
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  }
}

function resetForm() {
  form.value = { name: '', description: '', personality: '', scenario: '', greeting: '', examples: '', tagsInput: '', avatar: '' }
}

onMounted(async () => {
  try {
    const res = await fetch('/api/characters')
    if (res.ok) characters.value = await res.json()
  } catch (e) {
    console.error('加载角色失败:', e)
  }
})
</script>

<style scoped>
.character-manager {
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

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.toolbar-left .search-box {
  flex: 1;
  max-width: 300px;
  position: relative;
}

.toolbar-left .search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.toolbar-left .input {
  padding-left: 32px;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.characters-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  padding-bottom: 20px;
}

.character-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.character-card:hover { border-color: var(--border-hover); }
.character-card.selected { border-color: var(--accent-color); box-shadow: 0 0 0 2px var(--accent-subtle); }

.card-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.card-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-avatar .avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--text-secondary);
}

.card-body { flex: 1; min-width: 0; }

.card-name {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 6px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.card-tags .tag {
  font-size: 0.7rem;
  padding: 2px 7px;
}

.card-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.character-card:hover .card-actions { opacity: 1; }

/* 头像上传 */
.avatar-upload {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-preview {
  position: relative;
  width: 64px;
  height: 64px;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.remove-avatar {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #ef4444;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-placeholder-upload {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: 2px dashed var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.avatar-placeholder-upload:hover { border-color: var(--accent-color); }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

@media screen and (max-width: 640px) {
  .toolbar-left { flex-direction: column; align-items: stretch; }
  .toolbar-left .search-box { max-width: 100%; }
  .characters-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  .form-row { grid-template-columns: 1fr; }
}
</style>
