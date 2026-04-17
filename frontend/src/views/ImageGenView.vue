<template>
  <div class="image-gen-view">
    <div class="gen-layout">
      <!-- 左侧：生成控制 -->
      <aside class="control-panel">
        <h2>图片生成</h2>

        <div class="service-status">
          <div class="status-item">
            <span class="status-dot" :class="{ active: sdAvailable }"></span>
            Stable Diffusion: {{ sdAvailable ? '可用' : '未配置' }}
          </div>
          <div class="status-item">
            <span class="status-dot" :class="{ active: dalleAvailable }"></span>
            DALL-E: {{ dalleAvailable ? '可用' : '未配置' }}
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">生成器</label>
          <select v-model="engine" class="select" style="width: 100%;">
            <option v-for="s in availableServices" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">提示词 *</label>
          <textarea v-model="form.prompt" class="input textarea" rows="4" placeholder="描述你想生成的图片..."></textarea>
        </div>

        <div class="form-group">
          <label class="form-label">负面提示词</label>
          <textarea v-model="form.negativePrompt" class="input textarea" rows="2" placeholder="不想出现在图片中的元素..."></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">宽度</label>
            <select v-model="form.width" class="select" style="width: 100%;">
              <option :value="512">512px</option>
              <option :value="768">768px</option>
              <option :value="1024">1024px</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">高度</label>
            <select v-model="form.height" class="select" style="width: 100%;">
              <option :value="512">512px</option>
              <option :value="768">768px</option>
              <option :value="1024">1024px</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">生成步数: {{ form.steps }}</label>
          <input v-model.number="form.steps" type="range" min="10" max="50" step="1" style="width: 100%;" />
        </div>

        <div class="form-group">
          <label class="form-label">CFG 强度: {{ form.cfgScale }}</label>
          <input v-model.number="form.cfgScale" type="range" min="1" max="15" step="0.5" style="width: 100%;" />
        </div>

        <div class="form-group">
          <label class="form-label">Seed（留空随机）</label>
          <input v-model.number="form.seed" type="number" class="input" placeholder="随机" />
        </div>

        <div v-if="engine === 'Stable Diffusion'" class="form-group">
          <label class="form-label">采样器</label>
          <select v-model="form.sampler" class="select" style="width: 100%;">
            <option v-for="s in samplers" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <button class="btn btn-primary" style="width: 100%;" @click="generate" :disabled="isGenerating || !form.prompt.trim()">
          {{ isGenerating ? '生成中...' : '生成图片' }}
        </button>
      </aside>

      <!-- 右侧：图片展示 -->
      <main class="gallery-panel">
        <div v-if="isGenerating" class="loading-state">
          <div class="loading-spinner"></div>
          <p>正在生成图片...</p>
        </div>

        <div v-else-if="currentImage" class="image-result">
          <img :src="currentImage" alt="Generated" class="result-image" />
          <div class="image-actions">
            <button class="btn btn-secondary" @click="downloadImage">📥 下载</button>
            <button class="btn btn-secondary" @click="copyImage">📋 复制</button>
            <button class="btn btn-ghost" @click="currentImage = null">🗑️ 清除</button>
          </div>
          <div v-if="lastSeed" class="image-meta">Seed: {{ lastSeed }}</div>
        </div>

        <div v-else class="empty-gallery">
          <div class="empty-icon">🖼️</div>
          <p>输入提示词开始生成图片</p>
        </div>

        <div v-if="history.length > 0" class="history-section">
          <h3>历史记录</h3>
          <div class="history-grid">
            <div v-for="(img, idx) in history" :key="idx" class="history-item">
              <img :src="img.data" @click="currentImage = img.data" />
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()

const engine = ref('Stable Diffusion')
const isGenerating = ref(false)
const currentImage = ref<string | null>(null)
const lastSeed = ref<number | null>(null)
const history = ref<Array<{ data: string; prompt: string; seed?: number }>>([])

const form = reactive({
  prompt: '',
  negativePrompt: '',
  width: 512,
  height: 512,
  steps: 25,
  cfgScale: 7.0,
  seed: null as number | null,
  sampler: 'Euler a',
  model: ''
})

const samplers = [
  'Euler a', 'Euler', 'LMS', 'Heun', 'DPM2', 'DPM2 a',
  'DPM++ 2S a', 'DPM++ 2M', 'DPM++ SDE', 'DDIM', 'PLMS'
]

const sdAvailable = ref(false)
const dalleAvailable = ref(false)

const availableServices = computed(() => {
  const svcs: string[] = []
  if (sdAvailable.value) svcs.push('Stable Diffusion')
  if (dalleAvailable.value) svcs.push('DALL-E')
  return svcs.length ? svcs : ['无可用服务']
})

async function checkStatus() {
  try {
    const res = await fetch('/api/image/status')
    if (res.ok) {
      const data = await res.json()
      sdAvailable.value = data.stable_diffusion || false
      dalleAvailable.value = data.dalle || false
    }
  } catch {
    console.error('获取图片服务状态失败')
  }
}

async function generate() {
  if (!form.prompt.trim() || isGenerating.value) return
  isGenerating.value = true
  currentImage.value = null

  try {
    const payload: Record<string, unknown> = {
      prompt: form.prompt,
      negative_prompt: form.negativePrompt,
      width: form.width,
      height: form.height,
      steps: form.steps,
      cfg_scale: form.cfgScale,
    }
    if (form.seed) payload.seed = form.seed
    if (form.sampler) payload.sampler = form.sampler

    const res = await fetch('/api/image/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (res.ok) {
      const data = await res.json()
      currentImage.value = data.image
      lastSeed.value = data.seed ?? null
      history.value.unshift({ data: data.image, prompt: form.prompt, seed: data.seed })
      if (history.value.length > 20) history.value.pop()
    } else {
      const err = await res.json()
      uiStore.showError(err.detail || '生成失败')
    }
  } catch {
    uiStore.showError('图片生成失败')
  } finally {
    isGenerating.value = false
  }
}

function downloadImage() {
  if (!currentImage.value) return
  const a = document.createElement('a')
  a.href = currentImage.value
  a.download = `astral_gen_${Date.now()}.png`
  a.click()
}

async function copyImage() {
  if (!currentImage.value) return
  try {
    const res = await fetch(currentImage.value)
    const blob = await res.blob()
    await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })])
    uiStore.showSuccess('已复制到剪贴板')
  } catch {
    uiStore.showError('复制失败')
  }
}

onMounted(() => {
  checkStatus()
})
</script>

<style scoped>
.image-gen-view {
  height: 100%;
  overflow: hidden;
}

.gen-layout {
  display: flex;
  height: 100%;
}

.control-panel {
  width: 320px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.control-panel h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.service-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}
.status-dot.active {
  background: #10b981;
  box-shadow: 0 0 4px rgba(16,185,129,0.5);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.gallery-panel {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.image-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.result-image {
  max-width: 100%;
  max-height: 60vh;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  object-fit: contain;
}

.image-actions {
  display: flex;
  gap: 8px;
}

.image-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.empty-gallery {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}
.empty-icon { font-size: 4rem; }

.history-section {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}
.history-section h3 {
  margin: 0 0 12px;
  font-size: 0.95rem;
  color: var(--text-secondary);
}
.history-grid { display: flex; gap: 8px; flex-wrap: wrap; }
.history-item img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-md);
  cursor: pointer;
  border: 1px solid var(--border-color);
  transition: border-color var(--transition-fast);
}
.history-item img:hover { border-color: var(--accent-color); }

@media screen and (max-width: 768px) {
  .gen-layout { flex-direction: column; }
  .control-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    max-height: 50vh;
  }
}
</style>
