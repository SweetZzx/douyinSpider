import axios from 'axios'
import type { VideoData, TaskStatus, Author, AuthorGroup, DashboardData } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

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
