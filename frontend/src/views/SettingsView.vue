<template>
  <div class="settings-view">
    <div class="settings-page">
      <h1>{{ $t('settings.title') }}</h1>
      <div class="settings-grid">
        <!-- 模型设置 -->
        <div class="settings-card">
          <div class="card-header">
            <span class="card-icon">🤖</span>
            <h2>{{ $t('settings.model') }}</h2>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label class="form-label">{{ $t('settings.provider') }}</label>
              <select v-model="settings.model.provider" class="select" style="width: 100%;">
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
          </div>
        </div>

        <!-- 界面设置 -->
        <div class="settings-card">
          <div class="card-header">
            <span class="card-icon">🎨</span>
            <h2>{{ $t('settings.ui') }}</h2>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label class="form-label">{{ $t('settings.theme') }}</label>
              <div class="theme-options">
                <div :class="['theme-option', { active: settings.ui.theme === 'dark' }]" @click="settings.ui.theme = 'dark'">🌙 {{ $t('settings.darkTheme') }}</div>
                <div :class="['theme-option', { active: settings.ui.theme === 'light' }]" @click="settings.ui.theme = 'light'">☀️ {{ $t('settings.lightTheme') }}</div>
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
              <label class="form-label">{{ $t('settings.language') }}</label>
              <select v-model="settings.ui.language" class="select" style="width: 100%;">
                <option value="zh">🇨🇳 简体中文</option>
                <option value="en">🇺🇸 English</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div class="settings-card">
          <div class="card-header">
            <span class="card-icon">🛡️</span>
            <h2>{{ $t('settings.safety') }}</h2>
          </div>
          <div class="card-body">
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
          </div>
        </div>

        <!-- TTS 设置 -->
        <div class="settings-card">
          <div class="card-header">
            <span class="card-icon">🔊</span>
            <h2>{{ $t('settings.tts') }}</h2>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label class="toggle-label">
                <div :class="['toggle', { active: settings.tts.enabled }]" @click="settings.tts.enabled = !settings.tts.enabled"></div>
                {{ settings.tts.enabled ? '已启用' : '未启用' }}
              </label>
            </div>
            <div v-if="settings.tts.enabled" class="form-group">
              <label class="form-label">{{ $t('settings.provider') }}</label>
              <select v-model="settings.tts.provider" class="select" style="width: 100%;">
                <option value="cosyvoice">CosyVoice</option>
                <option value="gptsovits">GPT-SoVITS</option>
              </select>
            </div>
            <div v-if="settings.tts.enabled" class="form-group">
              <label class="form-label">{{ $t('settings.speechSpeed') }}: {{ settings.tts.speech_speed }}x</label>
              <input v-model.number="settings.tts.speech_speed" type="range" min="0.5" max="2" step="0.1" style="width: 100%;" />
            </div>
          </div>
        </div>

        <!-- 关于 -->
        <div class="settings-card about-card">
          <div class="card-header">
            <span class="card-icon">✨</span>
            <h2>{{ $t('settings.about') }}</h2>
          </div>
          <div class="card-body about-body">
            <div class="about-logo">✨</div>
            <div class="about-name">{{ $t('settings.appName') }}</div>
            <div class="about-version">{{ $t('settings.version') }} {{ $t('settings.versionNumber') }}</div>
            <div class="about-desc">{{ $t('settings.description') }}</div>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <button class="btn btn-primary btn-lg" @click="saveSettings">{{ $t('common.save') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import { useUIStore } from '@/stores/ui'

const { t } = useI18n()
const settingsStore = useSettingsStore()
const uiStore = useUIStore()

const settings = reactive({
  model: { ...settingsStore.model },
  ui: { ...settingsStore.ui },
  safety: { ...settingsStore.safety },
  tts: { ...settingsStore.tts }
})

const accentColors = ['#667eea', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#ec4899', '#8b5cf6']

async function saveSettings() {
  Object.assign(settingsStore.model, settings.model)
  Object.assign(settingsStore.ui, settings.ui)
  Object.assign(settingsStore.safety, settings.safety)
  Object.assign(settingsStore.tts, settings.tts)
  await settingsStore.saveSettings()
  settingsStore.applyTheme()
  uiStore.showSuccess(t('settings.saveSuccess'))
}

onMounted(() => {
  Object.assign(settings, {
    model: { ...settingsStore.model },
    ui: { ...settingsStore.ui },
    safety: { ...settingsStore.safety },
    tts: { ...settingsStore.tts }
  })
})
</script>

<style scoped>
.settings-view {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.settings-page {
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 24px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.settings-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.about-card { grid-column: 1 / -1; }

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 { margin: 0; font-size: 1rem; font-weight: 600; }
.card-icon { font-size: 1.2rem; }

.card-body { padding: 16px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.theme-options { display: flex; gap: 8px; }

.theme-option {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: center;
  font-size: 0.85rem;
  background: var(--bg-tertiary);
  transition: all var(--transition-fast);
}

.theme-option:hover { border-color: var(--border-hover); }
.theme-option.active { border-color: var(--accent-color); background: var(--accent-subtle); }

.color-options { display: flex; gap: 8px; }

.color-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all var(--transition-fast);
}

.color-option:hover { transform: scale(1.1); }
.color-option.active { border-color: white; box-shadow: 0 0 0 2px var(--accent-color); }

.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; }

.about-body { text-align: center; padding: 24px; }
.about-logo { font-size: 3rem; margin-bottom: 12px; }
.about-name { font-size: 1.3rem; font-weight: 700; margin-bottom: 6px; }
.about-version { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 10px; }
.about-desc { color: var(--text-secondary); font-size: 0.85rem; }

.settings-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

@media screen and (max-width: 640px) {
  .settings-grid { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
