<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { getVideos, getAuthors, getGroups } from '../services/api'
import type { VideoData, Author, AuthorGroup } from '../types'

const videos = ref<VideoData[]>([])
const authors = ref<Author[]>([])
const groups = ref<AuthorGroup[]>([])
const loading = ref(false)
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
  if (n >= 10000) return (n/10000).toFixed(1) + 'w'
  if (n >= 1000) return (n/1000).toFixed(1) + 'k'
  return String(n)
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

onMounted(loadVideos)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h2 style="margin: 0;">视频列表</h2>
      <div style="display: flex; gap: 12px; align-items: center;">
        <el-select
          v-model="selectedFilter"
          placeholder="筛选视频"
          style="width: 200px;"
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
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <el-card shadow="never">
      <template #header>
        <span>共 <b>{{ total }}</b> 个视频</span>
      </template>

      <el-table :data="videos" stripe v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="#" width="50" />

        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <a :href="row.video_url" target="_blank">
              <el-image
                :src="row.cover"
                style="width: 56px; height: 74px;"
                fit="cover"
                lazy
              />
            </a>
          </template>
        </el-table-column>

        <el-table-column label="UP主" width="120">
          <template #default="{ row }">
            {{ row.author_nickname || '--' }}
          </template>
        </el-table-column>

        <el-table-column label="标题" min-width="250">
          <template #default="{ row }">
            <a :href="row.video_url" target="_blank" style="color: #333; text-decoration: none;">
              {{ row.desc || '无标题' }}
            </a>
          </template>
        </el-table-column>

        <el-table-column label="👍" width="70" align="center">
          <template #default="{ row }">
            {{ formatNum(row.digg_count) }}
          </template>
        </el-table-column>

        <el-table-column label="💬" width="70" align="center">
          <template #default="{ row }">
            {{ formatNum(row.comment_count) }}
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="110" align="center">
          <template #default="{ row }">
            {{ formatDate(row.create_time) }}
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next"
        />
      </div>

      <el-empty v-if="!loading && videos.length === 0" description="暂无视频，请先添加UP主" />
    </el-card>
  </div>
</template>
