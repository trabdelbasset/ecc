<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useThemeStore } from '@/stores/themeStore'
import { useWorkspace } from '@/composables/useWorkspace'

const themeStore = useThemeStore()
const { loadRecentProjects } = useWorkspace()

onMounted(async () => {
  themeStore.initTheme()
  // 在应用启动时加载最近项目，确保 currentProject 被初始化
  await loadRecentProjects()
})
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
  max-width: 100vw;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
