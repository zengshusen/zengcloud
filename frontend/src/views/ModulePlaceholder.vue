<template>
  <section class="page">
    <div class="intro">
      <h2>{{ title }}</h2>
      <p>{{ description }}</p>
    </div>
    <div class="panel">
      <p class="hint">模块骨架已接入主布局，业务能力将在后续迭代实现。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string) || '模块')
const description = computed(
  () => (route.meta.description as string) || '该模块尚在建设中。',
)
</script>

<style scoped lang="scss">
.page {
  display: grid;
  gap: 1rem;
  max-width: 72rem;
}

.intro {
  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.35rem;
    color: var(--zc-brand);
  }

  p {
    margin: 0.4rem 0 0;
    color: rgba(18, 32, 31, 0.68);
    line-height: 1.55;
  }
}

.panel {
  border: 1px solid var(--zc-border);
  background: rgba(255, 252, 247, 0.9);
  padding: 1.25rem 1.35rem;
}

.hint {
  margin: 0;
  color: rgba(18, 32, 31, 0.62);
  font-size: 0.95rem;
}
</style>
