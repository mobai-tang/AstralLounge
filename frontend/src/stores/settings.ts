/**
 * Settings Store - 全局设置管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ModelSettings, TTSSettings, UISettings, SafetySettings } from '@/types'

const API_BASE = '/api'

export const useSettingsStore = defineStore('settings', () => {
  // 模型设置
  const model = ref<ModelSettings>({
    provider: 'ollama',
    model_name: 'llama3.2',
    api_url: 'http://localhost:11434',
    temperature: 0.7,
    max_tokens: 4096,
    top_p: 0.9,
    presence_penalty: 0,
    frequency_penalty: 0,
    stream: true
  })

  // TTS 设置
  const tts = ref<TTSSettings>({
    enabled: false,
    provider: 'cosyvoice',
    cosyvoice_url: 'http://localhost:5000',
    gptsovits_url: 'http://localhost:5001',
    default_voice: 'female_zh',
    speech_speed: 1.0
  })

  // UI 设置
  const ui = ref<UISettings>({
    theme: 'dark',
    accent_color: '#667eea',
    typing_effect: true,
    stream_response: true,
    compact_mode: false,
    language: 'zh'
  })

  // 安全设置
  const safety = ref<SafetySettings>({
    enabled: true,
    block_enabled: false,
    log_enabled: true,
    sensitive_action: 'warn',
    blocked_words: [],
    sensitive_words: []
  })

  const isLoaded = ref(false)
  const isSaving = ref(false)

  async function loadSettings() {
    try {
      const res = await fetch(`${API_BASE}/config/settings`)
      if (res.ok) {
        const data = await res.json()
        if (data.model) model.value = { ...model.value, ...data.model }
        if (data.tts) tts.value = { ...tts.value, ...data.tts }
        if (data.ui) ui.value = { ...ui.value, ...data.ui }
        if (data.safety) safety.value = { ...safety.value, ...data.safety }
        isLoaded.value = true
      }
    } catch (e) {
      console.error('加载设置失败:', e)
    }
  }

  async function saveSettings() {
    isSaving.value = true
    try {
      await fetch(`${API_BASE}/config/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: model.value,
          tts: tts.value,
          ui: ui.value,
          safety: safety.value
        })
      })
    } catch (e) {
      console.error('保存设置失败:', e)
    } finally {
      isSaving.value = false
    }
  }

  async function testConnection(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/health`)
      return res.ok
    } catch {
      return false
    }
  }

  function applyTheme() {
    const theme = ui.value.theme ?? 'dark'
    document.documentElement.setAttribute('data-theme', theme)
    if (theme === 'light') {
      document.documentElement.style.setProperty('--bg-primary', '#f5f5fa')
      document.documentElement.style.setProperty('--bg-secondary', '#ffffff')
      document.documentElement.style.setProperty('--bg-tertiary', '#eeeef4')
      document.documentElement.style.setProperty('--bg-elevated', '#ffffff')
      document.documentElement.style.setProperty('--text-primary', '#1a1a2e')
      document.documentElement.style.setProperty('--text-secondary', '#6b6b80')
      document.documentElement.style.setProperty('--text-muted', '#9999aa')
      document.documentElement.style.setProperty('--border-color', '#d8d8e6')
      document.documentElement.style.setProperty('--border-hover', '#c0c0d2')
    } else {
      document.documentElement.style.setProperty('--bg-primary', '#0f0f17')
      document.documentElement.style.setProperty('--bg-secondary', '#16161f')
      document.documentElement.style.setProperty('--bg-tertiary', '#1e1e2a')
      document.documentElement.style.setProperty('--bg-elevated', '#242432')
      document.documentElement.style.setProperty('--text-primary', '#e4e4ed')
      document.documentElement.style.setProperty('--text-secondary', '#9999a8')
      document.documentElement.style.setProperty('--text-muted', '#5c5c6d')
      document.documentElement.style.setProperty('--border-color', '#2a2a3c')
      document.documentElement.style.setProperty('--border-hover', '#3a3a50')
    }

    const accent = ui.value.accent_color ?? '#667eea'
    document.documentElement.style.setProperty('--accent-color', accent)
    document.documentElement.style.setProperty('--accent-hover', adjustColor(accent, -15))
    document.documentElement.style.setProperty('--accent-subtle', hexToRgba(accent, 0.12))
    document.documentElement.style.setProperty('--accent-subtle-hover', hexToRgba(accent, 0.18))
  }

  function hexToRgba(hex: string, alpha: number): string {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  function adjustColor(hex: string, amount: number): string {
    const r = Math.max(0, Math.min(255, parseInt(hex.slice(1, 3), 16) + amount))
    const g = Math.max(0, Math.min(255, parseInt(hex.slice(3, 5), 16) + amount))
    const b = Math.max(0, Math.min(255, parseInt(hex.slice(5, 7), 16) + amount))
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
  }

  return {
    model,
    tts,
    ui,
    safety,
    isLoaded,
    isSaving,
    loadSettings,
    saveSettings,
    testConnection,
    applyTheme
  }
})
