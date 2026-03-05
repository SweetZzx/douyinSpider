<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPromptTemplates, createPromptTemplate, updatePromptTemplate, copyPromptTemplate, deletePromptTemplate } from '../services/api'
import type { PromptTemplate } from '../types'

const templates = ref<PromptTemplate[]>([])
const templateDialogVisible = ref(false)
const isEditMode = ref(false)
const saving = ref(false)

const templateForm = ref({
  id: 0,
  name: '',
  content: '',
  description: '',
  is_default: false,
  category: 'rewrite'
})

// 文案仿写提示词
const rewritePrompt = ref('')
const savingPrompt = ref(false)
const selectedRewriteTemplateId = ref<number | null>(null)
const selectedWritingTemplateId = ref<number | null>(null)

// 提示词管理tab中选中的分类
const managementCategory = ref<'rewrite' | 'writing'>('rewrite')

// 加载模板列表
const loadTemplates = async () => {
  try {
    const result = await getPromptTemplates()
    if (result.success) {
      templates.value = result.templates
      // 自动选择各分类的默认模板
      const rewriteDefault = result.templates.find(t => t.category === 'rewrite' && t.is_default)
      const writingDefault = result.templates.find(t => t.category === 'writing' && t.is_default)

      if (rewriteDefault) {
        selectedRewriteTemplateId.value = rewriteDefault.id
        rewritePrompt.value = rewriteDefault.content
      }
      if (writingDefault) selectedWritingTemplateId.value = writingDefault.id
    }
  } catch (e) {
    ElMessage.error('加载模板失败')
  }
}

// 更新选中的模板
const handleUpdatePrompt = async () => {
  if (!selectedRewriteTemplateId.value) {
    ElMessage.warning('请先选择一个模板')
    return
  }

  if (!rewritePrompt.value.trim()) {
    ElMessage.warning('提示词不能为空')
    return
  }

  savingPrompt.value = true
  try {
    const result = await updatePromptTemplate(selectedRewriteTemplateId.value, {
      content: rewritePrompt.value.trim()
    })
    if (result.success) {
      ElMessage.success(result.message)
      await loadTemplates()
    }
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    savingPrompt.value = false
  }
}

// 删除选中的模板
const handleDeleteTemplate = async () => {
  if (!selectedRewriteTemplateId.value) {
    ElMessage.warning('请先选择一个模板')
    return
  }

  const template = templates.value.find(t => t.id === selectedRewriteTemplateId.value)
  if (!template) return

  if (template.is_system) {
    ElMessage.warning('系统默认模板不能删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${template.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const result = await deletePromptTemplate(selectedRewriteTemplateId.value)
    if (result.success) {
      ElMessage.success(result.message)
      await loadTemplates()
      // 清空文本框
      rewritePrompt.value = ''
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 复制选中的模板
const handleCopyTemplate = async () => {
  if (!selectedRewriteTemplateId.value) {
    ElMessage.warning('请先选择一个模板')
    return
  }

  try {
    const result = await copyPromptTemplate(selectedRewriteTemplateId.value)
    if (result.success) {
      ElMessage.success(result.message)
      await loadTemplates()
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '复制失败')
  }
}

// 选择模板
const handleTemplateChange = (templateId: number | null) => {
  if (templateId !== null) {
    const template = templates.value.find(t => t.id === templateId)
    if (template) {
      rewritePrompt.value = template.content
    }
  } else {
    // 清空选择时，清空文本框
    rewritePrompt.value = ''
  }
}

// 切换分类
const handleCategoryChange = () => {
  // 清空当前选择
  selectedRewriteTemplateId.value = null
  rewritePrompt.value = ''

  // 自动选择新分类的默认模板
  const defaultTemplate = templates.value.find(
    t => t.category === managementCategory.value && t.is_default
  )
  if (defaultTemplate) {
    selectedRewriteTemplateId.value = defaultTemplate.id
    rewritePrompt.value = defaultTemplate.content
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEditMode.value = false
  templateForm.value = {
    id: 0,
    name: '',
    content: '',
    description: '',
    is_default: false,
    category: managementCategory.value
  }
  templateDialogVisible.value = true
}

// 保存模板
const saveTemplate = async () => {
  if (!templateForm.value.name.trim()) {
    ElMessage.warning('请输入模板名称')
    return
  }
  if (!templateForm.value.content.trim()) {
    ElMessage.warning('请输入提示词内容')
    return
  }

  saving.value = true
  try {
    if (isEditMode.value) {
      const result = await updatePromptTemplate(templateForm.value.id, templateForm.value)
      if (result.success) {
        ElMessage.success(result.message)
      }
    } else {
      const result = await createPromptTemplate(templateForm.value)
      if (result.success) {
        ElMessage.success(result.message)
      }
    }
    templateDialogVisible.value = false
    await loadTemplates()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<template>
  <div>
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">提示词设置</h2>
    </div>

    <!-- 设置卡片 -->
    <el-card shadow="never" class="settings-card">
      <el-tabs type="border-card">
        <!-- 提示词管理 -->
        <el-tab-pane label="📝 提示词管理">
          <el-form label-position="top" class="compact-form">
            <el-form-item label="提示词分类">
              <el-radio-group v-model="managementCategory" @change="handleCategoryChange">
                <el-radio-button value="rewrite">文案仿写</el-radio-button>
                <el-radio-button value="writing">文案写作</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="选择提示词模板">
              <div class="template-selector-row">
                <el-select
                  v-model="selectedRewriteTemplateId"
                  placeholder="选择已配置的提示词模板"
                  clearable
                  @change="handleTemplateChange"
                  class="template-select"
                >
                  <el-option
                    v-for="template in templates.filter(t => t.category === managementCategory)"
                    :key="template.id"
                    :label="template.name"
                    :value="template.id"
                  >
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                      <span>{{ template.name }}</span>
                      <el-tag v-if="template.is_system" type="danger" size="small" style="margin-left: 8px">
                        sys
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
                <el-button type="primary" size="small" @click="showCreateDialog">
                  + 新建模板
                </el-button>
              </div>
            </el-form-item>
            <el-form-item :label="`${managementCategory === 'rewrite' ? '文案仿写' : '文案写作'}提示词`">
              <el-input
                v-model="rewritePrompt"
                type="textarea"
                :rows="10"
                :placeholder="`输入自定义的${managementCategory === 'rewrite' ? '文案仿写' : '文案写作'}提示词...`"
              />
              <div class="prompt-actions">
                <el-button size="small" type="danger" @click="handleDeleteTemplate">
                  删除
                </el-button>
                <el-button size="small" type="info" @click="handleCopyTemplate">
                  复制
                </el-button>
                <el-button type="primary" size="small" @click="handleUpdatePrompt" :loading="savingPrompt">
                  保存
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 模板编辑对话框 -->
    <el-dialog
      v-model="templateDialogVisible"
      :title="isEditMode ? '编辑模板' : '新建模板'"
      width="700px"
    >
      <el-form :model="templateForm" label-width="100px" class="template-form">
        <el-form-item label="模板名称" required>
          <el-input v-model="templateForm.name" placeholder="输入模板名称" />
        </el-form-item>
        <el-form-item label="模板描述">
          <el-input v-model="templateForm.description" placeholder="输入模板描述" />
        </el-form-item>
        <el-form-item label="提示词内容" required>
          <el-input
            v-model="templateForm.content"
            type="textarea"
            :rows="15"
            placeholder="输入提示词内容..."
          />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="templateForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 20px;
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

.template-selector-row {
  display: flex;
  gap: 12px;
  align-items: center;
  width: 100%;
}

.template-selector-row :deep(.el-select) {
  flex: 1;
  max-width: calc(100% - 100px);
}

.prompt-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  justify-content: flex-end;
}

.settings-toolbar {
  margin-bottom: 16px;
}

.prompt-settings {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.prompt-section {
  padding: 8px 0;
}

.template-table {
  margin-top: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.template-form {
  max-width: 100%;
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

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .section-title {
    font-size: 13px;
  }

  .template-selector-row {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .template-selector-row :deep(.el-select) {
    max-width: 100%;
  }

  .template-selector-row .el-button {
    width: 100%;
  }

  .prompt-actions {
    flex-wrap: wrap;
  }

  .prompt-actions .el-button {
    flex: 1;
    min-width: 80px;
  }

  .prompt-section {
    padding: 6px 0;
  }

  .prompt-settings {
    gap: 16px;
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

  .template-form :deep(.el-form-item__label) {
    font-size: 13px;
  }

  .template-form :deep(.el-input__inner),
  .template-form :deep(.el-textarea__inner) {
    font-size: 14px;
  }
}
</style>
