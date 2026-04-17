<template>
  <div class="settings-modal-overlay" @click.self="$emit('close')">
    <div class="modal" style="max-width: 700px; max-height: calc(100vh - 48px);">
      <div class="modal-header">
        <h2>{{ $t('settings.title') }}</h2>
        <button class="btn btn-ghost btn-icon" @click="$emit('close')">×</button>
      </div>

      <div class="settings-layout">
        <!-- 侧边标签 -->
        <nav class="settings-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['settings-nav-item', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            <span class="nav-icon">{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
          </button>
        </nav>

        <!-- 设置内容 -->
        <div class="settings-content">
          <!-- 模型设置 -->
          <div v-if="activeTab === 'model'" class="settings-section">
            <h3>{{ $t('settings.model') }}</h3>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.provider') }}</label>
              <select v-model="settings.model.provider" class="select">
                <option value="ollama">Ollama (本地)</option>
                <option value="deepseek">DeepSeek</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="custom">自定义</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.modelName') }}</label>
              <input v-model="settings.model.model_name" class="input" />
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.apiUrl') }}</label>
              <input v-model="settings.model.api_url" class="input" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.temperature') }}</label>
                <input v-model.number="settings.model.temperature" type="number" class="input" min="0" max="2" step="0.1" />
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.maxTokens') }}</label>
                <input v-model.number="settings.model.max_tokens" type="number" class="input" min="0" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.topP') }}</label>
                <input v-model.number="settings.model.top_p" type="number" class="input" min="0" max="1" step="0.05" />
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.presencePenalty') }}</label>
                <input v-model.number="settings.model.presence_penalty" type="number" class="input" min="-2" max="2" step="0.1" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.frequencyPenalty') }}</label>
              <input v-model.number="settings.model.frequency_penalty" type="number" class="input" min="-2" max="2" step="0.1" />
            </div>
            <div class="form-row">
              <button class="btn btn-secondary" @click="testConnection" :disabled="testing">
                {{ testing ? $t('settings.testing') : $t('settings.testConnection') }}
              </button>
              <button class="btn btn-secondary" @click="refreshModels">🔄 {{ $t('settings.refreshModels') }}</button>
            </div>
            <div v-if="testResult !== null" :class="['test-result', testResult ? 'success' : 'error']">
              {{ testResult ? $t('settings.connectionSuccess') : $t('settings.connectionFailed') }}
            </div>
          </div>

          <!-- 界面设置 -->
          <div v-if="activeTab === 'ui'" class="settings-section">
            <h3>{{ $t('settings.ui') }}</h3>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.theme') }}</label>
              <div class="theme-options">
                <div :class="['theme-option', { active: settings.ui.theme === 'dark' }]" @click="settings.ui.theme = 'dark'">
                  🌙 {{ $t('settings.darkTheme') }}
                </div>
                <div :class="['theme-option', { active: settings.ui.theme === 'light' }]" @click="settings.ui.theme = 'light'">
                  ☀️ {{ $t('settings.lightTheme') }}
                </div>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.accentColor') }}</label>
              <div class="color-options">
                <div v-for="c in accentColors" :key="c" :class="['color-option', { active: settings.ui.accent_color === c }]" :style="{ background: c }" @click="settings.ui.accent_color = c"></div>
              </div>
            </div>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.ui.typing_effect }]" @click="settings.ui.typing_effect = !settings.ui.typing_effect"></div>
                {{ $t('settings.typingEffect') }}
              </label>
            </div>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.ui.stream_response }]" @click="settings.ui.stream_response = !settings.ui.stream_response"></div>
                {{ $t('settings.streamResponse') }}
              </label>
            </div>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.ui.compact_mode }]" @click="settings.ui.compact_mode = !settings.ui.compact_mode"></div>
                {{ $t('settings.compactMode') }}
              </label>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.language') }}</label>
              <select v-model="settings.ui.language" class="select">
                <option value="zh">🇨🇳 简体中文</option>
                <option value="en">🇺🇸 English</option>
              </select>
            </div>
          </div>

          <!-- 安全设置 -->
          <div v-if="activeTab === 'safety'" class="settings-section">
            <h3>{{ $t('settings.safety') }}</h3>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.safety.enabled }]" @click="settings.safety.enabled = !settings.safety.enabled"></div>
                {{ $t('settings.safetyEnabled') }}
              </label>
            </div>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.safety.block_enabled }]" @click="settings.safety.block_enabled = !settings.safety.block_enabled"></div>
                {{ $t('settings.blockEnabled') }}
              </label>
            </div>
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.safety.log_enabled }]" @click="settings.safety.log_enabled = !settings.safety.log_enabled"></div>
                {{ $t('settings.logEnabled') }}
              </label>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.sensitiveAction') }}</label>
              <select v-model="settings.safety.sensitive_action" class="select">
                <option value="block">{{ $t('settings.blockAction') }}</option>
                <option value="warn">{{ $t('common.warning') }}</option>
                <option value="ignore">{{ $t('common.info') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.blockedWords') }}</label>
              <div class="word-tags">
                <span v-for="(word, i) in settings.safety.blocked_words" :key="i" class="word-tag">
                  {{ word }} <button @click="removeWord('blocked_words', i)">×</button>
                </span>
              </div>
              <div class="word-add">
                <input v-model="newBlockedWord" class="input" @keyup.enter="addWord('blocked_words')" />
                <button class="btn btn-sm btn-secondary" @click="addWord('blocked_words')">{{ $t('settings.addWord') }}</button>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">{{ $t('settings.sensitiveWords') }}</label>
              <div class="word-tags">
                <span v-for="(word, i) in settings.safety.sensitive_words" :key="i" class="word-tag">
                  {{ word }} <button @click="removeWord('sensitive_words', i)">×</button>
                </span>
              </div>
              <div class="word-add">
                <input v-model="newSensitiveWord" class="input" @keyup.enter="addWord('sensitive_words')" />
                <button class="btn btn-sm btn-secondary" @click="addWord('sensitive_words')">{{ $t('settings.addWord') }}</button>
              </div>
            </div>
          </div>

          <!-- 关于 -->
          <div v-if="activeTab === 'about'" class="settings-section">
            <h3>{{ $t('settings.about') }}</h3>
            <div class="about-info">
              <div class="about-logo">✨</div>
              <div class="about-name">{{ $t('settings.appName') }}</div>
              <div class="about-version">{{ $t('settings.version') }} {{ $t('settings.versionNumber') }}</div>
              <div class="about-desc">{{ $t('settings.description') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-ghost" @click="$emit('close')">{{ $t('common.cancel') }}</button>
        <button class="btn btn-primary" @click="save" :disabled="saving">
          {{ saving ? $t('common.loading') : $t('common.save') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import { useUIStore } from '@/stores/ui'

const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const settingsStore = useSettingsStore()
const uiStore = useUIStore()

const activeTab = ref('model')
const testing = ref(false)
const testResult = ref<boolean | null>(null)
const saving = ref(false)
const newBlockedWord = ref('')
const newSensitiveWord = ref('')

const settings = reactive({
  model: { ...settingsStore.model },
  ui: { ...settingsStore.ui },
  safety: { ...settingsStore.safety }
})

const accentColors = ['#667eea', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#ec4899', '#8b5cf6']

const tabs = [
  { key: 'model', icon: '🤖', label: t('settings.model') },
  { key: 'ui', icon: '🎨', label: t('settings.ui') },
  { key: 'safety', icon: '🛡️', label: t('settings.safety') },
  { key: 'about', icon: 'ℹ️', label: t('settings.about') },
]

async function testConnection() {
  testing.value = true
  testResult.value = null
  testResult.value = await settingsStore.testConnection()
  testing.value = false
}

async function refreshModels() {
  try {
    const res = await fetch('/api/config/models/refresh', { method: 'POST' })
    if (res.ok) uiStore.showSuccess(t('common.success'))
  } catch {
    uiStore.showError(t('common.error'))
  }
}

function addWord(type: 'blocked_words' | 'sensitive_words') {
  const word = type === 'blocked_words' ? newBlockedWord.value.trim() : newSensitiveWord.value.trim()
  if (!word) return
  if (!settings.safety[type].includes(word)) {
    settings.safety[type].push(word)
  }
  if (type === 'blocked_words') newBlockedWord.value = ''
  else newSensitiveWord.value = ''
}

function removeWord(type: 'blocked_words' | 'sensitive_words', index: number) {
  settings.safety[type].splice(index, 1)
}

async function save() {
  saving.value = true
  Object.assign(settingsStore.model, settings.model)
  Object.assign(settingsStore.ui, settings.ui)
  Object.assign(settingsStore.safety, settings.safety)
  await settingsStore.saveSettings()
  settingsStore.applyTheme()
  saving.value = false
  uiStore.showSuccess(t('settings.saveSuccess'))
  emit('close')
}

onMounted(() => {
  tabs[0].label = t('settings.model')
  tabs[1].label = t('settings.ui')
  tabs[2].label = t('settings.safety')
  tabs[3].label = t('settings.about')
})
</script>

<style scoped>
.settings-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
  backdrop-filter: blur(4px);
}

.settings-layout {
  display: flex;
  height: calc(100% - 130px);
  overflow: hidden;
}

.settings-nav {
  width: 160px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-right: 1px solid var(--border-color);
}

.settings-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
  font-size: 0.9rem;
  text-align: left;
}

.settings-nav-item:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.settings-nav-item.active { background: var(--accent-subtle); color: var(--accent-color); }

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.settings-section h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.theme-options { display: flex; gap: 8px; }

.theme-option {
  padding: 10px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: var(--bg-tertiary);
}

.theme-option:hover { border-color: var(--border-hover); }
.theme-option.active { border-color: var(--accent-color); background: var(--accent-subtle); }

.color-options { display: flex; gap: 8px; }

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all var(--transition-fast);
}

.color-option:hover { transform: scale(1.1); }
.color-option.active { border-color: white; box-shadow: 0 0 0 2px var(--accent-color); }

.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; margin-bottom: 12px; }

.word-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }

.word-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.word-tag button {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.1);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.word-add { display: flex; gap: 8px; }

.test-result {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
}

.test-result.success { background: rgba(16,185,129,0.15); color: #10b981; }
.test-result.error { background: rgba(239,68,68,0.15); color: #ef4444; }

.about-info {
  text-align: center;
  padding: 32px;
}

.about-logo { font-size: 4rem; margin-bottom: 16px; }
.about-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; }
.about-version { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 16px; }
.about-desc { font-size: 0.875rem; color: var(--text-secondary); }

.form-row { display: flex; gap: 10px; margin-top: 12px; }

@media screen and (max-width: 640px) {
  .settings-layout { flex-direction: column; height: auto; }
  .settings-nav { width: 100%; flex-direction: row; overflow-x: auto; border-right: none; border-bottom: 1px solid var(--border-color); }
  .settings-nav-item { white-space: nowrap; }
}
</style>
