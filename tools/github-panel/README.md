# GitHub 上传面板（免手写命令）

本地小工具：用按钮完成常见的 GitHub 上传流程。

## 启动

双击仓库根目录的 **`打开GitHub上传面板.bat`**，或：

```bat
tools\github-panel\start-github-panel.bat
```

浏览器会打开：http://127.0.0.1:8787/

## 推荐流程

1. 在 GitHub 网页新建一个**空仓库**（不要勾选自动生成 README，避免首次推送冲突）
2. 复制仓库地址，例如 `https://github.com/你的用户名/zengcloud.git`
3. 粘贴到面板「GitHub 地址」
4. 填写提交说明
5. 点 **一键上传到 GitHub**

也可以逐步点：

| 按钮 | 对应命令 |
|------|----------|
| 初始化仓库 | `git init` + `git branch -M main` |
| 设置远程地址 | `git remote add/set-url origin ...` |
| 添加全部文件 | `git add -A` |
| 提交代码 | `git commit -m "..."` |
| 推送到 GitHub | `git push -u origin <branch>` |
| 拉取更新 | `git pull` |
| 查看状态 / 记录 | `git status` / `git log` |

## 说明

- 仅监听本机 `127.0.0.1`，不会对外网开放
- `.env`、`.venv`、`node_modules` 等已在根目录 `.gitignore`，不会上传
- 首次 `push` 需要本机已登录 GitHub（Git Credential Manager / Personal Access Token）
