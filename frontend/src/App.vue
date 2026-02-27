<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DataLine, User, VideoPlay, Setting } from '@element-plus/icons-vue'
import SettingsModal from './components/SettingsModal.vue'

const router = useRouter()
const route = useRoute()
const showSettings = ref(false)

const menuItems = [
  { path: '/', icon: DataLine, label: '数据看板' },
  { path: '/authors', icon: User, label: 'UP主管理' },
  { path: '/videos', icon: VideoPlay, label: '视频列表' },
]

const handleMenuSelect = (path: string) => {
  router.push(path)
}
</script>

<template>
  <el-container style="height: 100vh;">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background: #001529;">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: bold;">
        🎬 抖音Spider
      </div>
      <el-menu
        :default-active="route.path"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#fe2c55"
        @select="handleMenuSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header style="background: #fff; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: flex-end; padding: 0 20px;">
        <el-button link @click="showSettings = true">
          <el-icon><Setting /></el-icon> 设置
        </el-button>
      </el-header>

      <el-main style="background: #f5f7fa; padding: 20px;">
        <router-view />
      </el-main>
    </el-container>

    <!-- 设置弹窗 -->
    <SettingsModal v-if="showSettings" @close="showSettings = false" />
  </el-container>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.el-menu-item.is-active {
  background-color: rgba(254, 44, 85, 0.2) !important;
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}
</style>
