# Apriori 功能接入说明

## 目标

将 `Bayesian_1130/Apriori/Apriori.py` 的 CLI 流程完全绑定到 PyQt 项目中，实现 **页面一（数据导入）** 与 **页面二（规则挖掘）** 的端到端调用，同时保持原版脚本的执行顺序：`load_data → clean_data → preprocess → optimize_discretization → analyze → 导出/展示`。

---

## 项目结构变动

```
pyqt_apriori/
├── services/
│   ├── __init__.py                # 暴露 AprioriService
│   └── apriori_service.py         # GUI 与 Bayesian_1130 Apriori 脚本的桥梁
├── components/
│   └── dataset_config_dialog.py   # 在 GUI 中替代 CLI 的列配置对话框
├── view/pages/
│   ├── page_one*.py               # 新增数据配置/清洗逻辑
│   ├── page_two*.py               # 规则挖掘 UI 与 Handler
│   └── ...                        # 其余页面未修改
└── workers/
    └── apriori_worker.py          # 重写，直接驱动 Bayesian_1130/Apriori
```

---

## 软件界面运行流程

### 页面一（数据导入）

1. **导入 CSV**  
   `PageOne` 调用 `PageOneHandler.select_file()` → `AprioriService.configure_dataset()`：  
   - 通过 `dataset_config_dialog` 勾选列、目标值、正常值、规则模式。  
   - `AprioriService` 设置 `EquipmentAnalyzer` 的 `dataset_config/rule_config`，使用 `load_data(auto_detect=False)` 读取数据并缓存。

2. **展示数据预览**  
   `textEdit` 展示“数据集配置确认 + 数据预览”，并向主窗口广播 `dataset_config_info`（包含 dataset_config、rule_config、数值列、分类列等）。

3. **数据清洗**（可选）  
   `pushButton_clean` 在配置完成后解锁，点击触发 `AprioriService.clean_data()`：  
   - 使用 `EquipmentAnalyzer.clean_data()`，捕获 `print` 输出写入 `LogDialog`。  
   - 将清洗后的 DataFrame 替换缓存（供 Page2 使用）。  
   - 预览区域更新为“清洗后数据”。

### 页面二（规则挖掘）

1. **参数设置**  
   `doubleSpinBox_support/confidence/lift/binning` 对应 `min_support/min_confidence/min_lift/num_bins`。  
   `textEdit_3` 开头展示 `dataset_config_info` 摘要，确认与 Page1 保持一致。

2. **提取语料（pushButton_extract）**  
   Handler 汇总参数 + Page1 的 `dataset_config/rule_config` + 清洗后的 DataFrame，构造 `AprioriWorker`。

3. **后台挖掘**  
   `AprioriWorker` 直接导入 `Bayesian_1130/Apriori/Apriori.py`：  
   - 若 Page1 已清洗，则跳过 `clean_data/print_cleaning_report`（防止重复日志）。  
   - `progressBar` 分段更新：准备 5%→加载 15%→离散化方法（逐条日志 +5%）→关联规则 85%→过滤 90%→成功 100%。  
   - 日志通过自定义 `LogEmitter` 流式写入 `LogDialog`，并在日志中检测“测试离散化方法”来实时刷新状态标签。

4. **结果显示**  
   Worker 成功后 emit DataFrame → Handler 在 `textEdit_3` 用统一 HTML 模板展示规则；主窗口缓存 `initial_rules_df`，供后续贝叶斯步骤使用。

---

## 核心思路

- **共用单一脚本** ：所有逻辑均调用 `Bayesian_1130/Apriori/Apriori.py` 的 `EquipmentAnalyzer`，确保 CLI 与 GUI 行为一致，不再维护 `apriori/apriori1.py`。
- **Service 抽象** ：`AprioriService` 提供 `configure_dataset / clean_data / get_dataset_config` 等 API，隔离 GUI 与脚本细节。
- **DataFrame 复用** ：Page1 的原始/清洗数据直接传到 Page2，避免重复读取/清洗；Worker 内部重写 `load_data`、`clean_data` 以保证脚本仍按既定顺序执行，但不会重复打印清洗日志。
- **日志与进度可视化** ：自定义 `LogEmitter` 捕获 `print`，在 GUI 中边挖掘边输出；进度条与状态标签根据日志和阶段自动更新。

---

## 代码绑定范围

仅绑定 `Bayesian_1130/Apriori/Apriori.py`，未更改脚本本身的逻辑。GUI 层通过 Service + Worker 驱动其原本的执行流程，并与页面交互解耦。

---

## 部署提示

- 所有路径均基于 `__file__` 动态计算（如 `os.path.join(project_root, "Bayesian_1130", "datas")`），不存在硬编码盘符，可直接拷贝到新设备。
- 如果后续需要扩展贝叶斯训练/预测页面，可复用 `AprioriService` 中的 `dataset_config`、`rule_config` 与结果文件。

