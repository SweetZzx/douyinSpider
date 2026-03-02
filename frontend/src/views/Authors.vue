<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, FolderAdd } from '@element-plus/icons-vue'
import {
  getAuthors,
  addAuthor,
  deleteAuthor,
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  moveAuthorToGroup
} from '../services/api'
import type { Author, AuthorGroup } from '../types'

const authors = ref<Author[]>([])
const groups = ref<AuthorGroup[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const newAuthorUrl = ref('')
const addLoading = ref(false)

// 分组相关
const showGroupDialog = ref(false)
const editingGroup = ref<AuthorGroup | null>(null)
const groupName = ref('')
const groupLoading = ref(false)

// 拖拽相关
const draggedAuthor = ref<Author | null>(null)
const dragOverGroupId = ref<number | 'none' | null>(null)

// 按分组整理的UP主
const groupedAuthors = computed(() => {
  const result: Record<string, Author[]> = {
    'none': [] // 未分组
  }

  // 初始化所有分组
  groups.value.forEach(g => {
    result[g.id] = []
  })

  // 分配UP主到各分组
  authors.value.forEach(author => {
    if (author.group_id && result[author.group_id]) {
      result[author.group_id].push(author)
    } else {
      result['none'].push(author)
    }
  })

  return result
})

const loadData = async () => {
  loading.value = true
  try {
    const [authorsData, groupsData] = await Promise.all([
      getAuthors(),
      getGroups()
    ])
    authors.value = authorsData
    groups.value = groupsData
  } catch (e) {
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  if (!newAuthorUrl.value.trim()) {
    ElMessage.warning('请输入UP主链接')
    return
  }

  addLoading.value = true
  try {
    await addAuthor(newAuthorUrl.value.trim())
    ElMessage.success('添加成功')
    showAddDialog.value = false
    newAuthorUrl.value = ''
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

const handleDelete = async (author: Author) => {
  try {
    await ElMessageBox.confirm(`确定删除UP主「${author.nickname || author.sec_user_id}」？\n相关视频也会被删除。`, '确认删除', {
      type: 'warning',
    })
    await deleteAuthor(author.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 分组操作
const openCreateGroup = () => {
  editingGroup.value = null
  groupName.value = ''
  showGroupDialog.value = true
}

const openEditGroup = (group: AuthorGroup) => {
  editingGroup.value = group
  groupName.value = group.name
  showGroupDialog.value = true
}

const handleSaveGroup = async () => {
  if (!groupName.value.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }

  groupLoading.value = true
  try {
    if (editingGroup.value) {
      await updateGroup(editingGroup.value.id, groupName.value.trim())
      ElMessage.success('分组已更新')
    } else {
      await createGroup(groupName.value.trim())
      ElMessage.success('分组已创建')
    }
    showGroupDialog.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    groupLoading.value = false
  }
}

const handleDeleteGroup = async (group: AuthorGroup) => {
  const authorCount = groupedAuthors.value[group.id]?.length || 0
  try {
    await ElMessageBox.confirm(
      `确定删除分组「${group.name}」？${authorCount > 0 ? `\n该分组内的 ${authorCount} 个UP主将变为未分组。` : ''}`,
      '确认删除',
      { type: 'warning' }
    )
    await deleteGroup(group.id)
    ElMessage.success('分组已删除')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 拖拽操作
const handleDragStart = (e: DragEvent, author: Author) => {
  draggedAuthor.value = author
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', author.id.toString())
  }
}

const handleDragEnd = () => {
  draggedAuthor.value = null
  dragOverGroupId.value = null
}

const handleDragOver = (e: DragEvent, groupId: number | 'none') => {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
  dragOverGroupId.value = groupId
}

const handleDragLeave = () => {
  dragOverGroupId.value = null
}

const handleDrop = async (e: DragEvent, groupId: number | 'none') => {
  e.preventDefault()
  dragOverGroupId.value = null

  if (!draggedAuthor.value) return

  const targetGroupId = groupId === 'none' ? null : groupId

  // 如果UP主已经在该分组，不做操作
  if (draggedAuthor.value.group_id === targetGroupId) return

  try {
    await moveAuthorToGroup(draggedAuthor.value.id, targetGroupId)
    ElMessage.success('移动成功')
    loadData()
  } catch (e: any) {
    ElMessage.error('移动失败')
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">UP主管理</h2>
      <div class="page-actions">
        <el-button @click="openCreateGroup" class="action-btn">
          <el-icon><FolderAdd /></el-icon>
          <span class="btn-text">新建分组</span>
        </el-button>
        <el-button type="primary" @click="showAddDialog = true" class="action-btn">
          <el-icon><Plus /></el-icon>
          <span class="btn-text">添加UP主</span>
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="groups-container">
      <!-- 已创建的分组 -->
      <div
        v-for="group in groups"
        :key="group.id"
        class="group-section"
        :class="{ 'drag-over': dragOverGroupId === group.id }"
        @dragover="handleDragOver($event, group.id)"
        @dragleave="handleDragLeave"
        @drop="handleDrop($event, group.id)"
      >
        <div class="group-header">
          <div class="group-title">
            <span class="group-name">{{ group.name }}</span>
            <span class="group-count">({{ groupedAuthors[group.id]?.length || 0 }})</span>
          </div>
          <div class="group-actions">
            <el-button type="primary" link size="small" @click="openEditGroup(group)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button type="danger" link size="small" @click="handleDeleteGroup(group)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <div class="group-content">
          <div
            v-for="author in groupedAuthors[group.id]"
            :key="author.id"
            class="author-card"
            draggable="true"
            @dragstart="handleDragStart($event, author)"
            @dragend="handleDragEnd"
          >
            <el-avatar :size="40" :src="author.avatar">
              {{ author.nickname?.charAt(0) || '?' }}
            </el-avatar>
            <div class="author-info">
              <div class="author-name">{{ author.nickname || '--' }}</div>
              <div class="author-meta">
                <span>视频: {{ author.video_count || 0 }}</span>
              </div>
            </div>
            <div class="author-actions">
              <el-button type="danger" link size="small" @click="handleDelete(author)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="!groupedAuthors[group.id]?.length" class="empty-hint">
            拖拽UP主到此处
          </div>
        </div>
      </div>

      <!-- 未分组 -->
      <div
        class="group-section ungrouped"
        :class="{ 'drag-over': dragOverGroupId === 'none' }"
        @dragover="handleDragOver($event, 'none')"
        @dragleave="handleDragLeave"
        @drop="handleDrop($event, 'none')"
      >
        <div class="group-header">
          <div class="group-title">
            <span class="group-name">未分组</span>
            <span class="group-count">({{ groupedAuthors['none']?.length || 0 }})</span>
          </div>
        </div>
        <div class="group-content">
          <div
            v-for="author in groupedAuthors['none']"
            :key="author.id"
            class="author-card"
            draggable="true"
            @dragstart="handleDragStart($event, author)"
            @dragend="handleDragEnd"
          >
            <el-avatar :size="40" :src="author.avatar">
              {{ author.nickname?.charAt(0) || '?' }}
            </el-avatar>
            <div class="author-info">
              <div class="author-name">{{ author.nickname || '--' }}</div>
              <div class="author-meta">
                <span>视频: {{ author.video_count || 0 }}</span>
              </div>
            </div>
            <div class="author-actions">
              <el-button type="danger" link size="small" @click="handleDelete(author)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
          <div v-if="!groupedAuthors['none']?.length" class="empty-hint">
            新添加的UP主会显示在这里
          </div>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && authors.length === 0 && groups.length === 0" description="暂无UP主，点击上方按钮添加" />

    <!-- 添加UP主弹窗 -->
    <el-dialog v-model="showAddDialog" title="添加UP主" width="500px" class="responsive-dialog">
      <el-form @submit.prevent="handleAdd">
        <el-form-item label="UP主链接">
          <el-input
            v-model="newAuthorUrl"
            placeholder="https://www.douyin.com/user/MS4wLjABAAAA..."
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">添加</el-button>
      </template>
    </el-dialog>

    <!-- 创建/编辑分组弹窗 -->
    <el-dialog v-model="showGroupDialog" :title="editingGroup ? '编辑分组' : '新建分组'" width="400px" class="responsive-dialog">
      <el-form @submit.prevent="handleSaveGroup">
        <el-form-item label="分组名称">
          <el-input
            v-model="groupName"
            placeholder="请输入分组名称"
            clearable
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGroupDialog = false">取消</el-button>
        <el-button type="primary" :loading="groupLoading" @click="handleSaveGroup">保存</el-button>
      </template>
    </el-dialog>
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
}

/* 分组容器 */
.groups-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.group-section {
  background: #fff;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  transition: all 0.3s;
}

.group-section.drag-over {
  border: 2px dashed #409eff !important;
  background: rgba(64, 158, 255, 0.2) !important;
}

.group-section.ungrouped.drag-over {
  border-style: dashed;
  border-color: #67c23a;
  background: #f0f9eb;
}

.group-section.ungrouped {
  border-style: dashed;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
  border-radius: 6px 6px 0 0;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.group-count {
  font-size: 13px;
  color: #909399;
}

.group-actions {
  display: flex;
  gap: 4px;
}

.group-content {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px;
  min-height: 70px;
}

.author-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
  border: 1px solid transparent;
  flex: 1;
  min-width: 200px;
  max-width: 100%;
}

.author-card:hover {
  background: #e9ecf0;
  border-color: #409eff;
}

.author-card:active {
  cursor: grabbing;
}

.author-info {
  flex: 1;
  min-width: 80px;
  overflow: hidden;
}

.author-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.author-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.author-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.author-card:hover .author-actions {
  opacity: 1;
}

.empty-hint {
  width: 100%;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 16px 0;
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
    justify-content: flex-end;
  }

  .btn-text {
    display: none;
  }

  .action-btn {
    padding: 8px 12px;
  }

  .groups-container {
    gap: 12px;
  }

  .group-header {
    padding: 8px 12px;
  }

  .group-name {
    font-size: 14px;
  }

  .group-content {
    padding: 10px;
    gap: 8px;
  }

  .author-card {
    min-width: 0 !important;
    flex: 0 0 calc(50% - 4px) !important;
    max-width: calc(50% - 4px) !important;
    width: calc(50% - 4px) !important;
    padding: 8px 10px;
    font-size: 13px;
  }

  .author-name {
    font-size: 13px;
  }

  .author-info {
    min-width: 60px;
  }

  /* 移动端始终显示操作按钮 */
  .author-actions {
    opacity: 1;
  }

  .author-name {
    font-size: 13px;
  }
}

/* 弹窗适配 */
:global(.responsive-dialog) {
  max-width: 90vw !important;
}
</style>
