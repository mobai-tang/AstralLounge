<template>
  <div class="personas-view">
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input v-model="searchQuery" class="input" placeholder="搜索人设..." />
        </div>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-primary" @click="openCreateModal">
          <span>+</span> 创建人设
        </button>
      </div>
    </div>

    <!-- 统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-value">{{ personas.length }}</span>
        <span class="stat-label">人设总数</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ defaultCount }}</span>
        <span class="stat-label">默认人设</span>
      </div>
    </div>

    <!-- 人设网格 -->
    <div v-if="filteredPersonas.length > 0" class="personas-grid">
      <div
        v-for="persona in filteredPersonas"
        :key="persona.id"
        :class="['persona-card', { 'is-default': persona.isDefault }]"
      >
        <div class="card-avatar">
          <img v-if="persona.avatar" :src="persona.avatar" :alt="persona.name" />
          <span v-else class="avatar-placeholder">{{ persona.name?.charAt(0) || '?' }}</span>
          <div v-if="persona.isDefault" class="default-badge">默认</div>
        </div>
        <div class="card-body">
          <div class="card-name">{{ persona.name }}</div>
          <div v-if="persona.description" class="card-desc">{{ persona.description }}</div>
          <div v-if="persona.systemPrompt" class="card-prompt">{{ persona.systemPrompt }}</div>
        </div>
        <div class="card-actions">
          <button class="btn btn-ghost btn-sm" @click="openEditModal(persona)">编辑</button>
          <button v-if="!persona.isDefault" class="btn btn-ghost btn-sm" @click="setDefault(persona)">设为默认</button>
          <button class="btn btn-ghost btn-sm" @click="deletePersona(persona)">删除</button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🎭</div>
      <div class="empty-title">暂无用户人设</div>
      <button class="btn btn-primary" @click="openCreateModal">+ 创建人设</button>
    </div>

    <!-- 创建/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal" style="max-width: 600px;">
        <div class="modal-header">
          <h2>{{ editingPersona ? '编辑人设' : '创建人设' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">名称 *</label>
              <input v-model="form.name" class="input" required />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea v-model="form.description" class="input textarea" rows="2" placeholder="人设简介..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">系统提示词</label>
            <textarea v-model="form.systemPrompt" class="input textarea" rows="4" placeholder="定义你的身份和说话方式..."></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">头像</label>
            <div class="avatar-upload" @click="avatarInput?.click()">
              <div v-if="form.avatar" class="avatar-preview">
                <img :src="form.avatar" alt="avatar" />
                <button class="remove-avatar" @click.stop="form.avatar = ''">×</button>
              </div>
              <div v-else class="avatar-placeholder-upload">
                <span>点击上传</span>
              </div>
            </div>
            <input ref="avatarInput" type="file" accept="image/*" hidden @change="onAvatarChange" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="savePersona">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'

interface Persona {
  id: string
  name: string
  description?: string
  avatar?: string
  systemPrompt?: string
  isDefault?: boolean
  createdAt?: number
  updatedAt?: number
}

const uiStore = useUIStore()

const personas = ref<Persona[]>([])
const searchQuery = ref('')
const showModal = ref(false)
const editingPersona = ref<Persona | null>(null)
const avatarInput = ref<HTMLInputElement | null>(null)

const form = reactive({
  name: '',
  description: '',
  systemPrompt: '',
  avatar: ''
})

const defaultCount = computed(() => personas.value.filter(p => p.isDefault).length)

const filteredPersonas = computed(() => {
  if (!searchQuery.value.trim()) return personas.value
  const q = searchQuery.value.toLowerCase()
  return personas.value.filter(p =>
    p.name?.toLowerCase().includes(q) ||
    p.description?.toLowerCase().includes(q)
  )
})

function openCreateModal() {
  editingPersona.value = null
  Object.assign(form, { name: '', description: '', systemPrompt: '', avatar: '' })
  showModal.value = true
}

function openEditModal(persona: Persona) {
  editingPersona.value = persona
  Object.assign(form, {
    name: persona.name,
    description: persona.description ?? '',
    systemPrompt: persona.systemPrompt ?? '',
    avatar: persona.avatar ?? ''
  })
  showModal.value = true
}

async function savePersona() {
  if (!form.name.trim()) return
  const data = {
    name: form.name,
    description: form.description,
    systemPrompt: form.systemPrompt,
    avatar: form.avatar
  }
  try {
    const url = editingPersona.value ? `/api/personas/${editingPersona.value.id}` : '/api/personas'
    const method = editingPersona.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (res.ok) {
      const saved: Persona = await res.json()
      if (editingPersona.value) {
        const idx = personas.value.findIndex(p => p.id === saved.id)
        if (idx !== -1) personas.value[idx] = saved
      } else {
        personas.value.push(saved)
      }
      showModal.value = false
      uiStore.showSuccess(editingPersona.value ? '保存成功' : '创建成功')
    }
  } catch {
    uiStore.showError('操作失败')
  }
}

async function setDefault(persona: Persona) {
  try {
    const res = await fetch(`/api/personas/${persona.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_default: true })
    })
    if (res.ok) {
      personas.value.forEach(p => p.isDefault = false)
      const updated = personas.value.find(p => p.id === persona.id)
      if (updated) updated.isDefault = true
      uiStore.showSuccess('已设为默认')
    }
  } catch {
    uiStore.showError('操作失败')
  }
}

async function deletePersona(persona: Persona) {
  if (!confirm('确定要删除这个人设吗？')) return
  try {
    const res = await fetch(`/api/personas/${persona.id}`, { method: 'DELETE' })
    if (res.ok) {
      personas.value = personas.value.filter(p => p.id !== persona.id)
      uiStore.showSuccess('删除成功')
    }
  } catch {
    uiStore.showError('操作失败')
  }
}

function onAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    form.avatar = ev.target?.result as string
  }
  reader.readAsDataURL(file)
}

onMounted(async () => {
  try {
    const res = await fetch('/api/personas')
    if (res.ok) personas.value = await res.json()
  } catch (e) {
    console.error('加载人设失败:', e)
  }
})
</script>

<style scoped>
.personas-view {
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

.toolbar-left { display: flex; align-items: center; gap: 10px; }
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

.personas-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding-bottom: 20px;
}

.persona-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color var(--transition-fast);
}
.persona-card:hover { border-color: var(--border-hover); }
.persona-card.is-default { border-color: var(--accent-color); box-shadow: 0 0 0 1px var(--accent-subtle); }

.card-avatar {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}
.card-avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder {
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
.default-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--accent-color);
  color: white;
  font-size: 0.6rem;
  padding: 2px 5px;
  border-radius: 8px;
  font-weight: 600;
}

.card-body { flex: 1; min-width: 0; }
.card-name { font-weight: 600; font-size: 1rem; margin-bottom: 4px; }
.card-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}
.card-prompt {
  font-size: 0.75rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.persona-card:hover .card-actions { opacity: 1; }

.avatar-upload { display: flex; align-items: center; gap: 12px; }
.avatar-preview { position: relative; width: 64px; height: 64px; }
.avatar-preview img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.remove-avatar {
  position: absolute; top: -4px; right: -4px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #ef4444; color: white; border: none; cursor: pointer;
  font-size: 0.8rem; display: flex; align-items: center; justify-content: center;
}
.avatar-placeholder-upload {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--bg-tertiary); border: 2px dashed var(--border-color);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; font-size: 0.75rem; color: var(--text-muted);
  transition: all var(--transition-fast);
}
.avatar-placeholder-upload:hover { border-color: var(--accent-color); }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

@media screen and (max-width: 640px) {
  .personas-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
