<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { setCookie as saveCookie, verifyCookie, getModelConfig, saveTranscribeModelConfig, saveRewriteModelConfig } from '../services/api'

const cookieValue = ref('')
const loading = ref(false)
const verifying = ref(false)
const cookieStatus = ref<{ valid: boolean; message: string } | null>(null)

// 模型配置
const transcribeApiBase = ref('')
const transcribeApiKey = ref('')
const transcribeModel = ref('')
const rewriteApiBase = ref('')
const rewriteApiKey = ref('')
const rewriteModel = ref('')
const savingModel = ref(false)

const handleVerify = async () => {
  verifying.value = true
  try {
    cookieStatus.value = await verifyCookie()
    if (cookieStatus.value.valid) {
      ElMessage.success('Cookie有效')
    } else {
      ElMessage.warning(cookieStatus.value.message)
    }
  } catch (e) {
    ElMessage.error('验证失败')
  } finally {
    verifying.value = false
  }
}

const handleSave = async () => {
  if (!cookieValue.value.trim()) {
    ElMessage.warning('请输入Cookie')
    return
  }

  loading.value = true
  try {
    await saveCookie(cookieValue.value.trim())
    ElMessage.success('Cookie保存成功')
    // 保存后自动验证
    await handleVerify()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}

// 加载模型配置
const loadModelConfig = async () => {
  try {
    const result = await getModelConfig()
    if (result.success) {
      transcribeApiBase.value = result.transcribe.api_base
      transcribeApiKey.value = result.transcribe.api_key
      transcribeModel.value = result.transcribe.model
      rewriteApiBase.value = result.rewrite.api_base
      rewriteApiKey.value = result.rewrite.api_key
      rewriteModel.value = result.rewrite.model
    }
  } catch (e) {
    console.error('加载模型配置失败:', e)
  }
}

// 保存语音转写模型配置
const handleSaveTranscribeModel = async () => {
  if (!transcribeApiBase.value.trim() || !transcribeApiKey.value.trim() || !transcribeModel.value.trim()) {
    ElMessage.warning('请填写完整的语音转写模型配置')
    return
  }

  savingModel.value = true
  try {
    const result = await saveTranscribeModelConfig(
      transcribeApiBase.value.trim(),
      transcribeApiKey.value.trim(),
      transcribeModel.value.trim()
    )
    if (result.success) {
      ElMessage.success(result.message)
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingModel.value = false
  }
}

// 保存文案仿写模型配置
const handleSaveRewriteModel = async () => {
  if (!rewriteApiBase.value.trim() || !rewriteApiKey.value.trim() || !rewriteModel.value.trim()) {
    ElMessage.warning('请填写完整的文案仿写模型配置')
    return
  }

  savingModel.value = true
  try {
    const result = await saveRewriteModelConfig(
      rewriteApiBase.value.trim(),
      rewriteApiKey.value.trim(),
      rewriteModel.value.trim()
    )
    if (result.success) {
      ElMessage.success(result.message)
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingModel.value = false
  }
}

onMounted(() => {
  // 页面加载时自动验证Cookie
  handleVerify()
  // 加载模型配置
  loadModelConfig()
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">系统设置</h2>
    </div>

    <!-- 设置卡片 -->
    <el-card shadow="never" class="settings-card">
      <el-tabs type="border-card">
        <!-- 模型设置 -->
        <el-tab-pane label="🔧 模型设置">
          <el-form label-position="top" class="compact-form">
            <!-- 语音转写配置 -->
            <div class="model-section">
              <h4 class="section-title">🎤 语音转写模型</h4>
              <el-form-item label="API地址">
                <el-input
                  v-model="transcribeApiBase"
                  placeholder="例如: https://open.bigmodel.cn/api/paas/v4"
                />
              </el-form-item>
              <el-form-item label="API密钥">
                <el-input
                  v-model="transcribeApiKey"
                  type="password"
                  show-password
                  placeholder="输入API密钥"
                />
              </el-form-item>
              <el-form-item label="模型名称">
                <el-input
                  v-model="transcribeModel"
                  placeholder="例如: glm-asr-2512"
                />
              </el-form-item>
              <div class="model-actions">
                <el-button type="primary" size="small" :loading="savingModel" @click="handleSaveTranscribeModel">
                  保存转写配置
                </el-button>
              </div>
              <el-divider />
            </div>

            <!-- 文案仿写配置 -->
            <div class="model-section">
              <h4 class="section-title">✨ 文案仿写模型</h4>
              <el-form-item label="API地址">
                <el-input
                  v-model="rewriteApiBase"
                  placeholder="例如: https://open.bigmodel.cn/api/paas/v4"
                />
              </el-form-item>
              <el-form-item label="API密钥">
                <el-input
                  v-model="rewriteApiKey"
                  type="password"
                  show-password
                  placeholder="输入API密钥"
                />
              </el-form-item>
              <el-form-item label="模型名称">
                <el-input
                  v-model="rewriteModel"
                  placeholder="例如: glm-4.7, glm-4, glm-4-air"
                />
              </el-form-item>
              <div class="model-actions">
                <el-button type="primary" size="small" :loading="savingModel" @click="handleSaveRewriteModel">
                  保存仿写配置
                </el-button>
              </div>
            </div>

            <el-alert type="warning" :closable="false" style="margin-top: 20px;">
              <template #title>
                <strong>⚠️ 重要提示：</strong>
                <ul style="margin: 8px 0 0 20px; padding: 0;">
                  <li>API密钥将加密保存在数据库中</li>
                  <li>更改配置后，新的任务将使用新配置</li>
                  <li>不同服务商的API格式可能不兼容，请确保配置正确</li>
                  <li>智谱AI: glm-asr-2512（转写）、glm-4.7（仿写）</li>
                </ul>
              </template>
            </el-alert>
          </el-form>
        </el-tab-pane>

        <!-- Cookie设置 -->
        <el-tab-pane label="🍪 Cookie设置">
          <el-form label-position="top" class="compact-form">
            <el-form-item label="Cookie">
              <el-input
                v-model="cookieValue"
                type="textarea"
                :rows="6"
                placeholder="粘贴从浏览器获取的Cookie..."
              />
            </el-form-item>

            <!-- Cookie状态显示 -->
            <div v-if="cookieStatus" class="cookie-status">
              <el-alert
                :type="cookieStatus.valid ? 'success' : 'error'"
                :closable="false"
                show-icon
              >
                <template #title>
                  {{ cookieStatus.valid ? 'Cookie状态：有效' : 'Cookie状态：无效' }}
                </template>
                <template #default v-if="!cookieStatus.valid">
                  {{ cookieStatus.message }}
                </template>
              </el-alert>
            </div>

            <el-alert type="info" :closable="false" class="info-alert">
              <template #title>
                <strong>获取方式：</strong>登录抖音网页版 → F12 → Network → 刷新 → 点击请求 → 复制Cookie
              </template>
            </el-alert>

            <div class="action-buttons">
              <el-button @click="handleVerify" :loading="verifying">
                验证Cookie
              </el-button>
              <el-button type="primary" :loading="loading" @click="handleSave">
                保存Cookie
              </el-button>
            </div>
          </el-form>
        </el-tab-pane>
      </el-tabs>
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

.settings-card {
  max-width: 900px;
}

.compact-form {
  max-width: 100%;
}

.cookie-status {
  margin-bottom: 15px;
}

.info-alert {
  margin-bottom: 15px;
}

.template-management {
  padding: 8px 0;
}

.toolbar {
  margin-bottom: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 15px;
}

.model-hint {
  margin-top: 4px;
  color: #909399;
}

.model-section {
  margin-bottom: 20px;
}

.section-title {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.model-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .page-title {
    font-size: 16px;
  }

  .settings-card {
    max-width: 100%;
  }

  .settings-card :deep(.el-tabs__header) {
    flex-wrap: wrap;
  }

  .settings-card :deep(.el-tabs__nav-wrap) {
    overflow-x: auto;
  }

  .settings-card :deep(.el-tabs__item) {
    font-size: 13px;
    padding: 0 12px;
    white-space: nowrap;
  }

  .settings-card :deep(.el-form-item__label) {
    font-size: 13px;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .section-title {
    font-size: 14px;
  }

  .model-actions {
    flex-wrap: wrap;
  }

  .model-actions .el-button {
    flex: 1;
    min-width: 100px;
  }

  .info-alert :deep(.el-alert__title) {
    font-size: 13px;
  }

  .info-alert :deep(.el-alert__description) {
    font-size: 12px;
  }

  /* 弹窗适配 */
  :deep(.el-dialog) {
    width: 95% !important;
    max-width: 95% !important;
    margin: 0 auto;
  }

  :deep(.el-dialog__body) {
    padding: 15px;
  }

  :deep(.el-dialog__footer) {
    padding: 10px 15px;
  }
}
</style>
