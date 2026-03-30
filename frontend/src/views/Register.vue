<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">🎬 Spider</h1>
        <p class="login-subtitle">注册新账号</p>
      </div>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        @submit.prevent="handleRegister"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名（至少3个字符）"
            prefix-icon="User"
            size="large"
            clearable
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="formData.email"
            type="email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
            size="large"
            clearable
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少6个字符）"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            size="large"
            class="login-button"
          >
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p class="login-tip">已有账号？<router-link to="/login">立即登录</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { register } from '../services/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== formData.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在3到50个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    await register(formData.username, formData.email, formData.password)

    ElMessage.success('注册成功，请登录')

    // 跳转到登录页
    router.push('/login')
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 8px 0;
  color: #333;
}

.login-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
}

.login-form {
  margin-top: 24px;
}

.login-button {
  width: 100%;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
}

.login-tip {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.login-tip a {
  color: #ff85a2;
  text-decoration: none;
}

.login-tip a:hover {
  text-decoration: underline;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-card {
    width: 90%;
    padding: 24px;
  }

  .login-title {
    font-size: 24px;
  }
}
</style>
