<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DataLine, User, VideoPlay, Setting, Fold, Expand } from '@element-plus/icons-vue'
import SettingsModal from './components/SettingsModal.vue'

const router = useRouter()
const route = useRoute()
const showSettings = ref(false)

// 侧边栏状态
const isCollapsed = ref(false)
const isMobile = ref(true) // 默认为移动端，避免闪烁
const showMobileMenu = ref(false)
const isReady = ref(false) // 标记是否已完成初始化

const menuItems = [
  { path: '/', icon: DataLine, label: '数据看板' },
  { path: '/authors', icon: User, label: 'UP主管理' },
  { path: '/videos', icon: VideoPlay, label: '视频列表' },
]

// 计算侧边栏宽度
const asideWidth = computed(() => {
  if (isMobile.value) return '220px'
  return isCollapsed.value ? '64px' : '220px'
})

// 检测屏幕宽度
const checkScreenSize = () => {
  const width = window.innerWidth
  isMobile.value = width < 768
  if (isMobile.value) {
    showMobileMenu.value = false
  }
}

// 切换侧边栏
const toggleSidebar = () => {
  if (isMobile.value) {
    showMobileMenu.value = !showMobileMenu.value
  } else {
    isCollapsed.value = !isCollapsed.value
  }
}

// 菜单选择
const handleMenuSelect = (path: string) => {
  router.push(path)
  if (isMobile.value) {
    showMobileMenu.value = false
  }
}

// 点击遮罩关闭菜单
const handleOverlayClick = () => {
  showMobileMenu.value = false
}

onMounted(() => {
  checkScreenSize()
  isReady.value = true
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<template>
  <el-container style="height: 100vh;">
    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && showMobileMenu"
      class="mobile-overlay"
      @click="handleOverlayClick"
    />

    <!-- 侧边栏 -->
    <el-aside
      v-if="isReady"
      :width="asideWidth"
      class="sidebar"
      :class="{
        'sidebar-collapsed': !isMobile && isCollapsed,
        'sidebar-mobile': isMobile,
        'sidebar-mobile-hidden': isMobile && !showMobileMenu
      }"
    >
      <!-- Logo -->
      <div class="logo">
        <span v-if="!isCollapsed || isMobile" class="logo-text">🎬 Spider</span>
        <span v-else class="logo-icon">🎬</span>
      </div>

      <!-- 菜单 -->
      <el-menu
        :default-active="route.path"
        :collapse="!isMobile && isCollapsed"
        background-color="#001529"
        text-color="#fff"
        active-text-color="#fe2c55"
        @select="handleMenuSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-button link class="toggle-btn" @click="toggleSidebar">
            <el-icon :size="20">
              <Fold v-if="(!isCollapsed && !isMobile) || (isMobile && showMobileMenu)" />
              <Expand v-else />
            </el-icon>
          </el-button>
        </div>
        <div class="header-right">
          <el-button link @click="showSettings = true">
            <el-icon><Setting /></el-icon>
            <span class="header-btn-text">设置</span>
          </el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
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

<style scoped>
/* 侧边栏 */
.sidebar {
  background: #001529;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
}

.sidebar-collapsed .el-menu {
  width: 64px;
}

/* 移动端侧边栏 */
.sidebar-mobile {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  z-index: 1001;
  transform: translateX(0);
}

.sidebar-mobile-hidden {
  transform: translateX(-100%);
}

/* 移动端遮罩 */
.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

/* Logo */
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
}

.logo-text {
  transition: opacity 0.3s;
}

.logo-icon {
  font-size: 24px;
}

/* 主容器 */
.main-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 顶部栏 */
.header {
  background: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 60px !important;
}

.header-left {
  display: flex;
  align-items: center;
}

.toggle-btn {
  padding: 8px;
}

.header-right {
  display: flex;
  align-items: center;
}

/* 主内容 */
.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .main-content {
    padding: 12px;
  }

  .header-btn-text {
    display: none;
  }

  .logo {
    font-size: 16px;
  }
}
</style>
