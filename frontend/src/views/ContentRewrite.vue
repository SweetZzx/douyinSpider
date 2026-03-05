<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, DocumentCopy, Edit } from '@element-plus/icons-vue'
import { getVideos, getAuthors, getGroups, extractAudio, getVideoAudio, transcribeVideos, getVideoTranscript, rewriteVideoContent, updateVideoTranscript, updateVideoRewrite, getPromptTemplates } from '../services/api'
import type { VideoData, Author, AuthorGroup, PromptTemplate } from '../types'

const videos = ref<VideoData[]>([])
const authors = ref<Author[]>([])
const groups = ref<AuthorGroup[]>([])
const loading = ref(false)
const extracting = ref<Record<number, boolean>>({})
const audioStatus = ref<Record<number, 'not_extracted' | 'processing' | 'completed' | 'failed'>>({})
const transcribing = ref<Record<number, boolean>>({})
const transcriptStatus = ref<Record<number, 'not_transcribed' | 'processing' | 'completed' | 'failed'>>({})
const transcripts = ref<Record<number, string>>({})
const rewriteStatus = ref<Record<number, 'not_rewritten' | 'processing' | 'completed' | 'failed'>>({})
const rewrites = ref<Record<number, string>>({})
const transcriptDialogVisible = ref(false)
const rewriteDialogVisible = ref(false)
const audioDialogVisible = ref(false)
const currentAudioUrl = ref('')
const currentTranscript = ref('')
const currentRewrite = ref('')
const currentVideoTitle = ref('')
const currentVideoId = ref<number | null>(null)
const currentVideoDesc = ref('')
const editingTranscript = ref(false)
const editingRewrite = ref(false)
const correctingTranscript = ref(false)
const correctingRewrite = ref(false)
const autoCorrectingVideos = ref<Set<number>>(new Set())  // 正在自动纠错的视频ID集合
const audioPaths = ref<Record<number, string>>({})
const selectedVideos = ref<VideoData[]>([])
const autoCorrectTranscript = ref(true)  // 批量提取时自动智能纠错开关（默认开启）

// 提示词模板相关
const promptTemplates = ref<PromptTemplate[]>([])
const selectedTemplateId = ref<number | null>(null)

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选相关
const filterType = ref<'all' | 'group' | 'author'>('all')
const selectedGroupId = ref<number | null>(null)
const selectedAuthorId = ref<number | null>(null)

// 筛选选项
const filterOptions = computed(() => {
  const options: { value: string; label: string; type: 'all' | 'group' | 'author'; id?: number }[] = [
    { value: 'all', label: '全部视频', type: 'all' }
  ]

  // 添加分组选项
  groups.value.forEach(g => {
    const count = authors.value.filter(a => a.group_id === g.id).length
    options.push({
      value: `group_${g.id}`,
      label: `📁 ${g.name} (${count}人)`,
      type: 'group',
      id: g.id
    })
  })

  // 添加UP主选项（按分组归类）
  const ungroupedAuthors = authors.value.filter(a => !a.group_id)
  if (ungroupedAuthors.length > 0) {
    options.push({
      value: 'group_none',
      label: '📁 未分组',
      type: 'group',
      id: 0
    })
  }

  // 添加单个UP主
  authors.value.forEach(a => {
    options.push({
      value: `author_${a.id}`,
      label: `👤 ${a.nickname || '未知用户'}`,
      type: 'author',
      id: a.id
    })
  })

  return options
})

const selectedFilter = ref('all')

const handleFilterChange = (value: string) => {
  if (value === 'all') {
    filterType.value = 'all'
    selectedGroupId.value = null
    selectedAuthorId.value = null
  } else if (value === 'group_none') {
    filterType.value = 'group'
    selectedGroupId.value = 0
    selectedAuthorId.value = null
  } else if (value.startsWith('group_')) {
    filterType.value = 'group'
    const groupId = parseInt(value.replace('group_', ''))
    selectedGroupId.value = groupId
    selectedAuthorId.value = null
  } else if (value.startsWith('author_')) {
    filterType.value = 'author'
    selectedAuthorId.value = parseInt(value.replace('author_', ''))
    selectedGroupId.value = null
  }
  page.value = 1
  loadVideos()
}

const formatDate = (ts: number) => {
  if (!ts) return '--'
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const loadVideos = async () => {
  loading.value = true
  try {
    const [authorData, groupData] = await Promise.all([
      getAuthors(),
      getGroups()
    ])
    authors.value = authorData
    groups.value = groupData

    const filter: { authorId?: number; groupId?: number } = {}
    if (filterType.value === 'author' && selectedAuthorId.value) {
      filter.authorId = selectedAuthorId.value
    } else if (filterType.value === 'group' && selectedGroupId.value !== null) {
      filter.groupId = selectedGroupId.value
    }

    const offset = (page.value - 1) * pageSize.value
    const videoData = await getVideos(pageSize.value, offset, Object.keys(filter).length > 0 ? filter : undefined)
    videos.value = videoData.videos || []
    total.value = videoData.total || 0

    for (const video of videos.value) {
      // 加载已有的仿写结果
      if (video.rewritten_text) {
        rewrites.value[video.id] = video.rewritten_text
        rewriteStatus.value[video.id] = 'completed'
      }

      if (!audioStatus.value[video.id]) {
        getVideoAudio(video.id).then(result => {
          if (result.has_audio) {
            audioStatus.value[video.id] = 'completed'
            if (result.audio_url) {
              audioPaths.value[video.id] = result.audio_url
            }
          } else if (result.status === 'failed') {
            audioStatus.value[video.id] = 'failed'
          } else {
            audioStatus.value[video.id] = 'not_extracted'
          }
        }).catch(() => {
          audioStatus.value[video.id] = 'not_extracted'
        })
      }
      if (!transcriptStatus.value[video.id]) {
        getVideoTranscript(video.id).then(result => {
          if (result.has_transcript) {
            transcriptStatus.value[video.id] = 'completed'
            transcripts.value[video.id] = result.text || ''
          } else if (result.status === 'failed') {
            transcriptStatus.value[video.id] = 'failed'
          } else {
            transcriptStatus.value[video.id] = 'not_transcribed'
          }
        }).catch(() => {
          transcriptStatus.value[video.id] = 'not_transcribed'
        })
      }
    }
  } catch (e) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 音频提取相关函数
const handleExtractAudio = async (video: VideoData) => {
  if (audioStatus.value[video.id] === 'processing') {
    ElMessage.warning('正在提取中，请稍候...')
    return
  }

  extracting.value[video.id] = true
  try {
    const result = await extractAudio([video.id])
    if (result.success) {
      ElMessage.success(result.message)
      audioStatus.value[video.id] = 'processing'
      checkAudioStatus(video)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提取失败')
  } finally {
    extracting.value[video.id] = false
  }
}

const checkAudioStatus = async (video: VideoData) => {
  try {
    const result = await getVideoAudio(video.id)
    if (result.has_audio) {
      audioStatus.value[video.id] = 'completed'
      if (result.audio_url) {
        audioPaths.value[video.id] = result.audio_url
      }
      ElMessage.success('音频提取完成！')
    } else if (result.status === 'failed') {
      audioStatus.value[video.id] = 'failed'
      ElMessage.error('音频提取失败: ' + result.error_message)
    } else {
      setTimeout(() => checkAudioStatus(video), 3000)
    }
  } catch (error) {
    console.error('检查音频状态失败:', error)
  }
}

// 批量提取音频
const handleBatchExtractAudio = async () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择视频')
    return
  }

  const videosToExtract = selectedVideos.value.filter(v => audioStatus.value[v.id] !== 'processing' && audioStatus.value[v.id] !== 'completed')
  if (videosToExtract.length === 0) {
    ElMessage.warning('所选视频均已提取或正在提取中')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要提取 ${videosToExtract.length} 个视频的音频吗？`,
      '批量提取确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const videoIds = videosToExtract.map(v => v.id)
    const result = await extractAudio(videoIds)
    if (result.success) {
      ElMessage.success(result.message)
      videosToExtract.forEach(v => {
        audioStatus.value[v.id] = 'processing'
        checkAudioStatus(v)
      })
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '提取失败')
    }
  }
}

// 语音转写相关函数
const handleTranscribe = async (video: VideoData) => {
  const audioResult = await getVideoAudio(video.id)
  if (!audioResult.has_audio) {
    ElMessage.warning('请先提取音频再进行转写')
    return
  }

  const audioDuration = audioResult.duration || 0
  const maxDuration = 180

  if (audioDuration > maxDuration) {
    const minutes = Math.floor(audioDuration / 60)
    const seconds = Math.floor(audioDuration % 60)
    ElMessage.warning(`语音转写仅支持3分钟内的音频\n当前音频: ${minutes}分${seconds}秒`)
    return
  }

  if (transcriptStatus.value[video.id] === 'processing') {
    ElMessage.warning('正在转写中，请稍候...')
    return
  }

  transcribing.value[video.id] = true
  try {
    const result = await transcribeVideos([video.id])
    if (result.success) {
      ElMessage.success(result.message)
      transcriptStatus.value[video.id] = 'processing'
      checkTranscriptStatus(video)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '转写失败')
  } finally {
    transcribing.value[video.id] = false
  }
}

const checkTranscriptStatus = async (video: any) => {
  try {
    const result = await getVideoTranscript(video.id)
    if (result.has_transcript) {
      transcriptStatus.value[video.id] = 'completed'
      transcripts.value[video.id] = result.text || ''

      // 如果开启了自动纠错，则进行智能纠错
      if (video.autoCorrect) {
        video.autoCorrect = false // 清除标志
        await performAutoCorrect(video.id)
      } else {
        ElMessage.success('语音转写完成！')
      }
    } else if (result.status === 'failed') {
      transcriptStatus.value[video.id] = 'failed'
      ElMessage.error('语音转写失败: ' + result.error_message)
    } else {
      setTimeout(() => checkTranscriptStatus(video), 3000)
    }
  } catch (error) {
    console.error('检查转写状态失败:', error)
  }
}

// 自动智能纠错
const performAutoCorrect = async (videoId: number) => {
  try {
    const originalText = transcripts.value[videoId] || ''
    if (!originalText || !originalText.trim()) {
      ElMessage.warning('文案内容为空，跳过智能纠错')
      return
    }

    // 标记为正在纠错
    autoCorrectingVideos.value.add(videoId)

    const result = await updateVideoTranscript(videoId, originalText, true)
    if (result.success) {
      transcripts.value[videoId] = result.text
      ElMessage.success(`视频 ${videoId} 智能纠错完成！`)
    }
  } catch (error: any) {
    console.error('自动纠错失败:', error)
    ElMessage.error(`视频 ${videoId} 智能纠错失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    // 移除纠错标记
    autoCorrectingVideos.value.delete(videoId)
  }
}

// 批量转写
const handleBatchTranscribe = async () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择视频')
    return
  }

  const videosToTranscribe = selectedVideos.value.filter(v =>
    audioStatus.value[v.id] === 'completed' &&
    transcriptStatus.value[v.id] !== 'processing' &&
    transcriptStatus.value[v.id] !== 'completed'
  )

  if (videosToTranscribe.length === 0) {
    ElMessage.warning('没有可转写的视频（请先提取音频）')
    return
  }

  try {
    const confirmMessage = autoCorrectTranscript.value
      ? `确定要转写 ${videosToTranscribe.length} 个视频的文案吗？\n转写完成后将自动进行智能纠错。`
      : `确定要转写 ${videosToTranscribe.length} 个视频的文案吗？`

    await ElMessageBox.confirm(
      confirmMessage,
      '批量转写确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )

    const videoIds = videosToTranscribe.map(v => v.id)
    const result = await transcribeVideos(videoIds)
    if (result.success) {
      ElMessage.success(result.message)
      videosToTranscribe.forEach(v => {
        transcriptStatus.value[v.id] = 'processing'
        // 标记是否需要自动纠错
        if (autoCorrectTranscript.value) {
          v.autoCorrect = true
        }
        checkTranscriptStatus(v)
      })
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '转写失败')
    }
  }
}

// 文案仿写相关函数
const handleRewrite = async (video: VideoData) => {
  if (transcriptStatus.value[video.id] !== 'completed') {
    ElMessage.warning('请先提取文案再进行仿写')
    return
  }

  const originalText = transcripts.value[video.id] || ''
  if (!originalText || !originalText.trim()) {
    ElMessage.warning('原文案内容为空，无法仿写')
    return
  }

  if (rewriteStatus.value[video.id] === 'processing') {
    ElMessage.warning('正在仿写中，请稍候...')
    return
  }

  rewriteStatus.value[video.id] = 'processing'
  try {
    const result = await rewriteVideoContent(video.id, selectedTemplateId.value || undefined)
    if (result.success) {
      rewrites.value[video.id] = result.rewritten_text
      rewriteStatus.value[video.id] = 'completed'
      ElMessage.success('文案仿写完成！')
    }
  } catch (error: any) {
    rewriteStatus.value[video.id] = 'failed'
    ElMessage.error(error.response?.data?.detail || '仿写失败')
  }
}

const copyTranscript = () => {
  navigator.clipboard.writeText(currentTranscript.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const copyRewrite = () => {
  navigator.clipboard.writeText(currentRewrite.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const viewAudio = async (video: VideoData) => {
  try {
    const result = await getVideoAudio(video.id)
    if (result.has_audio && result.audio_url) {
      currentAudioUrl.value = result.audio_url
      currentVideoTitle.value = video.desc || '无标题'
      audioDialogVisible.value = true
    } else {
      ElMessage.warning('音频文件不存在')
    }
  } catch (error: any) {
    ElMessage.error('获取音频失败')
  }
}

const downloadAudio = async (video: VideoData) => {
  try {
    const result = await getVideoAudio(video.id)
    if (result.has_audio && result.audio_url) {
      // 创建一个隐藏的a标签来下载文件
      const link = document.createElement('a')
      link.href = result.audio_url
      link.download = `audio_${video.id}.mp3`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      ElMessage.success('下载已开始')
    } else {
      ElMessage.warning('音频文件不存在')
    }
  } catch (error: any) {
    ElMessage.error('下载失败')
  }
}

const viewTranscript = (video: VideoData) => {
  currentTranscript.value = transcripts.value[video.id] || ''
  currentVideoTitle.value = video.desc || '无标题'
  currentVideoId.value = video.id
  currentVideoDesc.value = video.desc || ''
  transcriptDialogVisible.value = true
}

const viewRewrite = (video: VideoData) => {
  currentRewrite.value = rewrites.value[video.id] || ''
  currentVideoTitle.value = video.desc || '无标题'
  currentVideoId.value = video.id
  currentVideoDesc.value = video.desc || ''
  rewriteDialogVisible.value = true
}

// 智能纠错原文案
const handleCorrectTranscript = async () => {
  if (!currentVideoId.value) return

  const originalText = currentTranscript.value.trim()
  if (!originalText) {
    ElMessage.warning('文案内容为空，无法纠错')
    return
  }

  correctingTranscript.value = true
  try {
    // 调用智能纠错API
    const result = await updateVideoTranscript(currentVideoId.value, originalText, true)
    if (result.success) {
      currentTranscript.value = result.text
      transcripts.value[currentVideoId.value] = result.text
      ElMessage.success(result.message || '智能纠错完成！')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '智能纠错失败')
  } finally {
    correctingTranscript.value = false
  }
}

// 智能纠错仿写文案
const handleCorrectRewrite = async () => {
  if (!currentVideoId.value) return

  const originalText = currentRewrite.value.trim()
  if (!originalText) {
    ElMessage.warning('文案内容为空，无法纠错')
    return
  }

  correctingRewrite.value = true
  try {
    const context = currentVideoDesc.value ? `视频简介：${currentVideoDesc.value}\n\n` : ''
    const prompt = `${context}请对以下仿写的文案进行智能纠错，修正错别字、标点符号和语法错误，保持原意不变。只返回纠错后的文案，不要任何解释。\n\n文案：\n${originalText}`

    const result = await updateVideoRewrite(currentVideoId.value, originalText, prompt)
    if (result.success) {
      currentRewrite.value = result.rewritten_text
      rewrites.value[currentVideoId.value] = result.rewritten_text
      ElMessage.success('智能纠错完成！')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '智能纠错失败')
  } finally {
    correctingRewrite.value = false
  }
}

// 重新提取文案
const handleReExtractTranscript = async () => {
  if (!currentVideoId.value) return

  try {
    await ElMessageBox.confirm(
      '确定要重新提取文案吗？这将覆盖当前的文案内容。',
      '重新提取确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const result = await transcribeVideos([currentVideoId.value], true)  // force=true 强制重新提取
    if (result.success) {
      ElMessage.success('开始重新提取文案...')
      transcriptStatus.value[currentVideoId.value] = 'processing'
      transcriptDialogVisible.value = false

      // 查找对应的视频对象并检查状态
      const video = videos.value.find(v => v.id === currentVideoId.value)
      if (video) {
        checkTranscriptStatus(video)
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重新提取失败')
    }
  }
}

// 保存原文案
const handleSaveTranscript = async () => {
  if (!currentVideoId.value) return

  const text = currentTranscript.value.trim()
  if (!text) {
    ElMessage.warning('文案内容不能为空')
    return
  }

  editingTranscript.value = true
  try {
    const result = await updateVideoTranscript(currentVideoId.value, text)
    if (result.success) {
      transcripts.value[currentVideoId.value] = result.text
      ElMessage.success(result.message || '文案保存成功！')
      transcriptDialogVisible.value = false
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    editingTranscript.value = false
  }
}

// 保存仿写文案
const handleSaveRewrite = async () => {
  if (!currentVideoId.value) return

  const text = currentRewrite.value.trim()
  if (!text) {
    ElMessage.warning('文案内容不能为空')
    return
  }

  editingRewrite.value = true
  try {
    const result = await updateVideoRewrite(currentVideoId.value, text)
    if (result.success) {
      rewrites.value[currentVideoId.value] = result.rewritten_text
      ElMessage.success(result.message || '文案保存成功！')
      rewriteDialogVisible.value = false
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    editingRewrite.value = false
  }
}

const handleSelectionChange = (selection: VideoData[]) => {
  selectedVideos.value = selection
}

// 移动端复选框处理
const handleMobileCheckboxChange = (video: VideoData, checked: boolean) => {
  if (checked) {
    if (!selectedVideos.value.some(v => v.id === video.id)) {
      selectedVideos.value.push(video)
    }
  } else {
    selectedVideos.value = selectedVideos.value.filter(v => v.id !== video.id)
  }
}

// 智能截断文本到3行（基于字符数估算）
const truncateToThreeLines = (text: string): string => {
  if (!text) return ''
  // 估算：每行约12个中文字符，3行约35字符
  const maxChars = 35
  if (text.length <= maxChars) return text
  return text.substring(0, maxChars) + '...'
}

// 加载提示词模板
const loadPromptTemplates = async () => {
  try {
    const result = await getPromptTemplates()
    if (result.success) {
      promptTemplates.value = result.templates
      // 自动选择默认的仿写模板
      const defaultTemplate = result.templates.find(t => t.is_default && t.category === 'rewrite')
      if (defaultTemplate) {
        selectedTemplateId.value = defaultTemplate.id
      }
    }
  } catch (e) {
    console.error('加载提示词模板失败:', e)
  }
}

onMounted(() => {
  loadVideos()
  loadPromptTemplates()
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">文案仿写</h2>
      <div class="page-actions">
        <el-select
          v-model="selectedTemplateId"
          placeholder="选择提示词模板"
          clearable
          class="template-selector"
        >
          <el-option
            v-for="template in promptTemplates.filter(t => t.category === 'rewrite')"
            :key="template.id"
            :label="template.name"
            :value="template.id"
          >
            <div class="template-option">
              <span>{{ template.name }}</span>
              <el-tag v-if="template.is_default" type="success" size="small" style="margin-left: 8px">
                默认
              </el-tag>
            </div>
          </el-option>
        </el-select>
        <el-select
          v-model="selectedFilter"
          placeholder="筛选"
          class="filter-select"
          @change="handleFilterChange"
          filterable
          clearable
        >
          <el-option
            v-for="opt in filterOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-button @click="loadVideos" :loading="loading">
          <el-icon><Refresh /></el-icon>
          <span class="btn-text">刷新</span>
        </el-button>
      </div>
    </div>

    <!-- 视频列表 -->
    <el-card shadow="never" class="video-card">
      <template #header>
        <div class="card-header">
          <span>共 <b>{{ total }}</b> 个视频</span>
          <div class="batch-actions">
            <el-button
              type="primary"
              size="small"
              @click="handleBatchExtractAudio"
              :disabled="selectedVideos.length === 0"
            >
              <span class="btn-text-mobile">批量提取音频</span>
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handleBatchTranscribe"
              :disabled="selectedVideos.length === 0"
            >
              <span class="btn-text-mobile">批量提取文案</span>
            </el-button>
            <div class="smart-correct-toggle">
              <span class="toggle-label">智能纠错</span>
              <el-switch
                v-model="autoCorrectTranscript"
                size="small"
                inline-prompt
                active-text="开"
                inactive-text="关"
              />
            </div>
          </div>
        </div>
      </template>

      <!-- 移动端卡片列表 -->
      <div v-loading="loading" class="video-list-mobile">
        <div
          v-for="video in videos"
          :key="video.id"
          class="video-card-mobile"
        >
          <!-- 头部：复选框 + 图片 + 标题 -->
          <div class="mobile-card-header">
            <el-checkbox
              :model-value="selectedVideos.some(v => v.id === video.id)"
              @change="(val: boolean) => handleMobileCheckboxChange(video, val)"
              class="mobile-checkbox"
            />
            <div class="mobile-cover-wrapper">
              <img :src="video.cover" class="mobile-cover" />
            </div>
            <div class="mobile-title-section">
              <div class="mobile-title">{{ video.desc || '无标题' }}</div>
              <div class="mobile-meta">
                <span>👤 {{ video.author?.nickname || '未知' }}</span>
                <span>📅 {{ formatDate(video.create_time) }}</span>
              </div>
            </div>
          </div>

          <!-- 操作区域 -->
          <div class="mobile-actions-section">
            <!-- 音频 -->
            <div class="mobile-action-item">
              <div class="action-label">🎵 音频</div>
              <div v-if="audioStatus[video.id] === 'processing'" class="status-badge processing">
                <el-icon class="is-loading"><Refresh /></el-icon>
                提取中
              </div>
              <div v-else-if="audioStatus[video.id] === 'completed'" class="action-buttons">
                <el-button type="success" size="small" link @click="viewAudio(video)">
                  查看
                </el-button>
                <el-divider direction="vertical" />
                <el-button type="primary" size="small" link @click="downloadAudio(video)">
                  下载
                </el-button>
              </div>
              <el-button
                v-else
                type="primary"
                size="small"
                :loading="extracting[video.id]"
                @click="handleExtractAudio(video)"
              >
                提取
              </el-button>
            </div>

            <!-- 原文案 -->
            <div class="mobile-action-item">
              <div class="action-label">📝 原文案</div>
              <div v-if="autoCorrectingVideos.has(video.id)" class="status-badge processing">
                纠错中...
              </div>
              <div v-else-if="transcriptStatus[video.id] === 'processing'" class="status-badge processing">
                转写中...
              </div>
              <div v-else-if="transcriptStatus[video.id] === 'completed'" class="text-preview">
                <div class="clickable-text" @click="viewTranscript(video)">
                  {{ truncateToThreeLines(transcripts[video.id] || '') }}
                </div>
              </div>
              <div v-else class="action-buttons">
                <el-button
                  v-if="audioStatus[video.id] === 'completed'"
                  type="primary"
                  size="small"
                  :loading="transcribing[video.id]"
                  @click="handleTranscribe(video)"
                >
                  提取
                </el-button>
                <span v-else class="pending-text">未提取音频</span>
              </div>
            </div>

            <!-- 文案仿写 -->
            <div class="mobile-action-item">
              <div class="action-label">✨ 仿写</div>
              <div v-if="rewriteStatus[video.id] === 'processing'" class="status-badge processing">
                仿写中...
              </div>
              <div v-else-if="rewriteStatus[video.id] === 'completed'" class="text-preview">
                <div class="clickable-text" @click="viewRewrite(video)">
                  {{ truncateToThreeLines(rewrites[video.id] || '') }}
                </div>
              </div>
              <div v-else class="action-buttons">
                <el-button
                  v-if="transcriptStatus[video.id] === 'completed'"
                  type="success"
                  size="small"
                  @click="handleRewrite(video)"
                >
                  <el-icon><Edit /></el-icon>
                  仿写
                </el-button>
                <span v-else class="pending-text">请先提取文案</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- PC端表格 -->
      <el-table
        :data="videos"
        v-loading="loading"
        stripe
        class="content-rewrite-table"
        :style="{ width: '100%', tableLayout: 'fixed' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />

        <el-table-column label="视频" min-width="250">
          <template #default="{ row }">
            <div class="video-info">
              <img :src="row.cover" class="video-cover" />
              <div class="video-details">
                <div class="video-title">{{ row.desc || '无标题' }}</div>
                <div class="video-meta">
                  <span>👤 {{ row.author?.nickname || '未知' }}</span>
                  <span>📅 {{ formatDate(row.create_time) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="音频" width="140" align="center">
          <template #default="{ row }">
            <div v-if="audioStatus[row.id] === 'processing'" class="audio-status">
              <el-icon class="is-loading"><Refresh /></el-icon>
              <span>提取中...</span>
            </div>
            <div v-else-if="audioStatus[row.id] === 'completed'" class="audio-actions">
              <el-button type="success" size="small" link @click="viewAudio(row)">
                查看
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="primary" size="small" link @click="downloadAudio(row)">
                下载
              </el-button>
            </div>
            <el-button
              v-else
              type="primary"
              size="small"
              :loading="extracting[row.id]"
              @click="handleExtractAudio(row)"
            >
              提取音频
            </el-button>
          </template>
        </el-table-column>

        <el-table-column label="原文案" min-width="200">
          <template #default="{ row }">
            <div v-if="autoCorrectingVideos.has(row.id)" class="status-processing">
              纠错中...
            </div>
            <div v-else-if="transcriptStatus[row.id] === 'processing'" class="status-processing">
              转写中...
            </div>
            <div v-else-if="transcriptStatus[row.id] === 'completed'" class="transcript-preview">
              <div
                class="clickable-text"
                @click="viewTranscript(row)"
                title="点击查看完整内容"
              >
                {{ truncateToThreeLines(transcripts[row.id] || '') }}
              </div>
            </div>
            <div v-else class="status-pending">
              <el-button
                v-if="audioStatus[row.id] === 'completed'"
                type="primary"
                size="small"
                :loading="transcribing[row.id]"
                @click="handleTranscribe(row)"
              >
                提取文案
              </el-button>
              <span v-else>未提取音频</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="文案仿写" min-width="200">
          <template #default="{ row }">
            <div v-if="rewriteStatus[row.id] === 'processing'" class="status-processing">
              仿写中...
            </div>
            <div v-else-if="rewriteStatus[row.id] === 'completed'" class="rewrite-preview">
              <div
                class="clickable-text"
                @click="viewRewrite(row)"
                title="点击查看完整内容"
              >
                {{ truncateToThreeLines(rewrites[row.id] || '') }}
              </div>
            </div>
            <div v-else class="status-pending">
              <el-button
                v-if="transcriptStatus[row.id] === 'completed'"
                type="success"
                size="small"
                @click="handleRewrite(row)"
              >
                <el-icon><Edit /></el-icon>
                文案仿写
              </el-button>
              <span v-else>请先提取文案</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          background
        />
      </div>
    </el-card>

    <!-- 原文案查看弹窗 -->
    <el-dialog
      v-model="transcriptDialogVisible"
      :title="`📝 ${currentVideoTitle} - 原文案`"
      width="60%"
      :style="{ maxWidth: '700px' }"
    >
      <el-input
        v-model="currentTranscript"
        type="textarea"
        :rows="15"
        placeholder="暂无文案内容"
        class="transcript-textarea"
      />
      <template #footer>
        <el-button
          @click="handleReExtractTranscript"
          :icon="Refresh"
        >
          重新提取
        </el-button>
        <el-button
          @click="handleCorrectTranscript"
          :loading="correctingTranscript"
        >
          智能纠错
        </el-button>
        <el-button @click="copyTranscript" :icon="DocumentCopy">
          复制
        </el-button>
        <el-button
          type="primary"
          @click="handleSaveTranscript"
          :loading="editingTranscript"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 仿写文案查看弹窗 -->
    <el-dialog
      v-model="rewriteDialogVisible"
      :title="`✨ ${currentVideoTitle} - 仿写文案`"
      width="60%"
      :style="{ maxWidth: '700px' }"
    >
      <el-input
        v-model="currentRewrite"
        type="textarea"
        :rows="15"
        placeholder="暂无仿写内容"
        class="transcript-textarea"
      />
      <template #footer>
        <el-button
          @click="handleCorrectRewrite"
          :loading="correctingRewrite"
        >
          智能纠错
        </el-button>
        <el-button @click="copyRewrite" :icon="DocumentCopy">
          复制
        </el-button>
        <el-button
          type="primary"
          @click="handleSaveRewrite"
          :loading="editingRewrite"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 音频播放弹窗 -->
    <el-dialog
      v-model="audioDialogVisible"
      :title="`🎵 ${currentVideoTitle} - 音频播放`"
      width="600px"
      @close="currentAudioUrl = ''"
    >
      <div class="audio-player-container">
        <audio
          v-if="currentAudioUrl"
          :src="currentAudioUrl"
          controls
          autoplay
          class="audio-player"
        >
          您的浏览器不支持音频播放
        </audio>
        <div v-else class="no-audio">
          音频文件不存在
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="audioDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 18px;
}

.page-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-select {
  width: 200px;
}

.template-selector {
  width: 200px;
}

.template-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.btn-text {
  margin-left: 4px;
}

.info-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.info-card :deep(.el-card__body) {
  padding: 20px;
}

.info-content h3 {
  margin: 0 0 12px 0;
  color: #fff;
  font-size: 18px;
}

.info-content p {
  margin: 8px 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

.video-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.smart-correct-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 8px;
  border-left: 1px solid #dcdfe6;
  margin-left: 8px;
}

.toggle-label {
  font-size: 14px;
  color: #606266;
}

.video-info {
  display: flex;
  gap: 12px;
}

.video-cover {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-details {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-weight: 500;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.video-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 12px;
}

.status-processing {
  color: #e6a23c;
  font-weight: 500;
}

.audio-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #e6a23c;
  font-size: 13px;
}

.audio-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.audio-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.audio-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

.status-pending {
  color: #909399;
  font-weight: 500;
}

.transcript-preview,
.rewrite-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.clickable-text {
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.clickable-text:hover {
  background-color: #f0f7ff;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.transcript-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  font-size: 15px;
  color: #333;
  max-height: 60vh;
  min-height: 200px;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.transcript-textarea {
  font-size: 15px;
  line-height: 1.8;
}

.transcript-textarea :deep(textarea) {
  font-family: inherit;
  line-height: 1.8;
}

.audio-player-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  min-height: 100px;
}

.audio-player {
  width: 100%;
  max-width: 500px;
  outline: none;
}

.audio-player:focus {
  outline: 2px solid #409eff;
}

.no-audio {
  color: #999;
  font-size: 14px;
}

/* Force table to respect container width */
.content-rewrite-table {
  width: 100%;
  max-width: 100%;
}

.content-rewrite-table :deep(table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed !important;
}

@media (max-width: 768px) {
  /* 容器优化 */
  .video-card :deep(.el-card__body) {
    padding: 12px;
  }

  .video-card :deep(.el-card__header) {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 12px;
  }

  .page-title {
    font-size: 16px;
  }

  .page-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .template-selector,
  .filter-select {
    width: 100% !important;
  }

  .page-actions :deep(.el-select) {
    width: 100% !important;
  }

  .page-actions .el-button {
    width: 100%;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .card-header > span {
    font-size: 14px;
  }

  .batch-actions {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }

  .batch-actions .el-button {
    flex: 1;
    min-width: calc(50% - 4px);
    font-size: 13px;
  }

  .smart-correct-toggle {
    width: 100%;
    padding-left: 0;
    border-left: none;
    margin-left: 0;
    justify-content: space-between;
    background: #f5f7fa;
    padding: 8px 12px;
    border-radius: 4px;
  }

  .toggle-label {
    font-size: 13px;
  }

  .video-card {
    margin-top: 12px;
  }

  .video-cover {
    width: 80px;
    height: 45px;
  }

  /* 隐藏PC端表格 */
  .content-rewrite-table {
    display: none !important;
  }

  /* 显示移动端卡片列表 */
  .video-list-mobile {
    display: block !important;
    width: 100% !important;
    visibility: visible !important;
    opacity: 1 !important;
  }

  /* 移动端卡片 */
  .video-card-mobile {
    background: #fff;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 1px solid #ebeef5;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  /* 卡片头部：复选框 + 图片 + 标题 */
  .mobile-card-header {
    display: flex;
    align-items: stretch;
    gap: 8px;
    padding: 10px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
  }

  .mobile-checkbox {
    flex-shrink: 0;
    align-self: center;
  }

  .mobile-cover-wrapper {
    flex-shrink: 0;
    width: 100px;
    height: 56px;
    border-radius: 6px;
    overflow: hidden;
    background: #f0f0f0;
  }

  .mobile-cover {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .mobile-title-section {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 2px 0;
  }

  .mobile-title {
    font-weight: 500;
    font-size: 14px;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    color: #303133;
  }

  .mobile-meta {
    font-size: 11px;
    color: #909399;
    display: flex;
    gap: 8px;
    margin-top: 4px;
  }

  /* 操作区域 */
  .mobile-actions-section {
    padding: 8px 10px;
  }

  .mobile-action-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #f5f5f5;
  }

  .mobile-action-item:last-child {
    border-bottom: none;
  }

  .action-label {
    font-size: 13px;
    color: #606266;
    font-weight: 500;
    flex-shrink: 0;
    width: 60px;
  }

  .action-buttons {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    background: #fdf6ec;
    color: #e6a23c;
  }

  .text-preview {
    flex: 1;
    padding: 6px 10px;
    background: #f5f7fa;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.5;
    margin-left: 8px;
  }

  .clickable-text {
    cursor: pointer;
    word-break: break-word;
    color: #606266;
  }

  .clickable-text:active {
    color: #409eff;
  }

  .pending-text {
    color: #c0c4cc;
    font-size: 12px;
  }

  /* 弹窗移动端适配 */
  :deep(.el-dialog) {
    width: 95% !important;
    max-width: 95% !important;
    margin: 0 auto;
  }

  :deep(.el-dialog__header) {
    padding: 12px 15px;
  }

  :deep(.el-dialog__title) {
    font-size: 14px;
  }

  :deep(.el-dialog__body) {
    padding: 15px;
  }

  :deep(.el-dialog__footer) {
    padding: 10px 15px;
  }

  :deep(.el-textarea__inner) {
    font-size: 14px;
  }

  :deep(.el-button) {
    font-size: 13px;
    padding: 8px 12px;
  }
}

/* PC端隐藏移动端卡片列表 */
.video-list-mobile {
  display: none;
}
</style>
