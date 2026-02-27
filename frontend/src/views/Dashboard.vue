<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, VideoPlay, Bell, Refresh, Warning } from '@element-plus/icons-vue'
import { getDashboard, markAllVideosAsRead, verifyCookie, checkNewVideos } from '../services/api'
import type { DashboardData } from '../types'

const router = useRouter()
const dashboard = ref<DashboardData>({ author_count: 0, video_count: 0, new_video_count: 0, new_videos: [] })
const loading = ref(false)
const checking = ref(false)
const cookieValid = ref<boolean | null>(null)
const cookieMessage = ref('')

const formatDate = (ts: number) => {
  if (!ts) return '--'
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const loadDashboard = async () => {
  loading.value = true
  try {
    dashboard.value = await getDashboard()
  } catch (e: any) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
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

const handleCheckNewVideos = async () => {
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

    <h2 style="margin-bottom: 20px;">数据看板</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="goToAuthors">
          <div class="stat-content">
            <el-icon :size="40" color="#409EFF"><User /></el-icon>
            <div class="stat-info">
              <div class="stat-num">{{ dashboard.author_count }}</div>
              <div class="stat-label">关注UP主</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="goToVideos">
          <div class="stat-content">
            <el-icon :size="40" color="#67C23A"><VideoPlay /></el-icon>
            <div class="stat-info">
              <div class="stat-num">{{ dashboard.video_count }}</div>
              <div class="stat-label">视频总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon :size="40" color="#E6A23C"><Bell /></el-icon>
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
    <el-card shadow="never">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>
            <el-icon><Bell /></el-icon>
            新视频提醒
            <el-badge v-if="dashboard.new_video_count > 0" :value="dashboard.new_video_count" style="margin-left: 8px;" />
          </span>
          <div>
            <el-button size="small" @click="handleCheckNewVideos" :loading="checking">
              <el-icon><Refresh /></el-icon> 检查新视频
            </el-button>
            <el-button size="small" @click="loadDashboard" :loading="loading">
              刷新列表
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

      <el-table v-if="dashboard.new_videos.length > 0" :data="dashboard.new_videos" stripe>
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
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small">
              <a :href="row.video_url" target="_blank" style="color: inherit;">查看</a>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无新视频" />
    </el-card>
  </div>
</template>

<style scoped>
.stat-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.stat-card:hover {
  transform: translateY(-4px);
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-info {
  text-align: left;
}
.stat-num {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}
.stat-num.has-new {
  color: #E6A23C;
}
.stat-label {
  color: #909399;
  font-size: 14px;
}
</style>
