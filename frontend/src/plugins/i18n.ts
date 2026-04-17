/**
 * AstralLounge Vue i18n 插件
 * 支持后端翻译 + 前端内置翻译（后者作为兜底）
 */
import { createI18n } from 'vue-i18n'
import type { MessageSchema } from 'vue-i18n'
import { zh, en } from './i18n-messages'

const API_BASE = '/api'

const builtinMessages: Record<string, MessageSchema> = { zh, en } as any

type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

function deepMerge<T extends Record<string, unknown>>(target: T, source: DeepPartial<T>): T {
  const result = { ...target }
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(
        (target[key] ?? {}) as Record<string, unknown>,
        source[key] as DeepPartial<Record<string, unknown>>
      ) as T[Extract<keyof T, string>]
    } else if (source[key] !== undefined) {
      result[key] = source[key] as T[Extract<keyof T, string>]
    }
  }
  return result
}

async function loadFromBackend(lang: string): Promise<MessageSchema> {
  if (!builtinMessages[lang]) return {} as MessageSchema
  try {
    const res = await fetch(`${API_BASE}/i18n/translations?lang=${lang}`)
    if (res.ok) {
      const data = await res.json()
      return deepMerge(builtinMessages[lang] as Record<string, unknown>, data) as MessageSchema
    }
  } catch {
    // 忽略，使用内置翻译
  }
  return builtinMessages[lang] ?? {} as MessageSchema
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'zh',
  messages: { ...builtinMessages } as any,
})

export async function initI18n(lang = 'zh'): Promise<void> {
  const langs = [...new Set([lang, 'zh', 'en'])]
  const results = await Promise.all(
    langs.map(async (l): Promise<{ lang: string; messages: MessageSchema }> => {
      const msgs = await loadFromBackend(l)
      return { lang: l, messages: msgs }
    })
  )

  for (const { lang: l, messages } of results) {
    (i18n.global.messages.value as any)[l] = messages
  }

  i18n.global.locale.value = lang
  document.documentElement.lang = lang
}

export async function setI18nLanguage(lang: string): Promise<void> {
  if (!(i18n.global.messages.value as any)[lang]) {
    const messages = await loadFromBackend(lang)
    ;(i18n.global.messages.value as any)[lang] = messages
  }
  i18n.global.locale.value = lang
  document.documentElement.lang = lang

  try {
    await fetch(`${API_BASE}/i18n/language`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang })
    })
  } catch {
    // 忽略
  }

  localStorage.setItem('language', lang)
}

export async function getAvailableLanguages(): Promise<Array<{ code: string; name: string; native: string; flag: string }>> {
  try {
    const res = await fetch(`${API_BASE}/i18n/languages`)
    if (res.ok) return await res.json()
  } catch {
    // 忽略
  }
  return [
    { code: 'zh', name: '中文', native: '简体中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', native: 'English', flag: '🇺🇸' },
  ]
}

export default i18n
