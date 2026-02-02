<template>
  <div :class="[
    'flex w-full min-w-0',
    message.role === 'user' ? 'justify-end' : 'justify-start'
  ]">
    <!-- Info 消息 -->
    <div v-if="message.type === 'info' && message.infoData"
      class="w-full min-w-0 p-2 rounded-lg text-sm bg-(--bg-secondary) text-(--text-primary) border border-(--border-color) overflow-hidden">
      <!-- 标题栏 -->
      <div class="flex items-center gap-2 px-3 py-2 border-b border-(--border-color)">
        <i class="ri-file-list-3-line text-(--accent-color)"></i>
        <span class="font-semibold text-xs">{{ message.infoData.title }}</span>
        <span class="text-[10px] text-(--text-secondary) bg-(--bg-primary) px-2 py-0.5 rounded">
          {{ message.infoData.step }}
        </span>
      </div>

      <!-- 数据内容 - 直接显示表格 -->
      <div v-for="(item, index) in message.infoData.items" :key="index" class="info-content overflow-hidden">
        <!-- JSON 格式 - 简单对象渲染为表格 -->
        <div v-if="item.format === 'json' && isSimpleObject(item.content)" class="overflow-auto">
          <table class="w-full text-xs">
            <tbody>
              <tr v-for="(value, key) in item.content" :key="key"
                class="border-b border-(--border-color)/30 hover:bg-(--bg-primary)/30">
                <td class="py-2 px-3 font-medium text-(--text-secondary) whitespace-nowrap w-[40%]">{{ key }}</td>
                <td class="py-2 px-3 text-(--text-primary)">{{ formatValue(value) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- JSON 格式 - 复杂对象 -->
        <div v-else-if="item.format === 'json'" class="p-3 overflow-hidden">
          <pre
            class="text-[11px] bg-(--bg-primary) p-3 rounded whitespace-pre overflow-auto max-h-[400px] font-mono text-content-pre"><code>{{ JSON.stringify(item.content, null, 2) }}</code></pre>
        </div>

        <!-- CSV 格式 - 表格显示 -->
        <div v-else-if="item.format === 'csv'" class="overflow-auto max-h-[400px]">
          <table class="w-full text-xs border-collapse">
            <thead v-if="csvHeaders(item.content).length > 0" class="sticky top-0">
              <tr class="bg-(--bg-primary)">
                <th v-for="header in csvHeaders(item.content)" :key="header"
                  class="py-2 px-3 text-left font-medium text-(--text-secondary) border-b border-(--border-color)">
                  {{ header }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in csvRows(item.content)" :key="rowIndex"
                class="border-b border-(--border-color)/30 hover:bg-(--bg-primary)/30">
                <td v-for="(cell, cellIndex) in row" :key="cellIndex" class="py-2 px-3">
                  {{ cell }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 文本格式 -->
        <div v-else class="p-3 overflow-hidden">
          <pre
            class="text-[11px] bg-(--bg-primary) p-3 rounded whitespace-pre overflow-auto max-h-[350px] font-mono text-content-pre"><code>{{ item.content }}</code></pre>
        </div>
      </div>
    </div>

    <!-- 其他消息类型 -->
    <div v-else :class="[
      'max-w-[85%] rounded-lg text-sm',
      message.role === 'user'
        ? 'bg-(--accent-color) text-(--accent-text)'
        : 'bg-(--bg-secondary) text-(--text-primary) border border-(--border-color)'
    ]">
      <!-- 图片消息 -->
      <div v-if="message.type === 'image' && message.image" class="p-2">
        <p class="text-xs opacity-90">{{ message.image.label }}:</p>
        <p v-if="message.image.description" class="text-xs opacity-90 whitespace-pre-line mb-2">{{
          message.image.description }}</p>
        <div class="rounded-lg overflow-hidden mb-2">
          <img :src="message.image.url" :alt="message.image.label" class="w-full h-auto object-contain max-h-[400px]"
            loading="lazy" @load="handleImageLoad" />
        </div>
      </div>

      <!-- 文本消息 -->
      <div v-else class="px-4 py-2">
        <!-- 加载状态 -->
        <div v-if="message.status === 'loading' && !message.content" class="flex items-center gap-2">
          <div class="loading-dots flex gap-1">
            <span class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 0ms;"></span>
            <span class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 150ms;"></span>
            <span class="w-2 h-2 bg-current rounded-full animate-bounce" style="animation-delay: 300ms;"></span>
          </div>
          <span class="text-xs opacity-70">正在思考...</span>
        </div>

        <!-- 错误状态 -->
        <div v-else-if="message.status === 'error'" class="flex items-center gap-2 text-red-500">
          <i class="ri-error-warning-line"></i>
          <span>{{ message.content || '消息发送失败' }}</span>
        </div>

        <!-- 正常内容（Markdown 渲染） -->
        <div v-else class="markdown-body" v-html="renderedContent"></div>

        <!-- 流式加载时显示光标 -->
        <span v-if="message.status === 'loading' && message.content"
          class="inline-block w-2 h-4 bg-current animate-pulse ml-0.5"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import type { Message } from '../types'

const props = defineProps<{
  message: Message
}>()

const emit = defineEmits<{
  (e: 'img-load'): void
}>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const renderedContent = computed(() => {
  return md.render(props.message.content)
})

const handleImageLoad = () => {
  emit('img-load')
}

// 检查是否为简单对象（一层嵌套，可以用表格展示）
function isSimpleObject(obj: any): boolean {
  if (typeof obj !== 'object' || obj === null || Array.isArray(obj)) {
    return false
  }
  return Object.values(obj).every(v =>
    typeof v !== 'object' || v === null
  )
}

// 格式化值显示
function formatValue(value: any): string {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'number') {
    // 科学计数法格式化
    if (Math.abs(value) < 0.001 || Math.abs(value) > 10000) {
      return value.toExponential(3)
    }
    return value.toLocaleString()
  }
  return String(value)
}

// 解析 CSV 获取表头
function csvHeaders(content: string): string[] {
  if (typeof content !== 'string') return []
  const lines = content.trim().split('\n')
  if (lines.length === 0) return []
  return lines[0].split(',').map(h => h.trim())
}

// 解析 CSV 获取数据行
function csvRows(content: string): string[][] {
  if (typeof content !== 'string') return []
  const lines = content.trim().split('\n')
  if (lines.length <= 1) return []
  return lines.slice(1).map(line =>
    line.split(',').map(cell => cell.trim())
  )
}
</script>

<style scoped>
.markdown-body {
  line-height: 1.6;
  word-break: break-word;
}

.markdown-body :deep(p) {
  margin-bottom: 0.5rem;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
}

.markdown-body :deep(pre) {
  background-color: var(--bg-secondary);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5rem 0;
  border: 1px solid var(--border-color);
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
  display: block;
}

.markdown-body :deep(ul) {
  list-style-type: disc;
  padding-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(ol) {
  list-style-type: decimal;
  padding-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-body :deep(a) {
  color: var(--accent-color);
  text-decoration: underline;
}

.markdown-body :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
}

.markdown-body :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
}

.markdown-body :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(em) {
  font-style: italic;
}

.markdown-body :deep(u) {
  text-decoration: underline;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--accent-color);
  padding-left: 1rem;
  color: var(--text-secondary);
  font-style: italic;
  margin: 1rem 0;
  background-color: var(--bg-secondary);
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
  border-radius: 0 4px 4px 0;
}

/* 文本内容预格式化样式 - 防止撑开父容器 */
.text-content-pre {
  display: block;
  width: 0;
  min-width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.info-content {
  min-width: 0;
  max-width: 100%;
  width: 100%;
}

/* 确保 pre 和 code 元素不会撑开容器 */
.info-content pre {
  width: 0;
  min-width: 100%;
}

.info-content pre code {
  display: block;
}

/* 加载动画 */
.loading-dots span {
  animation: bounce 1s infinite;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-6px);
  }
}
</style>
