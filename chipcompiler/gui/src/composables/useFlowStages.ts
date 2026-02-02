import { ref, computed, watch, onMounted } from 'vue'
import { readTextFile } from '@tauri-apps/plugin-fs'
import { invoke } from '@tauri-apps/api/core'
import { useWorkspace } from './useWorkspace'
import { useTauri } from './useTauri'
import { StepEnum } from '@/api/type'

// ============ 类型定义 ============

/** flow.json 中的步骤数据结构 */
export interface FlowStep {
  name: string
  tool: string
  state: string
  runtime: string
  'peak memory (mb)': number
  info: Record<string, any>
}

/** flow.json 数据结构 */
export interface FlowData {
  steps: FlowStep[]
}

/** 流程阶段配置 */
export interface FlowStage {
  label: string
  path: string
  icon: string
  group: 'setup' | 'run'
  completed: boolean
  available: boolean
}

/** 步骤映射配置 */
interface StepMapping {
  path: string
  label: string
  icon: string
}

// ============ 常量配置 ============

/** 步骤名称到路由路径和图标的映射 */
const STEP_NAME_MAPPING: Record<string, StepMapping> = {
  'synthesis': { path: 'synthesis', label: 'Synth', icon: 'ri-node-tree' },
  'floorplan': { path: 'floorplan', label: 'Floor', icon: 'ri-layout-4-line' },
  'place': { path: 'place', label: 'Place', icon: 'ri-focus-2-line' },
  'cts': { path: 'cts', label: 'CTS', icon: 'ri-git-merge-line' },
  'route': { path: 'route', label: 'Route', icon: 'ri-route-line' },
  'drc': { path: 'drc', label: 'DRC', icon: 'ri-checkbox-circle-line' },
  'filler': { path: StepEnum.FILLER, label: 'Filler', icon: 'ri-grid-fill' }
}

/** 固定的设置页面步骤 */
const FIXED_SETUP_STAGES: FlowStage[] = [
  { label: 'Home', path: 'home', icon: 'ri-home-4-line', group: 'setup', completed: false, available: true },
  { label: 'Config', path: 'configure', icon: 'ri-settings-3-line', group: 'setup', completed: false, available: true }
]

// ============ Composable ============

/**
 * 流程阶段管理 Hook
 * 负责从 flow.json 加载流程步骤并管理状态
 */
export function useFlowStages() {
  const { isInTauri } = useTauri()
  const { currentProject } = useWorkspace()

  // 动态加载的流程步骤
  const dynamicFlowStages = ref<FlowStage[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 合并后的完整流程步骤
  const flowStages = computed<FlowStage[]>(() => {
    return [...FIXED_SETUP_STAGES, ...dynamicFlowStages.value]
  })

  /**
   * 请求文件系统访问权限
   */
  async function requestPermission(path: string): Promise<boolean> {
    try {
      await invoke('request_project_permission', { path })
      return true
    } catch (permError) {
      console.warn('请求文件访问权限失败:', permError)
      return false
    }
  }

  /**
   * 将 flow.json 数据转换为 FlowStage 格式
   */
  function transformFlowData(flowData: FlowData): FlowStage[] {
    const stages: FlowStage[] = []
    let previousCompleted = true // 第一个步骤默认可用

    for (const step of flowData.steps) {
      const stepNameLower = step.name.toLowerCase()
      const mapping = STEP_NAME_MAPPING[stepNameLower]

      if (mapping) {
        const isCompleted = step.state.toLowerCase() === 'success'
        const isAvailable = previousCompleted

        stages.push({
          label: mapping.label,
          path: mapping.path,
          icon: mapping.icon,
          group: 'run',
          completed: isCompleted,
          available: isAvailable
        })

        previousCompleted = isCompleted
      }
    }

    return stages
  }

  /**
   * 从 flow.json 加载流程步骤
   */
  async function loadFlowStages(): Promise<void> {
    if (!isInTauri || !currentProject.value?.path) {
      console.warn('无法加载 flow.json: 不在 Tauri 环境或没有打开的项目')
      dynamicFlowStages.value = []
      return
    }

    isLoading.value = true
    error.value = null

    try {
      const projectPath = currentProject.value.path
      const flowJsonPath = `${projectPath}/flow.json`
      console.log('Loading flow.json from:', flowJsonPath)

      // 先请求文件系统访问权限
      await requestPermission(projectPath)

      const fileContent = await readTextFile(flowJsonPath)
      const flowData: FlowData = JSON.parse(fileContent)

      console.log('Loaded flow data:', flowData)

      // 转换数据格式
      dynamicFlowStages.value = transformFlowData(flowData)
      console.log('Flow stages loaded:', dynamicFlowStages.value)

    } catch (err) {
      console.error('Failed to load flow.json:', err)
      error.value = err instanceof Error ? err.message : String(err)
      dynamicFlowStages.value = []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 重新加载流程步骤
   */
  async function refreshFlowStages(): Promise<void> {
    await loadFlowStages()
  }

  /**
   * 清空流程步骤
   */
  function clearFlowStages(): void {
    dynamicFlowStages.value = []
    error.value = null
  }

  // 监听当前项目变化，自动重新加载
  watch(
    () => currentProject.value?.path,
    async (newPath) => {
      if (newPath) {
        await loadFlowStages()
      } else {
        clearFlowStages()
      }
    },
    { immediate: true }
  )

  // 组件挂载时也尝试加载
  onMounted(async () => {
    if (currentProject.value?.path) {
      await loadFlowStages()
    }
  })

  return {
    // 状态
    flowStages,
    dynamicFlowStages,
    isLoading,
    error,

    // 方法
    loadFlowStages,
    refreshFlowStages,
    clearFlowStages
  }
}
