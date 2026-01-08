import { ref } from 'vue'
import type { Project } from '../types'
import { open } from '@tauri-apps/plugin-dialog'
import { invoke } from '@tauri-apps/api/core'

// 模拟的最近项目数据
const mockRecentProjects: Project[] = [
  {
    id: '1',
    name: '芯片设计项目 A',
    path: '~/Documents/Projects/chip-design-a',
    lastOpened: new Date(Date.now() - 1000 * 60 * 60 * 2) // 2小时前
  },
  {
    id: '2',
    name: 'FPGA 验证工程',
    path: '~/Documents/Projects/fpga-verification',
    lastOpened: new Date(Date.now() - 1000 * 60 * 60 * 24) // 1天前
  },
  {
    id: '3',
    name: 'IC 布局优化',
    path: '~/Documents/Projects/ic-layout',
    lastOpened: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3) // 3天前
  }
]

// 共享的状态实例（单例模式）
const currentProject = ref<Project | null>(null)
const recentProjects = ref<Project[]>(mockRecentProjects)

export function useProject() {

  const openProject = async (project?: Project) => {
    try {
      let selectedPath: string | null = null

      if (project) {
        selectedPath = project.path
      } else {
        // 1. 【收信】弹出文件夹选择对话框
        const result = await open({
          directory: true,
          multiple: false,
          title: '选择 ECC 项目目录'
        })
        if (!result) return
        selectedPath = result as string
      }

      // 2. 【发信】让 Python 加载项目状态
      const pyResult = await invoke('run_python', {
        script: 'test.py',
        args: ['--action', 'load', '--path', selectedPath]
      }) as { code: number, stdout: string, stderr: string }

      const response = JSON.parse(pyResult.stdout)

      if (pyResult.code === 0 && response.status === 'success') {
        const loadedProject: Project = {
          id: response.project.path,
          name: response.project.name,
          path: response.project.path,
          lastOpened: new Date()
        }

        currentProject.value = loadedProject

        // 更新最近列表
        const filtered = recentProjects.value.filter(p => p.path !== loadedProject.path)
        recentProjects.value = [loadedProject, ...filtered]

        return true
      } else {
        console.error('加载项目失败:', response.message || pyResult.stderr)
        return false
      }
    } catch (error) {
      console.error('Open project error:', error)
      return false
    }
  }

  const newProject = async () => {
    try {
      // 1. 【收信】选择新项目存放的位置
      const selectedPath = await open({
        directory: true,
        multiple: false,
        title: '选择新项目保存位置'
      })

      if (!selectedPath) return

      // 2. 【发信】初始化磁盘结构
      const projectName = 'New_Chip_Design'
      const pyResult = await invoke('run_python', {
        script: 'test.py',
        args: ['--action', 'init', '--path', selectedPath as string, '--name', projectName]
      }) as { code: number, stdout: string, stderr: string }

      const response = JSON.parse(pyResult.stdout)

      if (pyResult.code === 0 && response.status === 'success') {
        const createdProject: Project = {
          id: response.project.path,
          name: response.project.name,
          path: response.project.path,
          lastOpened: new Date()
        }

        currentProject.value = createdProject
        recentProjects.value.unshift(createdProject)
        return true
      } else {
        console.error('创建项目失败:', response.message)
        return false
      }
    } catch (error) {
      console.error('New project error:', error)
      return false
    }
  }

  const importProject = () => {
    // 导入可以复用 openProject 的逻辑，或者针对不同格式做特殊处理
    openProject()
  }

  const closeProject = () => {
    currentProject.value = null
  }

  return {
    currentProject,
    recentProjects,
    openProject,
    newProject,
    importProject,
    closeProject
  }
}

