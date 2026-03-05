<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, VideoPlay, Bell, Refresh, Warning } from '@element-plus/icons-vue'
import { getDashboard, markAllVideosAsRead, markVideoAsRead, verifyCookie, checkNewVideos, getAuthors, getGroups } from '../services/api'
import type { DashboardData, Author, AuthorGroup, VideoData } from '../types'

const router = useRouter()
const dashboard = ref<DashboardData>({ author_count: 0, video_count: 0, new_video_count: 0, new_videos: [] })
const loading = ref(false)
const checking = ref(false)
const cookieValid = ref<boolean | null>(null)
const cookieMessage = ref('')

// 分组筛选
const authors = ref<Author[]>([])
const groups = ref<AuthorGroup[]>([])
const selectedGroupId = ref<number | undefined>(undefined)
const filteredVideos = ref<VideoData[]>([])

// 节流：记录上次检查时间
const lastCheckTime = ref(0)
const CHECK_COOLDOWN = 30000 // 30秒冷却时间

// 分组选项
const groupOptions = computed(() => {
  const options: { value: number | undefined; label: string }[] = [
    { value: undefined, label: '全部分组' }
  ]
  groups.value.forEach(g => {
    const count = authors.value.filter(a => a.group_id === g.id).length
    options.push({ value: g.id, label: `${g.name} (${count}人)` })
  })
  return options
})

const formatDate = (ts: number) => {
  if (!ts) return '--'
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const loadDashboard = async () => {
  loading.value = true
  try {
    // 并行加载数据
    const [dashData, authorData, groupData] = await Promise.all([
      getDashboard(),
      getAuthors(),
      getGroups()
    ])
    dashboard.value = dashData
    authors.value = authorData
    groups.value = groupData
    // 应用分组筛选
    filterVideos()
  } catch (e: any) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 根据分组筛选视频
const filterVideos = () => {
  if (selectedGroupId.value === undefined) {
    filteredVideos.value = dashboard.value.new_videos
  } else {
    // 获取该分组的作者ID列表
    const groupAuthorIds = authors.value
      .filter(a => a.group_id === selectedGroupId.value)
      .map(a => a.id)
    filteredVideos.value = dashboard.value.new_videos.filter(v =>
      groupAuthorIds.includes(v.author_id)
    )
  }
}

// 分组变化处理
const handleGroupChange = () => {
  filterVideos()
}

const checkCookie = async () => {
  try {
    const result = await verifyCookie()
    cookieValid.value = result.valid
    cookieMessage.value = result.message
  } catch (e) {
    cookieValid.value = false
    cookieMessage.value = '验证失败'
  }
}

const handleMarkAllRead = async () => {
  try {
    await markAllVideosAsRead()
    ElMessage.success('已标记全部已读')
    loadDashboard()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleMarkRead = async (videoId: number) => {
  try {
    await markVideoAsRead(videoId)
    // 从列表中移除该视频
    dashboard.value.new_videos = dashboard.value.new_videos.filter(v => v.id !== videoId)
    dashboard.value.new_video_count = dashboard.value.new_videos.length
    filterVideos()
    ElMessage.success('已标记为已读')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleCheckNewVideos = async () => {
  const now = Date.now()
  const elapsed = now - lastCheckTime.value
  if (elapsed < CHECK_COOLDOWN) {
    const remaining = Math.ceil((CHECK_COOLDOWN - elapsed) / 1000)
    ElMessage.warning(`请${remaining}秒后再试`)
    return
  }

  lastCheckTime.value = now
  checking.value = true
  try {
    const result = await checkNewVideos()
    ElMessage.success(result.message || '正在检查...')
    // 3秒后刷新看板数据，给后台任务一些时间执行
    setTimeout(loadDashboard, 3000)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '检查失败')
  } finally {
    checking.value = false
  }
}

const goToVideos = () => router.push('/videos')
const goToAuthors = () => router.push('/authors')

onMounted(() => {
  loadDashboard()
  checkCookie()
})
</script>

<template>
  <div>
    <!-- Cookie失效警告 -->
    <el-alert
      v-if="cookieValid === false"
      type="error"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <template #title>
        <span style="display: flex; align-items: center; gap: 8px;">
          <el-icon><Warning /></el-icon>
          Cookie已失效，请点击右上角「设置」更新Cookie
        </span>
      </template>
      <template #default>
        {{ cookieMessage }}
      </template>
    </el-alert>

    <h2 class="page-title">数据看板</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stat-row">
      <el-col :xs="12" :sm="8">
        <el-card shadow="hover" class="stat-card" @click="goToAuthors">
          <div class="stat-content">
            <el-icon :size="32" color="#409EFF"><User /></el-icon>
            <div class="stat-info">
              <div class="stat-num">{{ dashboard.author_count }}</div>
              <div class="stat-label">关注UP主</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="8">
        <el-card shadow="hover" class="stat-card" @click="goToVideos">
          <div class="stat-content">
            <el-icon :size="32" color="#67C23A"><VideoPlay /></el-icon>
            <div class="stat-info">
              <div class="stat-num">{{ dashboard.video_count }}</div>
              <div class="stat-label">视频总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="32" color="#E6A23C"><Bell /></el-icon>
            <div class="stat-info">
              <div class="stat-num" :class="{ 'has-new': dashboard.new_video_count > 0 }">
                {{ dashboard.new_video_count }}
              </div>
              <div class="stat-label">新视频</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新视频提醒 -->
    <el-card shadow="never" class="video-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Bell /></el-icon>
            新视频提醒
            <el-badge v-if="dashboard.new_video_count > 0" :value="dashboard.new_video_count" class="new-badge" />
          </span>
          <div class="card-actions">
            <el-select
              v-model="selectedGroupId"
              placeholder="选择分组"
              size="small"
              class="group-select"
              @change="handleGroupChange"
              clearable
            >
              <el-option
                v-for="opt in groupOptions"
                :key="opt.value ?? 'all'"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-button size="small" @click="handleCheckNewVideos" :loading="checking">
              <el-icon class="btn-icon"><Refresh /></el-icon>
              <span class="btn-text">检查新视频</span>
            </el-button>
            <el-button
              v-if="dashboard.new_video_count > 0"
              size="small"
              type="primary"
              @click="handleMarkAllRead"
            >
              全部已读
            </el-button>
          </div>
        </div>
      </template>

      <!-- 移动端卡片列表 -->
      <div v-if="filteredVideos.length > 0" class="video-list-mobile">
        <div v-for="video in filteredVideos" :key="video.id" class="video-item">
          <a :href="video.video_url" target="_blank" class="video-link">
            <div class="video-author">{{ video.author_nickname || '--' }}</div>
            <div class="video-desc">{{ video.desc || '无标题' }}</div>
            <div class="video-meta">{{ formatDate(video.create_time) }}</div>
          </a>
        </div>
      </div>

      <!-- PC端表格 -->
      <el-table
        v-if="filteredVideos.length > 0"
        :data="filteredVideos"
        stripe
        class="video-table-pc"
        :style="{ width: '100%', tableLayout: 'fixed' }"
      >
        <el-table-column label="UP主" width="120">
          <template #default="{ row }">
            {{ row.author_nickname || '--' }}
          </template>
        </el-table-column>
        <el-table-column label="视频" min-width="300">
          <template #default="{ row }">
            <a :href="row.video_url" target="_blank" style="color: #333; text-decoration: none;">
              {{ row.desc || '无标题' }}
            </a>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="120" align="center">
          <template #default="{ row }">
            {{ formatDate(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small">
              <a :href="row.video_url" target="_blank" style="color: inherit;">查看</a>
            </el-button>
            <el-button type="success" link size="small" @click="handleMarkRead(row.id)">
              已读
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无新视频" />
    </el-card>
  </div>
</template>

<style scoped>
/* 页面标题 */
.page-title {
  margin: 0 0 20px 0;
  font-size: 18px;
}

/* 统计卡片 */
.stat-row {
  margin-bottom: 12px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
  margin-bottom: 8px;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-info {
  text-align: left;
}

.stat-num {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-num.has-new {
  color: #E6A23C;
}

.stat-label {
  color: #909399;
  font-size: 13px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.new-badge {
  margin-left: 4px;
}

.card-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.group-select {
  width: 140px;
}

/* 移动端视频列表 */
.video-list-mobile {
  display: none;
}

.video-item {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
}

.video-item:last-child {
  border-bottom: none;
}

.video-link {
  text-decoration: none;
  color: inherit;
}

.video-author {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.video-desc {
  color: #303133;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-meta {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
}

/* PC端表格 */
.video-table-pc {
  display: table;
  width: 100%;
  max-width: 100%;
}

.video-table-pc :deep(table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed !important;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .stat-card:hover {
    transform: none;
  }

  .stat-num {
    font-size: 20px;
  }

  .stat-content {
    gap: 8px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 6px;
  }

  /* 移动端：检查按钮只显示文字，刷新按钮只显示图标 */
  .btn-icon {
    display: none;
  }

  .video-list-mobile {
    display: block;
  }

  .video-table-pc {
    display: none;
  }
}
</style>
