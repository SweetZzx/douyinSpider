import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Authors from '../views/Authors.vue'
import Videos from '../views/Videos.vue'
import ContentRewrite from '../views/ContentRewrite.vue'
import ContentWriting from '../views/ContentWriting.vue'
import Settings from '../views/Settings.vue'
import Prompts from '../views/Prompts.vue'
import Login from '../views/Login.vue'
import { isLoggedIn } from '../services/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/authors',
    name: 'Authors',
    component: Authors,
    meta: { requiresAuth: true }
  },
  {
    path: '/videos',
    name: 'Videos',
    component: Videos,
    meta: { requiresAuth: true }
  },
  {
    path: '/content-rewrite',
    name: 'ContentRewrite',
    component: ContentRewrite,
    meta: { requiresAuth: true }
  },
  {
    path: '/content-writing',
    name: 'ContentWriting',
    component: ContentWriting,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings/prompts',
    name: 'Prompts',
    component: Prompts,
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false // 默认需要认证

  if (requiresAuth && !isLoggedIn()) {
    // 需要认证但未登录，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath } // 保存原始目标路径
    })
  } else if (to.path === '/login' && isLoggedIn()) {
    // 已登录用户访问登录页，跳转到首页
    next({ path: '/' })
  } else {
    next()
  }
})

export default router
