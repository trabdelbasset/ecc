import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useTauri } from './useTauri'

// ============ 类型定义 ============

/** 流程运行状态 */
export type RunnerStatus = 'idle' | 'running' | 'completed' | 'failed'

/** 运行结果 */
export interface RunResult {
  success: boolean
  message?: string
  data?: any
}

// ============ Composable ============

/**
 * 流程运行器 Hook
 * 负责处理流程的运行、停止、重置等操作
 */
export function useFlowRunner() {
  const { isInTauri, ensureTauri } = useTauri()
  const route = useRoute()

  // 状态
  const isRunning = ref(false)
  const status = ref<RunnerStatus>('idle')
  const error = ref<string | null>(null)
  const lastRunResult = ref<RunResult | null>(null)

  /**
   * 运行当前流程
   */
  async function runFlow(): Promise<RunResult> {
    // 检查是否在 Tauri 环境中
    if (!isInTauri) {
      console.warn('当前不在 Tauri 环境中，无法执行 Python 脚本')
      ensureTauri(true) // 显示警告弹窗
      return { success: false, message: 'Not in Tauri environment' }
    }

    if (isRunning.value) {
      return { success: false, message: 'Flow is already running' }
    }

    isRunning.value = true
    status.value = 'running'
    error.value = null

    // 获取当前路由名称
    const routeName = route.name || route.path || 'unknown'

    try {
      console.log('handleRunFlow', routeName)

      // TODO: 实现实际的流程运行逻辑
      // 这里可以调用后端 API 或 Tauri 命令来运行流程

      const result: RunResult = { success: true, data: { routeName } }
      lastRunResult.value = result
      status.value = 'completed'
      return result

    } catch (err) {
      console.error('❌ 调用 Python 失败:', err)
      const errorMessage = err instanceof Error ? err.message : String(err)
      error.value = errorMessage
      status.value = 'failed'

      const result: RunResult = { success: false, message: errorMessage }
      lastRunResult.value = result
      return result

    } finally {
      isRunning.value = false
    }
  }

  /**
   * 停止当前流程
   */
  async function stopFlow(): Promise<RunResult> {
    if (!isRunning.value) {
      return { success: false, message: 'No flow is running' }
    }

    try {
      // TODO: 实现停止流程的逻辑
      console.log('Stopping flow...')

      isRunning.value = false
      status.value = 'idle'

      return { success: true, message: 'Flow stopped' }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      error.value = errorMessage
      return { success: false, message: errorMessage }
    }
  }

  /**
   * 重置流程状态
   */
  async function resetFlow(): Promise<RunResult> {
    try {
      // TODO: 实现重置流程的逻辑
      console.log('Resetting flow...')

      isRunning.value = false
      status.value = 'idle'
      error.value = null
      lastRunResult.value = null

      return { success: true, message: 'Flow reset' }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err)
      error.value = errorMessage
      return { success: false, message: errorMessage }
    }
  }

  /**
   * 清除错误状态
   */
  function clearError(): void {
    error.value = null
  }

  return {
    // 状态
    isRunning,
    status,
    error,
    lastRunResult,

    // 方法
    runFlow,
    stopFlow,
    resetFlow,
    clearError
  }
}
