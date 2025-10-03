<template>
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Research Form -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <form @submit.prevent="startResearch">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Research Query
        </label>
        <textarea
          v-model="query"
          :disabled="isLoading"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          rows="3"
          placeholder="Enter your research question (e.g., 'What is Vue.js?')"
          required
        ></textarea>
        
        <div class="mt-4 flex justify-between">
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input v-model="useCache" type="checkbox" class="mr-2" />
              <span class="text-sm text-gray-600">Use cached results</span>
            </label>

            <label class="flex items-center">
              <input v-model="useWebSocket" type="checkbox" class="mr-2" />
              <span class="text-sm text-gray-600">Use WebSocket (real-time updates)</span>
            </label>
          </div>

          <button
            type="submit"
            :disabled="isLoading || query.length < 5"
            class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {{ isLoading ? '⏳ Researching...' : '🔍 Start Research' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Connection Status -->
    <div v-if="connectionStatus" class="bg-blue-50 rounded-lg p-3 mb-6">
      <p class="text-sm text-blue-700">{{ connectionStatus }}</p>
    </div>

    <!-- Loading Status -->
    <div v-if="isLoading" class="bg-blue-50 rounded-lg p-4 mb-6">
      <p class="text-blue-700">🔄 Research in progress... {{ currentStep }}</p>
      <div v-if="progress > 0" class="mt-2">
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div class="bg-blue-600 h-2 rounded-full transition-all duration-300"
               :style="`width: ${progress}%`"></div>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 rounded-lg p-4 mb-6">
      <p class="text-red-700">❌ {{ error }}</p>
    </div>

    <!-- Research Report -->
    <div v-if="report" class="bg-white rounded-lg shadow-sm border p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-bold">Research Report</h2>
        <button @click="copyReport" class="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
          📋 Copy
        </button>
      </div>
      
      <!-- Report Metadata -->
      <div v-if="metadata" class="grid grid-cols-3 gap-4 mb-4 py-3 border-y">
        <div>
          <p class="text-xs text-gray-500">Sources</p>
          <p class="font-semibold">{{ metadata.sources_found || 0 }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Processing Time</p>
          <p class="font-semibold">{{ Math.round(metadata.duration_seconds || 0) }}s</p>
        </div>
        <div>
          <p class="text-xs text-gray-500">Cached</p>
          <p class="font-semibold">{{ cached ? '✅' : '❌' }}</p>
        </div>
      </div>
      
      <!-- Report Content -->
      <div class="prose max-w-none" v-html="renderedReport"></div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'

// Form data
const query = ref('')
const useCache = ref(true)
const useWebSocket = ref(false)  // Toggle for WebSocket

// State
const isLoading = ref(false)
const error = ref<string | null>(null)
const report = ref<string | null>(null)
const metadata = ref<any>(null)
const cached = ref(false)
const connectionStatus = ref('')
const currentStep = ref('')
const progress = ref(0)

// WebSocket
let ws: WebSocket | null = null

// API configuration
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

// Computed
const renderedReport = computed(() => {
  if (!report.value) return ''
  return marked(report.value)
})

// Methods
async function startResearch() {
  if (query.value.length < 5) return

  isLoading.value = true
  error.value = null
  report.value = null
  metadata.value = null
  connectionStatus.value = ''
  currentStep.value = ''
  progress.value = 0

  try {
    if (useWebSocket.value) {
      await researchViaWebSocket()
    } else {
      await researchViaAPI()
    }
  } catch (err: any) {
    console.error('Research error:', err)
    error.value = err.message || 'An error occurred'
    isLoading.value = false
  }
}

function researchViaWebSocket() {
  return new Promise((resolve, reject) => {
    connectionStatus.value = '🔄 Connecting to WebSocket...'

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connectionStatus.value = '✅ WebSocket connected'
      console.log('WebSocket connected')

      // Send the query
      ws?.send(JSON.stringify({ query: query.value }))
      console.log('Query sent via WebSocket')
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('WebSocket message:', data)

      if (data.type === 'status') {
        currentStep.value = data.message
      } else if (data.type === 'progress') {
        currentStep.value = data.message
        progress.value = data.progress || 0
      } else if (data.type === 'complete') {
        report.value = data.report
        metadata.value = data.metadata
        cached.value = data.cached
        isLoading.value = false
        connectionStatus.value = ''
        ws?.close()
        resolve(true)
      } else if (data.type === 'error') {
        error.value = data.error
        isLoading.value = false
        ws?.close()
        reject(new Error(data.error))
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      connectionStatus.value = '❌ WebSocket error'
      error.value = 'WebSocket connection failed'
      isLoading.value = false
      reject(err)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      connectionStatus.value = ''
    }
  })
}

async function researchViaAPI() {
  currentStep.value = 'Processing research request...'

  try {
    const response = await axios.post(`${apiBaseUrl}/api/research`, {
      query: query.value,
      use_cache: useCache.value,
      report_type: 'summary'
    })

    if (response.data.success) {
      report.value = response.data.report
      metadata.value = response.data.metadata
      cached.value = response.data.cached
    } else {
      throw new Error(response.data.error || 'Research failed')
    }
  } catch (err: any) {
    console.error('Research error:', err)
    error.value = err.response?.data?.detail || err.message || 'An error occurred'
  } finally {
    isLoading.value = false
  }
}

function copyReport() {
  if (report.value) {
    navigator.clipboard.writeText(report.value)
    alert('Report copied to clipboard!')
  }
}

// Cleanup
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
/* Markdown content styling */
:deep(.prose) {
  max-width: none;
}
:deep(.prose h1) {
  font-size: 1.875rem;
  font-weight: bold;
  margin: 1rem 0;
}
:deep(.prose h2) {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 1rem 0;
  color: #2563eb;
}
:deep(.prose h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.75rem 0;
}
:deep(.prose p) {
  margin: 0.75rem 0;
  line-height: 1.7;
}
:deep(.prose ul) {
  list-style: disc;
  padding-left: 2rem;
  margin: 0.5rem 0;
}
:deep(.prose strong) {
  font-weight: 600;
}
</style>
