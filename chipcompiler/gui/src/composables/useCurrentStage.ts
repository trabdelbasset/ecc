import { computed } from 'vue'
import { useRoute } from 'vue-router'

// ============ Composable ============

/**
 * 当前阶段管理 Hook
 * 负责解析和管理当前路由对应的流程阶段
 */
export function useCurrentStage() {
  const route = useRoute()

  /** 当前阶段路径 */
  const currentStage = computed(() => {
    const pathParts = route.path.split('/')
    return pathParts[pathParts.length - 1] || 'home'
  })

  /** 是否显示进度面板 (Configure 和 Home 页面不显示) */
  const showProgressPanel = computed(() => {
    return currentStage.value !== 'configure' && currentStage.value !== 'home'
  })

  /** 是否在首页 */
  const isHome = computed(() => currentStage.value === 'home')

  /** 是否在配置页 */
  const isConfigure = computed(() => currentStage.value === 'configure')

  /** 是否在流程步骤页面 */
  const isFlowStep = computed(() => {
    return !isHome.value && !isConfigure.value
  })

  /**
   * 获取阶段的完整路由路径
   */
  function getStagePath(stagePath: string): string {
    return `/workspace/${stagePath}`
  }

  /**
   * 检查指定阶段是否为当前阶段
   */
  function isCurrentStage(stagePath: string): boolean {
    return currentStage.value === stagePath
  }

  return {
    // 状态
    currentStage,
    showProgressPanel,
    isHome,
    isConfigure,
    isFlowStep,

    // 方法
    getStagePath,
    isCurrentStage
  }
}
