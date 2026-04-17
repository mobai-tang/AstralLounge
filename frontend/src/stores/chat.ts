/**
 * Chat Store - 对话相关状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatSession, CharacterMessage, Group } from '@/types'

const API_BASE = '/api'

export const useChatStore = defineStore('chat', () => {
  // ============ 状态 ============
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const groups = ref<Group[]>([])
  const isLoading = ref(false)
  const isSending = ref(false)
  const isStreaming = ref(false)

  // Ghost 模式状态
  const ghostMode = ref(false)
  const ghostPendingMessage = ref<string | null>(null)

  // 搜索
  const searchQuery = ref('')
  const selectedGroupId = ref<string | null>(null)

  // ============ Getters ============
  const currentSession = computed(() => {
    if (!currentSessionId.value) return null
    return sessions.value.find(s => s.id === currentSessionId.value) ?? null
  })

  const filteredSessions = computed(() => {
    let list = sessions.value
    if (selectedGroupId.value) {
      list = list.filter(s => s.groupId === selectedGroupId.value)
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      list = list.filter(s => s.name.toLowerCase().includes(q))
    }
    return list.sort((a, b) => {
      if (a.pinned && !b.pinned) return -1
      if (!a.pinned && b.pinned) return 1
      return (b.updatedAt ?? 0) - (a.updatedAt ?? 0)
    })
  })

  const pinnedSessions = computed(() => sessions.value.filter(s => s.pinned))

  const contextWarning = computed(() => {
    const session = currentSession.value
    if (!session) return null
    const tokens = session.tokenCount ?? 0
    if (tokens > 8000) return 'critical'
    if (tokens > 5000) return 'warning'
    return null
  })

  // ============ Actions ============
  async function loadSessions() {
    isLoading.value = true
    try {
      const res = await fetch(`${API_BASE}/chat/sessions`)
      if (res.ok) {
        const data = await res.json()
        sessions.value = data.sessions ?? []
        if (sessions.value.length > 0 && !currentSessionId.value) {
          currentSessionId.value = sessions.value[0].id
        }
      }
    } catch (e) {
      console.error('加载会话失败:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function createSession(name?: string, characterId?: string, characterName?: string): Promise<ChatSession | null> {
    try {
      const res = await fetch(`${API_BASE}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, characterId, characterName })
      })
      if (res.ok) {
        const session: ChatSession = await res.json()
        sessions.value.unshift(session)
        currentSessionId.value = session.id
        return session
      }
    } catch (e) {
      console.error('创建会话失败:', e)
    }
    return null
  }

  async function deleteSession(sessionId: string) {
    try {
      const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { method: 'DELETE' })
      if (res.ok) {
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
        if (currentSessionId.value === sessionId) {
          currentSessionId.value = sessions.value[0]?.id ?? null
        }
      }
    } catch (e) {
      console.error('删除会话失败:', e)
    }
  }

  async function renameSession(sessionId: string, name: string) {
    const session = sessions.value.find(s => s.id === sessionId)
    if (!session) return
    session.name = name
    try {
      await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
    } catch (e) {
      console.error('重命名会话失败:', e)
    }
  }

  async function togglePinSession(sessionId: string) {
    const session = sessions.value.find(s => s.id === sessionId)
    if (!session) return
    session.pinned = !session.pinned
    try {
      await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pinned: session.pinned })
      })
    } catch (e) {
      console.error('切换置顶失败:', e)
    }
  }

  async function sendMessage(content: string) {
    if (!currentSession.value || isSending.value) return
    isSending.value = true

    // Ghost 模式处理
    if (ghostMode.value) {
      ghostPendingMessage.value = content
      return
    }

    // 添加用户消息
    const userMsg: CharacterMessage = {
      role: 'user',
      content,
      timestamp: Date.now()
    }
    currentSession.value.messages.push(userMsg)
    currentSession.value.updatedAt = Date.now()

    try {
      const res = await fetch(`${API_BASE}/chat/sessions/${currentSessionId.value}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      })

      if (res.ok && res.body) {
        const assistantMsg: CharacterMessage = {
          role: 'assistant',
          content: '',
          timestamp: Date.now()
        }
        currentSession.value.messages.push(assistantMsg)

        const reader = res.body.getReader()
        const decoder = new TextDecoder()

        isStreaming.value = true
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value)
          assistantMsg.content += chunk
        }
        isStreaming.value = false
      }
    } catch (e) {
      console.error('发送消息失败:', e)
    } finally {
      isSending.value = false
    }
  }

  function confirmGhostMessage() {
    if (!ghostPendingMessage.value) return
    sendMessage(ghostPendingMessage.value)
    ghostPendingMessage.value = null
    ghostMode.value = false
  }

  function discardGhostMessage() {
    ghostPendingMessage.value = null
    ghostMode.value = false
  }

  function switchSession(sessionId: string) {
    currentSessionId.value = sessionId
  }

  async function loadGroups() {
    try {
      const res = await fetch(`${API_BASE}/chat/groups`)
      if (res.ok) {
        groups.value = await res.json()
      }
    } catch (e) {
      console.error('加载分组失败:', e)
    }
  }

  async function createGroup(name: string, color?: string) {
    try {
      const res = await fetch(`${API_BASE}/chat/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, color })
      })
      if (res.ok) {
        const group: Group = await res.json()
        groups.value.push(group)
        return group
      }
    } catch (e) {
      console.error('创建分组失败:', e)
    }
    return null
  }

  async function moveSessionToGroup(sessionId: string, groupId?: string) {
    const session = sessions.value.find(s => s.id === sessionId)
    if (!session) return
    session.groupId = groupId
    try {
      await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groupId })
      })
    } catch (e) {
      console.error('移动会话失败:', e)
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    filteredSessions,
    pinnedSessions,
    groups,
    isLoading,
    isSending,
    isStreaming,
    ghostMode,
    ghostPendingMessage,
    contextWarning,
    searchQuery,
    selectedGroupId,
    loadSessions,
    createSession,
    deleteSession,
    renameSession,
    togglePinSession,
    sendMessage,
    confirmGhostMessage,
    discardGhostMessage,
    switchSession,
    loadGroups,
    createGroup,
    moveSessionToGroup
  }
})
