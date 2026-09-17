const HISTORY_KEY = 'zc_git_panel_history_v1'
const metaRoot = document.getElementById('meta-root')
const metaRepo = document.getElementById('meta-repo')
const metaBranch = document.getElementById('meta-branch')
const metaRemote = document.getElementById('meta-remote')
const statusBox = document.getElementById('status-box')
const logBox = document.getElementById('log-box')
const timelineEl = document.getElementById('timeline')
const remoteInput = document.getElementById('remote-url')
const commitInput = document.getElementById('commit-msg')
const branchInput = document.getElementById('branch-name')
const targetInput = document.getElementById('target-ref')
const userNameInput = document.getElementById('user-name')
const userEmailInput = document.getElementById('user-email')

function payloadFromForm() {
  return {
    remote_url: remoteInput.value.trim(),
    message: commitInput.value.trim(),
    branch: branchInput.value.trim(),
    target: targetInput.value.trim(),
    tag_name: targetInput.value.trim(),
    user_name: userNameInput.value.trim(),
    user_email: userEmailInput.value.trim(),
  }
}

function makeBtn(item, compact = false) {
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.className = compact ? 'btn compact' : 'btn'
  btn.dataset.action = item.action
  if (item.confirm) btn.dataset.confirm = item.confirm
  if (item.need) btn.dataset.need = item.need.join(',')
  btn.innerHTML = `${item.title}<br /><small>${item.cmd}</small>`
  return btn
}

function renderTop6() {
  const box = document.getElementById('top-actions')
  box.innerHTML = ''
  for (const item of window.ZC_COMMANDS.top6) {
    box.appendChild(makeBtn(item))
  }
}

function renderGroups() {
  const wrap = document.getElementById('more-groups')
  wrap.innerHTML = ''
  for (const group of window.ZC_COMMANDS.groups) {
    const details = document.createElement('details')
    details.className = 'group'
    details.open = Boolean(group.open)
    details.dataset.group = group.id

    const summary = document.createElement('summary')
    summary.innerHTML = `<span>${group.title}</span><span class="count">${group.items.length}</span>`
    details.appendChild(summary)

    const grid = document.createElement('div')
    grid.className = 'actions grid-more'
    for (const item of group.items) {
      grid.appendChild(makeBtn(item, true))
    }
    details.appendChild(grid)
    wrap.appendChild(details)
  }
}

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

function saveHistory(list) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(-80)))
}

function renderTimeline() {
  const list = loadHistory()
  timelineEl.innerHTML = ''
  if (!list.length) {
    timelineEl.innerHTML = '<li class="empty">还没有操作记录。执行命令后会按先后顺序显示在这里。</li>'
    return
  }
  list.forEach((item, index) => {
    const li = document.createElement('li')
    li.className = item.ok ? 'ok' : 'bad'
    li.innerHTML = `
      <div class="t-index">#${index + 1}</div>
      <div class="t-body">
        <div class="t-title">${item.title || item.action}</div>
        <div class="t-meta">${item.time} · ${item.ok ? '成功' : '失败'} · <code>${item.cmdPreview || item.action}</code></div>
      </div>
      <button type="button" class="ghost replay" data-idx="${index}">再执行</button>
    `
    timelineEl.appendChild(li)
  })
}

function appendLog(title, logs = [], timeText = '') {
  const chunks = [`▸ [${timeText || nowText()}] ${title}`]
  for (const item of logs) {
    const head = item.cmd ? `$ git ${item.cmd}` : ''
    const body = [item.stdout, item.stderr].filter(Boolean).join('\n')
    const mark = item.ok ? 'ok' : 'bad'
    chunks.push(`${head}\n<span class="${mark}">${escapeHtml(body || '(无输出)')}</span>`)
  }
  const block = document.createElement('div')
  block.innerHTML = chunks.join('\n') + '\n\n'
  logBox.appendChild(block)
  logBox.scrollTop = logBox.scrollHeight
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

function nowText() {
  const d = new Date()
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}

function findCommandMeta(action) {
  for (const item of window.ZC_COMMANDS.top6) {
    if (item.action === action) return item
  }
  for (const g of window.ZC_COMMANDS.groups) {
    for (const item of g.items) {
      if (item.action === action) return item
    }
  }
  if (action === 'one_click') return { title: '首次一键上传', cmd: 'init→remote→add→commit→push' }
  if (action === 'quick_sync') return { title: '日常一键同步', cmd: 'add→commit→push' }
  if (action === 'list_branches') return { title: '刷新分支列表', cmd: 'git fetch + branch' }
  if (action === 'branch_use_existing') return { title: '切换到已有分支', cmd: 'git switch' }
  if (action === 'branch_create_new') return { title: '新建分支', cmd: 'git checkout -b' }
  if (action === 'commit_history') return { title: '刷新提交历史', cmd: 'git log' }
  return { title: action, cmd: action }
}

function validateNeed(need = []) {
  const form = payloadFromForm()
  for (const key of need) {
    if (key === 'remote' && !form.remote_url) {
      alert('请先填写 GitHub 地址')
      remoteInput.focus()
      return false
    }
    if (key === 'message' && !form.message) {
      alert('请先填写提交说明')
      commitInput.focus()
      return false
    }
    if (key === 'branch' && !form.branch) {
      alert('请先填写分支名')
      branchInput.focus()
      return false
    }
    if (key === 'target' && !form.target) {
      alert('请先填写目标 commit / 标签名')
      targetInput.focus()
      return false
    }
    if (key === 'user_name' && !form.user_name) {
      alert('请先填写 Git 用户名')
      userNameInput.focus()
      return false
    }
    if (key === 'user_email' && !form.user_email) {
      alert('请先填写 Git 邮箱')
      userEmailInput.focus()
      return false
    }
  }
  return true
}

function renderSummary(summary) {
  if (!summary) return
  metaRoot.textContent = summary.root || '—'
  metaRepo.textContent = summary.is_repo ? '是' : '否'
  metaBranch.textContent = summary.branch || '—'
  metaRemote.textContent = summary.remote || '未设置'
  statusBox.textContent = summary.status || '—'
  const branchCurrent = document.getElementById('branch-current')
  if (branchCurrent) branchCurrent.textContent = summary.branch || '—'
  if (summary.remote && !remoteInput.value) remoteInput.value = summary.remote
  if (summary.branches) fillBranchSelect(summary.branches)
  if (Array.isArray(summary.commits)) renderCommitTimeline(summary.commits)
}

function renderCommitTimeline(commits) {
  const el = document.getElementById('commit-timeline')
  const badge = document.getElementById('commit-count-badge')
  if (!el) return
  if (badge) badge.textContent = `${commits.length} 条`

  el.innerHTML = ''
  if (!commits.length) {
    el.innerHTML =
      '<li class="empty">暂无提交记录。完成第一次 commit 后，这里会按时间先后展示完整历史。</li>'
    return
  }

  commits.forEach((c, index) => {
    const li = document.createElement('li')
    const refs = c.refs
      ? `<span class="commit-refs">${escapeHtml(c.refs)}</span>`
      : ''
    const body = c.body
      ? `<p class="commit-body">${escapeHtml(c.body)}</p>`
      : ''
    li.innerHTML = `
      <div class="commit-rail" aria-hidden="true">
        <span class="dot"></span>
        <span class="line"></span>
      </div>
      <div class="commit-main">
        <div class="commit-top">
          <time datetime="${escapeHtml(c.date)}">${escapeHtml(c.date)}</time>
          <code title="${escapeHtml(c.hash)}">${escapeHtml(c.short)}</code>
          ${refs}
        </div>
        <h3 class="commit-subject">${escapeHtml(c.subject || '(无提交说明)')}</h3>
        ${body}
        <div class="commit-meta">
          <span>#${index + 1}</span>
          <span>${escapeHtml(c.author || '未知作者')}</span>
          <span>${escapeHtml(c.email || '')}</span>
        </div>
      </div>
    `
    el.appendChild(li)
  })
}

function fillBranchSelect(branches) {
  const select = document.getElementById('branch-select')
  const hint = document.getElementById('branch-source-hint')
  if (!select) return
  const prev = select.value
  const localSet = new Set(branches.local || [])
  const remoteSet = new Set(branches.remote || [])
  const all = branches.all || []
  select.innerHTML = ''
  if (!all.length) {
    const opt = document.createElement('option')
    opt.value = ''
    opt.textContent = '暂无分支，请先刷新或初始化仓库'
    select.appendChild(opt)
  } else {
    const placeholder = document.createElement('option')
    placeholder.value = ''
    placeholder.textContent = `共 ${all.length} 个分支，请选择…`
    select.appendChild(placeholder)
    for (const name of all) {
      const opt = document.createElement('option')
      opt.value = name
      const tags = []
      if (localSet.has(name)) tags.push('本地')
      if (remoteSet.has(name)) tags.push('GitHub')
      if (name === branches.current) tags.push('当前')
      opt.textContent = tags.length ? `${name}（${tags.join(' · ')}）` : name
      select.appendChild(opt)
    }
  }
  if (prev && all.includes(prev)) select.value = prev
  else if (branches.current && all.includes(branches.current)) select.value = branches.current

  if (hint) {
    hint.textContent = `本地 ${localSet.size} 个 · GitHub/远程 ${remoteSet.size} 个。点「刷新 GitHub 分支」可同步最新远程列表。`
  }
  // 同步到参数区分支名，方便其他命令复用
  if (select.value) branchInput.value = select.value
}

function selectedBranch() {
  const select = document.getElementById('branch-select')
  return (select && select.value) || ''
}

function setBranchMode(mode) {
  document.getElementById('mode-existing').classList.toggle('active', mode === 'existing')
  document.getElementById('mode-create').classList.toggle('active', mode === 'create')
  document.getElementById('panel-existing').classList.toggle('hidden', mode !== 'existing')
  document.getElementById('panel-create').classList.toggle('hidden', mode !== 'create')
}

async function refreshBranches(fetchRemote = true) {
  await runAction('list_branches', { fetch_remote: fetchRemote }, {})
  // runAction already updates summary; also apply branches from last response via refresh
  const res = await fetch('/api/summary')
  const data = await res.json()
  renderSummary(data.summary)
}

async function refresh() {
  const res = await fetch('/api/summary')
  const data = await res.json()
  renderSummary(data.summary)
}

async function runAction(action, extra = {}, meta = {}) {
  const need = (meta.need || (extra.need ? String(extra.need).split(',') : []))
  if (need.length && !validateNeed(need)) return
  if (meta.confirm || extra.confirm) {
    const ok = confirm(meta.confirm || extra.confirm)
    if (!ok) return
  }

  const buttons = document.querySelectorAll('button')
  buttons.forEach((b) => {
    b.disabled = true
  })

  const form = payloadFromForm()
  const started = nowText()
  try {
    const res = await fetch('/api/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, ...form, ...extra }),
    })
    const data = await res.json()
    renderSummary(data.summary)
    if (data.branches) fillBranchSelect(data.branches)
    if (Array.isArray(data.commits)) renderCommitTimeline(data.commits)
    // 提交类操作后强制刷新完整时间线
    if (['commit', 'commit_amend', 'commit_empty', 'one_click', 'quick_sync', 'branch_create_new', 'pull', 'merge', 'rebase', 'cherry_pick', 'revert_head'].includes(action)) {
      const s = await fetch('/api/summary')
      const fresh = await s.json()
      renderSummary(fresh.summary)
    }
    const info = findCommandMeta(action)
    appendLog(info.title, data.logs || [], started)

    const cmdPreview =
      (data.logs || [])
        .map((x) => x.cmd)
        .filter(Boolean)
        .join(' → ') || info.cmd

    const history = loadHistory()
    history.push({
      time: started,
      action,
      title: info.title,
      ok: Boolean(data.ok),
      cmdPreview,
      payload: { ...form, ...extra },
    })
    saveHistory(history)
    renderTimeline()
  } catch (err) {
    appendLog(action, [{ ok: false, stderr: String(err), cmd: action }], started)
  } finally {
    buttons.forEach((b) => {
      b.disabled = false
    })
  }
}

function bindClicks(root = document) {
  root.querySelectorAll('[data-action]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const meta = {
        confirm: btn.dataset.confirm,
        need: btn.dataset.need ? btn.dataset.need.split(',') : [],
      }
      // special case for first upload
      if (btn.dataset.action === 'one_click' && !remoteInput.value.trim()) {
        alert('请先填写 GitHub 仓库地址')
        remoteInput.focus()
        return
      }
      runAction(btn.dataset.action, {}, meta)
    })
  })
}

document.getElementById('btn-refresh').addEventListener('click', refresh)
document.getElementById('btn-refresh-commits')?.addEventListener('click', async () => {
  await runAction('commit_history', { limit: 50 })
  const res = await fetch('/api/summary')
  const data = await res.json()
  renderSummary(data.summary)
})
document.getElementById('btn-clear-log').addEventListener('click', () => {
  logBox.textContent = '已清空输出。\n'
})
document.getElementById('btn-clear-history').addEventListener('click', () => {
  localStorage.removeItem(HISTORY_KEY)
  renderTimeline()
})
document.getElementById('btn-expand-all').addEventListener('click', () => {
  const groups = [...document.querySelectorAll('.group')]
  const shouldOpen = groups.some((g) => !g.open)
  groups.forEach((g) => {
    g.open = shouldOpen
  })
})

document.getElementById('mode-existing').addEventListener('click', () => setBranchMode('existing'))
document.getElementById('mode-create').addEventListener('click', () => setBranchMode('create'))

document.getElementById('branch-select').addEventListener('change', () => {
  const v = selectedBranch()
  if (v) branchInput.value = v
})

document.getElementById('btn-refresh-branches').addEventListener('click', () => {
  refreshBranches(true)
})

document.getElementById('btn-use-existing').addEventListener('click', () => {
  const name = selectedBranch()
  if (!name) {
    alert('请先从下拉框选择一个已有分支')
    return
  }
  branchInput.value = name
  runAction('branch_use_existing', { branch: name })
})

document.getElementById('btn-rename-to-selected').addEventListener('click', () => {
  const name = selectedBranch()
  if (!name) {
    alert('请先选择目标分支名（用作新名字）')
    return
  }
  if (!confirm(`将当前分支重命名为「${name}」？`)) return
  branchInput.value = name
  runAction('branch_rename', { branch: name })
})

document.getElementById('btn-delete-selected-local').addEventListener('click', () => {
  const name = selectedBranch()
  if (!name) {
    alert('请先选择要删除的本地分支')
    return
  }
  if (!confirm(`确认删除本地分支「${name}」？`)) return
  branchInput.value = name
  runAction('branch_delete', { branch: name })
})

document.getElementById('btn-delete-selected-remote').addEventListener('click', () => {
  const name = selectedBranch()
  if (!name) {
    alert('请先选择要删除的远程分支')
    return
  }
  if (!confirm(`确认删除 GitHub 远程分支「${name}」？`)) return
  branchInput.value = name
  runAction('branch_delete_remote', { branch: name })
})

document.getElementById('btn-create-branch').addEventListener('click', () => {
  const name = document.getElementById('new-branch-name').value.trim()
  if (!name) {
    alert('请填写新分支名称')
    document.getElementById('new-branch-name').focus()
    return
  }
  const pushAfter = document.getElementById('create-push-after').checked
  branchInput.value = name
  runAction('branch_create_new', { branch: name, push_after: pushAfter })
})

timelineEl.addEventListener('click', (e) => {
  const btn = e.target.closest('.replay')
  if (!btn) return
  const idx = Number(btn.dataset.idx)
  const item = loadHistory()[idx]
  if (!item) return
  const { action, payload = {} } = item
  if (payload.remote_url) remoteInput.value = payload.remote_url
  if (payload.message) commitInput.value = payload.message
  if (payload.branch) branchInput.value = payload.branch
  if (payload.target) targetInput.value = payload.target
  if (payload.user_name) userNameInput.value = payload.user_name
  if (payload.user_email) userEmailInput.value = payload.user_email
  runAction(action, payload)
})

renderTop6()
renderGroups()
bindClicks()
renderTimeline()
setBranchMode('existing')
refresh().then(() => refreshBranches(false))
