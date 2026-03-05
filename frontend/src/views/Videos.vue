<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getVideos, getAuthors, getGroups } from '../services/api'
import type { VideoData, Author, AuthorGroup } from '../types'

const videos = ref<VideoData[]>([])
const authors = ref<Author[]>([])
const groups = ref<AuthorGroup[]>([])
const loading = ref(false)
const tableRef = ref<InstanceType<typeof import('element-plus')['ElTable']>>()

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
      id: 0 // 特殊标记
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
    // 未分组
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
  page.value = 1 // 重置页码
  loadVideos()
}

const formatDate = (ts: number) => {
  if (!ts) return '--'
  const d = new Date(ts * 1000)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

const formatNum = (n: number) => {
  if (!n) return '0'
  if (n >= 10000) return (n/10000).toFixed(1) + 'w'
  if (n >= 1000) return (n/1000).toFixed(1) + 'k'
  return String(n)
}

const formatDuration = (ms: number) => {
  if (!ms) return '--'
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return minutes > 0 ? `${minutes}:${String(remainingSeconds).padStart(2, '0')}` : `${remainingSeconds}s`
}

const loadVideos = async () => {
  loading.value = true
  try {
    // 并行加载作者列表和分组
    const [authorData, groupData] = await Promise.all([
      getAuthors(),
      getGroups()
    ])
    authors.value = authorData
    groups.value = groupData

    // 构建筛选参数
    const filter: { authorId?: number; groupId?: number } = {}
    if (filterType.value === 'author' && selectedAuthorId.value) {
      filter.authorId = selectedAuthorId.value
    } else if (filterType.value === 'group' && selectedGroupId.value !== null) {
      filter.groupId = selectedGroupId.value
    }

    // 加载视频（服务端分页）
    const offset = (page.value - 1) * pageSize.value
    const videoData = await getVideos(pageSize.value, offset, Object.keys(filter).length > 0 ? filter : undefined)
    videos.value = videoData.videos || []
    total.value = videoData.total || 0
  } catch (e) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

// 监听分页变化
watch([page, pageSize], () => {
  loadVideos()
})

const openVideo = (url: string) => {
  window.open(url, '_blank')
}

const handleDelete = async (video: VideoData) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除视频"${video.desc || '无标题'}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    // TODO: 调用删除API
    ElMessage.warning('删除功能暂未实现，请联系管理员')
    // const result = await deleteVideo(video.id)
    // if (result.success) {
    //   ElMessage.success('删除成功')
    //   loadVideos()
    // }
  } catch {
    // 用户取消
  }
}

// 监听容器大小变化，强制表格重新计算布局
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  loadVideos()

  // 使用 ResizeObserver 监听主内容区域的宽度变化
  resizeObserver = new ResizeObserver(() => {
    if (tableRef.value) {
      // 使用 requestAnimationFrame 确保在 DOM 更新后调用
      requestAnimationFrame(() => {
        if (tableRef.value) {
          // 强制表格重新计算布局
          tableRef.value.doLayout()
        }
      })
    }
  })

  // 监听主内容区域
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    resizeObserver.observe(mainContent)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">视频列表</h2>
      <div class="page-actions">
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

    <el-card shadow="never" class="video-card">
      <template #header>
        <span>共 <b>{{ total }}</b> 个视频</span>
      </template>

      <!-- 移动端卡片列表 -->
      <div v-loading="loading" class="video-list-mobile">
        <a
          v-for="video in videos"
          :key="video.id"
          :href="video.video_url"
          target="_blank"
          class="video-item"
        >
          <img :src="video.cover" class="video-cover" alt="" />
          <div class="video-info">
            <div class="video-author">{{ video.author_nickname || '--' }}</div>
            <div class="video-desc">{{ video.desc || '无标题' }}</div>
            <div class="video-meta">
              <span>⏱️ {{ formatDuration(video.duration) }}</span>
              <span>👍 {{ formatNum(video.digg_count) }}</span>
              <span>⭐ {{ formatNum(video.collect_count) }}</span>
              <span>💬 {{ formatNum(video.comment_count) }}</span>
              <span>📅 {{ formatDate(video.create_time) }}</span>
            </div>
          </div>
        </a>
        <el-empty v-if="!loading && videos.length === 0" description="暂无视频" />
      </div>

      <!-- PC端表格 -->
      <el-table
        ref="tableRef"
        :data="videos"
        stripe
        v-loading="loading"
        class="video-table-pc"
        :style="{ width: '100%', tableLayout: 'fixed' }"
      >
        <el-table-column type="index" label="#" width="55" align="center" />

        <el-table-column label="封面" width="75" align="center">
          <template #default="{ row }">
            <a :href="row.video_url" target="_blank" @click.prevent="openVideo(row.video_url)">
              <el-image
                :src="row.cover"
                style="width: 50px; height: 66px;"
                fit="cover"
                lazy
              />
            </a>
          </template>
        </el-table-column>

        <el-table-column prop="author_nickname" label="UP主" width="90" show-overflow-tooltip />

        <el-table-column label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <a :href="row.video_url" target="_blank" @click.prevent="openVideo(row.video_url)" style="color: #333; text-decoration: none;">
              {{ row.desc || '无标题' }}
            </a>
          </template>
        </el-table-column>

        <el-table-column label="时长" width="60" align="center">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>

        <el-table-column prop="digg_count" label="点赞" width="60" align="center">
          <template #default="{ row }">
            {{ formatNum(row.digg_count) }}
          </template>
        </el-table-column>

        <el-table-column prop="collect_count" label="收藏" width="60" align="center">
          <template #default="{ row }">
            {{ formatNum(row.collect_count) }}
          </template>
        </el-table-column>

        <el-table-column prop="share_count" label="分享" width="60" align="center">
          <template #default="{ row }">
            {{ formatNum(row.share_count) }}
          </template>
        </el-table-column>

        <el-table-column prop="comment_count" label="评论" width="60" align="center">
          <template #default="{ row }">
            {{ formatNum(row.comment_count) }}
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="85" align="center">
          <template #default="{ row }">
            {{ formatDate(row.create_time) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="openVideo(row.video_url)"
            >
              查看
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && videos.length === 0" class="empty-pc" description="暂无视频，请先添加UP主" />

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          :pager-count="5"
          layout="total, prev, pager, next"
          small
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 18px;
}

.page-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.filter-select {
  width: 160px;
}

/* 视频卡片 */
.video-card {
  overflow: hidden;
}

.video-card :deep(.el-card__body) {
  padding: 0;
}

/* PC端表格 */
.video-table-pc {
  display: table;
  width: 100%;
  max-width: 100%;
}

.video-table-pc :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.video-table-pc :deep(.el-table__header-wrapper) {
  overflow-x: auto;
}

/* Force table to respect container width */
.video-table-pc :deep(table) {
  width: 100% !important;
  max-width: 100% !important;
  table-layout: fixed !important;
}

/* 移动端视频列表 */
.video-list-mobile {
  display: none;
}

.video-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #eee;
  text-decoration: none;
  color: inherit;
}

.video-item:last-child {
  border-bottom: none;
}

.video-cover {
  width: 80px;
  height: 106px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.video-author {
  font-size: 12px;
  color: #909399;
}

.video-desc {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-meta {
  font-size: 12px;
  color: #c0c4cc;
  display: flex;
  gap: 12px;
}

/* PC端表格 */
.video-table-pc {
  display: table;
}

.empty-pc {
  display: flex;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-title {
    font-size: 16px;
  }

  .page-actions {
    justify-content: space-between;
  }

  .filter-select {
    flex: 1;
    max-width: 200px;
  }

  .btn-text {
    display: none;
  }

  .video-list-mobile {
    display: block;
  }

  .video-table-pc {
    display: none;
  }

  .empty-pc {
    display: none;
  }

  .pagination-wrapper {
    justify-content: center;
  }

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
