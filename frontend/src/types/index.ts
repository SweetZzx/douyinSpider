// 视频数据类型
export interface VideoData {
  id: number
  author_id: number
  author_nickname: string
  aweme_id: string
  desc: string
  cover: string
  video_url: string
  download_url: string
  create_time: number
  duration: number
  digg_count: number
  comment_count: number
  share_count: number
  collect_count: number
  is_new: boolean
  created_at: string
}

// 分组数据类型
export interface AuthorGroup {
  id: number
  name: string
  sort_order: number
  created_at: string
}

// UP主数据类型
export interface Author {
  id: number
  sec_user_id: string
  nickname: string
  avatar: string
  signature: string
  video_count: number
  latest_video_time: number
  group_id: number | null
  group_name: string | null
  created_at: string
  updated_at: string
}

// 看板数据类型
export interface DashboardData {
  author_count: number
  video_count: number
  new_video_count: number
  new_videos: VideoData[]
}

// 任务状态类型
export interface TaskStatus {
  id: string
  status: 'running' | 'completed' | 'error'
  progress: number
  total: number
  message: string
}

// API响应类型
export interface ApiResponse<T> {
  data?: T
  error?: string
}
