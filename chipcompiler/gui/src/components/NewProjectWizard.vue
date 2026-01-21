<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <div
      class="relative w-full max-w-5xl mx-4 bg-(--bg-primary) rounded-2xl shadow-2xl border border-(--border-color) overflow-hidden max-h-[90vh] flex flex-col">
      <!-- Close Button -->
      <button @click="$emit('close')"
        class="absolute top-4 right-4 z-10 p-2 rounded-lg hover:bg-(--bg-secondary) transition-colors cursor-pointer">
        <i class="ri-close-line text-xl text-(--text-secondary) hover:text-(--text-primary)"></i>
      </button>

      <!-- Stepper Header -->
      <div class="px-8 pt-8 pb-6 border-b border-(--border-color) bg-(--bg-secondary)/50">
        <div class="flex items-center justify-between max-w-3xl mx-auto">
          <template v-for="(step, index) in steps" :key="step.id">
            <!-- Step Circle -->
            <div class="flex items-center">
              <div class="flex flex-col items-center">
                <div :class="[
                  'w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300',
                  currentStep > step.id
                    ? 'bg-(--accent-color) text-white'
                    : currentStep === step.id
                      ? 'bg-(--accent-color) text-white ring-4 ring-(--accent-color)/20'
                      : 'bg-(--bg-secondary) text-(--text-secondary) border-2 border-(--border-color)'
                ]">
                  <i v-if="currentStep > step.id" class="ri-check-line text-lg"></i>
                  <span v-else>{{ step.id }}</span>
                </div>
                <span :class="[
                  'mt-2 text-xs font-medium whitespace-nowrap transition-colors duration-300',
                  currentStep >= step.id ? 'text-(--text-primary)' : 'text-(--text-secondary)'
                ]">{{ step.title }}</span>
              </div>
            </div>

            <!-- Connector Line -->
            <div v-if="index < steps.length - 1" :class="[
              'flex-1 h-0.5 mx-4 transition-all duration-500',
              currentStep > step.id ? 'bg-(--accent-color)' : 'bg-(--border-color)'
            ]"></div>
          </template>
        </div>
      </div>

      <!-- Step Content -->
      <div class="flex-1 overflow-y-auto p-8">
        <Transition name="slide-fade" mode="out-in">
          <!-- Step 1: Basic Info -->
          <div v-if="currentStep === 1" key="step1" class="max-w-2xl mx-auto">
            <div class="mb-8">
              <span class="text-xs font-medium text-(--accent-color) uppercase tracking-wider">步骤 1</span>
              <h2 class="text-2xl font-bold text-(--text-primary) mt-1">项目基本信息</h2>
              <p class="text-(--text-secondary) mt-2">配置新项目的名称、描述和保存位置</p>
            </div>

            <div class="space-y-6">
              <!-- Project Name -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-2">
                  项目名称 <span class="text-red-500">*</span>
                </label>
                <input v-model="config.name" type="text" placeholder="例如: my_chip_design"
                  class="w-full px-4 py-3 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) placeholder:text-(--text-secondary) focus:outline-none focus:border-(--accent-color) focus:ring-2 focus:ring-(--accent-color)/20 transition-all" />
                <p class="mt-1 text-xs text-(--text-secondary)">项目名称只能包含字母、数字和下划线</p>
              </div>

              <!-- Project Description -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-2">
                  项目描述
                </label>
                <textarea v-model="config.description" rows="3" placeholder="简要描述您的芯片设计项目..."
                  class="w-full px-4 py-3 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) placeholder:text-(--text-secondary) focus:outline-none focus:border-(--accent-color) focus:ring-2 focus:ring-(--accent-color)/20 transition-all resize-none"></textarea>
              </div>

              <!-- Project Location -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-2">
                  保存位置 <span class="text-red-500">*</span>
                </label>
                <div class="flex gap-3">
                  <input v-model="config.location" type="text" readonly placeholder="点击选择文件夹..."
                    class="flex-1 px-4 py-3 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) placeholder:text-(--text-secondary) cursor-pointer" />
                  <button @click="selectLocation"
                    class="px-6 py-3 bg-(--accent-color) text-white rounded-lg hover:opacity-90 transition-opacity font-medium cursor-pointer flex items-center gap-2">
                    <i class="ri-folder-open-line"></i>
                    浏览
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 2: Design Files -->
          <div v-else-if="currentStep === 2" key="step2" class="max-w-2xl mx-auto">
            <div class="mb-8">
              <span class="text-xs font-medium text-(--accent-color) uppercase tracking-wider">步骤 2</span>
              <h2 class="text-2xl font-bold text-(--text-primary) mt-1">设计文件</h2>
              <p class="text-(--text-secondary) mt-2">上传或选择您的 RTL 设计文件</p>
            </div>

            <!-- Drag & Drop Zone -->
            <div @dragover.prevent="isDragging = true" @dragleave.prevent="isDragging = false"
              @drop.prevent="handleFileDrop" :class="[
                'relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer',
                isDragging
                  ? 'border-(--accent-color) bg-(--accent-color)/5'
                  : 'border-(--border-color) hover:border-(--accent-color)/50 hover:bg-(--bg-secondary)/50'
              ]" @click="selectDesignFiles">
              <div class="flex flex-col items-center">
                <div
                  class="w-16 h-16 rounded-full bg-(--accent-color)/10 flex items-center justify-center mb-4 transition-transform"
                  :class="{ 'scale-110': isDragging }">
                  <i class="ri-upload-cloud-2-line text-3xl text-(--accent-color)"></i>
                </div>
                <h3 class="text-lg font-semibold text-(--text-primary) mb-2">拖放文件到此处上传</h3>
                <p class="text-sm text-(--text-secondary) mb-4">支持 Verilog (.v), SystemVerilog (.sv), VHDL (.vhd)
                  文件</p>
                <button type="button"
                  class="px-6 py-2.5 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) hover:border-(--accent-color) transition-colors font-medium">
                  浏览文件
                </button>
              </div>
            </div>

            <!-- File List -->
            <div v-if="config.designFiles.length > 0" class="mt-6 space-y-2">
              <h4 class="text-sm font-medium text-(--text-primary) mb-3">已添加的文件 ({{ config.designFiles.length }})
              </h4>
              <TransitionGroup name="list">
                <div v-for="file in config.designFiles" :key="file.id"
                  class="flex items-center justify-between px-4 py-3 bg-(--bg-secondary) rounded-lg border border-(--border-color) group">
                  <div class="flex items-center gap-3 min-w-0">
                    <i :class="[
                      'text-xl',
                      file.type === 'verilog' || file.type === 'systemverilog'
                        ? 'ri-file-code-line text-blue-500'
                        : file.type === 'vhdl'
                          ? 'ri-file-code-line text-purple-500'
                          : 'ri-file-line text-(--text-secondary)'
                    ]"></i>
                    <div class="min-w-0">
                      <p class="font-medium text-(--text-primary) truncate">{{ file.name }}</p>
                      <p class="text-xs text-(--text-secondary) truncate">{{ file.path }}</p>
                    </div>
                  </div>
                  <button @click.stop="removeFile(file.id)"
                    class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-(--bg-primary) transition-all cursor-pointer">
                    <i class="ri-delete-bin-line text-(--text-secondary) hover:text-red-500"></i>
                  </button>
                </div>
              </TransitionGroup>
            </div>

            <!-- Top Module Selection -->
            <div v-if="config.designFiles.length > 0" class="mt-6">
              <label class="block text-sm font-medium text-(--text-primary) mb-2">
                顶层模块名称 <span class="text-red-500">*</span>
              </label>
              <input v-model="config.topModule" type="text" placeholder="例如: top_module"
                class="w-full px-4 py-3 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) placeholder:text-(--text-secondary) focus:outline-none focus:border-(--accent-color) focus:ring-2 focus:ring-(--accent-color)/20 transition-all" />
            </div>
          </div>

          <!-- Step 3: Technology Config -->
          <div v-else-if="currentStep === 3" key="step3" class="max-w-2xl mx-auto">
            <div class="mb-8">
              <span class="text-xs font-medium text-(--accent-color) uppercase tracking-wider">步骤 3</span>
              <h2 class="text-2xl font-bold text-(--text-primary) mt-1">工艺配置</h2>
              <p class="text-(--text-secondary) mt-2">选择目标工艺库和设计约束</p>
            </div>

            <div class="space-y-6">
              <!-- PDK Selection -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-3">
                  工艺设计套件 (PDK) <span class="text-red-500">*</span>
                </label>
                <div class="grid grid-cols-2 gap-4">
                  <button v-for="pdk in pdkOptions" :key="pdk.id" @click="config.pdk = pdk.id" :class="[
                    'flex items-start gap-4 p-4 rounded-xl border-2 transition-all cursor-pointer text-left',
                    config.pdk === pdk.id
                      ? 'border-(--accent-color) bg-(--accent-color)/5'
                      : 'border-(--border-color) hover:border-(--accent-color)/50 bg-(--bg-secondary)'
                  ]">
                    <div :class="[
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      config.pdk === pdk.id ? 'bg-(--accent-color) text-white' : 'bg-(--bg-primary) text-(--text-secondary)'
                    ]">
                      <i :class="pdk.icon"></i>
                    </div>
                    <div>
                      <h4 class="font-semibold text-(--text-primary)">{{ pdk.name }}</h4>
                      <p class="text-xs text-(--text-secondary) mt-1">{{ pdk.description }}</p>
                    </div>
                  </button>
                </div>
              </div>

              <!-- Technology Node -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-2">
                  工艺节点
                </label>
                <select v-model="config.technologyNode"
                  class="w-full px-4 py-3 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-(--text-primary) focus:outline-none focus:border-(--accent-color) focus:ring-2 focus:ring-(--accent-color)/20 transition-all cursor-pointer">
                  <option value="">选择工艺节点</option>
                  <option value="sky130">SkyWater 130nm</option>
                  <option value="gf180">GlobalFoundries 180nm</option>
                  <option value="asap7">ASAP 7nm (学术)</option>
                  <option value="nangate45">NanGate 45nm (学术)</option>
                </select>
              </div>

              <!-- Target Frequency -->
              <div>
                <label class="block text-sm font-medium text-(--text-primary) mb-2">
                  目标频率 (MHz)
                </label>
                <div class="flex items-center gap-4">
                  <input v-model.number="config.targetFrequency" type="range" min="10" max="1000" step="10"
                    class="flex-1 h-2 bg-(--bg-secondary) rounded-lg appearance-none cursor-pointer accent-(--accent-color)" />
                  <div
                    class="w-24 px-3 py-2 bg-(--bg-secondary) border border-(--border-color) rounded-lg text-center text-(--text-primary) font-mono">
                    {{ config.targetFrequency }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Tips Card -->
            <div class="mt-8 p-4 bg-(--accent-color)/5 border border-(--accent-color)/20 rounded-xl">
              <div class="flex gap-3">
                <i class="ri-lightbulb-line text-xl text-(--accent-color)"></i>
                <div>
                  <h4 class="font-medium text-(--text-primary)">提示</h4>
                  <p class="text-sm text-(--text-secondary) mt-1">
                    选择合适的工艺库对设计结果影响很大。SkyWater 130nm 是开源 PDK，适合学习和原型验证。
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 4: Review -->
          <div v-else-if="currentStep === 4" key="step4" class="max-w-2xl mx-auto">
            <div class="mb-8">
              <span class="text-xs font-medium text-(--accent-color) uppercase tracking-wider">步骤 4</span>
              <h2 class="text-2xl font-bold text-(--text-primary) mt-1">确认并创建</h2>
              <p class="text-(--text-secondary) mt-2">请检查项目配置，确认无误后点击创建</p>
            </div>

            <!-- Review Cards -->
            <div class="space-y-4">
              <!-- Basic Info Card -->
              <div class="p-5 bg-(--bg-secondary) rounded-xl border border-(--border-color)">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="font-semibold text-(--text-primary) flex items-center gap-2">
                    <i class="ri-information-line text-(--accent-color)"></i>
                    基本信息
                  </h3>
                  <button @click="currentStep = 1"
                    class="text-sm text-(--accent-color) hover:underline cursor-pointer">
                    编辑
                  </button>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-(--text-secondary)">项目名称</span>
                    <p class="font-medium text-(--text-primary) mt-1">{{ config.name || '-' }}</p>
                  </div>
                  <div>
                    <span class="text-(--text-secondary)">保存位置</span>
                    <p class="font-medium text-(--text-primary) mt-1 truncate">{{ config.location || '-' }}</p>
                  </div>
                  <div class="col-span-2">
                    <span class="text-(--text-secondary)">项目描述</span>
                    <p class="font-medium text-(--text-primary) mt-1">{{ config.description || '无描述' }}</p>
                  </div>
                </div>
              </div>

              <!-- Design Files Card -->
              <div class="p-5 bg-(--bg-secondary) rounded-xl border border-(--border-color)">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="font-semibold text-(--text-primary) flex items-center gap-2">
                    <i class="ri-file-code-line text-(--accent-color)"></i>
                    设计文件
                  </h3>
                  <button @click="currentStep = 2"
                    class="text-sm text-(--accent-color) hover:underline cursor-pointer">
                    编辑
                  </button>
                </div>
                <div class="text-sm">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-(--text-secondary)">文件数量</span>
                    <span class="font-medium text-(--text-primary)">{{ config.designFiles.length }} 个文件</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-(--text-secondary)">顶层模块</span>
                    <span class="font-medium text-(--text-primary)">{{ config.topModule || '-' }}</span>
                  </div>
                </div>
              </div>

              <!-- Technology Card -->
              <div class="p-5 bg-(--bg-secondary) rounded-xl border border-(--border-color)">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="font-semibold text-(--text-primary) flex items-center gap-2">
                    <i class="ri-cpu-line text-(--accent-color)"></i>
                    工艺配置
                  </h3>
                  <button @click="currentStep = 3"
                    class="text-sm text-(--accent-color) hover:underline cursor-pointer">
                    编辑
                  </button>
                </div>
                <div class="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span class="text-(--text-secondary)">PDK</span>
                    <p class="font-medium text-(--text-primary) mt-1">{{ getPdkName(config.pdk) }}</p>
                  </div>
                  <div>
                    <span class="text-(--text-secondary)">工艺节点</span>
                    <p class="font-medium text-(--text-primary) mt-1">{{ getNodeName(config.technologyNode) }}</p>
                  </div>
                  <div>
                    <span class="text-(--text-secondary)">目标频率</span>
                    <p class="font-medium text-(--text-primary) mt-1">{{ config.targetFrequency }} MHz</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Ready to Create -->
            <div
              class="mt-6 p-5 bg-linear-to-r from-(--accent-color)/10 to-(--accent-color)/5 border border-(--accent-color)/20 rounded-xl">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-(--accent-color)/20 flex items-center justify-center">
                  <i class="ri-rocket-line text-2xl text-(--accent-color)"></i>
                </div>
                <div>
                  <h4 class="font-semibold text-(--text-primary)">准备就绪</h4>
                  <p class="text-sm text-(--text-secondary)">所有配置已完成，点击下方按钮创建您的芯片设计项目</p>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Footer Actions -->
      <div class="px-8 py-5 border-t border-(--border-color) bg-(--bg-secondary)/30 flex items-center justify-between">
        <button v-if="currentStep > 1" @click="prevStep"
          class="px-6 py-2.5 text-(--text-primary) hover:bg-(--bg-secondary) rounded-lg transition-colors font-medium cursor-pointer flex items-center gap-2">
          <i class="ri-arrow-left-line"></i>
          上一步
        </button>
        <div v-else></div>

        <div class="flex items-center gap-3">
          <button @click="$emit('close')"
            class="px-6 py-2.5 text-(--text-secondary) hover:text-(--text-primary) hover:bg-(--bg-secondary) rounded-lg transition-colors font-medium cursor-pointer">
            取消
          </button>
          <button v-if="currentStep < 4" @click="nextStep" :disabled="!canProceed"
            class="px-6 py-2.5 bg-(--accent-color) text-white rounded-lg hover:opacity-90 transition-opacity font-medium cursor-pointer flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            下一步
            <i class="ri-arrow-right-line"></i>
          </button>
          <button v-else @click="createProject" :disabled="isCreating"
            class="px-8 py-2.5 bg-(--accent-color) text-white rounded-lg hover:opacity-90 transition-opacity font-medium cursor-pointer flex items-center gap-2 disabled:opacity-50">
            <i v-if="isCreating" class="ri-loader-4-line animate-spin"></i>
            <i v-else class="ri-add-line"></i>
            {{ isCreating ? '创建中...' : '创建项目' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { open } from '@tauri-apps/plugin-dialog'
import type { ProjectConfig, DesignFile } from '../types'

interface Emits {
  (e: 'close'): void
  (e: 'create', config: ProjectConfig): void
}

const emit = defineEmits<Emits>()

const currentStep = ref(1)
const isDragging = ref(false)
const isCreating = ref(false)

const steps = [
  { id: 1, title: '基本信息' },
  { id: 2, title: '设计文件' },
  { id: 3, title: '工艺配置' },
  { id: 4, title: '确认创建' }
]

const pdkOptions = [
  {
    id: 'CS55_PDK',
    name: 'CS55 PDK',
    description: 'CS55 PDK for ICSPROUT 55',
    icon: 'ri-settings-3-line text-xl'
  }
]

const config = ref<ProjectConfig>({
  name: '',
  description: '',
  location: '',
  designFiles: [],
  topModule: '',
  pdk: 'CS55_PDK',
  technologyNode: 'CS55',
  targetFrequency: 100,
  constraintFiles: []
})

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      return config.value.name.trim() !== '' && config.value.location.trim() !== ''
    case 2:
      return config.value.designFiles.length > 0 && config.value.topModule.trim() !== ''
    case 3:
      return config.value.pdk !== ''
    default:
      return true
  }
})

const selectLocation = async () => {
  const result = await open({
    directory: true,
    multiple: false,
    title: '选择项目保存位置'
  })
  if (result) {
    config.value.location = result as string
  }
}

const selectDesignFiles = async () => {
  const result = await open({
    multiple: true,
    filters: [{
      name: 'HDL Files',
      extensions: ['v', 'sv', 'vhd', 'vhdl']
    }],
    title: '选择设计文件'
  })
  if (result) {
    const files = Array.isArray(result) ? result : [result]
    addFiles(files as string[])
  }
}

const handleFileDrop = (event: DragEvent) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files) {
    const paths = Array.from(files).map(f => f.name)
    // Note: In Tauri, we need to handle this differently
    console.log('Dropped files:', paths)
  }
}

const addFiles = (paths: string[]) => {
  for (const path of paths) {
    const name = path.split('/').pop() || path
    const ext = name.split('.').pop()?.toLowerCase()
    let type: DesignFile['type'] = 'other'

    if (ext === 'v') type = 'verilog'
    else if (ext === 'sv') type = 'systemverilog'
    else if (ext === 'vhd' || ext === 'vhdl') type = 'vhdl'

    // Avoid duplicates
    if (!config.value.designFiles.find(f => f.path === path)) {
      config.value.designFiles.push({
        id: crypto.randomUUID(),
        name,
        path,
        type
      })
    }
  }
}

const removeFile = (id: string) => {
  config.value.designFiles = config.value.designFiles.filter(f => f.id !== id)
}

const getPdkName = (id: string) => {
  return pdkOptions.find(p => p.id === id)?.name || id
}

const getNodeName = (node: string) => {
  const nodes: Record<string, string> = {
    'sky130': 'SkyWater 130nm',
    'gf180': 'GlobalFoundries 180nm',
    'asap7': 'ASAP 7nm',
    'nangate45': 'NanGate 45nm'
  }
  return nodes[node] || node || '-'
}

const nextStep = () => {
  if (currentStep.value < 4 && canProceed.value) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const createProject = async () => {
  isCreating.value = true
  try {
    emit('create', config.value)
  } finally {
    isCreating.value = false
  }
}
</script>

<style scoped>
/* Slide fade transition */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* List transition */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* Custom range slider */
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: var(--bg-secondary);
  border-radius: 8px;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--accent-color);
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

input[type="range"]::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--accent-color);
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
</style>
