<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DataLine, User, VideoPlay, EditPen, Setting, Fold, Expand, Document } from '@element-plus/icons-vue'
import { logout, getUserInfo } from './services/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()

// 侧边栏状态
const isCollapsed = ref(false)
const isMobile = ref(true) // 默认为移动端，避免闪烁
const showMobileMenu = ref(false)
const isReady = ref(false) // 标记是否已完成初始化

// 子菜单展开状态
const settingsMenuOpen = ref(false)

// 当前用户角色
const userRole = ref<string>('user')

// 监听路由，自动展开设置菜单
const currentRoute = computed(() => route.path)

// 判断是否是认证页面（登录或注册）
const isAuthPage = computed(() => route.path === '/login' || route.path === '/register')

// 基础菜单项
const baseMenuItems = [
  { path: '/', icon: DataLine, label: '数据看板' },
  { path: '/authors', icon: User, label: 'UP主管理' },
  { path: '/videos', icon: VideoPlay, label: '视频列表' },
  { path: '/content-rewrite', icon: EditPen, label: '文案仿写' },
  { path: '/content-writing', icon: EditPen, label: '文案写作' },
]

// 动态菜单项（根据用户角色显示）
const menuItems = computed(() => {
  const items = [...baseMenuItems]
  // 只有super_admin角色显示"每日报告"菜单
  if (userRole.value === 'super_admin') {
    // 在"文案写作"后面插入"每日报告"
    items.splice(5, 0, { path: '/daily-report', icon: Document, label: '每日报告' })
  }
  return items
})

// 设置子菜单
const settingsSubMenus = [
  { path: '/settings', icon: Setting, label: '系统设置' },
  { path: '/settings/prompts', icon: EditPen, label: '提示词设置' },
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

// 切换设置子菜单
const toggleSettingsMenu = () => {
  settingsMenuOpen.value = !settingsMenuOpen.value
}

// 点击遮罩关闭菜单
const handleOverlayClick = () => {
  showMobileMenu.value = false
}

// 登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await logout()
    ElMessage.success('已退出登录')

    // 跳转到登录页
    router.push('/login')
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('登出失败:', error)
    }
  }
}

onMounted(() => {
  checkScreenSize()
  isReady.value = true
  // 检查当前路由是否在设置子菜单中
  if (currentRoute.value.startsWith('/settings')) {
    settingsMenuOpen.value = true
  }
  window.addEventListener('resize', checkScreenSize)

  // 获取当前用户角色
  const userInfo = getUserInfo()
  if (userInfo) {
    userRole.value = userInfo.role
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<template>
  <!-- 登录/注册页面：独立全屏显示 -->
  <div v-if="isAuthPage" class="login-page-wrapper">
    <router-view />
  </div>

  <!-- 主应用：带侧边栏和顶部栏 -->
  <el-container v-else style="height: 100vh;">
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
        active-text-color="#ff85a2"
        @select="handleMenuSelect"
      >
        <!-- 主菜单项 -->
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>

        <!-- 设置子菜单 -->
        <el-sub-menu
          index="settings"
          :popper-class="{ 'sidebar-submenu': true }"
          @click.native="toggleSettingsMenu"
        >
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item
            v-for="subItem in settingsSubMenus"
            :key="subItem.path"
            :index="subItem.path"
          >
            <el-icon><component :is="subItem.icon" /></el-icon>
            <template #title>{{ subItem.label }}</template>
          </el-menu-item>
        </el-sub-menu>
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
          <el-button link @click="handleLogout">
            <el-icon :size="18"><Setting /></el-icon>
            <span class="header-btn-text">退出登录</span>
          </el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
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

/* 登录页面包装器 */
.login-page-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>

<style scoped>
/* 侧边栏 */
.sidebar {
  background: #001529;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  border-right: none;
}

/* 移除el-aside默认边框 */
:deep(.el-aside) {
  border-right: none;
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
  background: #fff;
}

/* 顶部栏 */
.header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 60px !important;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
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
  /* 移除可能的默认边框 */
  border: none;
}

/* 确保整个容器平滑 */
:deep(.el-container) {
  border: none;
}

:deep(.el-main) {
  border: none;
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
