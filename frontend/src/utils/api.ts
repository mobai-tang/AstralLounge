/**
 * AstralLounge API 客户端封装
 */

const API_BASE = '/api'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    method: string,
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    }

    const response = await fetch(url, {
      method,
      headers,
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: '请求失败' }))
      throw new Error(error.detail || error.message || `HTTP ${response.status}`)
    }

    // 流式响应直接返回
    if (response.body) {
      return response as unknown as T
    }

    return response.json()
  }

  // ============ 健康检查 ============
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request('GET', '/health')
  }

  // ============ 配置 ============
  async getSettings() {
    return this.request('GET', '/config/settings')
  }

  async saveSettings(data: object) {
    return this.request('POST', '/config/settings', { body: JSON.stringify(data) })
  }

  async getAvailableModels() {
    return this.request<{ models: string[] }>('GET', '/config/models/available')
  }

  async refreshModels() {
    return this.request('POST', '/config/models/refresh')
  }

  async switchModel(modelName: string) {
    return this.request('POST', '/config/models/switch', {
      body: JSON.stringify({ type: 'ollama', model_name: modelName }),
    })
  }

  // ============ 角色 ============
  async getCharacters() {
    return this.request<any[]>('GET', '/characters')
  }

  async getCharacter(id: string) {
    return this.request('GET', `/characters/${id}`)
  }

  async createCharacter(data: object) {
    return this.request('POST', '/characters', { body: JSON.stringify(data) })
  }

  async updateCharacter(id: string, data: object) {
    return this.request('PUT', `/characters/${id}`, { body: JSON.stringify(data) })
  }

  async deleteCharacter(id: string) {
    return this.request('DELETE', `/characters/${id}`)
  }

  async importCharacters(data: string, filename?: string) {
    return this.request('POST', '/characters/import', {
      body: JSON.stringify({ data, filename }),
    })
  }

  getCharacterAvatar(id: string): string {
    return `${this.baseUrl}/characters/${id}/avatar`
  }

  // ============ 对话 ============
  async getSessions() {
    return this.request<{ sessions: any[] }>('GET', '/chat/sessions')
  }

  async getSession(id: string) {
    return this.request('GET', `/chat/sessions/${id}`)
  }

  async createSession(data: { name?: string; characterId?: string; characterName?: string }) {
    return this.request('POST', '/chat/sessions', { body: JSON.stringify(data) })
  }

  async updateSession(id: string, data: object) {
    return this.request('PATCH', `/chat/sessions/${id}`, { body: JSON.stringify(data) })
  }

  async deleteSession(id: string) {
    return this.request('DELETE', `/chat/sessions/${id}`)
  }

  async sendMessage(sessionId: string, content: string): Promise<Response> {
    return this.request('POST', `/chat/sessions/${sessionId}/messages`, {
      body: JSON.stringify({ content }),
    })
  }

  // ============ 分组 ============
  async getGroups() {
    return this.request<any[]>('GET', '/chat/groups')
  }

  async createGroup(name: string, color?: string) {
    return this.request('POST', '/chat/groups', {
      body: JSON.stringify({ name, color }),
    })
  }

  async deleteGroup(id: string) {
    return this.request('DELETE', `/chat/groups/${id}`)
  }

  // ============ 群聊 ============
  async getGroupChats() {
    return this.request<any[]>('GET', '/group-chat/groups')
  }

  async createGroupChat(name: string) {
    return this.request('POST', '/group-chat/groups', {
      body: JSON.stringify({ name }),
    })
  }

  async getGroupChatMessages(groupId: string) {
    return this.request<any[]>(`/group-chat/${groupId}/messages`)
  }

  async addGroupChatMember(groupId: string, characterId: string, name: string) {
    return this.request('POST', `/group-chat/${groupId}/members`, {
      body: JSON.stringify({ characterId, name }),
    })
  }

  async removeGroupChatMember(groupId: string, memberId: string) {
    return this.request('DELETE', `/group-chat/${groupId}/members/${memberId}`)
  }

  // ============ 世界设定 ============
  async getLorebooks() {
    return this.request<any[]>('GET', '/lorebooks')
  }

  async getLorebook(id: string) {
    return this.request('GET', `/lorebooks/${id}`)
  }

  async createLorebook(data: object) {
    return this.request('POST', '/lorebooks', { body: JSON.stringify(data) })
  }

  async updateLorebook(id: string, data: object) {
    return this.request('PUT', `/lorebooks/${id}`, { body: JSON.stringify(data) })
  }

  async deleteLorebook(id: string) {
    return this.request('DELETE', `/lorebooks/${id}`)
  }

  async createLorebookEntry(bookId: string, data: object) {
    return this.request('POST', `/lorebooks/${bookId}/entries`, { body: JSON.stringify(data) })
  }

  async updateLorebookEntry(bookId: string, entryId: string, data: object) {
    return this.request('PUT', `/lorebooks/${bookId}/entries/${entryId}`, {
      body: JSON.stringify(data),
    })
  }

  async deleteLorebookEntry(bookId: string, entryId: string) {
    return this.request('DELETE', `/lorebooks/${bookId}/entries/${entryId}`)
  }

  // ============ 记忆 ============
  async getMemories() {
    return this.request<any[]>('GET', '/memory')
  }

  async getMemory(id: string) {
    return this.request('GET', `/memory/${id}`)
  }

  async createMemory(data: object) {
    return this.request('POST', '/memory', { body: JSON.stringify(data) })
  }

  async updateMemory(id: string, data: object) {
    return this.request('PUT', `/memory/${id}`, { body: JSON.stringify(data) })
  }

  async deleteMemory(id: string) {
    return this.request('DELETE', `/memory/${id}`)
  }

  async searchMemories(query: string, limit = 10) {
    return this.request<any[]>('POST', '/memory/search', {
      body: JSON.stringify({ query, limit }),
    })
  }

  // ============ 插件 ============
  async getPlugins() {
    return this.request<any[]>('GET', '/plugins')
  }

  async getPlugin(name: string) {
    return this.request('GET', `/plugins/${name}`)
  }

  async reloadPlugin(name: string) {
    return this.request('POST', `/plugins/${name}/reload`)
  }

  async reloadAllPlugins() {
    return this.request('POST', '/plugins/reload-all')
  }
}

export const api = new ApiClient()
export default api
