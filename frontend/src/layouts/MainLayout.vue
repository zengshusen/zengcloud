<template>
  <div class="layout" :class="{ collapsed: sidebarCollapsed }">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="mark" aria-hidden="true" />
        <div v-show="!sidebarCollapsed" class="brand-text">
          <strong>ZengCloud</strong>
          <span>智能运维平台</span>
        </div>
      </div>

      <nav class="menu" aria-label="主导航">
        <template v-for="item in appMenus" :key="item.path">
          <button
            v-if="!item.children"
            type="button"
            class="menu-item"
            :class="{ active: isActive(item.path) }"
            :title="item.title"
            @click="go(item.path)"
          >
            <el-icon :size="18"><component :is="item.icon" /></el-icon>
            <span v-show="!sidebarCollapsed" class="label">{{ item.title }}</span>
          </button>

          <div v-else class="menu-group">
            <button
              type="button"
              class="menu-item"
              :class="{ active: isActive(item.path), open: openGroups[item.path] }"
              :title="item.title"
              @click="toggleGroup(item.path)"
            >
              <el-icon :size="18"><component :is="item.icon" /></el-icon>
              <span v-show="!sidebarCollapsed" class="label">{{ item.title }}</span>
              <span v-show="!sidebarCollapsed" class="chevron" />
            </button>
            <div v-show="!sidebarCollapsed && openGroups[item.path]" class="sub-menu">
              <button
                v-for="child in item.children"
                :key="child.path"
                type="button"
                class="sub-item"
                :class="{ active: isActive(child.path) }"
                @click="go(child.path)"
              >
                {{ child.title }}
              </button>
            </div>
          </div>
        </template>
      </nav>

      <button
        type="button"
        class="collapse-btn"
        :aria-label="sidebarCollapsed ? '展开侧栏' : '收起侧栏'"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        {{ sidebarCollapsed ? '»' : '«' }}
      </button>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="crumb">
          <h1>{{ currentTitle }}</h1>
          <p>{{ currentDesc }}</p>
        </div>
        <div class="top-actions">
          <div class="user-chip">
            <span class="avatar">{{ avatarLetter }}</span>
            <div class="user-meta">
              <strong>{{ auth.user?.username || '用户' }}</strong>
              <span>{{ auth.user?.is_staff ? '管理员' : '运维成员' }}</span>
            </div>
          </div>
          <button type="button" class="logout" @click="onLogout">退出</button>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { appMenus } from '@/config/menus'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const sidebarCollapsed = ref(false)
const openGroups = reactive<Record<string, boolean>>({})

for (const item of appMenus) {
  if (item.children) {
    openGroups[item.path] = route.path.startsWith(item.path)
  }
}

watch(
  () => route.path,
  (path) => {
    for (const item of appMenus) {
      if (item.children && path.startsWith(item.path)) {
        openGroups[item.path] = true
      }
    }
  },
)

const currentTitle = computed(() => (route.meta.title as string) || 'ZengCloud')
const currentDesc = computed(() => (route.meta.description as string) || '')
const avatarLetter = computed(() => (auth.user?.username || 'U').slice(0, 1).toUpperCase())

function isActive(path: string) {
  if (path === '/overview') {
    return route.path === '/overview' || route.path === '/'
  }
  return route.path === path || route.path.startsWith(`${path}/`)
}

function toggleGroup(path: string) {
  if (sidebarCollapsed.value) {
    sidebarCollapsed.value = false
    openGroups[path] = true
    return
  }
  openGroups[path] = !openGroups[path]
}

function go(path: string) {
  router.push(path)
}

async function onLogout() {
  await auth.logout()
  await router.replace({ name: 'login' })
}
</script>

<style scoped lang="scss">
.layout {
  --sidebar-w: 15.5rem;
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  min-height: 100vh;
  background:
    radial-gradient(ellipse 50% 40% at 100% 0%, rgba(94, 234, 212, 0.16), transparent 55%),
    #f3f6f5;
  transition: grid-template-columns 0.22s ease;

  &.collapsed {
    --sidebar-w: 4.5rem;
  }
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem 0.75rem;
  background:
    linear-gradient(180deg, #0f3d3a 0%, #0a2f2c 100%);
  color: #f0e6d2;
  z-index: 20;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.35rem 0.55rem 1.1rem;
  border-bottom: 1px solid rgba(240, 230, 210, 0.12);
  margin-bottom: 0.85rem;
}

.mark {
  width: 2rem;
  height: 2rem;
  flex-shrink: 0;
  border-radius: 0.45rem;
  background:
    linear-gradient(145deg, #5eead4 0%, #1a7a6d 70%);
  box-shadow: inset 0 0 0 2px rgba(240, 230, 210, 0.2);
}

.brand-text {
  display: grid;
  gap: 0.1rem;
  min-width: 0;

  strong {
    font-family: var(--font-display);
    font-size: 1.05rem;
    letter-spacing: -0.03em;
    line-height: 1.1;
  }

  span {
    font-size: 0.72rem;
    opacity: 0.7;
  }
}

.menu {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding-right: 0.15rem;
}

.menu-item,
.sub-item,
.collapse-btn,
.logout {
  font: inherit;
  cursor: pointer;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  border: 0;
  border-radius: 0.45rem;
  background: transparent;
  color: rgba(240, 230, 210, 0.82);
  padding: 0.7rem 0.7rem;
  text-align: left;
  transition: background 0.15s ease, color 0.15s ease;

  .label {
    flex: 1;
    font-size: 0.92rem;
    font-weight: 500;
  }

  .chevron {
    width: 0.4rem;
    height: 0.4rem;
    border-right: 1.5px solid currentColor;
    border-bottom: 1.5px solid currentColor;
    transform: rotate(45deg);
    opacity: 0.7;
    transition: transform 0.15s ease;
  }

  &.open .chevron {
    transform: rotate(-135deg);
  }

  &:hover {
    background: rgba(240, 230, 210, 0.08);
    color: #fff;
  }

  &.active {
    background: rgba(94, 234, 212, 0.18);
    color: #5eead4;
  }
}

.sub-menu {
  display: grid;
  gap: 0.15rem;
  padding: 0.15rem 0 0.35rem 2.35rem;
}

.sub-item {
  border: 0;
  background: transparent;
  color: rgba(240, 230, 210, 0.7);
  text-align: left;
  padding: 0.45rem 0.55rem;
  border-radius: 0.35rem;
  font-size: 0.86rem;

  &:hover {
    color: #fff;
    background: rgba(240, 230, 210, 0.08);
  }

  &.active {
    color: #5eead4;
    background: rgba(94, 234, 212, 0.12);
  }
}

.collapse-btn {
  margin-top: 0.5rem;
  border: 1px solid rgba(240, 230, 210, 0.16);
  background: transparent;
  color: rgba(240, 230, 210, 0.8);
  border-radius: 0.4rem;
  padding: 0.45rem;
}

.main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(15, 61, 58, 0.1);
  background: rgba(255, 252, 247, 0.82);
  backdrop-filter: blur(10px);
}

.crumb {
  min-width: 0;

  h1 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.25rem;
    color: var(--zc-brand);
    letter-spacing: -0.02em;
  }

  p {
    margin: 0.2rem 0 0;
    font-size: 0.86rem;
    color: rgba(18, 32, 31, 0.58);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-shrink: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: var(--zc-brand);
  color: var(--zc-sand);
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 600;
}

.user-meta {
  display: grid;
  line-height: 1.15;

  strong {
    font-size: 0.9rem;
    color: var(--zc-ink);
  }

  span {
    font-size: 0.75rem;
    color: rgba(18, 32, 31, 0.55);
  }
}

.logout {
  border: 1px solid rgba(15, 61, 58, 0.16);
  background: #fff;
  color: var(--zc-brand);
  padding: 0.45rem 0.85rem;
  border-radius: 0.35rem;

  &:hover {
    background: rgba(15, 61, 58, 0.04);
  }
}

.content {
  flex: 1;
  padding: 1.35rem 1.5rem 2rem;
}

@media (max-width: 860px) {
  .layout,
  .layout.collapsed {
    --sidebar-w: 4.5rem;
  }

  .brand-text,
  .label,
  .chevron,
  .sub-menu,
  .user-meta {
    display: none !important;
  }

  .crumb p {
    display: none;
  }
}
</style>
