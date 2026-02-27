<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { setCookie as saveCookie, verifyCookie } from '../services/api'

const emit = defineEmits<{
  close: []
}>()

const cookieValue = ref('')
const loading = ref(false)
const verifying = ref(false)
const cookieStatus = ref<{ valid: boolean; message: string } | null>(null)

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
    emit('close')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-dialog
    title="设置"
    :model-value="true"
    @close="emit('close')"
    width="550px"
  >
    <el-form label-position="top">
      <el-form-item label="Cookie">
        <el-input
          v-model="cookieValue"
          type="textarea"
          :rows="5"
          placeholder="粘贴从浏览器获取的Cookie..."
        />
      </el-form-item>

      <!-- Cookie状态显示 -->
      <div v-if="cookieStatus" style="margin-bottom: 16px;">
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

      <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
        <template #title>
          获取方式：登录抖音网页版 → F12 → Network → 刷新 → 点击请求 → 复制Cookie
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <el-button @click="emit('close')">取消</el-button>
      <el-button @click="handleVerify" :loading="verifying">
        验证Cookie
      </el-button>
      <el-button type="danger" :loading="loading" @click="handleSave">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>
