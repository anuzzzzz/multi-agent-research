<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <span class="text-2xl">🤖</span>
            <h1 class="ml-3 text-xl font-semibold text-gray-900">
              Multi-Agent Research Assistant
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">
              Powered by LangGraph + GPT-4
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Component -->
    <ResearchApp />
  </div>
</template>

<script setup lang="ts">
import ResearchApp from './components/ResearchApp.vue'
</script>

<style scoped>
/* App styles with Tailwind */
</style>
