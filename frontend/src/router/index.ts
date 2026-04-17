import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
  },
  {
    path: '/characters',
    name: 'Characters',
    component: () => import('@/views/CharactersView.vue'),
  },
  {
    path: '/lorebooks',
    name: 'Lorebooks',
    component: () => import('@/views/LorebooksView.vue'),
  },
  {
    path: '/memory',
    name: 'Memory',
    component: () => import('@/views/MemoryView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
  },
  {
    path: '/plugins',
    name: 'Plugins',
    component: () => import('@/views/PluginsView.vue'),
  },
  {
    path: '/group-chat',
    name: 'GroupChat',
    component: () => import('@/views/GroupChatView.vue'),
  },
  {
    path: '/test',
    name: 'Test',
    component: () => import('@/views/TestView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
