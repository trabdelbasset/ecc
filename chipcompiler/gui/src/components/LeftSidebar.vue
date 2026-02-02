<template>
  <div class="flex h-full">
    <!-- 第一栏：流程步骤导航 (优化版) -->
    <div
      class="w-[52px] shrink-0 bg-(--bg-sidebar) border-r border-(--border-color) flex flex-col justify-between py-3 overflow-y-auto">
      <div class="overflow-y-auto">
        <router-link v-for="stage in flowStages" :key="stage.path"
          :to="stage.available !== false ? '/workspace/' + stage.path : route.path"
          @click="stage.available === false && $event.preventDefault()"
          class="flex flex-col items-center justify-center py-4 transition-all group relative mb-1" :class="[
            currentStage === stage.path ? 'text-(--accent-color)' : 'text-(--text-secondary)',
            stage.available === false ? 'opacity-40 grayscale cursor-not-allowed' : 'hover:bg-white/5'
          ]">
          <!-- 选中状态的指示条 -->
          <div v-if="currentStage === stage.path"
            class="absolute left-0 top-2 bottom-2 w-1 bg-(--accent-color) rounded-r-full shadow-[0_0_10px_var(--accent-color)]">
          </div>

          <!-- 图标容器 -->
          <div class="relative transition-transform group-hover:-translate-y-0.5">
            <i :class="stage.icon" class="text-xl mb-1.5 inline-block"></i>

            <!-- 完成状态指示点 -->
            <i v-if="stage.completed"
              class="ri-checkbox-circle-fill absolute -top-1 -right-1 text-[10px] text-green-500 bg-(--bg-sidebar) rounded-full"></i>
          </div>

          <span class="text-[9px] font-bold text-center leading-tight uppercase tracking-tighter scale-90">
            {{ stage.label }}
          </span>
        </router-link>
      </div>
      <button @click="toggleTheme" class="p-2 text-(--text-secondary) hover:text-(--text-primary) transition-colors"
        title="切换主题">
        <i :class="isDark ? 'ri-sun-line' : 'ri-moon-line'" class="text-lg"></i>
      </button>
    </div>

    <!-- 第二栏：流程进度面板 (Configure 页面不显示) -->
    <div v-if="showProgressPanel"
      class="w-[240px] min-w-[200px] max-w-[300px] bg-(--bg-primary) border-r border-(--border-color) flex flex-col overflow-hidden shrink-0">
      <!-- 顶部标题栏 -->
      <div class="px-4 py-3 border-b border-(--border-color)">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-(--accent-color)/20 flex items-center justify-center">
            <i class="ri-focus-2-line text-(--accent-color) text-lg"></i>
          </div>
          <div>
            <h3 class="text-[13px] font-bold text-(--text-primary)">{{ currentStepTitle }}</h3>
            <p class="text-[10px] text-(--text-secondary)">{{ currentStepEngine }}</p>
          </div>
        </div>
      </div>

      <!-- 进度统计 -->
      <div class="px-4 py-3 border-b border-(--border-color) bg-(--bg-secondary)/30">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] text-(--text-secondary) uppercase tracking-wider">Progress</span>
          <span class="text-[11px] font-bold text-(--accent-color)">{{ completedSteps }}/{{ totalSteps || 0
          }}</span>
        </div>
        <div class="h-1.5 bg-(--bg-secondary) rounded-full overflow-hidden">
          <div class="h-full bg-(--accent-color) rounded-full transition-all duration-500"
            :style="{ width: `${progressPercent}%` }"></div>
        </div>
        <div class="flex items-center justify-between mt-2 text-[9px] text-(--text-secondary)">
          <span>Total: {{ totalTime }}</span>
          <span
            :class="overallStatus === 'completed' ? 'text-green-500' : overallStatus === 'running' ? 'text-blue-400' : 'text-(--text-secondary)'">
            {{ overallStatus === 'completed' ? 'Completed' : overallStatus === 'running' ? 'Running...' : 'Ready' }}
          </span>
        </div>
      </div>

      <!-- 步骤列表 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 加载状态 -->
        <div v-if="isLoadingSubflow" class="flex items-center justify-center h-full">
          <div class="text-center">
            <i class="ri-loader-4-line text-2xl text-(--accent-color) animate-spin"></i>
            <p class="text-[11px] text-(--text-secondary) mt-2">Loading subflow...</p>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="subflowSteps.length === 0" class="flex items-center justify-center h-full">
          <div class="text-center px-4">
            <i class="ri-file-list-3-line text-3xl text-(--text-secondary) opacity-50"></i>
            <p class="text-[11px] text-(--text-secondary) mt-2">No subflow data available</p>
            <p class="text-[10px] text-(--text-secondary) opacity-70 mt-1">Run the step to generate subflow</p>
          </div>
        </div>

        <!-- 步骤列表 -->
        <div v-else class="p-3 space-y-1">
          <div v-for="(step, index) in subflowSteps" :key="step.id" class="group relative"
            :class="{ 'opacity-50': step.status === 'pending' && index > 0 && subflowSteps[index - 1].status === 'pending' }">
            <!-- 连接线：从圆形底部到下一个圆形顶部 -->
            <div v-if="index < subflowSteps.length - 1"
              class="absolute left-[22px] top-[42px] w-0.5 h-[calc(100%-34px)]" :class="[
                step.status === 'completed' ? 'bg-green-500/50' :
                  step.status === 'running' ? 'bg-linear-to-b from-blue-400/50 to-(--border-color)' :
                    'bg-(--border-color)'
              ]"></div>

            <!-- 步骤项 -->
            <div
              class="flex items-start gap-3 p-2 rounded-lg transition-all hover:bg-(--bg-secondary)/50 cursor-pointer"
              :class="{ 'bg-(--bg-secondary)/30': step.status === 'running' }">
              <!-- 状态图标 -->
              <div class="relative shrink-0 mt-0.5">
                <!-- 完成状态 -->
                <div v-if="step.status === 'completed'"
                  class="w-[30px] h-[30px] rounded-full bg-green-500/20 border-2 border-green-500 flex items-center justify-center">
                  <i class="ri-check-line text-green-500 text-sm"></i>
                </div>
                <!-- 运行状态 -->
                <div v-else-if="step.status === 'running'"
                  class="w-[30px] h-[30px] rounded-full bg-blue-500/20 border-2 border-blue-400 flex items-center justify-center">
                  <i class="ri-loader-4-line text-blue-400 text-sm animate-spin"></i>
                </div>
                <!-- 失败状态 -->
                <div v-else-if="step.status === 'failed'"
                  class="w-[30px] h-[30px] rounded-full bg-red-500/20 border-2 border-red-500 flex items-center justify-center">
                  <i class="ri-close-line text-red-500 text-sm"></i>
                </div>
                <!-- 等待状态 -->
                <div v-else
                  class="w-[30px] h-[30px] rounded-full bg-(--bg-secondary) border-2 border-(--border-color) flex items-center justify-center">
                  <span class="text-[10px] font-bold text-(--text-secondary)">{{ index + 1 }}</span>
                </div>
              </div>

              <!-- 步骤信息 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="text-[12px] font-semibold truncate" :class="[
                    step.status === 'completed' ? 'text-green-500' :
                      step.status === 'running' ? 'text-blue-400' :
                        step.status === 'failed' ? 'text-red-500' :
                          'text-(--text-primary)'
                  ]">
                    {{ step.name }}
                  </span>
                  <!-- 运行中的脉冲动画 -->
                  <span v-if="step.status === 'running'"
                    class="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></span>
                </div>
                <p class="text-[10px] text-(--text-secondary) mt-0.5 truncate">{{ step.description }}</p>
                <!-- 耗时显示 -->
                <div v-if="step.duration || step.status === 'running'" class="flex items-center gap-2 mt-1">
                  <i class="ri-time-line text-[10px] text-(--text-secondary)"></i>
                  <span class="text-[10px]"
                    :class="step.status === 'running' ? 'text-blue-400' : 'text-(--text-secondary)'">
                    {{ step.duration || 'calculating...' }}
                  </span>
                </div>
              </div>

              <!-- 展开箭头 -->
              <i
                class="ri-arrow-right-s-line text-(--text-secondary) opacity-0 group-hover:opacity-100 transition-opacity shrink-0"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="p-3 border-t border-(--border-color) bg-(--bg-secondary)/30 space-y-2">
        <!-- 操作按钮组 -->
        <div class="flex gap-2">
          <button @click="handleRunFlow" :disabled="isRunning"
            class="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-(--accent-color) text-white text-[11px] font-bold rounded hover:brightness-110 active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-(--accent-color)/20">
            <i :class="isRunning ? 'ri-loader-4-line animate-spin' : 'ri-play-fill'"></i>
            {{ isRunning ? 'RUNNING' : 'RUN' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/themeStore'
import { useFlowStages } from '@/composables/useFlowStages'
import { useSubflow } from '@/composables/useSubflow'
import { useFlowRunner } from '@/composables/useFlowRunner'
import { useCurrentStage } from '@/composables/useCurrentStage'

// ============ Composables ============
const route = useRoute()
const themeStore = useThemeStore()

// 流程阶段管理
const { flowStages } = useFlowStages()

// 子流程管理
const {
  subflowSteps,
  isLoading: isLoadingSubflow,
  currentStepTitle,
  currentStepEngine,
  completedSteps,
  progressPercent,
  totalTime,
  overallStatus,
  totalSteps
} = useSubflow()

// 流程运行器
const {
  isRunning,
  runFlow,
} = useFlowRunner()

// 当前阶段
const { currentStage, showProgressPanel } = useCurrentStage()

// ============ 主题相关 ============
const isDark = computed(() => themeStore.themeName === 'dark')

const toggleTheme = () => {
  themeStore.toggleTheme()
}

// ============ 事件处理 ============
const handleRunFlow = async () => {
  await runFlow()
}
</script>

<style scoped>
/* 自定义滚动条 - 更细的样式 */
::-webkit-scrollbar {
  width: 3px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
</style>
