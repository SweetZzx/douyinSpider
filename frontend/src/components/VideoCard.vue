<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { VideoData } from '../types'
import { extractAudio, getVideoAudio } from '../services/api'

const props = defineProps<{
  video: VideoData
  index: number
}>()

const emit = defineEmits<{
  audioExtracted: [videoId: number]
}>()

const extracting = ref(false)
const audioStatus = ref<'not_extracted' | 'processing' | 'completed' | 'failed'>('not_extracted')

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

const handleExtractAudio = async () => {
  if (audioStatus.value === 'processing') {
    ElMessage.warning('正在提取中，请稍候...')
    return
  }

  extracting.value = true
  try {
    const result = await extractAudio([props.video.id])
    if (result.success) {
      ElMessage.success(result.message)
      audioStatus.value = 'processing'
      emit('audioExtracted', props.video.id)

      // 轮询检查提取状态
      checkAudioStatus()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提取失败')
  } finally {
    extracting.value = false
  }
}

const checkAudioStatus = async () => {
  try {
    const result = await getVideoAudio(props.video.id)
    if (result.has_audio) {
      audioStatus.value = 'completed'
      ElMessage.success('音频提取完成！')
    } else if (result.status === 'failed') {
      audioStatus.value = 'failed'
      ElMessage.error('音频提取失败: ' + result.error_message)
    } else {
      // 继续轮询
      setTimeout(checkAudioStatus, 3000)
    }
  } catch (error) {
    console.error('检查音频状态失败:', error)
  }
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

    <!-- 音频提取按钮 -->
    <div class="video-actions">
      <el-button
        v-if="audioStatus === 'not_extracted' || audioStatus === 'failed'"
        type="warning"
        size="small"
        :loading="extracting"
        @click="handleExtractAudio"
      >
        提取音频
      </el-button>
      <el-tag v-else-if="audioStatus === 'processing'" type="warning" size="small">
        提取中...
      </el-tag>
      <el-tag v-else-if="audioStatus === 'completed'" type="success" size="small">
        ✓ 已提取
      </el-tag>
    </div>
  </div>
</template>
