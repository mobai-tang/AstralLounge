<template>
  <div class="plugin-market">
    <div class="toolbar">
      <div class="toolbar-left">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            class="input"
            :placeholder="$t('plugins.searchPlaceholder')"
          />
        </div>
      </div>
      <div class="toolbar-right">
        <button class="btn btn-secondary" @click="reloadPlugins">🔄 {{ $t('plugins.reload') }}</button>
      </div>
    </div>

    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'installed' }]" @click="activeTab = 'installed'">
        {{ $t('plugins.installedTab') }} ({{ installedPlugins.length }})
      </button>
      <button :class="['tab', { active: activeTab === 'market' }]" @click="activeTab = 'market'">
        {{ $t('plugins.market') }}
      </button>
      <button :class="['tab', { active: activeTab === 'skills' }]" @click="activeTab = 'skills'">
        {{ $t('plugins.skills') }}
      </button>
    </div>

    <!-- 已安装插件 -->
    <div v-if="activeTab === 'installed'" class="plugin-list">
      <div v-if="installedPlugins.length === 0" class="empty-state">
        <div class="empty-icon">🔌</div>
        <div class="empty-title">{{ $t('plugins.noPlugins') }}</div>
      </div>
      <div v-for="plugin in installedPlugins" :key="plugin.id" class="plugin-card">
        <div class="plugin-info">
          <div class="plugin-name">{{ plugin.displayName || plugin.name }}</div>
          <div v-if="plugin.version" class="plugin-version">{{ $t('plugins.version') }}: {{ plugin.version }}</div>
          <div v-if="plugin.author" class="plugin-author">{{ $t('plugins.author') }}: {{ plugin.author }}</div>
          <div v-if="plugin.description" class="plugin-desc">{{ plugin.description }}</div>
        </div>
        <div class="plugin-actions">
          <div :class="['toggle', { active: plugin.enabled }]" @click="togglePlugin(plugin)"></div>
          <button class="btn btn-sm btn-danger" @click="uninstallPlugin(plugin.id)">{{ $t('plugins.uninstall') }}</button>
        </div>
      </div>
    </div>

    <!-- 插件市场 -->
    <div v-if="activeTab === 'market'" class="market-section">
      <div class="install-form">
        <input
          v-model="installUrl"
          class="input"
          :placeholder="$t('plugins.installPlaceholder')"
        />
        <button class="btn btn-primary" @click="installPlugin" :disabled="installing">
          {{ installing ? $t('plugins.installing') : $t('plugins.installButton') }}
        </button>
      </div>

      <div v-if="featuredPlugins.length > 0">
        <h3>{{ $t('plugins.featured') }}</h3>
        <div class="plugin-list">
          <div v-for="plugin in featuredPlugins" :key="plugin.id" class="plugin-card">
            <div class="plugin-info">
              <div class="plugin-name">{{ plugin.displayName || plugin.name }}</div>
              <div v-if="plugin.version" class="plugin-version">{{ $t('plugins.version') }}: {{ plugin.version }}</div>
              <div v-if="plugin.description" class="plugin-desc">{{ plugin.description }}</div>
            </div>
            <div class="plugin-actions">
              <button
                v-if="!isInstalled(plugin.id)"
                class="btn btn-sm btn-primary"
                @click="quickInstall(plugin)"
              >
                {{ $t('plugins.install') }}
              </button>
              <span v-else class="badge badge-success">{{ $t('plugins.installed') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 技能管理 -->
    <div v-if="activeTab === 'skills'" class="skills-section">
      <div class="skills-stats">
        <span>{{ $t('plugins.skillsStats.total') }}: {{ skills.length }}</span>
        <span>{{ $t('plugins.skillsStats.enabled') }}: {{ skills.filter(s => s.enabled).length }}</span>
      </div>
      <div v-if="skills.length === 0" class="empty-state">
        <div class="empty-icon">⚡</div>
        <div class="empty-title">{{ $t('plugins.noSkills') }}</div>
        <div class="empty-desc">{{ $t('plugins.skillsHint') }}</div>
      </div>
      <div v-for="skill in skills" :key="skill.id" class="skill-card">
        <div class="skill-info">
          <div class="skill-name">{{ skill.name }}</div>
          <div v-if="skill.description" class="skill-desc">{{ skill.description }}</div>
        </div>
        <div :class="['toggle', { active: skill.enabled }]" @click="toggleSkill(skill)"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUIStore } from '@/stores/ui'
import type { Plugin, Skill } from '@/types'

const { t } = useI18n()
const uiStore = useUIStore()

const activeTab = ref('installed')
const searchQuery = ref('')
const installUrl = ref('')
const installing = ref(false)
const plugins = ref<Plugin[]>([])
const skills = ref<Skill[]>([])
const featuredPlugins = ref<Plugin[]>([])

const installedPlugins = computed(() => {
  let list = plugins.value.filter(p => p.installed)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(p => p.name.toLowerCase().includes(q) || p.displayName?.toLowerCase().includes(q))
  }
  return list
})

function isInstalled(id: string) {
  return plugins.value.some(p => p.id === id && p.installed)
}

async function loadPlugins() {
  try {
    const res = await fetch('/api/plugins')
    if (res.ok) plugins.value = await res.json()
  } catch (e) {
    console.error('加载插件失败:', e)
  }
}

async function loadSkills() {
  try {
    const res = await fetch('/api/plugins/skills')
    if (res.ok) skills.value = await res.json()
  } catch (e) {
    console.error('加载技能失败:', e)
  }
}

async function reloadPlugins() {
  try {
    await fetch('/api/plugins/reload', { method: 'POST' })
    await loadPlugins()
    await loadSkills()
    uiStore.showSuccess(t('plugins.reloadSuccess'))
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function togglePlugin(plugin: Plugin) {
  plugin.enabled = !plugin.enabled
  try {
    await fetch(`/api/plugins/${plugin.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: plugin.enabled })
    })
  } catch {
    plugin.enabled = !plugin.enabled
    uiStore.showError(t('common.error'))
  }
}

async function uninstallPlugin(id: string) {
  if (!confirm(t('settings.confirmUninstall'))) return
  try {
    const res = await fetch(`/api/plugins/${id}`, { method: 'DELETE' })
    if (res.ok) {
      plugins.value = plugins.value.filter(p => p.id !== id)
      uiStore.showSuccess(t('plugins.uninstallSuccess'))
    }
  } catch {
    uiStore.showError(t('common.error'))
  }
}

async function installPlugin() {
  if (!installUrl.value.trim() || installing.value) return
  installing.value = true
  try {
    const res = await fetch('/api/plugins/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: installUrl.value })
    })
    if (res.ok) {
      uiStore.showSuccess(t('plugins.installSuccess'))
      installUrl.value = ''
      await loadPlugins()
    }
  } catch {
    uiStore.showError(t('common.error'))
  } finally {
    installing.value = false
  }
}

async function quickInstall(plugin: Plugin) {
  installing.value = true
  try {
    const res = await fetch('/api/plugins/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: plugin.metadata?.url })
    })
    if (res.ok) {
      plugin.installed = true
      uiStore.showSuccess(t('plugins.installSuccess'))
      await loadPlugins()
    }
  } catch {
    uiStore.showError(t('common.error'))
  } finally {
    installing.value = false
  }
}

async function toggleSkill(skill: Skill) {
  skill.enabled = !skill.enabled
  try {
    await fetch(`/api/plugins/skills/${skill.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: skill.enabled })
    })
  } catch {
    skill.enabled = !skill.enabled
    uiStore.showError(t('common.error'))
  }
}

onMounted(async () => {
  await Promise.all([loadPlugins(), loadSkills()])
})
</script>

<style scoped>
.plugin-market {
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

.plugin-list { display: flex; flex-direction: column; gap: 10px; overflow-y: auto; flex: 1; }

.plugin-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  gap: 16px;
}

.plugin-info { flex: 1; min-width: 0; }
.plugin-name { font-weight: 600; margin-bottom: 2px; }
.plugin-version, .plugin-author { font-size: 0.8rem; color: var(--text-secondary); }
.plugin-desc { font-size: 0.85rem; color: var(--text-secondary); margin-top: 4px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }

.plugin-actions { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.install-form { display: flex; gap: 8px; margin-bottom: 20px; }
.install-form .input { flex: 1; }

.market-section h3 { font-size: 1rem; font-weight: 600; margin-bottom: 12px; }

.skills-section { display: flex; flex-direction: column; gap: 12px; }
.skills-stats { display: flex; gap: 16px; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 4px; }

.skill-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.skill-info { flex: 1; }
.skill-name { font-weight: 600; }
.skill-desc { font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px; }

@media screen and (max-width: 640px) {
  .plugin-card { flex-direction: column; align-items: flex-start; }
  .install-form { flex-direction: column; }
}
</style>
