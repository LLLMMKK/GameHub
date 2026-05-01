# GameHub - 本地游戏管理器

GameHub 是一款基于 PyQt6 的本地游戏库管理与启动工具，面向 Windows 桌面使用场景。它提供游戏导入、分类浏览、封面管理、游玩时长统计、隐私模式、多主题界面、启动首页和无边框窗口体验。

## 功能概览

- **游戏库管理**：通过顶部“添加游戏”统一入口添加单个游戏、手动多选启动文件，或扫描目录批量导入。
- **隐私保护的启动首页**：可默认进入独立首页，首页只展示概览、最近继续和快速操作，不展示完整游戏库内容。
- **高性能游戏网格**：游戏库使用 `QListView + QAbstractListModel + delegate` 自绘卡片，适合更大的本地库，滚动更稳定。
- **详情页启动**：卡片点击进入详情页，启动、编辑、文件位置、删除和素材导入等操作集中在详情页完成。
- **启动器**：支持 `.exe`、`.bat`、`.cmd` 启动文件，支持额外启动参数，并同步运行状态。
- **分类与搜索**：左侧栏提供分类筛选、实时搜索、自定义分类和分类计数。
- **库概览**：展示当前范围内的游戏数量、已通关、未通关和总游玩时长。
- **游玩统计**：自动记录每次启动/退出时间，累计总游玩时长和最近游玩时间。
- **通关标记**：每个游戏可标记为已通关，卡片和详情页会显示对应状态。
- **封面管理**：支持本地封面、网络图片 URL 预览、裁剪保存、默认渐变封面和隐私马赛克。
- **素材导入**：内置封面/介绍导入面板，可从网络资料中粘贴图片 URL 或介绍文本。
- **多主题**：内置暗夜、赛博朋克、毛玻璃、拟物质感、极简白 5 套主题。
- **窗口体验**：支持无边框模式、内部标题栏、窗口按钮、拖动移动和边缘缩放。
- **偏好设置**：可设置默认启动页面、进入游戏库时默认打开的分类、默认游戏目录、主题、隐私模式和无边框模式。
- **数据安全**：游戏数据和配置采用原子写入；损坏 JSON 文件会自动备份为 `.bad-时间戳` 并在启动时提示。

## 快速开始

推荐使用 `uv` 管理运行环境：

```bash
uv sync
uv run python main.py
```

Windows 下也可以使用无终端入口：

```bash
uv run python GameHub.pyw
```

如果不使用 `uv`，也可以继续使用 `pip`：

```bash
pip install -r requirements.txt
python main.py
```

运行要求：

- Python 3.10+
- PyQt6 6.5+
- Windows 桌面环境

## 开发环境

安装开发/打包依赖：

```bash
uv sync --group dev
```

检查单个文件语法：

```bash
uv run python -m py_compile main.py
```

`pyproject.toml` 是当前推荐的项目配置入口；`requirements.txt` 保留给传统 pip 工作流兼容使用。

## 打包

安装开发依赖后可用 PyInstaller 打包：

```bash
uv run pyinstaller --onefile --windowed --icon=ui/icon.ico --add-data "ui/icon.ico;ui" --name GameHub --distpath . --specpath build GameHub.pyw
```

打包后生成的 `GameHub.exe` 可独立运行。运行时数据会保存在 exe 同目录下的 `data/` 文件夹中。

## 项目结构

```text
GameHub/
├── .gitignore
├── README.md
├── pyproject.toml            # uv/项目依赖配置
├── requirements.txt          # pip 兼容依赖
├── main.py                   # 控制台入口
├── GameHub.pyw               # 无终端入口
├── data/                     # 运行时数据（不提交）
│   ├── games.json
│   ├── config.json
│   └── covers/
├── core/
│   ├── bootstrap.py          # 应用启动与主题初始化
│   ├── game_model.py         # 数据模型与持久化
│   ├── game_launcher.py      # 游戏启动与进程管理
│   ├── game_scanner.py       # 目录扫描
│   └── play_tracker.py       # 游玩时长追踪
├── ui/
│   ├── main_window.py        # 主窗口、启动首页、库概览
│   ├── game_grid_view.py     # 高性能自绘游戏网格
│   ├── sidebar.py            # 分类导航与搜索
│   ├── game_card.py          # 封面工具与旧卡片组件
│   ├── game_detail.py        # 游戏详情页
│   ├── add_game_dialog.py    # 添加/编辑游戏
│   ├── scan_result_dialog.py # 扫描结果确认
│   ├── settings_dialog.py    # 设置、主题、分类管理
│   ├── web_search_dialog.py  # 封面/介绍素材导入
│   ├── crop_dialog.py        # 封面裁剪
│   ├── styles.py             # QSS 主题
│   └── widgets/              # 无边框窗口相关控件
└── utils/
    └── file_utils.py         # 文件与封面工具
```

## 使用说明

1. 点击顶部“添加游戏”选择添加方式：添加单个、手动多选或扫描目录。
2. 扫描目录后先在结果对话框中确认条目，再批量导入。
3. 默认可停留在启动首页；点击“进入游戏库”后会按设置中指定的默认分类打开。
4. 在左侧栏切换分类或搜索游戏；在设置中可以添加/删除自定义分类。
5. 点击游戏卡片进入详情页，再点击“启动游戏”运行。
6. 详情页可编辑信息、标记通关、删除游戏、打开文件位置、搜索 Steam 或导入封面/介绍素材。
7. 设置中可切换主题、默认启动页面、进入游戏库默认分类、默认游戏库目录、隐私模式和无边框模式。

## 数据文件

默认数据目录为项目根目录下的 `data/`：

- `data/games.json`：游戏列表、分类和游玩记录。
- `data/config.json`：主题、隐私模式、默认目录、启动页面、进入游戏库默认分类等配置。
- `data/covers/`：游戏封面图片。

删除游戏只会从 GameHub 列表移除记录和封面，不会删除原始游戏文件。
