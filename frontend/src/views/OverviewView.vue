<template>
  <section class="overview">
    <div class="hero-line">
      <p>现场驾驶舱 · 聚焦 SLA、告警与风险项</p>
    </div>

    <div class="metrics">
      <article v-for="item in metrics" :key="item.label" class="metric">
        <span class="label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <em>{{ item.hint }}</em>
      </article>
    </div>

    <div class="note">
      <h2>下一步</h2>
      <p>指标将接入可观测、工单与事件中心的真实聚合数据；当前为布局与导航联调占位。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
const metrics = [
  { label: '平台 SLA', value: '—', hint: '待接入' },
  { label: '产品 SLA', value: '—', hint: '待接入' },
  { label: '工单及时率', value: '—', hint: '待接入' },
  { label: '活跃告警', value: '—', hint: '待接入' },
]
</script>

<style scoped lang="scss">
.overview {
  display: grid;
  gap: 1.25rem;
  max-width: 72rem;
}

.hero-line p {
  margin: 0;
  color: rgba(18, 32, 31, 0.62);
  font-size: 0.95rem;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
}

.metric {
  border: 1px solid var(--zc-border);
  background: rgba(255, 252, 247, 0.92);
  padding: 1rem 1.1rem;
  display: grid;
  gap: 0.35rem;

  .label {
    font-size: 0.8rem;
    color: rgba(18, 32, 31, 0.55);
  }

  strong {
    font-family: var(--font-display);
    font-size: 1.7rem;
    color: var(--zc-brand);
    letter-spacing: -0.03em;
    line-height: 1;
  }

  em {
    font-style: normal;
    font-size: 0.78rem;
    color: var(--zc-accent);
  }
}

.note {
  border-top: 1px solid rgba(15, 61, 58, 0.1);
  padding-top: 1rem;

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.05rem;
    color: var(--zc-brand);
  }

  p {
    margin: 0.4rem 0 0;
    color: rgba(18, 32, 31, 0.66);
    line-height: 1.55;
  }
}

@media (max-width: 960px) {
  .metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .metrics {
    grid-template-columns: 1fr;
  }
}
</style>
