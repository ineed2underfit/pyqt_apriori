# 故障预测分析桌面应用（PySide6 + Fluent Widgets）

一款多页面桌面端，用于设备故障预测的端到端流程：数据导入 → Apriori 规则挖掘 → 贝叶斯网络训练/预测 → 评估与报表生成/导出。

## 1) 项目定位与目标
- 为工业设备提供数据驱动的故障预测流程，包含规则挖掘、概率模型、可视化与报告输出。
- 以桌面化交互（PySide6/Fluent）集成数据预处理、模型训练、批量/单次预测、结果对比、报告生成/导出。

## 2) 核心功能页面
- Page1 数据导入：选择数据集后弹出“数据集配置”对话框（目标列/正常值/数值列/分类列/规则模式等），并支持数据清洗（输出清洗日志/报告），主窗口持久化 `dataset_path` 并缓存配置/列统计。
- Page2 Apriori：规则挖掘与离散化对比，支持设置最小支持度/置信度/提升度/分箱数，带日志弹窗与进度条，生成规则文件、分箱配置与 4 张对比图，并在页面内预览规则表格。
- Page3 贝叶斯网络：训练/构建 BN，带日志弹窗与进度条，保存 `final_bn_model.pkl`，输出 `bn_structure.png` 并在页面展示。
- Page4 预测评估：批量/单次预测；批量生成 `confusion_matrix.png` 与 `prediction_report.txt`，单次按结果生成 `health_assessment_single_report.txt` 或 `fault_diagnosis_single_report.txt`。
- Page5 数据可视化/历史查询：基于 Page4 测试集进行设备故障记录查询（未导入测试集时提示先完成 Page4），通过下拉框选择设备型号并点击查询，自动识别设备/目标列并输出故障统计与明细（仅界面展示，不落盘）。
- Page6 报告：提供“生成质量评价报告/导出报告”两个按钮；生成会汇总 `result/` 下图表与 txt 并展示到页面，同时生成 `装备使用质量评价分析报告_YYYY-MM-DD.docx`；导出可自定义保存路径/文件夹名，复制页面所需图表与 txt 并附带 Word 报告（自动拼接当天日期）。

### 各页面输入/输出资产
- Page1 数据导入  
  - 输入：用户选择的数据集文件 + 配置对话框中的字段设置  
  - 输出：`dataset_path`（内存共享，主窗体持有）+ `dataset_config_info`（配置/列统计缓存，供 Page2/4/5 使用）  
  - 清洗：可选数据清洗流程，生成清洗日志与摘要报告（通过日志弹窗展示）
- Page2 Apriori  
  - 输入：`dataset_path`  
  - 说明：优先使用 Page1 清洗后的数据进行规则挖掘  
  - 输出（落地 `Bayesian_1130/result/apriori_results/`）：  
    - `关联规则分析结果.csv`  
    - `完整数据配置.json`、`分箱配置.json`  
    - `故障预测规则提升度.png`  
    - `离散化方法规则数量对比.png`  
    - `离散化方法执行时间对比.png`  
    - `离散化方法性能综合对比.png`
- Page3 贝叶斯网络  
  - 输入：`dataset_path` + `Bayesian_1130/result/apriori_results/关联规则分析结果.csv` + `分箱配置.json`  
  - 输出：`Bayesian_1130/Bayesian/models/final_bn_model.pkl`，图 `Bayesian_1130/result/bayesian_results/bn_structure.png`
- Page4 预测评估  
  - 输入：  
    - 批量：Page4 选择的测试数据集（不从 Page1 传入）  
    - 单次：Page4 弹窗输入 + Page1 已选数据集（健康评估基准）  
    - 依赖文件：`Bayesian_1130/result/apriori_results/分箱配置.json`、`关联规则分析结果.csv`、`Bayesian_1130/Bayesian/models/final_bn_model.pkl`  
  - 输出（落地 `Bayesian_1130/result/bayesian_results/`）：  
    - 批量：`confusion_matrix.png`、`prediction_report.txt`  
    - 单次：`health_assessment_single_report.txt` 或 `fault_diagnosis_single_report.txt`
  - 交互流程：  
    - 批量：点击“导入测试集”→ 点击“批量质量评估”→ 展示报告与混淆矩阵，并保存到结果目录  
    - 单次：点击“单次质量评估”→ 弹窗输入参数 → 按健康/故障展示对应报告，并保存到结果目录
- Page5 历史查询  
  - 输入：Page4 选择的测试数据集  
  - 输出：页面展示故障统计与明细表（不落盘）
- Page6 报告  
  - 输入：Page2/3/4 生成的图表与 `prediction_report.txt`  
  - 输出：`Bayesian_1130/装备使用质量评价分析报告_YYYY-MM-DD.docx`；导出时复制上述全部资产到用户指定目录
  - 资产来源清单：  
    - Page2 → `Bayesian_1130/result/apriori_results/故障预测规则提升度.png`  
    - Page2 → `Bayesian_1130/result/apriori_results/离散化方法规则数量对比.png`  
    - Page2 → `Bayesian_1130/result/apriori_results/离散化方法执行时间对比.png`  
    - Page2 → `Bayesian_1130/result/apriori_results/离散化方法性能综合对比.png`  
    - Page3 → `Bayesian_1130/result/bayesian_results/bn_structure.png`  
    - Page4 → `Bayesian_1130/result/bayesian_results/confusion_matrix.png`  
    - Page4 → `Bayesian_1130/result/bayesian_results/prediction_report.txt`

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
  - `result/apriori_results/`：规则 CSV、分箱配置与 4 张 Apriori 对比图
  - `result/bayesian_results/`：`bn_structure.png`、`confusion_matrix.png`、`prediction_report.txt`、`health_assessment_single_report.txt`、`fault_diagnosis_single_report.txt`
  - `generate_report.py`：读取上述资产生成 `装备使用质量评价分析报告_YYYY-MM-DD.docx`
- `services/`：服务层（如 AprioriService）为页面提供数据/算法接口。
- `resource/`：静态资源（图片、i18n、qss）。
- `requirements.txt`：依赖列表（PySide6、Fluent Widgets、mlxtend、pgmpy、matplotlib、python-docx 等）。

## 4) 架构关系（简版）
- **View (view/pages/*.py)**：呈现 UI、收集输入、发出信号。
- **Handler (view/pages/*_handler.py)**：业务编排，调用 Service/Worker，处理回调并更新 UI。
- **Worker (workers/*.py)**：耗时算法/IO 在线程中运行，完成后通过信号返回结果。
- **Service (services/)**：封装数据/算法接口，供 Handler 使用（Apriori 使用 Service，Bayesian/Prediction 直接由 Worker 封装算法脚本）。
- **Bayesian_1130/**：算法产出与报告生成的落地目录。
- **资源流**：Page1/2/3/4 逐步生成数据与图表 → Page6 读这些资产生成/导出 docx。

输入/输出示例：
- Page2 输入：`dataset_path`；输出：`关联规则分析结果.csv` + `分箱配置.json` + 4 张 Apriori 图（落地到 `result/apriori_results/`）
- Page3 输入：`dataset_path` + `关联规则分析结果.csv` + `分箱配置.json`；输出：`final_bn_model.pkl` + `bn_structure.png`
- Page4 输入：批量测试集 + 单次弹窗输入 + Page1 基准数据；输出：`confusion_matrix.png`、`prediction_report.txt`，单次生成 `health_assessment_single_report.txt`/`fault_diagnosis_single_report.txt`
- Page6 输入：以上全部资产；输出：`装备使用质量评价分析报告_YYYY-MM-DD.docx`（在 `Bayesian_1130/`），并可一键导出到用户目录。

## 5) 运行流程（启动→结束）
1. `python entry.py`
2. 创建 QApplication，加载翻译/图标 → 登录窗口（或自动登录）→ 进入 MainWindow。
3. MainWindow 初始化导航与共享状态，实例化各页面并绑定信号槽。
4. 用户按流程操作：
   - Page1 选数据 → Page2 挖掘 → Page3 训练 BN → Page4 评估/生成报告资产 → Page6 生成/导出 Word 报告。
5. 关闭主窗体或退出 QApplication 结束进程。

## 6) 数据与控制流
- 数据流：`dataset_path` → Apriori 规则/分箱配置/图表 → BN 模型 + 结构图 → Page4 批量输出 (混淆矩阵 + prediction_report.txt) / 单次输出 (health_assessment_single_report.txt 或 fault_diagnosis_single_report.txt) → Word 报告。
- 控制流：用户事件触发 View → Handler 编排 → Worker 在线程执行 → 信号回调更新 UI/状态。
- 导出：Page6 Handler 校验资产齐全 → 复制图/txt/docx 到目标目录，刷新文件与 docx 核心属性时间戳。

## 7) 报告生成与导出要点
- 生成：`Bayesian_1130/generate_report.py` 读取 apriori/bayesian 结果与 txt，写入 `装备使用质量评价分析报告_YYYY-MM-DD.docx` 并同步 core properties 时间。
- 导出：Page6 “导出报告” 将 4 张 Apriori 图 + BN 图 + 混淆矩阵 + txt + docx 复制到用户选定目录，同步文件时间与 Word 元数据。

## 8) 快速使用
- 安装依赖：`pip install -r requirements.txt`（Python 3.10 环境已验证）
- 运行：`python entry.py`
- 修改 UI 后打包资源：`python pack_resources.py`
- CLI 直接生成 Word 报告（无需打开 UI）：`python Bayesian_1130/generate_report.py`
- 打包顺序（如需分发）：  
  1) `python pack_resources.py`（若 .ui/.qrc 有改动）  
  2) `pyinstaller --clean pyqt_apriori.spec`

## 9) 分层与联动
系统将功能拆分为清晰的 5 个层次，以实现职责分离与松耦合：
- **视图层 / UI 定义层（View，view/pages/*.py + ui_page/**）**：仅负责界面显示、控件初始化和用户输入事件绑定；发出信号，不做耗时运算。
- **控制层 / 业务逻辑层（Handler，view/pages/*_handler.py）**：处理业务编排与数据校验，接收 View 信号，调用 Service/Worker，整理结果并回写 View。
- **服务层（Service，services/**）**：封装算法/数据接口，为 Handler 提供可复用的业务服务。
- **工作层（Worker，workers/**）**：耗时任务在线程中执行，通过信号将完成/错误结果回传 Handler，避免阻塞 UI。
- **核心数据与资产层（Bayesian_1130/**）**：模型、结果、报告生成脚本与落地文件的集中存储与读写。

层间联动：
- View → Handler：用户事件触发信号，Handler 负责业务决策与调度。
- Handler → Service/Worker：同步调用 Service；耗时操作使用 Worker（QThread）异步执行。
- Worker → Handler → View：Worker 发出完成/错误信号，Handler 处理并更新 View。
- Handler/Service → 核心资产：读写 `Bayesian_1130` 下的模型、结果、报告文件，Page6 汇总导出。

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
