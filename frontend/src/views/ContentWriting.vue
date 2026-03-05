<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { chatWithAI, getPromptTemplates } from '../services/api'
import type { PromptTemplate } from '../types'

// 对话消息
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const messages = ref<Message[]>([])
const userInput = ref('')
const loading = ref(false)
const chatContainer = ref<HTMLElement>()

// 提示词模板
const templates = ref<PromptTemplate[]>([])
const selectedTemplateId = ref<number | null>(null)

// 加载提示词模板
const loadTemplates = async () => {
  try {
    const result = await getPromptTemplates()
    if (result.success) {
      templates.value = result.templates
      // 自动选择默认的写作模板
      const defaultTemplate = result.templates.find(t => t.is_default && t.category === 'writing')
      if (defaultTemplate) {
        selectedTemplateId.value = defaultTemplate.id
      }
    }
  } catch (e) {
    console.error('加载模板失败:', e)
  }
}

// 获取选中的提示词
const getSelectedPrompt = () => {
  if (selectedTemplateId.value) {
    const template = templates.value.find(t => t.id === selectedTemplateId.value)
    return template?.content || ''
  }
  return ''
}

// 发送消息
const sendMessage = async () => {
  const content = userInput.value.trim()
  if (!content) {
    ElMessage.warning('请输入消息')
    return
  }

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content,
    timestamp: new Date()
  })

  userInput.value = ''
  loading.value = true

  // 滚动到底部
  await scrollToBottom()

  try {
    const customPrompt = getSelectedPrompt()
    const result = await chatWithAI(content, messages.value.slice(0, -1).map(m => ({
      role: m.role,
      content: m.content
    })), customPrompt)

    if (result.success) {
      // 添加助手回复
      messages.value.push({
        role: 'assistant',
        content: result.response,
        timestamp: new Date()
      })
    } else {
      ElMessage.error(result.message || '发送失败')
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '发送失败')
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 按回车发送
const handleKeyPress = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 清空对话
const clearChat = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

// 获取当前时间
const formatTime = (date: Date) => {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadTemplates()
  // 添加欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是你的文案写作助手，有什么可以帮助你的吗？',
    timestamp: new Date()
  })
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">文案写作</h2>
      <div class="page-actions">
        <el-select
          v-model="selectedTemplateId"
          placeholder="选择提示词模板"
          clearable
          class="template-selector"
        >
          <el-option
            v-for="template in templates.filter(t => t.category === 'writing')"
            :key="template.id"
            :label="template.name"
            :value="template.id"
          >
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <span>{{ template.name }}</span>
              <el-tag v-if="template.is_default" type="success" size="small" style="margin-left: 8px">
                默认
              </el-tag>
            </div>
          </el-option>
        </el-select>
      </div>
    </div>

    <!-- 对话区域 -->
    <el-card shadow="never" class="chat-card">
      <div ref="chatContainer" class="chat-messages">
        <div
          v-for="(message, index) in messages"
          :key="index"
          :class="['message', message.role]"
        >
          <div class="message-avatar">
            <span v-if="message.role === 'user'">👤</span>
            <span v-else>🤖</span>
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="loading" class="message assistant loading">
          <div class="message-avatar">
            <span>🤖</span>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-area">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="2"
          placeholder="输入你的消息... (Enter 发送，Shift+Enter 换行)"
          @keydown="handleKeyPress"
          :disabled="loading"
        />
        <div class="input-actions">
          <el-button @click="clearChat" :disabled="loading || messages.length === 0">
            清空对话
          </el-button>
          <el-button
            type="primary"
            @click="sendMessage"
            :loading="loading"
            :disabled="!userInput.trim()"
          >
            发送
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 18px;
}

.page-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.template-selector {
  width: 200px;
}

.chat-card {
  margin-bottom: 20px;
}

.chat-messages {
  height: 500px;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.message {
  display: flex;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message.user .message-avatar {
  margin-left: 12px;
}

.message.assistant .message-avatar {
  margin-right: 12px;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 8px;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
}

.message.user .message-text {
  background: #fe2c55;
  color: #fff;
}

.message.assistant .message-text {
  background: #fff;
  color: #303133;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  padding: 0 4px;
}

.message.loading .message-text {
  background: #fff;
  padding: 16px 20px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fe2c55;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.chat-input-area {
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 移动端适配 */
@media (max-width: 768px) {
  /* 容器优化 */
  :deep(.el-card__body) {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 12px;
  }

  .page-title {
    font-size: 16px;
  }

  .page-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .page-actions :deep(.el-select) {
    width: 100% !important;
  }

  .template-selector {
    width: 100%;
  }

  .chat-card {
    margin-bottom: 12px;
  }

  :deep(.chat-card .el-card__body) {
    padding: 12px;
  }

  .chat-messages {
    height: calc(100vh - 280px);
    min-height: 250px;
    max-height: 60vh;
    padding: 10px;
  }

  .message {
    margin-bottom: 10px;
  }

  .message-avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .message.user .message-avatar {
    margin-left: 8px;
  }

  .message.assistant .message-avatar {
    margin-right: 8px;
  }

  .message-content {
    max-width: 75%;
  }

  .message-text {
    padding: 8px 12px;
    font-size: 14px;
    line-height: 1.5;
    border-radius: 12px;
  }

  .message.user .message-text {
    border-bottom-right-radius: 4px;
  }

  .message.assistant .message-text {
    border-bottom-left-radius: 4px;
  }

  .message-time {
    font-size: 10px;
    margin-top: 2px;
    padding: 0 2px;
  }

  .chat-input-area {
    padding: 10px;
  }

  .chat-input-area :deep(.el-textarea__inner) {
    font-size: 14px;
    padding: 8px 10px;
    min-height: 50px !important;
  }

  .input-actions {
    flex-direction: row-reverse;
    gap: 8px;
    margin-top: 8px;
  }

  .input-actions .el-button {
    flex: 1;
    font-size: 14px;
    padding: 8px 12px;
  }

  .typing-indicator {
    padding: 8px 12px;
  }

  .typing-indicator span {
    width: 6px;
    height: 6px;
  }
}
</style>
