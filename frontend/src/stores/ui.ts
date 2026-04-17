/**
 * UI Store - 界面状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Notification, Toast } from '@/types'

let toastCounter = 0

export const useUIStore = defineStore('ui', () => {
  // 通知
  const notifications = ref<Notification[]>([])
  const notificationCount = ref(0)

  // Toast
  const toasts = ref<Toast[]>([])

  // 全屏加载
  const isFullscreenLoading = ref(false)
  const fullscreenMessage = ref('')

  // 侧边栏
  const sidebarOpen = ref(true)

  // 当前路由名称（用于高亮）
  const currentRoute = ref('')

  function init() {
    const saved = localStorage.getItem('notifications')
    if (saved) {
      try {
        notifications.value = JSON.parse(saved)
        updateCount()
      } catch {}
    }
  }

  function addNotification(n: Omit<Notification, 'id' | 'read' | 'timestamp'>) {
    const notif: Notification = {
      id: `notif-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      read: false,
      timestamp: Date.now(),
      ...n
    }
    notifications.value.unshift(notif)
    if (notifications.value.length > 100) {
      notifications.value = notifications.value.slice(0, 100)
    }
    saveNotifications()
    updateCount()
  }

  function markNotificationRead(id: string) {
    const n = notifications.value.find(n => n.id === id)
    if (n) n.read = true
    saveNotifications()
    updateCount()
  }

  function markAllNotificationsRead() {
    notifications.value.forEach(n => (n.read = true))
    saveNotifications()
    updateCount()
  }

  function clearNotifications() {
    notifications.value = []
    saveNotifications()
    updateCount()
  }

  function saveNotifications() {
    localStorage.setItem('notifications', JSON.stringify(notifications.value))
  }

  function updateCount() {
    notificationCount.value = notifications.value.filter(n => !n.read).length
  }

  function showToast(message: string, type: Toast['type'] = 'info', duration = 3000) {
    const id = `toast-${++toastCounter}`
    const toast: Toast = { id, message, type, duration }
    toasts.value.push(toast)
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  function showSuccess(message: string) { showToast(message, 'success') }
  function showError(message: string) { showToast(message, 'error', 5000) }
  function showWarning(message: string) { showToast(message, 'warning', 4000) }
  function showInfo(message: string) { showToast(message, 'info') }

  function setFullscreenLoading(loading: boolean, message = '') {
    isFullscreenLoading.value = loading
    fullscreenMessage.value = message
  }

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function setCurrentRoute(name: string) {
    currentRoute.value = name
  }

  return {
    notifications,
    notificationCount,
    toasts,
    isFullscreenLoading,
    fullscreenMessage,
    sidebarOpen,
    currentRoute,
    init,
    addNotification,
    markNotificationRead,
    markAllNotificationsRead,
    clearNotifications,
    showToast,
    removeToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    setFullscreenLoading,
    toggleSidebar,
    setCurrentRoute
  }
})
