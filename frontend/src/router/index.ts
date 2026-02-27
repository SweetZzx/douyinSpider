import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Authors from '../views/Authors.vue'
import Videos from '../views/Videos.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/authors', name: 'Authors', component: Authors },
  { path: '/videos', name: 'Videos', component: Videos },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
