<template>
  <div class="settings-view">
    <div class="settings-page">
      <div class="settings-header">
        <h1>{{ $t('settings.title') }}</h1>
      </div>

      <div class="settings-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- 模型提供商管理 -->
      <div v-if="activeTab === 'providers'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.modelProvider.title') }}</h2>
          <div class="header-actions">
            <button class="btn btn-secondary" @click="testAllProviders" :disabled="testingAll">
              {{ testingAll ? $t('settings.modelProvider.testing') : $t('settings.modelProvider.testAll') }}
            </button>
            <button class="btn btn-secondary" @click="showAddProvider = true">
              + {{ $t('settings.modelProvider.addCustom') }}
            </button>
          </div>
        </div>

        <!-- 分类展示提供商 -->
        <div v-for="category in providerCategories" :key="category.id" class="provider-category">
          <div class="category-header">
            <span class="category-icon">{{ category.icon }}</span>
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">{{ getProvidersByCategory(category.id).length }}</span>
          </div>
          <div class="provider-grid">
            <div
              v-for="provider in getProvidersByCategory(category.id)"
              :key="provider.id"
              :class="['provider-card', { active: currentProvider === provider.id, connected: providerStatus[provider.id]?.success }]"
            >
              <div class="provider-header">
                <div class="provider-color" :style="{ background: provider.color }"></div>
                <div class="provider-info">
                  <div class="provider-name">{{ provider.name }}</div>
                  <div class="provider-desc">{{ provider.description }}</div>
                </div>
                <div class="provider-status">
                  <span v-if="providerStatus[provider.id]" :class="['status-badge', providerStatus[provider.id].success ? 'success' : 'error']">
                    {{ providerStatus[provider.id].success ? '✓' : '✗' }}
                  </span>
                  <span v-if="provider.requiresApiKey && !provider.hasApiKey" class="status-badge warning" title="需要配置 API Key">!</span>
                </div>
              </div>

              <div class="provider-config">
                <div class="config-row">
                  <label class="config-label">{{ $t('settings.modelProvider.baseUrl') }}</label>
                  <input
                    v-model="providerConfigs[provider.id].baseUrl"
                    class="input"
                    :placeholder="provider.defaultUrl"
                  />
                </div>

                <div v-if="provider.requiresApiKey" class="config-row">
                  <label class="config-label">{{ $t('settings.modelProvider.apiKey') }}</label>
                  <div class="api-key-input">
                    <input
                      v-model="providerConfigs[provider.id].apiKey"
                      :type="showApiKeys[provider.id] ? 'text' : 'password'"
                      class="input"
                      :placeholder="$t('settings.modelProvider.enterApiKey')"
                    />
                    <button class="btn btn-ghost btn-icon" @click="toggleApiKeyVisibility(provider.id)">
                      {{ showApiKeys[provider.id] ? '👁️' : '👁️‍🗨️' }}
                    </button>
                  </div>
                </div>

                <div class="config-row">
                  <label class="config-label">{{ $t('settings.modelProvider.model') }}</label>
                  <div class="model-select-row">
                    <select v-model="providerConfigs[provider.id].model" class="select">
                      <option value="">{{ $t('settings.modelProvider.selectModel') }}</option>
                      <option v-for="m in provider.models" :key="m" :value="m">{{ m }}</option>
                      <option v-if="!provider.models.length" value="custom">{{ $t('settings.modelProvider.customModel') }}</option>
                    </select>
                    <button class="btn btn-secondary btn-sm" @click="refreshModels(provider.id)" :disabled="refreshingModels[provider.id]">
                      {{ refreshingModels[provider.id] ? '...' : '🔄' }}
                    </button>
                  </div>
                </div>

                <div v-if="providerConfigs[provider.id].model === 'custom'" class="config-row">
                  <label class="config-label">{{ $t('settings.modelProvider.customModelName') }}</label>
                  <input v-model="providerConfigs[provider.id].customModel" class="input" />
                </div>
              </div>

              <div class="provider-actions">
                <button class="btn btn-primary btn-sm" @click="selectProvider(provider.id)">
                  {{ currentProvider === provider.id ? $t('settings.modelProvider.selected') : $t('settings.modelProvider.select') }}
                </button>
                <button class="btn btn-secondary btn-sm" @click="testProvider(provider.id)" :disabled="testingProviders[provider.id]">
                  {{ testingProviders[provider.id] ? '...' : $t('settings.modelProvider.test') }}
                </button>
                <button class="btn btn-ghost btn-sm" @click="saveProviderConfig(provider.id)">
                  {{ $t('common.save') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 模型参数配置 -->
      <div v-if="activeTab === 'parameters'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.modelParameters.title') }}</h2>
        </div>

        <div class="settings-card">
          <div class="card-body">
            <div class="param-grid">
              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.temperature') }}</label>
                  <span class="param-value">{{ modelParams.temperature }}</span>
                </div>
                <input v-model.number="modelParams.temperature" type="range" min="0" max="2" step="0.1" class="range-input" />
                <div class="param-hints">
                  <span>0.0</span>
                  <span>1.0</span>
                  <span>2.0</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.temperatureHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.maxTokens') }}</label>
                  <span class="param-value">{{ modelParams.maxTokens }}</span>
                </div>
                <input v-model.number="modelParams.maxTokens" type="range" min="64" max="8192" step="64" class="range-input" />
                <div class="param-hints">
                  <span>64</span>
                  <span>4096</span>
                  <span>8192</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.maxTokensHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.topP') }}</label>
                  <span class="param-value">{{ modelParams.topP }}</span>
                </div>
                <input v-model.number="modelParams.topP" type="range" min="0" max="1" step="0.05" class="range-input" />
                <div class="param-hints">
                  <span>0</span>
                  <span>0.5</span>
                  <span>1</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.topPHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.topK') }}</label>
                  <span class="param-value">{{ modelParams.topK }}</span>
                </div>
                <input v-model.number="modelParams.topK" type="range" min="1" max="100" step="1" class="range-input" />
                <div class="param-hints">
                  <span>1</span>
                  <span>50</span>
                  <span>100</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.topKHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.presencePenalty') }}</label>
                  <span class="param-value">{{ modelParams.presencePenalty }}</span>
                </div>
                <input v-model.number="modelParams.presencePenalty" type="range" min="-2" max="2" step="0.1" class="range-input" />
                <div class="param-hints">
                  <span>-2</span>
                  <span>0</span>
                  <span>2</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.presencePenaltyHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.frequencyPenalty') }}</label>
                  <span class="param-value">{{ modelParams.frequencyPenalty }}</span>
                </div>
                <input v-model.number="modelParams.frequencyPenalty" type="range" min="-2" max="2" step="0.1" class="range-input" />
                <div class="param-hints">
                  <span>-2</span>
                  <span>0</span>
                  <span>2</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.frequencyPenaltyHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.repeatPenalty') }}</label>
                  <span class="param-value">{{ modelParams.repeatPenalty }}</span>
                </div>
                <input v-model.number="modelParams.repeatPenalty" type="range" min="1" max="2" step="0.05" class="range-input" />
                <div class="param-hints">
                  <span>1.0</span>
                  <span>1.5</span>
                  <span>2.0</span>
                </div>
                <div class="param-desc">{{ $t('settings.modelParameters.repeatPenaltyHint') }}</div>
              </div>

              <div class="param-item">
                <div class="param-header">
                  <label class="param-label">{{ $t('settings.modelParameters.stopSequences') }}</label>
                  <span class="param-value">{{ modelParams.stopSequences.length }}</span>
                </div>
                <div class="stop-sequences-input">
                  <input
                    v-model="stopSequenceInput"
                    class="input"
                    :placeholder="$t('settings.modelParameters.stopSequencesPlaceholder')"
                    @keyup.enter="addStopSequence"
                  />
                  <button class="btn btn-secondary btn-sm" @click="addStopSequence">+</button>
                </div>
                <div class="stop-sequences-list">
                  <span v-for="(seq, idx) in modelParams.stopSequences" :key="idx" class="stop-sequence-tag">
                    {{ seq }}
                    <button class="btn-remove" @click="removeStopSequence(idx)">×</button>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="settings-card">
          <div class="card-header">
            <span class="card-icon">⚡</span>
            <h3>{{ $t('settings.modelParameters.streaming') }}</h3>
          </div>
          <div class="card-body">
            <div class="toggle-row">
              <label class="toggle-label">
                <div :class="['toggle', { active: modelParams.stream }]" @click="modelParams.stream = !modelParams.stream"></div>
                {{ $t('settings.modelParameters.enableStreaming') }}
              </label>
            </div>
            <div class="toggle-row">
              <label class="toggle-label">
                <div :class="['toggle', { active: modelParams.typingEffect }]" @click="modelParams.typingEffect = !modelParams.typingEffect"></div>
                {{ $t('settings.modelParameters.typingEffect') }}
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 界面设置 -->
      <div v-if="activeTab === 'ui'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.ui') }}</h2>
        </div>

        <div class="settings-grid">
          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🎨</span>
              <h2>{{ $t('settings.appearance') }}</h2>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.theme') }}</label>
                <div class="theme-options">
                  <div :class="['theme-option', { active: settings.ui.theme === 'dark' }]" @click="settings.ui.theme = 'dark'">
                    🌙 {{ $t('settings.darkTheme') }}
                  </div>
                  <div :class="['theme-option', { active: settings.ui.theme === 'light' }]" @click="settings.ui.theme = 'light'">
                    ☀️ {{ $t('settings.lightTheme') }}
                  </div>
                  <div :class="['theme-option', { active: settings.ui.theme === 'auto' }]" @click="settings.ui.theme = 'auto'">
                    🌓 {{ $t('settings.autoTheme') }}
                  </div>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.accentColor') }}</label>
                <div class="color-options">
                  <div
                    v-for="c in accentColors"
                    :key="c"
                    :class="['color-option', { active: settings.ui.accent_color === c }]"
                    :style="{ background: c }"
                    @click="settings.ui.accent_color = c"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🌐</span>
              <h2>{{ $t('settings.languageRegion') }}</h2>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.language') }}</label>
                <select v-model="settings.ui.language" class="select" style="width: 100%;">
                  <option value="zh">🇨🇳 简体中文</option>
                  <option value="en">🇺🇸 English</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.dateFormat') }}</label>
                <select v-model="settings.ui.dateFormat" class="select" style="width: 100%;">
                  <option value="YYYY-MM-DD">2024-01-01</option>
                  <option value="DD/MM/YYYY">01/01/2024</option>
                  <option value="MM/DD/YYYY">01/01/2024</option>
                </select>
              </div>
            </div>
          </div>

          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">💬</span>
              <h2>{{ $t('settings.chatDisplay') }}</h2>
            </div>
            <div class="card-body">
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.ui.typing_effect }]" @click="settings.ui.typing_effect = !settings.ui.typing_effect"></div>
                  {{ $t('settings.typingEffect') }}
                </label>
              </div>
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.ui.stream_response }]" @click="settings.ui.stream_response = !settings.ui.stream_response"></div>
                  {{ $t('settings.streamResponse') }}
                </label>
              </div>
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.ui.compact_mode }]" @click="settings.ui.compact_mode = !settings.ui.compact_mode"></div>
                  {{ $t('settings.compactMode') }}
                </label>
              </div>
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.ui.showTimestamps }]" @click="settings.ui.showTimestamps = !settings.ui.showTimestamps"></div>
                  {{ $t('settings.showTimestamps') }}
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 安全设置 -->
      <div v-if="activeTab === 'safety'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.safety') }}</h2>
        </div>

        <div class="settings-grid">
          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🛡️</span>
              <h2>{{ $t('settings.safetyControls') }}</h2>
            </div>
            <div class="card-body">
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.safety.enabled }]" @click="settings.safety.enabled = !settings.safety.enabled"></div>
                  {{ $t('settings.safetyEnabled') }}
                </label>
              </div>
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.safety.block_enabled }]" @click="settings.safety.block_enabled = !settings.safety.block_enabled"></div>
                  {{ $t('settings.blockEnabled') }}
                </label>
              </div>
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.safety.log_enabled }]" @click="settings.safety.log_enabled = !settings.safety.log_enabled"></div>
                  {{ $t('settings.logEnabled') }}
                </label>
              </div>
            </div>
          </div>

          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🚫</span>
              <h2>{{ $t('settings.wordFilters') }}</h2>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.blockedWords') }}</label>
                <div class="word-input-row">
                  <input v-model="newBlockedWord" class="input" :placeholder="$t('settings.addWord')" @keyup.enter="addBlockedWord" />
                  <button class="btn btn-secondary btn-sm" @click="addBlockedWord">+</button>
                </div>
                <div class="word-tags">
                  <span v-for="(word, idx) in settings.safety.blocked_words" :key="idx" class="word-tag">
                    {{ word }}
                    <button class="btn-remove" @click="removeBlockedWord(idx)">×</button>
                  </span>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.sensitiveWords') }}</label>
                <div class="word-input-row">
                  <input v-model="newSensitiveWord" class="input" :placeholder="$t('settings.addWord')" @keyup.enter="addSensitiveWord" />
                  <button class="btn btn-secondary btn-sm" @click="addSensitiveWord">+</button>
                </div>
                <div class="word-tags">
                  <span v-for="(word, idx) in settings.safety.sensitive_words" :key="idx" class="word-tag warning">
                    {{ word }}
                    <button class="btn-remove" @click="removeSensitiveWord(idx)">×</button>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TTS 设置 -->
      <div v-if="activeTab === 'tts'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.tts') }}</h2>
        </div>

        <div class="settings-grid">
          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🔊</span>
              <h2>{{ $t('settings.ttsBasic') }}</h2>
            </div>
            <div class="card-body">
              <div class="toggle-row">
                <label class="toggle-label">
                  <div :class="['toggle', { active: settings.tts.enabled }]" @click="settings.tts.enabled = !settings.tts.enabled"></div>
                  {{ settings.tts.enabled ? $t('settings.ttsEnabled') : $t('settings.ttsDisabled') }}
                </label>
              </div>
              <div v-if="settings.tts.enabled" class="form-group">
                <label class="form-label">{{ $t('settings.provider') }}</label>
                <select v-model="settings.tts.provider" class="select" style="width: 100%;">
                  <option value="cosyvoice">CosyVoice</option>
                  <option value="gptsovits">GPT-SoVITS</option>
                </select>
              </div>
            </div>
          </div>

          <div v-if="settings.tts.enabled" class="settings-card">
            <div class="card-header">
              <span class="card-icon">⚙️</span>
              <h2>{{ $t('settings.ttsAdvanced') }}</h2>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">{{ $t('settings.ttsUrl') }}</label>
                <input v-model="settings.tts.cosyvoice_url" class="input" :placeholder="'http://localhost:5000'" />
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.speechSpeed') }}: {{ settings.tts.speech_speed }}x</label>
                <input v-model.number="settings.tts.speech_speed" type="range" min="0.5" max="2" step="0.1" style="width: 100%;" />
              </div>
              <div class="form-group">
                <label class="form-label">{{ $t('settings.defaultVoice') }}</label>
                <select v-model="settings.tts.default_voice" class="select" style="width: 100%;">
                  <option value="female_zh">女声-中文</option>
                  <option value="male_zh">男声-中文</option>
                  <option value="female_en">女声-英文</option>
                  <option value="male_en">男声-英文</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据管理 -->
      <div v-if="activeTab === 'data'" class="tab-content">
        <div class="section-header">
          <h2>{{ $t('settings.dataManagement') }}</h2>
        </div>

        <div class="settings-grid">
          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">📤</span>
              <h2>{{ $t('settings.export') }}</h2>
            </div>
            <div class="card-body">
              <p class="card-desc">{{ $t('settings.exportDesc') }}</p>
              <div class="export-buttons">
                <button class="btn btn-secondary" @click="exportSettings">
                  📤 {{ $t('settings.exportAllSettings') }}
                </button>
                <button class="btn btn-secondary" @click="exportApiConfig">
                  📤 {{ $t('settings.exportApiConfig') }}
                </button>
              </div>
            </div>
          </div>

          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">📥</span>
              <h2>{{ $t('settings.import') }}</h2>
            </div>
            <div class="card-body">
              <p class="card-desc">{{ $t('settings.importDesc') }}</p>
              <div class="import-area" @click="triggerImportFile" @dragover.prevent @drop.prevent="handleFileDrop">
                <span class="import-icon">📁</span>
                <span>{{ $t('settings.importFile') }}</span>
                <input ref="importFileInput" type="file" accept=".json" style="display: none;" @change="handleImportFile" />
              </div>
            </div>
          </div>

          <div class="settings-card">
            <div class="card-header">
              <span class="card-icon">🗄️</span>
              <h2>{{ $t('settings.storage') }}</h2>
            </div>
            <div class="card-body">
              <div class="storage-info">
                <div class="storage-item">
                  <span class="storage-label">{{ $t('settings.characters') }}</span>
                  <span class="storage-value">{{ storageInfo.characters }} {{ $t('settings.items') }}</span>
                </div>
                <div class="storage-item">
                  <span class="storage-label">{{ $t('settings.conversations') }}</span>
                  <span class="storage-value">{{ storageInfo.conversations }} {{ $t('settings.items') }}</span>
                </div>
                <div class="storage-item">
                  <span class="storage-label">{{ $t('settings.memories') }}</span>
                  <span class="storage-value">{{ storageInfo.memories }} {{ $t('settings.items') }}</span>
                </div>
                <div class="storage-item">
                  <span class="storage-label">{{ $t('settings.lorebooks') }}</span>
                  <span class="storage-value">{{ storageInfo.lorebooks }} {{ $t('settings.items') }}</span>
                </div>
              </div>
              <div class="danger-zone">
                <h4>{{ $t('settings.dangerZone') }}</h4>
                <button class="btn btn-danger btn-sm" @click="confirmClearData">{{ $t('settings.clearAllData') }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 关于 -->
      <div v-if="activeTab === 'about'" class="tab-content">
        <div class="about-container">
          <div class="about-logo">✨</div>
          <div class="about-name">{{ $t('settings.appName') }}</div>
          <div class="about-version">{{ $t('settings.version') }} {{ $t('settings.versionNumber') }}</div>
          <div class="about-desc">{{ $t('settings.description') }}</div>

          <div class="about-links">
            <a href="https://github.com" target="_blank" class="about-link">📖 GitHub</a>
            <a href="https://discord.com" target="_blank" class="about-link">💬 Discord</a>
          </div>

          <div class="about-stats">
            <div class="stat-item">
              <span class="stat-value">{{ supportedProviders.length }}</span>
              <span class="stat-label">{{ $t('settings.supportedProviders') }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ totalModels }}</span>
              <span class="stat-label">{{ $t('settings.availableModels') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="settings-footer">
        <button class="btn btn-primary btn-lg" @click="saveAllSettings">
          {{ isSaving ? '...' : $t('common.save') }}
        </button>
      </div>
    </div>

    <!-- 添加自定义提供商弹窗 -->
    <div v-if="showAddProvider" class="modal-overlay" @click.self="showAddProvider = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ $t('settings.modelProvider.addCustom') }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showAddProvider = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">{{ $t('settings.modelProvider.providerName') }}</label>
            <input v-model="newProvider.name" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('settings.modelProvider.baseUrl') }}</label>
            <input v-model="newProvider.baseUrl" class="input" placeholder="https://api.example.com/v1" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('settings.modelProvider.defaultModel') }}</label>
            <input v-model="newProvider.defaultModel" class="input" />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('settings.modelProvider.color') }}</label>
            <div class="color-options">
              <div
                v-for="c in providerColors"
                :key="c"
                :class="['color-option', { active: newProvider.color === c }]"
                :style="{ background: c }"
                @click="newProvider.color = c"
              ></div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddProvider = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" @click="addCustomProvider">{{ $t('common.create') }}</button>
        </div>
      </div>
    </div>

    <!-- Toast 通知 -->
    <Transition name="toast">
      <div v-if="toast.show" :class="['toast', toast.type]">
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSettingsStore } from '@/stores/settings'
import { useUIStore } from '@/stores/ui'

const { t } = useI18n()
const settingsStore = useSettingsStore()
const uiStore = useUIStore()

// Tab 状态
const activeTab = ref('providers')
const tabs = [
  { id: 'providers', label: computed(() => t('settings.tabs.providers')), icon: '🤖' },
  { id: 'parameters', label: computed(() => t('settings.tabs.parameters')), icon: '⚙️' },
  { id: 'ui', label: computed(() => t('settings.tabs.ui')), icon: '🎨' },
  { id: 'safety', label: computed(() => t('settings.tabs.safety')), icon: '🛡️' },
  { id: 'tts', label: computed(() => t('settings.tabs.tts')), icon: '🔊' },
  { id: 'data', label: computed(() => t('settings.tabs.data')), icon: '💾' },
  { id: 'about', label: computed(() => t('settings.tabs.about')), icon: '✨' },
]

// 提供商相关状态
const providerConfigs = ref<Record<string, { baseUrl: string; apiKey: string; model: string; customModel: string }>>({})
const showApiKeys = ref<Record<string, boolean>>({})
const testingProviders = ref<Record<string, boolean>>({})
const refreshingModels = ref<Record<string, boolean>>({})
const providerStatus = ref<Record<string, { success: boolean; message: string }>>({})
const currentProvider = ref('')
const testingAll = ref(false)

// 提供商分类
const providerCategories = [
  { id: 'local', name: computed(() => t('settings.modelProvider.categories.local')), icon: '💻' },
  { id: 'cloud', name: computed(() => t('settings.modelProvider.categories.cloud')), icon: '☁️' },
  { id: 'aggregate', name: computed(() => t('settings.modelProvider.categories.aggregate')), icon: '🔗' },
  { id: 'custom', name: computed(() => t('settings.modelProvider.categories.custom')), icon: '🔧' },
]

// 模型参数
const modelParams = reactive({
  temperature: 0.7,
  maxTokens: 4096,
  topP: 0.9,
  topK: 40,
  presencePenalty: 0,
  frequencyPenalty: 0,
  repeatPenalty: 1.1,
  stopSequences: [] as string[],
  stream: true,
  typingEffect: true,
})
const stopSequenceInput = ref('')

// UI 设置
const settings = reactive({
  model: { ...settingsStore.model },
  ui: {
    theme: 'dark',
    accent_color: '#667eea',
    typing_effect: true,
    stream_response: true,
    compact_mode: false,
    language: 'zh',
    dateFormat: 'YYYY-MM-DD',
    showTimestamps: true,
    ...settingsStore.ui,
  },
  safety: { ...settingsStore.safety },
  tts: { ...settingsStore.tts },
})

// 安全设置
const newBlockedWord = ref('')
const newSensitiveWord = ref('')

// TTS 设置
const ttsEnabled = ref(false)

// 数据管理
const storageInfo = ref({ characters: 0, conversations: 0, memories: 0, lorebooks: 0 })
const importFileInput = ref<HTMLInputElement | null>(null)

// 自定义提供商
const showAddProvider = ref(false)
const newProvider = reactive({
  name: '',
  baseUrl: '',
  defaultModel: '',
  color: '#6b7280',
})
const providerColors = ['#ff6b35', '#10a37f', '#0066cc', '#cc785c', '#0078d4', '#a855f7', '#00d4aa', '#c800a0', '#ff4500', '#7c3aed', '#06b6d4', '#f59e0b', '#84cc16', '#6b7280']

// Toast
const toast = reactive({ show: false, message: '', type: 'info' as 'info' | 'success' | 'warning' | 'error' })
const isSaving = ref(false)

// 计算属性
const supportedProviders = computed(() => settingsStore.providers)
const totalModels = computed(() => settingsStore.providers.reduce((acc, p) => acc + (p.models?.length || 0), 0))
const accentColors = ['#667eea', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#ec4899', '#8b5cf6']

// 方法
function showToast(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => { toast.show = false }, 3000)
}

function getProvidersByCategory(category: string) {
  return settingsStore.providers.filter(p => p.category === category)
}

function toggleApiKeyVisibility(providerId: string) {
  showApiKeys.value[providerId] = !showApiKeys.value[providerId]
}

async function loadProviders() {
  await settingsStore.loadProviders()
  // 初始化提供商配置
  settingsStore.providers.forEach(p => {
    if (!providerConfigs.value[p.id]) {
      providerConfigs.value[p.id] = {
        baseUrl: p.baseUrl || p.defaultUrl,
        apiKey: '',
        model: p.currentModel || p.defaultModel,
        customModel: '',
      }
    }
  })
}

async function testProvider(providerId: string) {
  testingProviders.value[providerId] = true
  try {
    const config = providerConfigs.value[providerId]
    const result = await settingsStore.testProvider(providerId, config.apiKey, config.baseUrl, config.model || config.customModel)
    providerStatus.value[providerId] = { success: result.success, message: result.message }
    showToast(result.message, result.success ? 'success' : 'error')
  } catch (e) {
    providerStatus.value[providerId] = { success: false, message: t('settings.modelProvider.testFailed') }
  }
  testingProviders.value[providerId] = false
}

async function testAllProviders() {
  testingAll.value = true
  for (const p of settingsStore.providers) {
    if (p.requiresApiKey && !providerConfigs.value[p.id]?.apiKey) continue
    await testProvider(p.id)
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  testingAll.value = false
}

async function refreshModels(providerId: string) {
  refreshingModels.value[providerId] = true
  try {
    const models = await settingsStore.getProviderModels(providerId)
    if (models.length > 0) {
      const provider = settingsStore.providers.find(p => p.id === providerId)
      if (provider) {
        provider.models = models
      }
    }
  } catch (e) {
    console.error('刷新模型列表失败:', e)
  }
  refreshingModels.value[providerId] = false
}

function selectProvider(providerId: string) {
  currentProvider.value = providerId
  settings.model.provider = providerId
  const config = providerConfigs.value[providerId]
  settings.model.model_name = config.model || config.customModel
  settings.model.api_url = config.baseUrl
  showToast(t('settings.modelProvider.selected') + ': ' + settingsStore.providers.find(p => p.id === providerId)?.name, 'success')
}

async function saveProviderConfig(providerId: string) {
  const config = providerConfigs.value[providerId]
  selectProvider(providerId)
  await settingsStore.saveSettings()
  showToast(t('settings.saveSuccess'), 'success')
}

function addStopSequence() {
  if (stopSequenceInput.value.trim() && !modelParams.stopSequences.includes(stopSequenceInput.value.trim())) {
    modelParams.stopSequences.push(stopSequenceInput.value.trim())
    stopSequenceInput.value = ''
  }
}

function removeStopSequence(idx: number) {
  modelParams.stopSequences.splice(idx, 1)
}

function addBlockedWord() {
  if (newBlockedWord.value.trim() && !settings.safety.blocked_words?.includes(newBlockedWord.value.trim())) {
    if (!settings.safety.blocked_words) settings.safety.blocked_words = []
    settings.safety.blocked_words.push(newBlockedWord.value.trim())
    newBlockedWord.value = ''
  }
}

function removeBlockedWord(idx: number) {
  settings.safety.blocked_words?.splice(idx, 1)
}

function addSensitiveWord() {
  if (newSensitiveWord.value.trim() && !settings.safety.sensitive_words?.includes(newSensitiveWord.value.trim())) {
    if (!settings.safety.sensitive_words) settings.safety.sensitive_words = []
    settings.safety.sensitive_words.push(newSensitiveWord.value.trim())
    newSensitiveWord.value = ''
  }
}

function removeSensitiveWord(idx: number) {
  settings.safety.sensitive_words?.splice(idx, 1)
}

function addCustomProvider() {
  // 自定义提供商添加逻辑
  showAddProvider.value = false
  showToast(t('settings.modelProvider.customProviderAdded'), 'success')
}

function exportSettings() {
  const data = {
    version: '1.0.0',
    exportedAt: new Date().toISOString(),
    settings: {
      model: settings.model,
      ui: settings.ui,
      safety: settings.safety,
      tts: settings.tts,
      modelParams: modelParams,
    },
  }
  downloadJSON(data, 'astral-settings.json')
}

function exportApiConfig() {
  const apiConfigs: Record<string, { baseUrl: string; apiKey: string; model: string }> = {}
  Object.entries(providerConfigs.value).forEach(([id, config]) => {
    apiConfigs[id] = { baseUrl: config.baseUrl, apiKey: config.apiKey ? '***' : '', model: config.model || config.customModel }
  })
  const data = { version: '1.0.0', exportedAt: new Date().toISOString(), apiConfigs }
  downloadJSON(data, 'astral-api-config.json')
}

function downloadJSON(data: object, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function triggerImportFile() {
  importFileInput.value?.click()
}

function handleImportFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target?.result as string)
        if (data.apiConfigs) {
          Object.entries(data.apiConfigs).forEach(([id, config]: [string, any]) => {
            if (providerConfigs.value[id]) {
              providerConfigs.value[id].baseUrl = config.baseUrl || providerConfigs.value[id].baseUrl
              providerConfigs.value[id].apiKey = config.apiKey || providerConfigs.value[id].apiKey
              providerConfigs.value[id].model = config.model || providerConfigs.value[id].model
            }
          })
          showToast(t('settings.importSuccess'), 'success')
        }
      } catch (e) {
        showToast(t('settings.importFailed'), 'error')
      }
    }
    reader.readAsText(file)
  }
}

function handleFileDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file && file.name.endsWith('.json')) {
    const reader = new FileReader()
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target?.result as string)
        if (data.settings) {
          if (data.settings.ui) Object.assign(settings.ui, data.settings.ui)
          if (data.settings.safety) Object.assign(settings.safety, data.settings.safety)
          if (data.settings.tts) Object.assign(settings.tts, data.settings.tts)
          if (data.settings.modelParams) Object.assign(modelParams, data.settings.modelParams)
        }
        showToast(t('settings.importSuccess'), 'success')
      } catch (e) {
        showToast(t('settings.importFailed'), 'error')
      }
    }
    reader.readAsText(file)
  }
}

function confirmClearData() {
  if (confirm(t('settings.confirmClearData'))) {
    showToast(t('settings.dataCleared'), 'success')
  }
}

async function saveAllSettings() {
  isSaving.value = true
  try {
    Object.assign(settingsStore.model, settings.model)
    Object.assign(settingsStore.ui, settings.ui)
    Object.assign(settingsStore.safety, settings.safety)
    Object.assign(settingsStore.tts, settings.tts)
    await settingsStore.saveSettings()
    settingsStore.applyTheme()
    showToast(t('settings.saveSuccess'), 'success')
  } catch (e) {
    showToast(t('settings.saveFailed'), 'error')
  }
  isSaving.value = false
}

onMounted(async () => {
  await settingsStore.loadSettings()
  await loadProviders()

  // 从存储的设置中恢复
  if (settingsStore.model.temperature) modelParams.temperature = settingsStore.model.temperature
  if (settingsStore.model.max_tokens) modelParams.maxTokens = settingsStore.model.max_tokens
  if (settingsStore.model.top_p) modelParams.topP = settingsStore.model.top_p
  modelParams.stream = settingsStore.model.stream ?? true
  currentProvider.value = settingsStore.model.provider
})

watch(() => settings.ui.theme, () => {
  settingsStore.applyTheme()
})
</script>

<style scoped>
.settings-view {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
}

.settings-page {
  max-width: 1100px;
  margin: 0 auto;
}

.settings-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 20px;
}

.settings-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.85rem;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.tab-btn:hover { background: var(--bg-elevated); color: var(--text-primary); }
.tab-btn.active { background: var(--accent-color); color: white; }
.tab-icon { font-size: 1rem; }

.tab-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 { font-size: 1.1rem; font-weight: 600; }
.header-actions { display: flex; gap: 8px; }

.provider-category { margin-bottom: 24px; }

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
}

.category-icon { font-size: 1.1rem; }
.category-name { font-weight: 600; font-size: 0.9rem; }
.category-count { margin-left: auto; font-size: 0.8rem; color: var(--text-muted); background: var(--bg-secondary); padding: 2px 8px; border-radius: 10px; }

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 12px;
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 14px;
  transition: all var(--transition-fast);
}

.provider-card.active { border-color: var(--accent-color); box-shadow: 0 0 0 1px var(--accent-color); }
.provider-card.connected .provider-color { box-shadow: 0 0 6px 2px rgba(16, 185, 129, 0.4); }

.provider-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.provider-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
}

.provider-info { flex: 1; min-width: 0; }
.provider-name { font-weight: 600; font-size: 0.95rem; margin-bottom: 2px; }
.provider-desc { font-size: 0.75rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.provider-status { display: flex; gap: 4px; }
.status-badge {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: bold;
}

.status-badge.success { background: #10b981; color: white; }
.status-badge.error { background: #ef4444; color: white; }
.status-badge.warning { background: #f59e0b; color: white; }

.provider-config { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }

.config-row { display: flex; flex-direction: column; gap: 4px; }
.config-label { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; }

.api-key-input { display: flex; gap: 4px; }
.api-key-input .input { flex: 1; }

.model-select-row { display: flex; gap: 4px; }
.model-select-row .select { flex: 1; }

.provider-actions { display: flex; gap: 6px; justify-content: flex-end; }

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.settings-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
}

.card-header h2, .card-header h3 { margin: 0; font-size: 0.95rem; font-weight: 600; }
.card-icon { font-size: 1.1rem; }
.card-body { padding: 16px; }

.form-group { margin-bottom: 14px; }
.form-group:last-child { margin-bottom: 0; }
.form-label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 6px; font-weight: 500; }

.theme-options { display: flex; gap: 8px; }
.theme-option {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: center;
  font-size: 0.8rem;
  background: var(--bg-tertiary);
  transition: all var(--transition-fast);
}
.theme-option:hover { border-color: var(--border-hover); }
.theme-option.active { border-color: var(--accent-color); background: var(--accent-subtle); }

.color-options { display: flex; gap: 8px; flex-wrap: wrap; }
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

.toggle-row { display: flex; align-items: center; margin-bottom: 12px; }
.toggle-row:last-child { margin-bottom: 0; }
.toggle-label { display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 0.85rem; }

.toggle {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: var(--bg-tertiary);
  position: relative;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.toggle::after {
  content: '';
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform var(--transition-fast);
}
.toggle.active { background: var(--accent-color); }
.toggle.active::after { transform: translateX(18px); }

.param-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.param-item { display: flex; flex-direction: column; gap: 6px; }

.param-header { display: flex; justify-content: space-between; align-items: center; }
.param-label { font-size: 0.85rem; font-weight: 500; color: var(--text-primary); }
.param-value { font-size: 0.9rem; font-weight: 600; color: var(--accent-color); }

.range-input { width: 100%; accent-color: var(--accent-color); }

.param-hints { display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); }

.param-desc { font-size: 0.75rem; color: var(--text-muted); }

.stop-sequences-input { display: flex; gap: 4px; }
.stop-sequences-input .input { flex: 1; }

.stop-sequences-list { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.stop-sequence-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-family: monospace;
}

.word-input-row { display: flex; gap: 6px; margin-bottom: 8px; }
.word-input-row .input { flex: 1; }

.word-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.word-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
}
.word-tag.warning { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }

.btn-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0;
  font-size: 0.9rem;
  line-height: 1;
}
.btn-remove:hover { color: var(--text-primary); }

.card-desc { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px; }
.export-buttons { display: flex; gap: 8px; flex-wrap: wrap; }

.import-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-md);
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.import-area:hover { border-color: var(--accent-color); background: var(--accent-subtle); }
.import-icon { font-size: 2rem; display: block; margin-bottom: 8px; }

.storage-info { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
.storage-item { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border-color); }
.storage-label { font-size: 0.8rem; color: var(--text-secondary); }
.storage-value { font-size: 0.8rem; font-weight: 500; }

.danger-zone { border-top: 1px solid var(--border-color); padding-top: 12px; }
.danger-zone h4 { font-size: 0.85rem; color: #ef4444; margin-bottom: 8px; }

.about-container { text-align: center; padding: 40px 20px; }
.about-logo { font-size: 4rem; margin-bottom: 16px; }
.about-name { font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; }
.about-version { color: var(--text-secondary); margin-bottom: 8px; }
.about-desc { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 24px; max-width: 500px; margin-left: auto; margin-right: auto; }

.about-links { display: flex; gap: 16px; justify-content: center; margin-bottom: 32px; }
.about-link { color: var(--accent-color); text-decoration: none; font-size: 0.9rem; }
.about-link:hover { text-decoration: underline; }

.about-stats { display: flex; gap: 32px; justify-content: center; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-value { font-size: 2rem; font-weight: 700; color: var(--accent-color); }
.stat-label { font-size: 0.8rem; color: var(--text-secondary); }

.settings-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 24px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 { margin: 0; font-size: 1rem; font-weight: 600; }

.modal-body { padding: 20px; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  z-index: 2000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toast.info { background: var(--accent-color); color: white; }
.toast.success { background: #10b981; color: white; }
.toast.warning { background: #f59e0b; color: white; }
.toast.error { background: #ef4444; color: white; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(16px); }

@media screen and (max-width: 640px) {
  .settings-tabs { flex-wrap: nowrap; overflow-x: auto; }
  .provider-grid { grid-template-columns: 1fr; }
  .settings-grid { grid-template-columns: 1fr; }
  .param-grid { grid-template-columns: 1fr; }
}
</style>
