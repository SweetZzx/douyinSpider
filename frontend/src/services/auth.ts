import axios from 'axios'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user_info'

/**
 * 设置访问令牌
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 获取访问令牌
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 移除访问令牌
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

/**
 * 设置用户信息
 */
export function setUserInfo(userInfo: { username: string }): void {
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
}

/**
 * 获取用户信息
 */
export function getUserInfo(): { username: string } | null {
  const info = localStorage.getItem(USER_KEY)
  if (info) {
    try {
      return JSON.parse(info)
    } catch {
      return null
    }
  }
  return null
}

/**
 * 检查是否已登录
 */
export function isLoggedIn(): boolean {
  return !!getToken()
}

/**
 * 用户登录
 */
export async function login(username: string, password: string): Promise<{
  access_token: string
  token_type: string
  username: string
}> {
  const response = await axios.post('/api/auth/login', { username, password })
  const { access_token, username: user } = response.data

  // 保存令牌和用户信息
  setToken(access_token)
  setUserInfo({ username: user })

  return response.data
}

/**
 * 用户登出
 */
export async function logout(): Promise<void> {
  try {
    await axios.post('/api/auth/logout')
  } catch (error) {
    console.error('登出请求失败:', error)
  } finally {
    removeToken()
  }
}

/**
 * 验证令牌有效性
 */
export async function verifyToken(): Promise<boolean> {
  try {
    const response = await axios.post('/api/auth/verify')
    return response.data.logged_in
  } catch {
    return false
  }
}

// 为axios请求添加认证头
axios.interceptors.request.use(
  (config) => {
    const token = getToken()
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
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除本地存储的令牌
      removeToken()

      // 如果不是在登录页面，跳转到登录页
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
