<script setup lang="ts">
import type { VideoData } from '../types'

defineProps<{
  video: VideoData
  index: number
}>()

const formatDate = (timestamp: number): string => {
  if (!timestamp) return '--'
  const date = new Date(timestamp * 1000)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${month}-${day}`
}

const formatNumber = (num: number): string => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}
</script>

<template>
  <div class="video-list-item">
    <!-- 序号 -->
    <div class="video-index">{{ index + 1 }}</div>

    <!-- 封面 -->
    <a :href="video.video_url" target="_blank" class="video-cover">
      <img :src="video.cover" :alt="video.desc" loading="lazy" />
    </a>

    <!-- 标题 -->
    <div class="video-info">
      <a :href="video.video_url" target="_blank" class="video-title">
        {{ video.desc || '无标题' }}
      </a>
    </div>

    <!-- 点赞 -->
    <div class="video-stat">{{ formatNumber(video.digg_count) }}</div>

    <!-- 评论 -->
    <div class="video-stat">{{ formatNumber(video.comment_count) }}</div>

    <!-- 时间 -->
    <div class="video-time">{{ formatDate(video.create_time) }}</div>
  </div>
</template>
