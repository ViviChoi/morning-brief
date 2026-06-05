# launchers/ — 双击启动器

这个文件夹里有 4 个启动器，让你不需要打开终端，直接双击就能用 Morning Brief。

## Mac 用户

文件：`Daily-Brief.command` 和 `Portfolio-Explorer.command`

**第一次使用（只需做一次）：**

macOS 对没有开发者签名的脚本会弹出安全警告。处理方式：

1. 右键点击 `.command` 文件 → 选"打开"
2. 弹出对话框说"无法验证开发者" → 点"打开"
3. 脚本正常运行后，之后就可以直接双击，不再弹警告

**如果双击没反应：**

可能是文件没有执行权限。打开 Terminal，运行一次：

```bash
chmod +x ~/Desktop/morning-brief/launchers/*.command
```

运行 `install_launchd.sh` 也会自动设置权限。

## Windows 用户

文件：`Daily-Brief.bat` 和 `Portfolio-Explorer.bat`

**第一次使用（只需做一次）：**

Windows SmartScreen 可能拦截未知来源的 `.bat` 文件。处理方式：

1. 双击 `.bat` 文件
2. 如果弹出蓝色 SmartScreen 对话框 → 点"更多信息"
3. 然后点"仍然运行"
4. 之后就可以直接双击，不再拦截

## 启动器说明

| 文件 | 平台 | 功能 |
|------|------|------|
| `Daily-Brief.command` | Mac | 跑今天的 Daily Brief，完成后打开浏览器 |
| `Portfolio-Explorer.command` | Mac | 启动 Portfolio Explorer WebUI |
| `Daily-Brief.bat` | Windows | 跑今天的 Daily Brief |
| `Portfolio-Explorer.bat` | Windows | 启动 Portfolio Explorer WebUI |

所有启动器都会自动检测是否完成了首次安装（.venv 是否存在），如果没有会给出安装提示。
