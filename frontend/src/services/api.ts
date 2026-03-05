import axios from 'axios'
import type { VideoData, TaskStatus, Author, AuthorGroup, DashboardData } from '../types'

const TOKEN_KEY = 'access_token'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 为API实例添加认证拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 处理401错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除本地存储的令牌
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('user_info')

      // 如果不是在登录页面，跳转到登录页
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ==================== 看板 ====================
export async function getDashboard(): Promise<DashboardData> {
  const response = await api.get('/dashboard')
  return response.data
}

// ==================== 分组管理 ====================
export async function getGroups(): Promise<AuthorGroup[]> {
  const response = await api.get('/groups')
  return response.data
}

export async function createGroup(name: string): Promise<{ success: boolean; group: AuthorGroup }> {
  const response = await api.post('/groups', { name })
  return response.data
}

export async function updateGroup(id: number, name: string): Promise<{ success: boolean; group: AuthorGroup }> {
  const response = await api.put(`/groups/${id}`, { name })
  return response.data
}

export async function deleteGroup(id: number): Promise<void> {
  await api.delete(`/groups/${id}`)
}

export async function moveAuthorToGroup(authorId: number, groupId: number | null): Promise<{ success: boolean }> {
  const response = await api.put(`/authors/${authorId}/group`, { group_id: groupId })
  return response.data
}

// ==================== UP主管理 ====================
export async function getAuthors(): Promise<Author[]> {
  const response = await api.get('/authors')
  return response.data
}

export async function addAuthor(url: string): Promise<{ success: boolean; author: Author; message: string }> {
  const response = await api.post('/authors', { url })
  return response.data
}

export async function deleteAuthor(id: number): Promise<void> {
  await api.delete(`/authors/${id}`)
}

export async function refreshAuthor(id: number): Promise<{ success: boolean; message: string }> {
  const response = await api.post(`/authors/${id}/refresh`)
  return response.data
}

// ==================== 视频管理 ====================
export interface VideoListResponse {
  total: number
  new_count: number
  videos: VideoData[]
}

export async function getVideos(
  limit: number = 100,
  offset: number = 0,
  filter?: { authorId?: number; groupId?: number | null }
): Promise<VideoListResponse> {
  let url = `/videos?limit=${limit}&offset=${offset}`
  if (filter?.authorId) {
    url += `&author_id=${filter.authorId}`
  } else if (filter?.groupId !== undefined && filter?.groupId !== null) {
    url += `&group_id=${filter.groupId}`
  }
  const response = await api.get(url)
  return response.data
}

export async function getNewVideos(): Promise<{ count: number; videos: VideoData[] }> {
  const response = await api.get('/videos/new')
  return response.data
}

export async function markAllVideosAsRead(): Promise<{ success: boolean; count: number }> {
  const response = await api.post('/videos/read-all')
  return response.data
}

export async function markVideoAsRead(videoId: number): Promise<{ success: boolean }> {
  const response = await api.post(`/videos/${videoId}/read`)
  return response.data
}

export async function checkNewVideos(): Promise<{ success: boolean; message: string }> {
  const response = await api.post('/videos/check')
  return response.data
}

// ==================== 旧接口兼容 ====================
export async function startTask(target: string, limit: number = 0): Promise<{ task_id: string; status: string }> {
  const response = await api.post('/task/start', { target, limit })
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await api.get(`/task/status?task_id=${taskId}`)
  return response.data
}

export async function getTaskResults(taskId: string): Promise<VideoData[]> {
  const response = await api.get(`/task/results/${taskId}`)
  return response.data
}

// ==================== 设置 ====================
export async function getSettings(): Promise<{ cookie_configured: boolean; download_path: string }> {
  const response = await api.get('/settings')
  return response.data
}

export async function setCookie(cookie: string): Promise<{ success: boolean; message: string }> {
  const response = await api.post(`/settings/cookie?cookie=${encodeURIComponent(cookie)}`)
  return response.data
}

export async function verifyCookie(): Promise<{ valid: boolean; message: string }> {
  const response = await api.get('/settings/cookie/verify')
  return response.data
}

// ==================== 文案仿写提示词 ====================

export async function getRewritePrompt(): Promise<{
  success: boolean
  prompt: string
}> {
  const response = await api.get('/settings/rewrite-prompt')
  return response.data
}

export async function saveRewritePrompt(prompt: string): Promise<{
  success: boolean
  message: string
}> {
  const response = await api.post('/settings/rewrite-prompt', { prompt })
  return response.data
}

export async function resetRewritePrompt(): Promise<{
  success: boolean
  message: string
}> {
  const response = await api.post('/settings/rewrite-prompt/reset')
  return response.data
}

// ==================== 模型配置 ====================

export async function getModelConfig(): Promise<{
  success: boolean
  transcribe: {
    api_base: string
    api_key: string
    model: string
  }
  rewrite: {
    api_base: string
    api_key: string
    model: string
  }
}> {
  const response = await api.get('/settings/models')
  return response.data
}

export async function saveTranscribeModelConfig(apiBase: string, apiKey: string, model: string): Promise<{
  success: boolean
  message: string
}> {
  const response = await api.post('/settings/models/transcribe', {
    api_base: apiBase,
    api_key: apiKey,
    model: model
  })
  return response.data
}

export async function saveRewriteModelConfig(apiBase: string, apiKey: string, model: string): Promise<{
  success: boolean
  message: string
}> {
  const response = await api.post('/settings/models/rewrite', {
    api_base: apiBase,
    api_key: apiKey,
    model: model
  })
  return response.data
}

// ==================== 音频提取 ====================

export async function extractAudio(videoIds: number[]): Promise<{ success: boolean; message: string; count: number }> {
  const response = await api.post('/audio/extract', { video_ids: videoIds })
  return response.data
}

export async function getVideoAudio(videoId: number): Promise<{
  video_id: number
  aweme_id: string
  has_audio: boolean
  audio_path: string | null
  audio_url: string | null
  status: string
  duration: number
  file_size: number
  error_message: string
}> {
  const response = await api.get(`/audio/videos/${videoId}/audio`)
  return response.data
}

export async function getAudioExtractions(limit: number = 50, offset: number = 0): Promise<{
  total: number
  extractions: any[]
}> {
  const response = await api.get(`/audio/extractions?limit=${limit}&offset=${offset}`)
  return response.data
}

// ==================== 语音转写 ====================

export async function transcribeVideos(videoIds: number[], force: boolean = false): Promise<{ success: boolean; message: string; count: number }> {
  const response = await api.post('/transcribe/transcribe', { video_ids: videoIds, force: force })
  return response.data
}

export async function getVideoTranscript(videoId: number): Promise<{
  video_id: number
  aweme_id: string
  has_transcript: boolean
  text: string | null
  segments: any[] | null
  status: string
  language: string
  duration: number
  confidence: number
  error_message: string
}> {
  const response = await api.get(`/transcribe/videos/${videoId}/transcript`)
  return response.data
}

export async function getTranscripts(limit: number = 50, offset: number = 0): Promise<{
  total: number
  transcripts: any[]
}> {
  const response = await api.get(`/transcribe/transcripts?limit=${limit}&offset=${offset}`)
  return response.data
}

// ==================== 文案仿写 ====================

export async function rewriteContent(originalText: string): Promise<{
  success: boolean
  original_text: string
  rewritten_text: string
}> {
  const response = await api.post('/content-rewrite', { original_text: originalText })
  return response.data
}

export async function rewriteVideoContent(
  videoId: number,
  templateId?: number
): Promise<{
  success: boolean
  video_id: number
  original_text: string
  rewritten_text: string
}> {
  const url = templateId
    ? `/videos/${videoId}/rewrite?template_id=${templateId}`
    : `/videos/${videoId}/rewrite`
  const response = await api.post(url)
  return response.data
}

export async function updateVideoTranscript(
  videoId: number,
  text: string,
  correct?: boolean
): Promise<{
  success: boolean
  message: string
  text: string
}> {
  const response = await api.put(`/transcribe/videos/${videoId}/transcript`, {
    text,
    correct: correct || false
  }, {
    timeout: correct ? 180000 : 60000  // 智能纠错需要更长时间（3分钟）
  })
  return response.data
}

export async function updateVideoRewrite(
  videoId: number,
  rewrittenText: string,
  prompt?: string
): Promise<{
  success: boolean
  message: string
  rewritten_text: string
}> {
  const response = await api.put(`/videos/${videoId}/rewrite`, {
    rewritten_text: rewrittenText,
    prompt: prompt
  }, {
    timeout: prompt ? 180000 : 60000  // 智能纠错需要更长时间（3分钟）
  })
  return response.data
}

// ==================== 提示词模板管理 ====================

import type { PromptTemplate } from '../types'

export async function getPromptTemplates(category?: string): Promise<{
  success: boolean
  templates: PromptTemplate[]
}> {
  const url = category ? `/prompt-templates?category=${category}` : '/prompt-templates'
  const response = await api.get(url)
  return response.data
}

export async function createPromptTemplate(data: {
  name: string
  content: string
  description?: string
  category?: string
  is_default?: boolean
  sort_order?: number
}): Promise<{
  success: boolean
  template: PromptTemplate
  message: string
}> {
  const response = await api.post('/prompt-templates', data)
  return response.data
}

export async function updatePromptTemplate(
  id: number,
  data: Partial<PromptTemplate>
): Promise<{
  success: boolean
  template: PromptTemplate
  message: string
}> {
  const response = await api.put(`/prompt-templates/${id}`, data)
  return response.data
}

export async function deletePromptTemplate(id: number): Promise<{
  success: boolean
  message: string
}> {
  const response = await api.delete(`/prompt-templates/${id}`)
  return response.data
}

export async function setDefaultTemplate(id: number): Promise<{
  success: boolean
  template: PromptTemplate
  message: string
}> {
  const response = await api.post(`/prompt-templates/${id}/set-default`)
  return response.data
}

export async function copyPromptTemplate(id: number, newName?: string): Promise<{
  success: boolean
  template: PromptTemplate
  message: string
}> {
  const body = newName ? { new_name: newName } : {}
  const response = await api.post(`/prompt-templates/${id}/copy`, body)
  return response.data
}

// ==================== AI对话 ====================

export async function chatWithAI(
  message: string,
  history: Array<{ role: string; content: string }> = [],
  customPrompt: string = ''
): Promise<{
  success: boolean
  response: string
  message?: string
}> {
  const response = await api.post('/chat', {
    message,
    history,
    custom_prompt: customPrompt
  }, {
    timeout: 120000  // 2分钟超时
  })
  return response.data
}
