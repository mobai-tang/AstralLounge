<template>
  <div class="tts-player">
    <div v-if="!enabled" class="tts-disabled">
      <span class="tts-hint">🔇 语音合成未启用</span>
    </div>
    <div v-else class="tts-controls">
      <button
        v-if="!isPlaying"
        class="btn btn-sm btn-secondary"
        @click="play"
        :disabled="!currentText"
        :title="$t('settings.testVoice')"
      >
        🔊 {{ $t('settings.testVoice') }}
      </button>
      <button v-else class="btn btn-sm btn-secondary" @click="stop">
        ⏹ 停止
      </button>
      <input
        v-model="text"
        class="input"
        :placeholder="$t('chat.typeMessage')"
        @keyup.enter="play"
      />
      <div class="speed-control">
        <label class="speed-label">{{ $t('settings.speechSpeed') }}: {{ speed.toFixed(1) }}x</label>
        <input v-model.number="speed" type="range" min="0.5" max="2" step="0.1" class="speed-slider" />
      </div>
      <select v-model="voice" class="select voice-select">
        <option v-for="v in voices" :key="v" :value="v">{{ v }}</option>
      </select>
    </div>

    <div v-if="isPlaying" class="waveform">
      <span v-for="i in 5" :key="i" class="wave" :style="{ animationDelay: `${i * 0.1}s` }"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const enabled = ref(false)
const isPlaying = ref(false)
const text = ref('')
const speed = ref(1.0)
const voice = ref('female_zh')
const voices = ref(['female_zh', 'male_zh', 'female_en', 'male_en'])

const currentText = computed(() => text.value.trim())

async function play() {
  if (!currentText.value || isPlaying.value) return
  isPlaying.value = true
  try {
    const res = await fetch('/api/tts/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: currentText.value, voice: voice.value, speed: speed.value })
    })
    if (res.ok) {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.playbackRate = speed.value
      audio.onended = () => {
        isPlaying.value = false
        URL.revokeObjectURL(url)
      }
      audio.onerror = () => {
        isPlaying.value = false
        URL.revokeObjectURL(url)
      }
      await audio.play()
    }
  } catch (e) {
    console.error('TTS 播放失败:', e)
    isPlaying.value = false
  }
}

function stop() {
  isPlaying.value = false
}
</script>

<style scoped>
.tts-player {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tts-disabled {
  padding: 12px;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.tts-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tts-controls .input { flex: 1; min-width: 120px; }

.speed-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.speed-label { font-size: 0.8rem; color: var(--text-secondary); white-space: nowrap; }

.speed-slider {
  width: 80px;
  accent-color: var(--accent-color);
}

.voice-select { min-width: 100px; }

.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 24px;
}

.wave {
  width: 3px;
  height: 16px;
  background: var(--accent-color);
  border-radius: 2px;
  animation: wave 0.8s ease-in-out infinite;
}

@keyframes wave {
  0%, 100% { height: 6px; }
  50% { height: 20px; }
}
</style>
