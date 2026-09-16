<template>
  <div class="login-page">
    <div class="atmosphere" aria-hidden="true">
      <div class="grid" />
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="signal" />
    </div>

    <main class="stage">
      <section class="brand-block">
        <p class="eyebrow">Intelligent Operations</p>
        <h1 class="brand">ZengCloud</h1>
        <p class="tagline">
          面向真实运维现场的智能运维平台——可审计、可确认、可执行。
        </p>
      </section>

      <form class="login-panel" @submit.prevent="onSubmit">
        <header class="panel-head">
          <h2>登录控制台</h2>
          <p>使用组织账号进入运行概览与运维工作流</p>
        </header>

        <label class="field">
          <span>用户名</span>
          <input
            v-model.trim="username"
            type="text"
            name="username"
            autocomplete="username"
            placeholder="请输入用户名"
            required
          />
        </label>

        <label class="field">
          <span>密码</span>
          <div class="password-row">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              name="password"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
            <button type="button" class="ghost" @click="showPassword = !showPassword">
              {{ showPassword ? '隐藏' : '显示' }}
            </button>
          </div>
        </label>

        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <button class="submit" type="submit" :disabled="loading">
          {{ loading ? '正在登录…' : '进入平台' }}
        </button>
      </form>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect || '/')
  } catch (err: unknown) {
    const detail =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      '登录失败，请检查网络后重试'
    error.value = detail
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: var(--zc-ink);
}

.atmosphere {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 12% 18%, rgba(94, 234, 212, 0.35), transparent 55%),
    radial-gradient(ellipse 70% 50% at 88% 12%, rgba(240, 230, 210, 0.55), transparent 50%),
    linear-gradient(160deg, #d7ebe6 0%, #f7f3ea 48%, #cfe3de 100%);
}

.grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(15, 61, 58, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(15, 61, 58, 0.06) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(circle at 40% 30%, black 20%, transparent 75%);
  animation: drift 28s linear infinite;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
}

.orb-a {
  width: 28rem;
  height: 28rem;
  left: -8rem;
  bottom: -10rem;
  background: radial-gradient(circle, rgba(26, 122, 109, 0.28), transparent 70%);
  animation: float 12s ease-in-out infinite;
}

.orb-b {
  width: 18rem;
  height: 18rem;
  right: 8%;
  top: 18%;
  background: radial-gradient(circle, rgba(240, 230, 210, 0.7), transparent 70%);
  animation: float 16s ease-in-out infinite reverse;
}

.signal {
  position: absolute;
  left: 10%;
  bottom: 18%;
  width: min(42vw, 28rem);
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(15, 61, 58, 0.35), transparent);
  transform-origin: left center;
  animation: pulse 4.5s ease-in-out infinite;
}

.stage {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: grid;
  align-content: center;
  gap: 2.5rem;
  padding: clamp(1.5rem, 4vw, 3.5rem);
  max-width: 72rem;
  margin: 0 auto;
}

.brand-block {
  max-width: 36rem;
  animation: rise 0.8s ease-out both;
}

.eyebrow {
  margin: 0 0 0.75rem;
  font-family: var(--font-display);
  font-size: 0.8rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--zc-accent);
  font-weight: 600;
}

.brand {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2.8rem, 7vw, 4.6rem);
  line-height: 0.95;
  letter-spacing: -0.04em;
  color: var(--zc-brand);
  font-weight: 700;
}

.tagline {
  margin: 1rem 0 0;
  max-width: 28rem;
  font-size: 1.05rem;
  line-height: 1.65;
  color: rgba(18, 32, 31, 0.78);
}

.login-panel {
  width: min(100%, 26rem);
  padding: 1.75rem;
  border: 1px solid var(--zc-border);
  background: var(--zc-panel);
  backdrop-filter: blur(10px);
  animation: rise 0.9s 0.08s ease-out both;
}

.panel-head {
  margin-bottom: 1.5rem;

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 600;
    color: var(--zc-brand);
  }

  p {
    margin: 0.45rem 0 0;
    font-size: 0.92rem;
    color: rgba(18, 32, 31, 0.62);
  }
}

.field {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;

  span {
    font-size: 0.82rem;
    font-weight: 600;
    color: rgba(18, 32, 31, 0.72);
  }

  input {
    width: 100%;
    border: 1px solid rgba(15, 61, 58, 0.18);
    background: rgba(255, 255, 255, 0.72);
    color: var(--zc-ink);
    padding: 0.75rem 0.85rem;
    outline: none;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;

    &:focus {
      border-color: var(--zc-accent);
      box-shadow: 0 0 0 3px rgba(26, 122, 109, 0.15);
    }
  }
}

.password-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.5rem;
  align-items: stretch;
}

.ghost {
  border: 1px solid rgba(15, 61, 58, 0.16);
  background: transparent;
  color: var(--zc-brand);
  padding: 0 0.9rem;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: rgba(15, 61, 58, 0.05);
  }
}

.error {
  margin: 0 0 0.85rem;
  color: var(--zc-danger);
  font-size: 0.88rem;
}

.submit {
  width: 100%;
  border: 0;
  background: var(--zc-brand);
  color: var(--zc-sand);
  font-family: var(--font-display);
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.85rem 1rem;
  cursor: pointer;
  transition: transform 0.2s ease, background 0.2s ease;

  &:hover:not(:disabled) {
    background: #0a2f2c;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.7;
    cursor: wait;
  }
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-18px);
  }
}

@keyframes drift {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(48px, 24px, 0);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.25;
    transform: scaleX(0.7);
  }
  50% {
    opacity: 0.85;
    transform: scaleX(1);
  }
}

@media (min-width: 900px) {
  .stage {
    grid-template-columns: 1.15fr 0.85fr;
    align-items: center;
    gap: 4rem;
  }
}
</style>
