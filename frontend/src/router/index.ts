import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const placeholder = () => import('@/views/ModulePlaceholder.vue')

const appChildren: RouteRecordRaw[] = [
  {
    path: 'overview',
    name: 'overview',
    component: () => import('@/views/OverviewView.vue'),
    meta: {
      title: '运行概览',
      description: '智能运维平台驾驶舱，聚焦 SLA、告警与风险项',
    },
  },
  {
    path: 'assets',
    name: 'assets',
    component: placeholder,
    meta: {
      title: '资产登记',
      description: '维护一级业务、环境、资产与负责人',
    },
  },
  {
    path: 'platform',
    name: 'platform',
    component: placeholder,
    meta: {
      title: '平台管理',
      description: 'K8s 集群、容器环境与镜像管理',
    },
  },
  {
    path: 'observe',
    redirect: '/observe/overview',
  },
  {
    path: 'observe/overview',
    name: 'observe-overview',
    component: placeholder,
    meta: {
      title: '可观测性 · 平台总览',
      description: '观测面总览与关键健康指标',
    },
  },
  {
    path: 'observe/boards',
    name: 'observe-boards',
    component: placeholder,
    meta: {
      title: '可观测性 · 监控看板',
      description: 'Prometheus 兼容监控看板',
    },
  },
  {
    path: 'observe/logs',
    name: 'observe-logs',
    component: placeholder,
    meta: {
      title: '可观测性 · 日志中心',
      description: 'Loki / ELK 日志检索编排',
    },
  },
  {
    path: 'observe/alerts',
    name: 'observe-alerts',
    component: placeholder,
    meta: {
      title: '可观测性 · 告警中心',
      description: '告警收敛、路由与静默',
    },
  },
  {
    path: 'tasks',
    name: 'tasks',
    component: placeholder,
    meta: {
      title: '任务中心',
      description: '主机 / K8s 任务、Playbook 与执行记录',
    },
  },
  {
    path: 'tickets',
    name: 'tickets',
    component: placeholder,
    meta: {
      title: '工单系统',
      description: '发布、审批流、SQL 审计与事务工单',
    },
  },
  {
    path: 'events',
    name: 'events',
    component: placeholder,
    meta: {
      title: '事件中心',
      description: '平台 / 外部事件与排障复盘时间线',
    },
  },
  {
    path: 'aiops',
    name: 'aiops',
    component: placeholder,
    meta: {
      title: 'AIOps',
      description: '智能助手、知识图谱与受控 Action',
    },
  },
  {
    path: 'rbac',
    name: 'rbac',
    component: placeholder,
    meta: {
      title: '权限审计',
      description: 'RBAC、路由 / 菜单 / 按钮与 WebSocket 权限',
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/overview' },
        ...appChildren,
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/overview',
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.bootstrapped) {
    await auth.fetchMe()
  }

  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === 'login') {
      return { name: 'overview' }
    }
    return true
  }

  if (to.matched.some((record) => record.meta.requiresAuth) && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
