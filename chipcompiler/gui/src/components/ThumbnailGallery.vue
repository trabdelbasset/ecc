<template>
  <!-- 列表视图 -->
  <div class="flex flex-col h-full bg-(--bg-primary)">
    <!-- 标题 -->
    <div class="flex items-center justify-between px-4 py-1 border-b border-(--border-color)">
      <div class="flex items-center gap-2">
        <i class="ri-stack-line text-(--text-secondary)"></i>
        <h3 class="text-sm font-semibold text-(--text-primary)">Information</h3>
      </div>
      <div class="flex items-center gap-2">
        <button class="p-1 text-(--text-secondary) hover:text-(--text-primary) transition-colors">
          <i class="ri-filter-3-line text-sm"></i>
        </button>
        <button class="p-1 text-(--text-secondary) hover:text-(--text-primary) transition-colors">
          <i class="ri-more-2-line text-sm"></i>
        </button>
      </div>
    </div>

    <!-- 缩略图网格 2x3 -->
    <div class="flex-1 p-2 min-h-0 overflow-hidden">
      <div class="grid grid-cols-3 gap-2 h-full" style="grid-template-rows: 1fr 1fr;">
        <div v-for="thumb in thumbnails.slice(0, 6)" :key="thumb.id" class="group cursor-pointer flex flex-col min-h-0"
          @click="handleImageClick(thumb)">
          <div
            class="flex-1 min-h-0 bg-(--bg-secondary) rounded border border-(--border-color) flex items-center justify-center overflow-hidden group-hover:border-(--accent-color) transition-all shadow-sm">
            <img v-if="thumb.thumbnailUrl && !imageError.has(thumb.id)" :src="thumb.thumbnailUrl" :alt="thumb.label"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy"
              decoding="async" @error="handleImageError(thumb.id)" />
            <div v-else class="flex flex-col items-center gap-1">
              <i class="ri-image-line text-xl text-(--text-secondary)"></i>
              <span class="text-[8px] text-(--text-secondary)">Loading...</span>
            </div>
          </div>
          <p class="text-[9px] font-medium text-(--text-primary) truncate text-center mt-1 shrink-0">
            {{ thumb.label }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Thumbnail } from '../types'
import { useMessageStore } from '../stores/messageStore'

const messageStore = useMessageStore()
const selectedImage = ref<Thumbnail | null>(null)
const imageError = ref<Set<number>>(new Set())
const zoom = ref(100)

// Place 阶段特征分析图 - 6 张代表性图片
// const featureBasePath = '/data/ics55_00001/place_iEDA/feature'

const thumbnails: Thumbnail[] = [
//   {
//     id: 1,
//     label: '单元密度图',
//     description: `Cell Density Avg Mean: 3.535e-01, 
// Avg Max: 1.000e+00 
// Avg Hotspot Ratio (>90th percentile): 9.1%`,
//     thumbnailUrl: `${featureBasePath}/density_map/place_allcell_density.png`,
//     imageUrl: `${featureBasePath}/density_map/place_allcell_density.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG',
//   },
//   {
//     id: 2,
//     label: '引脚密度图',
//     description: 'Stdcell Pin Density - 标准单元引脚分布热点',
//     thumbnailUrl: `${featureBasePath}/density_map/place_stdcell_pin_density.png`,
//     imageUrl: `${featureBasePath}/density_map/place_stdcell_pin_density.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG'
//   },
//   {
//     id: 3,
//     label: '网络密度图',
//     description: 'All Net Density - 网络连接分布',
//     thumbnailUrl: `${featureBasePath}/density_map/place_allnet_density.png`,
//     imageUrl: `${featureBasePath}/density_map/place_allnet_density.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG'
//   },
//   {
//     id: 4,
//     label: '拥塞预测图',
//     description: `Congestion Avg Mean: -9.242e+00, 
// Avg Max: 5.000e+01 
// Avg Hotspot Ratio (>90th percentile): 9.2%`,
//     thumbnailUrl: `${featureBasePath}/egr_congestion_map/place_egr_union_overflow.png`,
//     imageUrl: `${featureBasePath}/egr_congestion_map/place_egr_union_overflow.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG'
//   },
//   {
//     id: 5,
//     label: '布线边距图',
//     description: 'Union Margin - 布线空间余量分析',
//     thumbnailUrl: `${featureBasePath}/margin_map/place_union_margin.png`,
//     imageUrl: `${featureBasePath}/margin_map/place_union_margin.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG'
//   },
//   {
//     id: 6,
//     label: 'RUDY 预测图',
//     description: 'RUDY Union - 线密度预测分析',
//     thumbnailUrl: `${featureBasePath}/RUDY_map/place_rudy_union.png`,
//     imageUrl: `${featureBasePath}/RUDY_map/place_rudy_union.png`,
//     size: '',
//     dimensions: '',
//     format: 'PNG'
//   },
]

const handleImageClick = (thumb: Thumbnail) => {
  selectedImage.value = thumb
  zoom.value = 100 // 重置缩放
  // 将图片添加到消息流中
  messageStore.addImageMessage(thumb)
}

const handleImageError = (id: number) => {
  imageError.value = new Set(imageError.value).add(id)
}

</script>
