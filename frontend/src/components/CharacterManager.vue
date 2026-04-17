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
        <button class="btn btn-ai" @click="showAIGenerateModal = true">
          <span>✨</span> AI 创建
        </button>
        <button class="btn btn-primary" @click="openCreateModal">
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
      <button class="btn btn-primary" @click="openCreateModal">+ {{ $t('characters.create') }}</button>
    </div>

    <!-- AI 生成角色弹窗 -->
    <div v-if="showAIGenerateModal" class="modal-overlay" @click.self="closeAIGenerate">
      <div class="modal ai-generate-modal">
        <div class="modal-header">
          <h2>✨ AI 智能创建角色</h2>
          <button class="btn btn-ghost btn-icon" @click="closeAIGenerate">×</button>
        </div>
        <div class="modal-body">
          <div class="ai-description-section">
            <div class="form-group">
              <label class="form-label">📝 角色描述</label>
              <textarea
                v-model="aiForm.description"
                class="input textarea"
                rows="5"
                :placeholder="aiForm.placeholder"
              ></textarea>
              <div class="form-hint">描述越详细，生成的角色越符合你的想象</div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label class="form-label">🎨 风格</label>
                <select v-model="aiForm.style" class="select" style="width: 100%;">
                  <option value="creative">创意模式</option>
                  <option value="formal">正式模式</option>
                  <option value="casual">轻松模式</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">🌐 语言</label>
                <select v-model="aiForm.language" class="select" style="width: 100%;">
                  <option value="zh">中文</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            <!-- 示例提示 -->
            <div class="examples-section">
              <div class="examples-title">💡 示例描述</div>
              <div class="example-chips">
                <button
                  v-for="(example, idx) in aiForm.examples"
                  :key="idx"
                  class="example-chip"
                  @click="aiForm.description = example"
                >
                  {{ example.slice(0, 20) }}{{ example.length > 20 ? '...' : '' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 预览区域 -->
          <div v-if="aiPreview" class="ai-preview-section">
            <div class="preview-header">
              <span>👁️ 角色预览</span>
              <button class="btn btn-ghost btn-sm" @click="regeneratePreview">重新生成</button>
            </div>
            <div class="preview-card">
              <div class="preview-name">{{ aiPreview.name || '未命名' }}</div>
              <div class="preview-field">
                <span class="field-label">描述：</span>
                <span class="field-content">{{ aiPreview.description || '-' }}</span>
              </div>
              <div class="preview-field">
                <span class="field-label">性格：</span>
                <span class="field-content">{{ (aiPreview.personality || '-').slice(0, 100) }}{{ (aiPreview.personality?.length || 0) > 100 ? '...' : '' }}</span>
              </div>
              <div class="preview-field">
                <span class="field-label">场景：</span>
                <span class="field-content">{{ aiPreview.scenario || '-' }}</span>
              </div>
              <div class="preview-field">
                <span class="field-label">开场白：</span>
                <span class="field-content">"{{ aiPreview.greeting || '-' }}"</span>
              </div>
              <div class="preview-field" v-if="aiPreview.tags?.length">
                <span class="field-label">标签：</span>
                <div class="preview-tags">
                  <span v-for="tag in aiPreview.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="isGenerating" class="generating-state">
            <div class="loading-spinner"></div>
            <p>AI 正在创建角色...</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeAIGenerate">{{ $t('common.cancel') }}</button>
          <button
            v-if="!aiPreview"
            class="btn btn-primary"
            @click="generateCharacterPreview"
            :disabled="isGenerating || !aiForm.description.trim()"
          >
            {{ isGenerating ? '生成中...' : '生成预览' }}
          </button>
          <button
            v-else
            class="btn btn-primary"
            @click="saveAIGeneratedCharacter"
            :disabled="isSaving"
          >
            {{ isSaving ? '保存中...' : '✨ 创建角色' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal create-modal">
        <div class="modal-header">
          <h2>{{ editingCharacter ? '编辑角色' : '创建角色' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="closeCreateModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">头像</label>
            <div class="avatar-upload">
              <div class="avatar-preview" @click="avatarInput?.click()">
                <img v-if="form.avatar" :src="form.avatar" alt="avatar" />
                <span v-else class="avatar-placeholder-upload">📷</span>
              </div>
              <div>
                <p class="form-hint">点击选择头像图片</p>
                <button v-if="form.avatar" class="btn btn-ghost btn-sm" @click="form.avatar = ''">移除头像</button>
              </div>
            </div>
            <input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatarChange" />
          </div>

          <div class="form-group">
            <label class="form-label">名称 *</label>
            <input v-model="form.name" class="input" type="text" placeholder="角色名称" />
          </div>

          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea v-model="form.description" class="input textarea" rows="2" placeholder="简短描述角色"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">性格</label>
            <textarea v-model="form.personality" class="input textarea" rows="3" placeholder="角色的性格特点"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">场景</label>
            <textarea v-model="form.scenario" class="input textarea" rows="2" placeholder="角色所在的场景背景"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">开场白</label>
            <textarea v-model="form.greeting" class="input textarea" rows="3" placeholder="角色首次对话时说的话"></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">示例对话</label>
            <textarea
              v-model="form.examples"
              class="input textarea"
              rows="4"
              placeholder="示例对话（用空行分隔多个示例）"
            ></textarea>
            <div class="form-hint">用空行分隔多个示例对话</div>
          </div>

          <div class="form-group">
            <label class="form-label">标签</label>
            <input
              v-model="form.tagsInput"
              class="input"
              type="text"
              placeholder="标签（用逗号分隔，如：魔法,冒险,可爱）"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeCreateModal">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="saveCharacter" :disabled="!form.name.trim() || isSaving">
            {{ isSaving ? '保存中...' : (editingCharacter ? '保存修改' : '创建角色') }}
          </button>
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
const showAIGenerateModal = ref(false)
const editingCharacter = ref<Character | null>(null)
const importTab = ref<'file' | 'paste'>('file')
const importText = ref('')
const isDragOver = ref(false)
const exportFormat = ref('sillytavern')
const exportingCharacter = ref<Character | null>(null)
const avatarInput = ref<HTMLInputElement | null>(null)
const importFileInput = ref<HTMLInputElement | null>(null)
const isSaving = ref(false)

// AI 生成相关状态
const aiForm = ref({
  description: '',
  style: 'creative',
  language: 'zh',
  placeholder: '例如：创建一个穿着斗篷的神秘精灵法师，喜欢用古老的咒语，偶尔会调皮地眨眼睛...',
  examples: [
    '一个高冷的龙族王子，在一次意外中失去了龙鳞，变得脆弱而渴望保护',
    '热情开朗的星际旅行商人，总是从宇宙各处带回奇怪的收藏品',
    '外表冷酷但内心温柔的吸血鬼医生，在黑暗中守护着人类的健康',
    '一只修炼千年的猫妖，性格傲娇但其实很在意主人'
  ]
})
const aiPreview = ref<Character | null>(null)
const isGenerating = ref(false)

// 普通表单数据
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

// 打开创建弹窗
function openCreateModal() {
  editingCharacter.value = null
  resetForm()
  showCreateModal.value = true
}

// 关闭创建弹窗
function closeCreateModal() {
  showCreateModal.value = false
  editingCharacter.value = null
  resetForm()
}

// 编辑角色
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
  isSaving.value = true
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
      closeCreateModal()
      uiStore.showSuccess(t('characters.saveSuccess'))
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  } finally {
    isSaving.value = false
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

// AI 生成相关函数
function closeAIGenerate() {
  showAIGenerateModal.value = false
  aiPreview.value = null
  aiForm.value.description = ''
}

async function generateCharacterPreview() {
  if (!aiForm.value.description.trim()) return
  isGenerating.value = true
  try {
    const res = await fetch('/api/characters/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description: aiForm.value.description,
        style: aiForm.value.style,
        language: aiForm.value.language
      })
    })
    if (res.ok) {
      aiPreview.value = await res.json()
    } else {
      uiStore.showError('生成失败，请重试')
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  } finally {
    isGenerating.value = false
  }
}

async function regeneratePreview() {
  aiPreview.value = null
  await generateCharacterPreview()
}

async function saveAIGeneratedCharacter() {
  if (!aiPreview.value) return
  isSaving.value = true
  try {
    const res = await fetch('/api/characters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(aiPreview.value)
    })
    if (res.ok) {
      const saved: Character = await res.json()
      characters.value.push(saved)
      closeAIGenerate()
      uiStore.showSuccess(t('characters.saveSuccess'))
    } else {
      uiStore.showError('保存失败，请重试')
    }
  } catch (e) {
    uiStore.showError(t('common.error'))
  } finally {
    isSaving.value = false
  }
}

// 导出相关
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

// 导入相关
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
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  border: 2px dashed var(--border-color);
  transition: border-color var(--transition-fast);
}

.avatar-preview:hover {
  border-color: var(--accent-color);
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder-upload {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  font-size: 1.2rem;
  color: var(--text-muted);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.create-modal {
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-body .form-group {
  margin-bottom: 16px;
}

@media screen and (max-width: 640px) {
  .toolbar-left { flex-direction: column; align-items: stretch; }
  .toolbar-left .search-box { max-width: 100%; }
  .characters-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  .form-row { grid-template-columns: 1fr; }
  .create-modal { max-width: 100%; }
}
</style>
