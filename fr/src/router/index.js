import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
// 从stores中获取用户信息
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import axios from 'axios'
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: '首页' }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登录', guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { title: '注册', guest: true }
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true, title: '聊天' }
    },
    {
      path: '/log',
      name: 'log',
      component: () => import('../views/log.vue'),
      meta: { guest: true, title: '日志' }
    },
    {
      path: '/files',
      name: 'files',
      component: () => import('../views/FileManagerView.vue'),
      meta: { requiresAuth: true, title: '文件管理' }
    },
    {
      path: '/file-manager',
      name: 'file-manager',
      component: () => import('../views/FileManagerView.vue'),
      meta: { requiresAuth: true, title: '文件管理' }
    },
    {
      path: '/extensions',
      name: 'extensions',
      component: () => import('../views/extension/ExtensionsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '扩展管理' }
    },
    {
      path: '/extensions/:id',
      name: 'extension-detail',
      component: () => import('../views/extension/ExtensionDetail.vue'),
      meta: { requiresAuth: true, title: '扩展详情' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/settings/SettingsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: '系统设置' }
    },
    {
      path: '/scheduler',
      name: 'scheduler',
      component: () => import('../views/scheduler/index.vue'),
      props: { activeTab: 'scheduler' },
      meta: { requiresAuth: true, requiresAdmin: true, title: '任务调度' }
    },
    {
      path: '/scheduler/add',
      name: 'AddJob-scheduler',
      component: () => import('../views/scheduler/AddJob.vue'),
      props: { activeTab: 'scheduler' },
      meta: { requiresAuth: true, requiresAdmin: true, title: '添加定时任务' }
    },
    {
      path: '/scheduler/job/:id',
      name: 'JobDetail-scheduler',
      component: () => import('../views/scheduler/JobDetail.vue'),
      props: { activeTab: 'scheduler' },
      meta: { requiresAuth: true, requiresAdmin: true, title: '管理定时任务' }
    },
    {
      path: '/help',
      name: 'help',
      component: () => import('../views/HelpView.vue'),
      meta: { title: '帮助' }
    },
    {
      path: '/example',
      name: 'example',
      component: () => import('../views/ExampleView.vue'),
      meta: { title: '示例' }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/UserProfile.vue'),
      meta: { requiresAuth: true, title: '用户资料' }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true, title: '控制面板' }
    },
    {
      path: '/database',
      name: 'database',
      component: () => import('../views/DatabaseManager.vue'),
      meta: {
        //requiresAuth: true,
        //permissions: ['manage_extension_db', 'view_extension_db'],
        title: '数据库管理'
      }
    },
    {
      path: '/extension-query',
      name: 'extension-query',
      component: () => import('../views/extension/ExtensionQueryView.vue'),
      meta: { requiresAuth: true, title: '扩展查询' }
    },
    //{
    //  path: '/extension-query/:id',
    //  name: 'extension-query-detail',
    //  component: () => import('../views/ExtensionQueryDetail.vue'),
    //  meta: { requiresAuth: true, title: '扩展查询详情' }
    //}
  ]
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  // 直接从 store 获取响应式状态
const userStore = useUserStore()
const { user, isLoggedIn } = storeToRefs(userStore)
const { logout, init } = userStore

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 智能助手系统` : '智能助手系统'
    
  // 检查路由是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try {
      //如果是登录状态，则直接通过
      if (isLoggedIn.value) {
        return next()
      }
      // 先尝试使用localStorage中的token
      const token = localStorage.getItem('token')
      if (!token) {
        // 未登录，重定向到登录页
        return next({ name: 'login', query: { redirect: to.fullPath } })
      }
      
      // 检查是否需要特定权限
      if (to.meta.permissions) {
        const userInfo = userStore?.user
        const userPermissions = userInfo?.permissions || []
        
        const hasPermission = to.meta.permissions.some(permission => 
          userPermissions.includes(permission)
        )
        
        if (!hasPermission) {
          return next({ name: 'dashboard' })
        }
      }
      
      // 检查是否需要特定权限
      if (to.meta.requiresPermission) {
        const userPermissions = userInfo.permissions || []
        
        if (!userPermissions.includes(to.meta.requiresPermission)) {
          return next({ name: 'dashboard' })
        }
      }
      
      // 检查是否需要管理员权限
      if (to.matched.some(record => record.meta.requiresAdmin)) {
        // 尝试从本地存储获取用户信息
        
        if (!user.is_superuser) {
          // 不是管理员，重定向到首页
          return next({ name: 'home' })
        }
        
        // 如果本地没有有效信息，尝试从API获取
        try {
          const response = await axios.get('/api/auth/me')
          const data = response.data
          if (!data || !data.id || !data.is_superuser) {
            // 不是管理员，重定向到首页
            return next({ name: 'home' })
          }
        } catch (error) {
          console.error('验证用户失败', error)
          return next({ name: 'login', query: { redirect: to.fullPath } })
        }
      }
      
      // 通过验证，继续导航
      next()
    } catch (error) {
      console.error('验证用户失败', error)
      next({ name: 'login', query: { redirect: to.fullPath } })
    }
  } else {
    // 不需要认证的路由，直接通过
    next()
  }
})

export default router