# 故障预测分析桌面应用（PySide6 + Fluent Widgets）

一款多页面桌面端，用于设备故障预测的端到端流程：数据导入 → Apriori 规则挖掘 → 贝叶斯网络训练/预测 → 评估与报表生成/导出。

## 1) 项目定位与目标
- 为工业设备提供数据驱动的故障预测流程，包含规则挖掘、概率模型、可视化与报告输出。
- 以桌面化交互（PySide6/Fluent）集成数据预处理、模型训练、批量/单次预测、结果对比、报告生成/导出。

## 2) 核心功能页面
- Page1 数据导入：选择并记录数据集路径，主窗口持久化 `dataset_path`。
- Page2 Apriori：运行规则挖掘与离散化对比，生成 4 张 Apriori 对比图。
- Page3 贝叶斯网络：训练/构建 BN，保存 `(model, bin_config)`，输出 `bn_structure.png`。
- Page4 预测评估：批量/单次预测，生成 `confusion_matrix.png` 与 `prediction_report.txt`。
- Page5 数据可视化：图表浏览。
- Page6 报告：生成最新 `故障预测分析报告.docx`；一键导出图表、txt、Word 报告到指定目录，并刷新文件/元数据时间戳。

### 各页面输入/输出资产
- Page1 数据导入  
  - 输入：用户选择的数据集文件  
  - 输出：`dataset_path`（内存共享，主窗体持有）
- Page2 Apriori  
  - 输入：`dataset_path`  
  - 输出（落地 `Bayesian_1130/result/apriori_results/`）：  
    - `故障预测规则提升度.png`  
    - `离散化方法规则数量对比.png`  
    - `离散化方法执行时间对比.png`  
    - `离散化方法性能综合对比.png`
- Page3 贝叶斯网络  
  - 输入：`dataset_path`  
  - 输出：模型与分箱配置 `new_bayesian/pkl/bn_bayesian_model.pkl`，图 `Bayesian_1130/result/bayesian_results/bn_structure.png`
- Page4 预测评估  
  - 输入：`bn_bayesian_model.pkl`（含 model+bin_config），评估数据  
  - 输出（落地 `Bayesian_1130/result/bayesian_results/`）：`confusion_matrix.png`、`prediction_report.txt`
- Page6 报告  
  - 输入：Page2/3/4 生成的图表与 `prediction_report.txt`  
  - 输出：`Bayesian_1130/故障预测分析报告.docx`；导出时复制上述全部资产到用户指定目录

## 3) 目录与职责
- `entry.py`：程序入口，创建 QApplication，加载翻译/图标，登录或直接进入主窗体。
- `view/`：UI 控制层（View + Handler 分层）
  - `main_window.py`：主窗体，管理导航、跨页共享数据（dataset/model/rules），连接信号槽。
  - `pages/`：各页面 View 与 Handler，负责 UI 事件与业务调用。
  - `login_window/`：登录对话框。
- `ui_page/`：Qt Designer 生成的 UI Python 文件（由 `.ui` 转换）。
- `workers/`：耗时任务的 QThread Worker（Apriori、Bayesian、Prediction），防止阻塞 UI。
- `common/`：通用工具（路径、对话框、配置、日志等）；`get_bayesian_root()` 决定数据/结果根目录。
- `Bayesian_1130/`：模型、结果与报告生成脚本
  - `result/apriori_results/`：4 张 Apriori 对比图
  - `result/bayesian_results/`：`bn_structure.png`、`confusion_matrix.png`、`prediction_report.txt`
  - `generate_report.py`：读取上述资产生成 `故障预测分析报告.docx`
- `services/`：服务层（如 AprioriService）为页面提供数据/算法接口。
- `resource/`：静态资源（图片、i18n、qss）。
- `requirements.txt`：依赖列表（PySide6、Fluent Widgets、mlxtend、pgmpy、matplotlib、python-docx 等）。

## 4) 架构关系（简版）
- **View (view/pages/*.py)**：呈现 UI、收集输入、发出信号。
- **Handler (view/pages/*_handler.py)**：业务编排，调用 Service/Worker，处理回调并更新 UI。
- **Worker (workers/*.py)**：耗时算法/IO 在线程中运行，完成后通过信号返回结果。
- **Service (services/)**：封装数据/算法接口，供 Handler 使用。
- **Bayesian_1130/**：算法产出与报告生成的落地目录。
- **资源流**：Page1/2/3/4 逐步生成数据与图表 → Page6 读这些资产生成/导出 docx。

输入/输出示例：
- Page2 输入：`dataset_path`；输出：4 张 Apriori 图（落地到 `result/apriori_results/`）
- Page3 输入：`dataset_path`；输出：BN 模型 + `bn_structure.png`
- Page4 输入：模型+bin_config；输出：`confusion_matrix.png`、`prediction_report.txt`
- Page6 输入：以上全部资产；输出：`故障预测分析报告.docx`（在 `Bayesian_1130/`），并可一键导出到用户目录。

## 5) 运行流程（启动→结束）
1. `python entry.py`
2. 创建 QApplication，加载翻译/图标 → 登录窗口（或自动登录）→ 进入 MainWindow。
3. MainWindow 初始化导航与共享状态，实例化各页面并绑定信号槽。
4. 用户按流程操作：
   - Page1 选数据 → Page2 挖掘 → Page3 训练 BN → Page4 评估/生成报告资产 → Page6 生成/导出 Word 报告。
5. 关闭主窗体或退出 QApplication 结束进程。

## 6) 数据与控制流
- 数据流：`dataset_path` → Apriori 结果图 → BN 模型/bin_config → 预测输出 (混淆矩阵 + txt) → Word 报告。
- 控制流：用户事件触发 View → Handler 编排 → Worker 在线程执行 → 信号回调更新 UI/状态。
- 导出：Page6 Handler 校验资产齐全 → 复制图/txt/docx 到目标目录，刷新文件与 docx 核心属性时间戳。

## 7) 报告生成与导出要点
- 生成：`Bayesian_1130/generate_report.py` 读取 apriori/bayesian 结果与 txt，写入 `故障预测分析报告.docx` 并同步 core properties 时间。
- 导出：Page6 “导出报告” 将 4 张 Apriori 图 + BN 图 + 混淆矩阵 + txt + docx 复制到用户选定目录，同步文件时间与 Word 元数据。

## 8) 快速使用
- 安装依赖：`pip install -r requirements.txt`（Python 3.10 环境已验证）
- 运行：`python entry.py`
- 修改 UI 后打包资源：`python pack_resources.py`
- CLI 直接生成 Word 报告（无需打开 UI）：`python Bayesian_1130/generate_report.py`
- 打包顺序（如需分发）：  
  1) `python pack_resources.py`（若 .ui/.qrc 有改动）  
  2) `pyinstaller --clean pyqt_apriori.spec`

## 9) 目录速览
- `entry.py` — 应用入口
- `view/main_window.py` — 主窗体与导航
- `view/pages/` — 各功能页 View/Handler
- `workers/` — Apriori/BN/预测的线程任务
- `Bayesian_1130/` — 数据/模型/结果/报告生成脚本
- `ui_page/` — Qt Designer 生成 UI 代码
- `common/` — 工具与配置
- `resource/` — 图片/i18n/qss
- `requirements.txt` — 依赖列表

## 10) 开发提示
- 维护 View/Handler/Worker 分层：UI 只负责展示与信号，耗时逻辑放 Worker。
- 修改 .ui 后记得运行 `pack_resources.py` 生成对应 UI Python。
- 注意中文文件名跨平台编码；若打包为可执行文件，需确保 `Bayesian_1130` 可写。
