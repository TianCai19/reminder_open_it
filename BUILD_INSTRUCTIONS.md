# 自动构建和发布说明

这个项目使用 GitHub Actions 实现自动化构建和发布流程。

## 🚀 如何触发自动构建

### 方法1：创建并推送标签（推荐）

```bash
# 1. 确保所有更改都已提交
git add .
git commit -m "准备发布版本 v1.0.0"

# 2. 创建标签
git tag v1.0.0

# 3. 推送标签到 GitHub
git push origin v1.0.0
```

### 方法2：手动触发

1. 在 GitHub 仓库页面点击 `Actions` 选项卡
2. 选择 `Build and Release` 工作流
3. 点击 `Run workflow` 按钮
4. 选择分支并点击 `Run workflow`

## 📦 构建产物

自动化流程会为以下平台创建可执行文件：

- **macOS**: `NotionReminder.app` (打包为 .zip)
- **Windows**: `NotionReminder.exe` (打包为 .zip)  
- **Linux**: `NotionReminder` 可执行文件 (打包为 .zip)

## 📋 发布流程

当推送标签时，系统会自动：

1. **构建阶段**：
   - 在 macOS、Windows、Linux 三个平台上同时构建
   - 使用 PyInstaller 打包成可执行文件
   - 将构建产物压缩为 zip 文件

2. **发布阶段**：
   - 创建 GitHub Release
   - 将三个平台的构建产物上传为 Release Assets
   - 生成发布说明

## 🛠 本地测试构建

如果你想在本地测试构建过程：

```bash
# 安装依赖
pip install -r requirements.txt

# macOS 构建
pyinstaller NotionReminder.spec

# Windows/Linux 构建
pyinstaller --onefile --windowed --name NotionReminder notion_reminder_gui.py
```

## 📝 版本管理建议

推荐使用语义化版本号：

- `v1.0.0` - 主要版本
- `v1.1.0` - 次要版本（新功能）
- `v1.1.1` - 补丁版本（bug 修复）

## 🔧 自定义构建

如需修改构建配置，可以编辑：

- `.github/workflows/build-and-release.yml` - GitHub Actions 工作流
- `requirements.txt` - Python 依赖
- `NotionReminder.spec` - PyInstaller macOS 配置

## ❗ 注意事项

1. 首次使用需要确保仓库有 Actions 权限
2. 标签推送会立即触发构建，请谨慎操作
3. 构建时间约 10-15 分钟（三个平台并行）
4. 发布的文件会自动出现在 GitHub Releases 页面
