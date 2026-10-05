# Z11 智能中控台 — Home Assistant 原生集成安装与配置指南
# Z11 Console Native Home Assistant Integration Installation & User Guide

---

## 1. 为什么它是最完美的“C-2 集成形态”？
- **零额外 Docker 容器**：无需在 NAS 上单独跑镜像，直接作为 Home Assistant 原生组件运行在 HA 进程内。
- **100% 绝对同源（Same-Origin）**：直接挂载在 `http://192.168.101.202:8123/z11/`，彻底告别跨域 Cookie 丢失与 HTTPS 证书限制。
- **激活全屏沉浸中控（Kiosk Mode）**：完美支持一键收起 HA 原生侧边栏与顶栏，平板与大屏无黑边全屏显示。
- **本地极速环回通信**：在 HA 内部直接连 `127.0.0.1:8123`，毫秒级响应，网络零延迟。

---

## 2. 目录结构说明
```text
/config/custom_components/z11_console/
├── manifest.json              # HA 集成元数据清单
├── const.py                   # 常量定义
├── __init__.py                # 核心入口：挂载 aiohttp 子路由与注册侧边栏面板
├── hacs.json                  # HACS 兼容描述
├── dist/                      # 编译就绪的 React 18 高性能前端静态包
│   ├── index.html
│   └── assets/
└── home_console_server/       # 原生 Python 3 异步业务服务 (天气/黄历/设备过滤/布局状态)
```

---

## 3. 安装步骤 (只需 3 步)

### 第一步：将集成文件夹放入 HA 的 custom_components 目录
- 打开 fnOS NAS 的【文件管理】（File Station），找到 Home Assistant 的挂载目录（通常位于 `/vol1/@appshare/home-assistant/config/` 或 Docker 映射的 `/config/` 路径）。
- 进入 `custom_components` 文件夹（若无请新建）。
- 将解压后的 `z11_console` 整个文件夹复制进去。
  *(或者直接使用生成的安装压缩包 `z11_console.zip` 解压至该目录)*

### 第二步：在 `configuration.yaml` 启用集成
用文本编辑器打开 HA 的 `configuration.yaml`，在任意空白处添加一行：
```yaml
z11_console:
```
*(可选高级配置：若希望开机自动配置免手动输入，可填入长期令牌)*：
```yaml
z11_console:
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhZjdiMGZjYjBiYjg0NWZjYjc5YjY4MmRjZjA1MDEyNCIsImlhdCI6MTc5MTE5MTMxNSwiZXhwIjoyMTA2NTUxMzE1fQ.kZqSbTlijLPOIPiDpvB1WfIMQ22_6o3o8dTu8EZ806s"
```

### 第三步：重启 Home Assistant
- 进入 Home Assistant【开发者工具】→【YAML 配置重新加载】，或【设置】→【系统】→【重启】。
- 重启后，Home Assistant 左侧菜单栏将直接出现 **【Z11 中控台】** 入口图标！
- 点击即可进入，右上角支持一键全屏沉浸模式！
