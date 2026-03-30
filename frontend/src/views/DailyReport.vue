<template>
  <div class="daily-report">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <span class="title">每日视频报告</span>
          <div class="info">
            <span class="time-range">{{ timeRange.start }} ~ {{ timeRange.end }}</span>
          </div>
        </div>
      </template>

      <div class="controls">
        <div class="date-picker-wrapper">
          <span class="label">选择日期：</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="handleDateChange"
          />
        </div>
        <div class="action-buttons">
          <el-button type="primary" @click="copyToClipboard" :disabled="!reportText">
            <el-icon><DocumentCopy /></el-icon>
            复制
          </el-button>
          <el-button @click="fetchReport" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <div class="stats">
        <span class="count">共 {{ videoCount }} 个视频</span>
      </div>

      <div class="editor-container">
        <el-input
          v-model="reportText"
          type="textarea"
          :rows="20"
          placeholder="暂无视频数据"
          readonly
          class="report-textarea"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DocumentCopy } from '@element-plus/icons-vue'
import { getDailyReport } from '../services/api'

const loading = ref(false)
const reportText = ref('')
const videoCount = ref(0)
const timeRange = ref({ start: '', end: '' })
const selectedDate = ref('')

// 获取默认日期（永远显示昨天的日期，过了午夜0点才更新）
const getDefaultDate = () => {
  const now = new Date()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  return yesterday.toISOString().split('T')[0]
}

const fetchReport = async () => {
  loading.value = true
  try {
    const result = await getDailyReport(selectedDate.value || undefined)
    if (result.success) {
      reportText.value = result.report || '暂无视频数据'
      videoCount.value = result.video_count
      timeRange.value = result.time_range
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取报告失败')
  } finally {
    loading.value = false
  }
}

const handleDateChange = () => {
  fetchReport()
}

const copyToClipboard = async () => {
  if (!reportText.value) return

  try {
    await navigator.clipboard.writeText(reportText.value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const textarea = document.createElement('textarea')
    textarea.value = reportText.value
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

onMounted(() => {
  selectedDate.value = getDefaultDate()
  fetchReport()
})
</script>

<style scoped>
.daily-report {
  padding: 20px;
}

.report-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.card-header .title {
  font-size: 18px;
  font-weight: bold;
}

.card-header .info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.time-range {
  color: #909399;
  font-size: 14px;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  flex-wrap: wrap;
  gap: 15px;
}

.date-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-picker-wrapper .label {
  color: #606266;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.stats {
  margin-bottom: 15px;
  padding: 10px 15px;
  background: #fff8e6;
  border-radius: 4px;
  border-left: 3px solid #ff85a2;
}

.count {
  color: #606266;
  font-size: 14px;
}

.editor-container {
  margin-bottom: 15px;
}

.report-textarea :deep(.el-textarea__inner) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.8;
  background: #fafafa;
}

@media (max-width: 768px) {
  .daily-report {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-header .info {
    width: 100%;
  }

  .time-range {
    font-size: 12px;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .date-picker-wrapper {
    flex-direction: column;
    align-items: flex-start;
  }

  .date-picker-wrapper :deep(.el-date-editor) {
    width: 100%;
  }
}
</style>