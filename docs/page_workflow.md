# 项目页面开发记录（Page1~Page4）

## 通用结构

```
pyqt_apriori/
├── view/main_window.py        # 导航与共享状态（dataset_path、rules_df、model路径）
├── services/
│   └── apriori_service.py     # 封装 Bayesian_1130/Apriori/EquipmentAnalyzer
├── workers/
│   ├── apriori_worker.py      # Apriori 关联规则挖掘
│   ├── bayesian_worker.py     # 贝叶斯网络训练（build_model）
│   └── prediction_worker.py   # 贝叶斯批量/单次预测（predict_status）
└── Bayesian_1130/             # 新算法目录（Apriori、Bayesian）
```

MainWindow 负责把 `dataset_path`、`initial_rules_df` 等共享信息分发给各页面，Service/Worker 则把 CLI 脚本包装成 GUI 可用的 API。

### 运行步骤（Quick Start）
1. **Page1：导入数据并配置列** → 可选点击 “数据清洗”。
2. **Page2：调整 min_support/min_confidence/min_lift/num_bins → 提取语料**，确认规则与统计图。
3. **Page3：点击“构建贝叶斯网络”**，生成模型 + `bn_structure.png`。
4. **Page4：导入测试集 → “质量评估”**，查看 `prediction_report.txt` 与 `confusion_matrix.png`。

### 共享状态说明
- **MainWindow.dataset_path**：Page1 发送；Page2、Page3、Page5 读取（训练/查询必须依赖）。
- **MainWindow.initial_rules_df**：Page2 `initial_rules_ready` 信号发射；Page3、Page4 使用以确保 Page2 先执行。
- **MainWindow.model_pkl_path**：Page3 构建后保存至 `Bayesian_1130/Bayesian/models/final_bn_model.pkl`，Page4 预测时用到。
- **dataset_config_info**（Page2 需要）：包括 dataset_config / rule_config / 展示摘要，来自 Page1 Handler。

### 路径约定
- **数据目录**：`Bayesian_1130/datas/`（导入/测试集的标准位置）。
- **Apriori 输出**：`Bayesian_1130/result/apriori_results/`（规则 CSV、分箱 JSON、图表）。
- **贝叶斯输出**：`Bayesian_1130/result/bayesian_results/`（bn_structure.png、prediction_report.txt、confusion_matrix.png 等）。
- **配置文件**：`Bayesian_1130/Apriori/分箱配置.json` 与 `result/apriori_results/分箱配置.json` 内容一致，训练/预测统一读取前者。

---

## Page1：数据导入与清洗

### 实现逻辑
1. **导入数据**：`pushButton` 选择 CSV（默认 `Bayesian_1130/datas`），读取后弹出 `DatasetConfigDialog` 选择目标列、数值列、分类列、正常状态、规则模式。
2. **配置服务**：`AprioriService.configure_dataset()` 初始化 `EquipmentAnalyzer` → `load_data(auto_detect=False)` → 缓存 Raw DataFrame / dataset_config / rule_config。
3. **数据预览**：`textEdit` 显示“数据集配置确认 + 数据预览（前 100 行）”。
4. **数据清洗**：`pushButton_clean` 触发 `AprioriService.clean_data()`，捕获 CLI `print` 输出，显示于 `LogDialog`，并把清洗后的 DataFrame 回写 Service。

### 关键方法
- `services/apriori_service.py::configure_dataset`
- `services/apriori_service.py::clean_data`
- `DatasetConfigDialog` 收集列信息

### 新增功能
- GUI 取代 CLI 交互式配置；缓存 dataset_config / rule_config。
- 清洗过程可视化（日志弹窗 + 清洗后数据预览）。

---

## Page2：关联规则挖掘

### 实现逻辑
1. **参数获取**：`doubleSpinBox_support/confidence/lift/binning` 直接映射到 Apriori 参数；`textEdit_3` 顶部展示来自 Page1 的配置摘要。
2. **触发挖掘**：`pushButton_extract` 调用 `AprioriWorker`，传入 dataset_config/rule_config/离散化后的 DataFrame。
3. **Worker 执行**：载入 `Bayesian_1130/Apriori/Apriori.py` → `load_data`（若已有清洗数据则跳过）→ `optimize_discretization` → `analyze`。日志通过 `LogEmitter` 流式写入 `LogDialog`。
4. **进度反馈**：阶段性更新 progress（准备/加载/离散化/生成/过滤/完成）。`_handle_log_message` 解析“测试离散化方法: …” 等日志刷新状态。
5. **结果展示**：`textEdit_3` 用 HTML 表格 + 统计信息渲染规则列表；`initial_rules_ready` 信号发送给 MainWindow，为 Page3/4 提供规则 DataFrame。

### 关键方法
- `workers/apriori_worker.AprioriWorker.run`
- `view/pages/page_two_handler.PageTwoHandler._handle_log_message`

### 新增功能
- 完全弃用 `apriori/apriori1.py`，改为调 `Bayesian_1130/Apriori`。
- 日志实时输出（而不是 CLI 结束后一次性打印）。
- 进度条与状态标签更细腻（多阶段）。
- 自动跳过重复清洗日志、自动复用清洗后的 DataFrame。

---

## Page3：贝叶斯网络训练

### 实现逻辑
1. **前置条件**：必须在 Page1 导入数据、Page2 完成挖掘（MainWindow 中 `dataset_path` / `initial_rules_df` 不为空）。
2. **启动训练**：`pushButton` → `BayesianWorker`。
3. **Worker 流程**：
   - 复制训练 CSV 到 `Bayesian_1130/datas`
   - 调 `Bayesian/build_model.build_and_save_bayesian_model()` 训练生成 `Bayesian/Bayesian/models/final_bn_model.pkl`、`result/bayesian_results/bn_structure.png`
   - 日志/进度（5% 准备 → 20% 训练 → 100% 完成）
4. **结果展示**：`graphicsView` 仅显示 `bn_structure.png`（第二张图片暂留空位）。

### 关键方法
- `workers/bayesian_worker.BayesianWorker`
- `view/pages/page_3_handler.PageThreeHandler`

### 新增功能
- Worker 直接加载 `Bayesian_1130/Bayesian/build_model.py`，取代老的 `new_bayesian/BN_new`。
- 线性日志 + 进度条；训练完成后图像自动展示。

---

## Page4：质量评估 & 混淆矩阵

### 实现逻辑
1. **导入测试集**：`pushButton_import` 选择 CSV（默认 `Bayesian_1130/datas`），同时启用 `pushButton_assessment`。
2. **批量评估**：`pushButton_assessment` 调用 `PredictionWorker`。
3. **Worker 流程**：
   - 将测试 CSV 复制到 `Bayesian_1130/datas`
   - 设置 `predict_status.py` 的 `MODEL_PATH / DATA_PATH / BINNING_CONFIG_PATH / RESULT_DIR`
   - 调 `predict_status.main()`，输出 `prediction_report.txt` 和 `confusion_matrix.png`
   - 将报告文本与混淆矩阵路径一起返回
4. **显示结果**：`textEdit_3` 先嵌入报告文字，再嵌入 `<img>`（使用 `max-width:90%; height:auto;`），保证图片随窗口宽度缩放。

### 关键方法
- `workers/prediction_worker.PredictionWorker._run_batch`
- `view/pages/page_4_handler.PageFourHandler.on_batch_assessment_finished`

### 新增功能
- 彻底移除 `new_bayesian/predict` 依赖，改为调用 `Bayesian_1130/Bayesian/predict_status.py`
- 报告 + 图像统一在 `textEdit_3` 中显示（自适应宽度），无需额外控件。

---

## 继续开发建议
1. **环境稳定性**：为新设备准备 `conda` 环境及 `QT_PLUGIN_PATH` 设置（参考 README）。
2. **Page3 后续**：如需在 Page3 同时展示预测结果，可在训练后调用 `PredictionWorker` 并把混淆矩阵嵌入 Page3。
3. **Page4 单次预测**：单条预测目前仍沿用旧 UI，可逐步迁移到 `predict_status.py` 的 `main_one()` 或自定义函数。
4. **Page5**：仍依赖 Page1 数据（查询历史记录），如需使用新的贝叶斯结果，可向 Handler 注入 Service/Worker。

该文档总结了四个页面的当前实现，方便未来在新设备上快速部署或进一步迭代。
