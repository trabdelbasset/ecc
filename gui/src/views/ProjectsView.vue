<template>
  <div class="flex flex-col h-full w-full text-(--text-primary) relative overflow-hidden">
    <div class="relative z-10 flex flex-col w-full max-w-5xl mx-auto px-8 py-6 h-full">

      <!-- Header -->
      <div class="flex items-center justify-between mb-5 shrink-0">
        <div class="flex items-center gap-4">
          <button @click="goBack"
            class="flex items-center gap-2 px-3 py-2 rounded-lg bg-(--bg-secondary) border border-(--border-color) hover:border-(--accent-color) text-(--text-secondary) hover:text-(--accent-color) transition-all duration-200 cursor-pointer text-sm">
            <i class="ri-arrow-left-line"></i>
            <span>ECOS</span>
          </button>
          <h1 class="text-xl font-semibold">Project Management</h1>
          <span class="text-sm text-(--text-secondary)">{{ filteredProjects.length }} projects</span>
        </div>
        <!-- Compare button -->
        <button v-if="selectedIds.size > 0" @click="showCompare = !showCompare"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
          :class="showCompare
            ? 'bg-(--accent-color) text-white'
            : 'bg-(--accent-color)/10 text-(--accent-color) hover:bg-(--accent-color)/20'">
          <i class="ri-git-compare-line"></i>
          Compare ({{ selectedIds.size }})
        </button>
      </div>

      <!-- Filter & Sort bar -->
      <div class="flex items-center gap-3 mb-4 shrink-0 flex-wrap">
        <select v-model="filterPdk"
          class="px-3 py-2 text-sm bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) cursor-pointer focus:border-(--accent-color) focus:outline-none transition-colors">
          <option value="">All PDKs</option>
          <option v-for="pdk in availablePdks" :key="pdk" :value="pdk">{{ pdk }}</option>
        </select>

        <select v-model="filterStatus"
          class="px-3 py-2 text-sm bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) cursor-pointer focus:border-(--accent-color) focus:outline-none transition-colors">
          <option value="">All Status</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="running">Running</option>
          <option value="in_progress">In Progress</option>
          <option value="not_started">Not Started</option>
        </select>

        <div class="flex-1 relative min-w-[200px]">
          <i class="ri-search-line absolute left-3 top-1/2 -translate-y-1/2 text-(--text-secondary) text-sm"></i>
          <input v-model="searchQuery" type="text" placeholder="Search projects..."
            class="w-full pl-9 pr-3 py-2 text-sm bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) placeholder:text-(--text-secondary)/50 focus:border-(--accent-color) focus:outline-none transition-colors" />
        </div>

        <select v-model="sortBy"
          class="px-3 py-2 text-sm bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) cursor-pointer focus:border-(--accent-color) focus:outline-none transition-colors">
          <option value="lastModified">Last Modified</option>
          <option value="name">Name</option>
          <option value="status">Status</option>
          <option value="progress">Progress</option>
        </select>

        <!-- View toggle -->
        <div class="flex items-center bg-(--bg-secondary) border border-(--border-color) rounded-lg overflow-hidden">
          <button @click="viewMode = 'list'"
            class="px-2.5 py-2 cursor-pointer transition-colors"
            :class="viewMode === 'list' ? 'bg-(--accent-color)/15 text-(--accent-color)' : 'text-(--text-secondary) hover:text-(--text-primary)'">
            <i class="ri-list-unordered text-sm"></i>
          </button>
          <button @click="viewMode = 'card'"
            class="px-2.5 py-2 cursor-pointer transition-colors"
            :class="viewMode === 'card' ? 'bg-(--accent-color)/15 text-(--accent-color)' : 'text-(--text-secondary) hover:text-(--text-primary)'">
            <i class="ri-grid-line text-sm"></i>
          </button>
        </div>
      </div>

      <!-- Compare Panel -->
      <div v-if="showCompare && selectedProjects.length >= 2"
        class="mb-4 bg-(--bg-secondary) rounded-xl border border-(--accent-color)/30 overflow-hidden shrink-0">
        <div class="flex items-center justify-between px-4 py-3 border-b border-(--border-color)">
          <div class="flex items-center gap-2">
            <i class="ri-git-compare-line text-(--accent-color)"></i>
            <span class="text-sm font-medium">Parameter Comparison</span>
          </div>
          <button @click="selectedIds.clear(); showCompare = false"
            class="text-xs text-(--text-secondary) hover:text-(--text-primary) cursor-pointer transition-colors">
            Clear Selection
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-(--border-color)">
                <th class="text-left px-4 py-2.5 text-xs font-medium text-(--text-secondary) min-w-[140px]">Parameter</th>
                <th v-for="p in selectedProjects" :key="p.id"
                  class="text-left px-4 py-2.5 text-xs font-medium text-(--text-primary) min-w-[140px]">
                  {{ p.name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.label" class="border-b border-(--border-color)/50">
                <td class="px-4 py-2 text-xs text-(--text-secondary)">{{ row.label }}</td>
                <td v-for="(val, i) in row.values" :key="i" class="px-4 py-2 text-xs font-mono"
                  :class="row.isDiff ? 'text-(--accent-color) font-medium' : 'text-(--text-primary)'">
                  {{ val }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-else-if="showCompare && selectedProjects.length < 2"
        class="mb-4 px-4 py-3 bg-(--bg-secondary) rounded-xl border border-dashed border-(--border-color) text-center text-sm text-(--text-secondary) shrink-0">
        Select at least 2 projects to compare (click checkboxes)
      </div>

      <!-- List View -->
      <div v-if="filteredProjects.length > 0 && viewMode === 'list'"
        class="flex-1 overflow-y-auto space-y-2 scrollbar-thin pb-4">
        <div v-for="project in filteredProjects" :key="project.id"
          class="flex items-center gap-3 px-4 py-3 bg-(--bg-secondary) rounded-xl border transition-all duration-200 group"
          :class="[
            project.pathExists === false ? 'border-(--border-color) opacity-50' : 'border-(--border-color) hover:border-(--accent-color) hover:shadow-md',
            selectedIds.has(project.id) ? 'border-(--accent-color)/50 bg-(--accent-color)/5' : ''
          ]">

          <!-- Checkbox for compare -->
          <button @click.stop="toggleSelect(project.id)"
            class="w-5 h-5 rounded border flex items-center justify-center shrink-0 cursor-pointer transition-all"
            :class="selectedIds.has(project.id)
              ? 'bg-(--accent-color) border-(--accent-color) text-white'
              : 'border-(--border-color) hover:border-(--accent-color)'">
            <i v-if="selectedIds.has(project.id)" class="ri-check-line text-xs"></i>
          </button>

          <!-- Status icon -->
          <div class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
            :class="statusIconBgClass(project.status)">
            <i :class="[statusIcon(project.status), statusIconColorClass(project.status), 'text-base']"
              :style="project.status === 'running' ? 'animation: spin 2s linear infinite' : ''"></i>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0 cursor-pointer" @click="project.pathExists !== false && handleOpen(project)">
            <div class="flex items-center gap-2">
              <span class="font-medium text-(--text-primary) text-sm truncate">{{ project.name }}</span>
              <span v-if="project.status" :class="statusBadgeClass(project.status)"
                class="text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0">{{ statusLabel(project.status) }}</span>
              <span v-if="project.pdk"
                class="text-[10px] px-1.5 py-0.5 rounded bg-(--accent-color)/10 text-(--accent-color) font-medium shrink-0">{{ project.pdk }}</span>
              <span v-if="project.pathExists === false"
                class="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-medium shrink-0">Unreachable</span>
            </div>
            <div class="flex items-center gap-3 mt-1 text-[11px] text-(--text-secondary)">
              <span v-if="project.topModule">{{ project.topModule }}</span>
              <span v-if="project.frequencyTarget">{{ project.frequencyTarget }}MHz</span>
              <span v-if="project.coreUtilization">{{ (project.coreUtilization * 100).toFixed(0) }}%</span>
              <span v-if="project.cellCount">{{ project.cellCount.toLocaleString() }} cells</span>
              <span v-if="project.totalRuntime">{{ project.totalRuntime }}</span>
            </div>
          </div>

          <!-- Progress -->
          <div v-if="project.totalSteps && project.totalSteps > 0" class="flex items-center gap-2 shrink-0 w-32">
            <div class="flex-1 h-1.5 bg-(--bg-primary) rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-300" :class="progressBarColor(project.status)"
                :style="{ width: `${((project.completedSteps || 0) / project.totalSteps) * 100}%` }"></div>
            </div>
            <span class="text-[11px] text-(--text-secondary) shrink-0 w-8 text-right">
              {{ project.completedSteps || 0 }}/{{ project.totalSteps }}
            </span>
          </div>

          <!-- Time + actions -->
          <span class="text-xs text-(--text-secondary) whitespace-nowrap shrink-0 w-16 text-right">{{ formatDate(project.lastOpened) }}</span>
          <button @click.stop="handleRemove(project.id)"
            class="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-500/10 transition-all cursor-pointer shrink-0"
            title="Remove from list">
            <i class="ri-close-line text-sm text-(--text-secondary) hover:text-red-500"></i>
          </button>
        </div>
      </div>

      <!-- Card View -->
      <div v-else-if="filteredProjects.length > 0 && viewMode === 'card'"
        class="flex-1 overflow-y-auto scrollbar-thin pb-4">
        <div class="grid grid-cols-2 gap-3">
          <div v-for="project in filteredProjects" :key="project.id"
            class="flex flex-col p-4 bg-(--bg-secondary) rounded-xl border transition-all duration-200 group"
            :class="[
              project.pathExists === false ? 'border-(--border-color) opacity-50' : 'border-(--border-color) hover:border-(--accent-color) hover:shadow-md cursor-pointer',
              selectedIds.has(project.id) ? 'border-(--accent-color)/50 bg-(--accent-color)/5' : ''
            ]"
            @click="project.pathExists !== false && handleOpen(project)">

            <!-- Card header -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2 min-w-0">
                <button @click.stop="toggleSelect(project.id)"
                  class="w-5 h-5 rounded border flex items-center justify-center shrink-0 cursor-pointer transition-all"
                  :class="selectedIds.has(project.id)
                    ? 'bg-(--accent-color) border-(--accent-color) text-white'
                    : 'border-(--border-color) hover:border-(--accent-color)'">
                  <i v-if="selectedIds.has(project.id)" class="ri-check-line text-xs"></i>
                </button>
                <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                  :class="statusIconBgClass(project.status)">
                  <i :class="[statusIcon(project.status), statusIconColorClass(project.status), 'text-sm']"
                    :style="project.status === 'running' ? 'animation: spin 2s linear infinite' : ''"></i>
                </div>
                <span class="font-medium text-sm text-(--text-primary) truncate">{{ project.name }}</span>
              </div>
              <button @click.stop="handleRemove(project.id)"
                class="p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-red-500/10 transition-all cursor-pointer shrink-0"
                title="Remove">
                <i class="ri-close-line text-xs text-(--text-secondary) hover:text-red-500"></i>
              </button>
            </div>

            <!-- Badges -->
            <div class="flex items-center gap-1.5 mb-3 flex-wrap">
              <span v-if="project.status" :class="statusBadgeClass(project.status)"
                class="text-[10px] px-1.5 py-0.5 rounded font-medium">{{ statusLabel(project.status) }}</span>
              <span v-if="project.pdk"
                class="text-[10px] px-1.5 py-0.5 rounded bg-(--accent-color)/10 text-(--accent-color) font-medium">{{ project.pdk }}</span>
              <span v-if="project.pathExists === false"
                class="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-medium">Unreachable</span>
            </div>

            <!-- Metrics grid -->
            <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 mb-3 text-[11px]">
              <div v-if="project.topModule" class="flex items-center gap-1 text-(--text-secondary)">
                <i class="ri-code-s-slash-line text-[10px]"></i>
                <span class="truncate">{{ project.topModule }}</span>
              </div>
              <div v-if="project.frequencyTarget" class="flex items-center gap-1 text-(--text-secondary)">
                <i class="ri-speed-line text-[10px]"></i>
                {{ project.frequencyTarget }}MHz
              </div>
              <div v-if="project.coreUtilization" class="flex items-center gap-1 text-(--text-secondary)">
                <i class="ri-layout-grid-line text-[10px]"></i>
                {{ (project.coreUtilization * 100).toFixed(0) }}% util
              </div>
              <div v-if="project.cellCount" class="flex items-center gap-1 text-(--text-secondary)">
                <i class="ri-apps-line text-[10px]"></i>
                {{ project.cellCount.toLocaleString() }} cells
              </div>
            </div>

            <!-- Progress + time -->
            <div class="mt-auto pt-2 border-t border-(--border-color)/50">
              <div class="flex items-center justify-between">
                <div v-if="project.totalSteps && project.totalSteps > 0" class="flex items-center gap-2 flex-1">
                  <div class="flex-1 h-1.5 bg-(--bg-primary) rounded-full overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-300" :class="progressBarColor(project.status)"
                      :style="{ width: `${((project.completedSteps || 0) / project.totalSteps) * 100}%` }"></div>
                  </div>
                  <span class="text-[11px] text-(--text-secondary) shrink-0">{{ project.completedSteps || 0 }}/{{ project.totalSteps }}</span>
                </div>
                <span class="text-[11px] text-(--text-secondary) ml-3">{{ formatDate(project.lastOpened) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex-1 flex flex-col items-center justify-center text-center">
        <i class="ri-folder-2-line text-6xl text-(--text-secondary) opacity-20 mb-4"></i>
        <p class="text-lg font-medium text-(--text-primary) mb-2">
          {{ recentProjects.length === 0 ? 'No projects yet' : 'No matching projects' }}
        </p>
        <p class="text-sm text-(--text-secondary) mb-6">
          {{ recentProjects.length === 0
            ? 'Create your first project from the Backend Design tool'
            : 'Try adjusting your filters or search query'
          }}
        </p>
        <button v-if="recentProjects.length === 0" @click="router.push('/ecc')"
          class="flex items-center gap-2 px-5 py-2.5 bg-(--accent-color)/10 text-(--accent-color) rounded-lg hover:bg-(--accent-color)/20 transition-colors cursor-pointer text-sm font-medium">
          <i class="ri-cpu-line"></i>
          Go to Backend Design
        </button>
        <button v-else @click="clearFilters"
          class="flex items-center gap-2 px-5 py-2.5 bg-(--bg-secondary) text-(--text-secondary) rounded-lg hover:text-(--text-primary) transition-colors cursor-pointer text-sm">
          <i class="ri-filter-off-line"></i>
          Clear Filters
        </button>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Project, ProjectStatus } from '../types'
import { useWorkspace } from '../composables/useWorkspace'

const router = useRouter()
const { recentProjects, openProject, removeRecentProject, loadRecentProjects } = useWorkspace()

const filterPdk = ref('')
const filterStatus = ref('')
const searchQuery = ref('')
const sortBy = ref('lastModified')
const viewMode = ref<'list' | 'card'>('list')

const selectedIds = reactive(new Set<string>())
const showCompare = ref(false)

onMounted(async () => {
  await loadRecentProjects()
})

function toggleSelect(id: string) {
  if (selectedIds.has(id)) {
    selectedIds.delete(id)
  } else {
    selectedIds.add(id)
  }
  if (selectedIds.size >= 2 && !showCompare.value) {
    showCompare.value = true
  }
}

const selectedProjects = computed(() =>
  recentProjects.value.filter(p => selectedIds.has(p.id))
)

// Compare table rows
const compareRows = computed(() => {
  const projects = selectedProjects.value
  if (projects.length < 2) return []

  const fields: { key: keyof Project | string; label: string; format?: (v: unknown) => string }[] = [
    { key: 'status', label: 'Status', format: v => statusLabel(v as ProjectStatus) },
    { key: 'pdk', label: 'PDK' },
    { key: 'topModule', label: 'Top Module' },
    { key: 'frequencyTarget', label: 'Frequency (MHz)' },
    { key: 'coreUtilization', label: 'Core Utilization', format: v => v != null ? `${((v as number) * 100).toFixed(0)}%` : '—' },
    { key: 'totalSteps', label: 'Total Steps' },
    { key: 'completedSteps', label: 'Completed Steps' },
    { key: 'currentStep', label: 'Current Step' },
    { key: 'totalRuntime', label: 'Total Runtime' },
    { key: 'cellCount', label: 'Cell Count', format: v => v != null ? (v as number).toLocaleString() : '—' },
    { key: 'frequency', label: 'Actual Freq (MHz)', format: v => v != null ? (v as number).toFixed(1) : '—' },
  ]

  return fields.map(f => {
    const values = projects.map(p => {
      const raw = (p as Record<string, unknown>)[f.key]
      if (raw == null || raw === '') return '—'
      return f.format ? f.format(raw) : String(raw)
    })
    const uniqueVals = new Set(values)
    return { label: f.label, values, isDiff: uniqueVals.size > 1 }
  })
})

const availablePdks = computed(() => {
  const pdks = new Set<string>()
  for (const p of recentProjects.value) {
    if (p.pdk) pdks.add(p.pdk)
  }
  return Array.from(pdks).sort()
})

const filteredProjects = computed(() => {
  let result = [...recentProjects.value]

  if (filterPdk.value) result = result.filter(p => p.pdk === filterPdk.value)
  if (filterStatus.value) result = result.filter(p => p.status === filterStatus.value)
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.name.toLowerCase().includes(q) ||
      p.path.toLowerCase().includes(q) ||
      (p.topModule && p.topModule.toLowerCase().includes(q))
    )
  }

  result.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'status': {
        const order: Record<string, number> = { success: 0, running: 1, in_progress: 2, failed: 3, not_started: 4 }
        return (order[a.status || 'not_started'] ?? 5) - (order[b.status || 'not_started'] ?? 5)
      }
      case 'progress': {
        const pa = a.totalSteps ? (a.completedSteps || 0) / a.totalSteps : 0
        const pb = b.totalSteps ? (b.completedSteps || 0) / b.totalSteps : 0
        return pb - pa
      }
      default:
        return new Date(b.lastOpened).getTime() - new Date(a.lastOpened).getTime()
    }
  })

  return result
})

function clearFilters() {
  filterPdk.value = ''
  filterStatus.value = ''
  searchQuery.value = ''
}

const goBack = () => router.push('/')

const handleOpen = async (project: Project) => {
  const success = await openProject(project)
  if (success) router.push('/workspace')
}

const handleRemove = async (projectId: string) => {
  selectedIds.delete(projectId)
  await removeRecentProject(projectId)
}

function statusBadgeClass(status?: ProjectStatus): string {
  if (!status) return 'bg-gray-500/15 text-gray-400'
  const map: Record<ProjectStatus, string> = {
    success: 'bg-emerald-500/15 text-emerald-400',
    failed: 'bg-red-500/15 text-red-400',
    running: 'bg-blue-500/15 text-blue-400',
    in_progress: 'bg-amber-500/15 text-amber-400',
    not_started: 'bg-gray-500/15 text-gray-400',
  }
  return map[status]
}

function statusLabel(status?: ProjectStatus): string {
  if (!status) return '—'
  const map: Record<ProjectStatus, string> = {
    success: 'Success', failed: 'Failed', running: 'Running',
    in_progress: 'In Progress', not_started: 'Not Started',
  }
  return map[status]
}

function statusIcon(status?: ProjectStatus): string {
  if (!status) return 'ri-question-line'
  const map: Record<ProjectStatus, string> = {
    success: 'ri-check-line', failed: 'ri-close-line', running: 'ri-loader-4-line',
    in_progress: 'ri-time-line', not_started: 'ri-subtract-line',
  }
  return map[status]
}

function statusIconBgClass(status?: ProjectStatus): string {
  if (!status) return 'bg-gray-500/10'
  const map: Record<ProjectStatus, string> = {
    success: 'bg-emerald-500/10', failed: 'bg-red-500/10', running: 'bg-blue-500/10',
    in_progress: 'bg-amber-500/10', not_started: 'bg-gray-500/10',
  }
  return map[status]
}

function statusIconColorClass(status?: ProjectStatus): string {
  if (!status) return 'text-gray-400'
  const map: Record<ProjectStatus, string> = {
    success: 'text-emerald-400', failed: 'text-red-400', running: 'text-blue-400',
    in_progress: 'text-amber-400', not_started: 'text-gray-400',
  }
  return map[status]
}

function progressBarColor(status?: ProjectStatus): string {
  if (!status) return 'bg-gray-500'
  const map: Record<ProjectStatus, string> = {
    success: 'bg-emerald-500', failed: 'bg-red-500', running: 'bg-blue-500',
    in_progress: 'bg-amber-500', not_started: 'bg-gray-500',
  }
  return map[status]
}

function formatDate(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - new Date(date).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return new Date(date).toLocaleDateString('en-US')
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
