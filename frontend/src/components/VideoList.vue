<script setup lang="ts">
import type { VideoData } from '../types'

defineProps<{
  videos: VideoData[]
  loading: boolean
  message?: string
}>()

const formatDate = (timestamp: number): string => {
  if (!timestamp) return '--'
  const date = new Date(timestamp * 1000)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const formatNum = (n: number): string => {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}
</script>

<template>
  <div class="video-list-container">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">{{ message || '加载中...' }}</div>
    </div>

    <!-- Table -->
    <template v-else-if="videos.length > 0">
      <div class="result-count">共 <span>{{ videos.length }}</span> 个视频</div>

      <table class="video-table">
        <thead>
          <tr>
            <th class="col-index">#</th>
            <th class="col-cover">封面</th>
            <th class="col-title">标题</th>
            <th class="col-stat">👍</th>
            <th class="col-stat">💬</th>
            <th class="col-time">时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(v, i) in videos" :key="v.id">
            <td class="col-index">{{ i + 1 }}</td>
            <td class="col-cover">
              <a :href="v.video_url" target="_blank" class="video-cover">
                <img :src="v.cover" loading="lazy" />
              </a>
            </td>
            <td class="col-title">
              <a :href="v.video_url" target="_blank" class="video-title">{{ v.desc || '无标题' }}</a>
            </td>
            <td class="col-stat"><span class="stat-num">{{ formatNum(v.digg_count) }}</span></td>
            <td class="col-stat"><span class="stat-num">{{ formatNum(v.comment_count) }}</span></td>
            <td class="col-time"><span class="time-text">{{ formatDate(v.create_time) }}</span></td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- Empty -->
    <div v-else class="empty-state">
      <div class="empty-icon">🎬</div>
      <h3>暂无数据</h3>
      <p>输入UP主链接查询</p>
    </div>
  </div>
</template>
