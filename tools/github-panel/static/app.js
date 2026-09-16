const metaRoot = document.getElementById('meta-root')
const metaRepo = document.getElementById('meta-repo')
const metaBranch = document.getElementById('meta-branch')
const metaRemote = document.getElementById('meta-remote')
const statusBox = document.getElementById('status-box')
const logBox = document.getElementById('log-box')
const remoteInput = document.getElementById('remote-url')
const commitInput = document.getElementById('commit-msg')

function appendLog(title, logs = []) {
  const chunks = [`▸ ${title}`]
  for (const item of logs) {
    const head = item.cmd ? `$ git ${item.cmd}` : ''
    const body = [item.stdout, item.stderr].filter(Boolean).join('\n')
    const mark = item.ok ? 'ok' : 'bad'
    chunks.push(`${head}\n<span class="${mark}">${body || '(无输出)'}</span>`)
  }
  const block = document.createElement('div')
  block.innerHTML = chunks.join('\n') + '\n\n'
  logBox.appendChild(block)
  logBox.scrollTop = logBox.scrollHeight
}

function renderSummary(summary) {
  if (!summary) return
  metaRoot.textContent = summary.root || '—'
  metaRepo.textContent = summary.is_repo ? '是' : '否'
  metaBranch.textContent = summary.branch || '—'
  metaRemote.textContent = summary.remote || '未设置'
  statusBox.textContent = summary.status || '—'
  if (summary.remote && !remoteInput.value) {
    remoteInput.value = summary.remote
  }
}

async function refresh() {
  const res = await fetch('/api/summary')
  const data = await res.json()
  renderSummary(data.summary)
}

async function runAction(action, extra = {}) {
  const buttons = document.querySelectorAll('button')
  buttons.forEach((b) => {
    b.disabled = true
  })
  try {
    const res = await fetch('/api/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        remote_url: remoteInput.value.trim(),
        message: commitInput.value.trim(),
        ...extra,
      }),
    })
    const data = await res.json()
    renderSummary(data.summary)
    appendLog(action, data.logs || [])
    if (!data.ok && (!data.logs || !data.logs.length)) {
      appendLog(action, [{ ok: false, stderr: '操作失败', cmd: action }])
    }
  } catch (err) {
    appendLog(action, [{ ok: false, stderr: String(err), cmd: action }])
  } finally {
    buttons.forEach((b) => {
      b.disabled = false
    })
  }
}

document.querySelectorAll('[data-action]').forEach((btn) => {
  btn.addEventListener('click', () => runAction(btn.dataset.action))
})

document.getElementById('btn-refresh').addEventListener('click', refresh)
document.getElementById('btn-clear').addEventListener('click', () => {
  logBox.textContent = '已清空。\n'
})
document.getElementById('btn-one-click').addEventListener('click', async () => {
  if (!remoteInput.value.trim()) {
    alert('请先填写 GitHub 仓库地址，例如 https://github.com/用户名/zengcloud.git')
    remoteInput.focus()
    return
  }
  const ok = confirm('将执行：初始化（如需要）→ 设置远程 → 添加文件 → 提交 → 推送。\n确认继续？')
  if (!ok) return
  await runAction('one_click')
})

refresh()
