import type { Component } from 'vue'
import {
  Monitor,
  Box,
  Platform,
  DataLine,
  List,
  Document,
  Bell,
  MagicStick,
  Lock,
} from '@element-plus/icons-vue'

export interface AppMenuItem {
  path: string
  title: string
  icon: Component
  children?: { path: string; title: string }[]
}

export const appMenus: AppMenuItem[] = [
  { path: '/overview', title: '运行概览', icon: Monitor },
  { path: '/assets', title: '资产登记', icon: Box },
  { path: '/platform', title: '平台管理', icon: Platform },
  {
    path: '/observe',
    title: '可观测性',
    icon: DataLine,
    children: [
      { path: '/observe/overview', title: '平台总览' },
      { path: '/observe/boards', title: '监控看板' },
      { path: '/observe/logs', title: '日志中心' },
      { path: '/observe/alerts', title: '告警中心' },
    ],
  },
  { path: '/tasks', title: '任务中心', icon: List },
  { path: '/tickets', title: '工单系统', icon: Document },
  { path: '/events', title: '事件中心', icon: Bell },
  { path: '/aiops', title: 'AIOps', icon: MagicStick },
  { path: '/rbac', title: '权限审计', icon: Lock },
]
