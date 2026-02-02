<template>
  <div class="flex flex-col h-full bg-(--bg-primary)">
    <!-- Tabs 标题栏 -->
    <div class="flex items-center border-b border-(--border-color)">
      <button v-for="tab in tabs" :key="tab.id" @click="handleTabChange(tab.id)" :class="[
        'flex-1 flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium transition-all border-b-2',
        activeTab === tab.id
          ? 'text-(--accent-color) border-(--accent-color) bg-(--accent-color)/5'
          : 'text-(--text-secondary) border-transparent hover:text-(--text-primary) hover:bg-(--bg-secondary)/50'
      ]">
        <i :class="tab.icon"></i>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- Tab 内容区域 -->
    <div class="flex-1 min-h-0 overflow-auto">
      <!-- 加载状态 -->
      <div v-if="isLoadingTab" class="flex items-center justify-center h-full">
        <div class="text-center">
          <i class="ri-loader-4-line text-2xl text-(--accent-color) animate-spin"></i>
          <p class="text-[11px] text-(--text-secondary) mt-2">Loading...</p>
        </div>
      </div>

      <!-- 无 step 时的提示 -->
      <div v-else-if="!currentStep" class="flex items-center justify-center h-full">
        <div class="text-center px-4">
          <i class="ri-information-line text-3xl text-(--text-secondary) opacity-50"></i>
          <p class="text-[11px] text-(--text-secondary) mt-2">请先选择一个流程步骤</p>
        </div>
      </div>

      <!-- 空数据提示 -->
      <div v-else-if="Object.keys(currentTabInfo).length === 0" class="flex items-center justify-center h-full">
        <div class="text-center px-4">
          <i class="ri-file-list-3-line text-3xl text-(--text-secondary) opacity-50"></i>
          <p class="text-[11px] text-(--text-secondary) mt-2">暂无数据</p>
        </div>
      </div>

      <!-- Info Keys 列表 -->
      <div v-else class="p-3 space-y-2">
        <button v-for="(path, key) in currentTabInfo" :key="key" @click="handleKeyClick(key as string, path as string)"
          :disabled="loadingKey === key"
          class="w-full flex items-center gap-3 p-3 rounded-lg border border-(--border-color) bg-(--bg-secondary) hover:border-(--accent-color) hover:bg-(--accent-color)/5 transition-all text-left disabled:opacity-50">
          <div class="w-8 h-8 rounded-lg bg-(--accent-color)/20 flex items-center justify-center shrink-0">
            <i v-if="loadingKey === key" class="ri-loader-4-line text-(--accent-color) animate-spin"></i>
            <i v-else :class="getFileIcon(path as string)" class="text-(--accent-color)"></i>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-xs font-medium text-(--text-primary) truncate">{{ key }}</p>
            <p class="text-[10px] text-(--text-secondary) truncate">{{ getFileName(path as string) }}</p>
          </div>
          <i class="ri-arrow-right-s-line text-(--text-secondary)"></i>
        </button>
      </div>

      <!-- 错误提示 -->
      <div v-if="errorMessage" class="p-3">
        <div class="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
          <p class="text-[11px] text-red-500">{{ errorMessage }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMessageStore } from '../stores/messageStore'
import { getInfoApi } from '../api/flow'
import { CMDEnum, InfoEnum, StepEnum, ResponseEnum } from '../api/type'
import { useTauri } from '../composables/useTauri'
import { readTextFile } from '@tauri-apps/plugin-fs'

const route = useRoute()
const messageStore = useMessageStore()
const { isInTauri } = useTauri()

// Tabs 定义
const tabs = [
  { id: InfoEnum.analysis, label: 'Analysis', icon: 'ri-pie-chart-line' },
  { id: InfoEnum.maps, label: 'Maps', icon: 'ri-map-2-line' },
  { id: InfoEnum.checklist, label: 'Checklist', icon: 'ri-list-check-line' }
]

const activeTab = ref<InfoEnum>(InfoEnum.analysis)
const isLoadingTab = ref(false)
const loadingKey = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

// 存储每个 tab 的 info 数据
const tabInfoCache = ref<Record<string, Record<string, string>>>({})

// 获取当前 step
const stepEnumValues = Object.values(StepEnum)

function getStepEnumFromPath(path: string): StepEnum | undefined {
  return stepEnumValues.find(step => step.toLowerCase() === path.toLowerCase())
}

const currentStep = computed(() => {
  const pathParts = route.path.split('/')
  const currentPath = pathParts[pathParts.length - 1] || ''
  return getStepEnumFromPath(currentPath)
})

// 当前 tab 的 info 数据
const currentTabInfo = computed(() => {
  if (!currentStep.value) return {}
  const cacheKey = `${currentStep.value}_${activeTab.value}`
  return tabInfoCache.value[cacheKey] || {}
})

// 根据文件扩展名获取图标
function getFileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase()
  if (ext === 'json') return 'ri-braces-line'
  if (ext === 'csv') return 'ri-table-line'
  if (ext === 'png' || ext === 'jpg' || ext === 'jpeg') return 'ri-image-line'
  if (ext === 'rpt' || ext === 'txt') return 'ri-file-text-line'
  return 'ri-file-line'
}

// 获取文件名
function getFileName(path: string): string {
  return path.split('/').pop() || path
}

// 根据文件扩展名确定格式
function getFileFormat(path: string): 'json' | 'csv' | 'text' {
  const ext = path.split('.').pop()?.toLowerCase()
  if (ext === 'json') return 'json'
  if (ext === 'csv') return 'csv'
  return 'text'
}

// 获取 Tab 数据
async function fetchTabInfo(tabId: InfoEnum) {
  if (!currentStep.value) return

  const cacheKey = `${currentStep.value}_${tabId}`

  // 如果已有缓存，不重新请求
  if (tabInfoCache.value[cacheKey]) return

  isLoadingTab.value = true
  errorMessage.value = null

  try {
    const response = await getInfoApi({
      cmd: CMDEnum.get_info,
      data: {
        step: currentStep.value,
        id: tabId
      }
    })

    console.log('getInfoApi response:', response)

    if (response.response !== ResponseEnum.success) {
      errorMessage.value = response.message?.join(', ') || '获取信息失败'
      return
    }

    const infoObj = response.data?.info
    if (infoObj && typeof infoObj === 'object') {
      tabInfoCache.value[cacheKey] = infoObj as Record<string, string>
    }
  } catch (err) {
    console.error('fetchTabInfo error:', err)
    errorMessage.value = err instanceof Error ? err.message : '未知错误'
  } finally {
    isLoadingTab.value = false
  }
}

// 处理 Tab 切换
async function handleTabChange(tabId: InfoEnum) {
  activeTab.value = tabId
  await fetchTabInfo(tabId)
}

// 处理 Key 点击 - 读取文件并显示到 chat
async function handleKeyClick(key: string, path: string) {
  if (!currentStep.value) return

  loadingKey.value = key
  errorMessage.value = null

  try {
    let content: any
    const format = getFileFormat(path)

    if (!isInTauri) {
      content = `文件路径: ${path}\n(需要在 Tauri 环境中才能读取)`
    } else {
      const fileContent = await readTextFile(path)

      if (format === 'json') {
        try {
          content = JSON.parse(fileContent)
        } catch {
          content = fileContent
        }
      } else {
        content = fileContent
      }
    }

    // 发送到 chat
    messageStore.addInfoMessage({
      title: key,
      step: currentStep.value,
      items: [{
        label: getFileName(path),
        content,
        format
      }]
    })

  } catch (err) {
    console.error('handleKeyClick error:', err)
    errorMessage.value = err instanceof Error ? err.message : '读取文件失败'
  } finally {
    loadingKey.value = null
  }
}

// 监听 step 变化，重新获取数据
watch(currentStep, async (newStep) => {
  if (newStep) {
    // 清除缓存
    tabInfoCache.value = {}
    // 获取当前 tab 的数据
    await fetchTabInfo(activeTab.value)
  }
}, { immediate: true })
</script>
