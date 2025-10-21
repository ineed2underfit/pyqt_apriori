# 项目结构与工作流程详解

## 📋 目录
1. [整体架构](#整体架构)
2. [文件夹结构详解](#文件夹结构详解)
3. [工作流程](#工作流程)
4. [数据流向](#数据流向)
5. [关键设计模式](#关键设计模式)

---

## 🏗 整体架构

### 架构模式：MVC + Handler 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    entry.py (入口)                       │
│                  启动应用 → 登录 → 主窗口                  │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              MainWindow (主窗口控制器)                    │
│  - 管理所有页面实例                                        │
│  - 存储共享数据 (dataset_path, model_pkl_path)           │
│  - 处理页面间通信                                          │
└─────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ Page 1  │        │ Page 3  │        │ Page 4  │
   │ (View)  │        │ (View)  │        │ (View)  │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        ↓                  ↓                  ↓
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │Handler 1│        │Handler 3│        │Handler 4│
   │(Logic)  │        │(Logic)  │        │(Logic)  │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        ↓                  ↓                  ↓
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ Worker  │        │ Worker  │        │ Worker  │
   │(Async)  │        │(Async)  │        │(Async)  │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
        ↓                  ↓                  ↓
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │Apriori  │        │Bayesian │        │Predict  │
   │(Core)   │        │(Core)   │        │(Core)   │
   └─────────┘        └─────────┘        └─────────┘
```

---

## 📁 文件夹结构详解

### 1️⃣ **入口层** (程序启动)

```
entry.py                    # 程序入口，启动应用
├── 创建 QApplication
├── 加载配置和翻译
├── 显示登录窗口 (可选)
└── 启动主窗口
```

---

### 2️⃣ **视图层** (UI界面)

#### `view/` - 视图主目录
```
view/
├── main_window.py          # 主窗口控制器
│   ├── 管理所有页面实例 (PageOne, PageTwo, Page3, Page4, Page5)
│   ├── 存储共享数据
│   │   ├── dataset_path: 数据集路径
│   │   ├── model_pkl_path: 模型文件路径
│   │   ├── initial_rules_df: 初始规则
│   │   └── optimized_rules_df: 优化规则
│   └── 处理页面间信号通信
│
├── login_window/           # 登录窗口模块
│   ├── window.py           # 登录窗口视图
│   └── handler.py          # 登录逻辑处理
│
└── pages/                  # 功能页面目录
    ├── page_one.py         # Page 1: 数据导入页面 (View)
    ├── page_one_handler.py # Page 1: 业务逻辑 (Handler)
    ├── page_two.py         # Page 2: Apriori规则挖掘 (View)
    ├── page_two_handler.py # Page 2: 业务逻辑 (Handler)
    ├── page_3.py           # Page 3: 贝叶斯网络构建 (View)
    ├── page_3_handler.py   # Page 3: 业务逻辑 (Handler)
    ├── page_4.py           # Page 4: 故障预测评估 (View)
    ├── page_4_handler.py   # Page 4: 业务逻辑 (Handler)
    ├── page_5.py           # Page 5: 数据可视化 (View)
    ├── page_5_handler.py   # Page 5: 业务逻辑 (Handler)
    └── setting_page.py     # 设置页面
```

**职责说明**：
- **View (页面.py)**: 
  - 继承自 `QWidget` 和 UI类
  - 负责界面显示和控件初始化
  - 绑定按钮事件到 Handler
  - 提供界面更新方法 (如 `update_progress`, `display_images`)
  
- **Handler (页面_handler.py)**:
  - 继承自 `QObject`
  - 处理所有业务逻辑
  - 调用 Worker 执行异步任务
  - 处理任务回调和错误

---

### 3️⃣ **UI定义层** (Qt Designer生成)

```
ui_page/                    # 页面UI文件目录
├── page_1.ui               # Page 1 的 Qt Designer 文件
├── page_2.ui               # Page 2 的 Qt Designer 文件
├── page_3.ui               # Page 3 的 Qt Designer 文件
├── page_4.ui               # Page 4 的 Qt Designer 文件
├── page_5.ui               # Page 5 的 Qt Designer 文件
├── ui_page_one.py          # 由 page_1.ui 生成的 Python 代码
├── ui_page_two.py          # 由 page_2.ui 生成的 Python 代码
├── ui_page_3.py            # 由 page_3.ui 生成的 Python 代码
├── ui_page_4.py            # 由 page_4.ui 生成的 Python 代码
└── ui_page_5.py            # 由 page_5.ui 生成的 Python 代码

ui_view/                    # 登录界面UI文件
└── ui_login_window.py      # 登录窗口UI代码
```

**工作流程**：
1. 在 Qt Designer 中编辑 `.ui` 文件
2. 运行 `python pack_resources.py` 将 `.ui` 转换为 `.py`
3. View 类继承生成的 UI 类

---

### 4️⃣ **异步任务层** (后台处理)

```
workers/                    # 异步任务管理
├── TaskManager.py          # 任务管理器 (QRunnable封装)
├── apriori_worker.py       # Apriori算法异步任务
│   └── AprioriWorker(QObject)
│       ├── run(): 执行Apriori算法
│       ├── finished信号: 任务完成
│       └── error信号: 任务失败
│
├── bayesian_worker.py      # 贝叶斯网络构建异步任务
│   └── BayesianWorker(QObject)
│       ├── run(): 构建贝叶斯网络
│       ├── finished信号: 任务完成
│       └── error信号: 任务失败
│
└── prediction_worker.py    # 预测任务异步处理
    └── PredictionWorker(QObject)
        ├── run(): 执行预测
        ├── batch_finished信号: 批量预测完成
        ├── single_prediction_finished信号: 单次预测完成
        └── error信号: 任务失败
```

**设计模式**：
- 使用 `QThread` + `QObject` 模式
- Worker 在独立线程中运行，避免阻塞UI
- 通过 Signal/Slot 机制与主线程通信

---

### 5️⃣ **核心算法层** (业务逻辑实现)

```
apriori/                    # Apriori算法模块
├── apriori1.py             # Apriori算法核心实现
└── equipment_analyzer.py   # 设备分析器

new_bayesian/               # 贝叶斯网络模块
├── BN_new/                 # 贝叶斯网络构建
│   └── bn_bayesian.py      # 核心类: BayesianNetwork
│       ├── load_data(): 加载数据
│       ├── preprocess_data(): 数据预处理和分箱
│       ├── build_network(): 构建网络结构
│       ├── train_model(): 训练模型
│       └── save_model(): 保存模型和分箱配置
│
├── predict/                # 预测模块
│   └── predict.py          # 预测核心实现
│       ├── load_model(): 加载模型和bin_config
│       ├── predict_single(): 单次预测
│       ├── predict_with_naive_bayes(): 批量预测
│       └── _discretize_single_value(): 单值分箱
│
├── dataset/                # 数据集目录
│   ├── testdata_info/      # 测试数据
│   └── training_data/      # 训练数据
│
├── pkl/                    # 模型文件目录
│   └── bn_bayesian_model.pkl  # 保存的模型 (model, bin_config)
│
└── result/                 # 结果输出目录
    └── bayesian_result/    # 贝叶斯网络结果
```

**关键数据结构**：
```python
# bin_config 结构 (保存在 .pkl 文件中)
bin_config = {
    'temp': {
        'bins': [50.0, 60.5, 70.2, 80.8, 90.0],
        'labels': ['极低温', '低温', '中温', '高温', '极高温']
    },
    'vibration': {
        'bins': [0.1, 0.3, 0.5, 0.7, 0.9],
        'labels': ['极低振动', '低振动', '中振动', '高振动', '极高振动']
    },
    # ... 其他特征
}
```

---

### 6️⃣ **通用工具层**

```
common/                     # 通用工具库
├── config.py               # 配置管理 (读写 config.json)
├── utils.py                # 通用工具函数
│   ├── show_dialog(): 显示对话框
│   └── 其他工具函数
├── my_logger.py            # 日志系统
└── aes.py                  # AES加密模块

components/                 # 自定义组件库
├── bar.py                  # 自定义进度条
├── icon.py                 # 图标管理
├── label_widget.py         # 自定义标签
└── log_dialog.py           # 日志对话框

resource/                   # 资源文件目录
├── images/                 # 图片资源
├── i18n/                   # 国际化文件
└── qss/                    # 样式表

api/                        # API接口层
└── api.py                  # 外部API接口
```

---

## 🔄 工作流程

### Page 4 控件与数据字段映射表

| 数据字段 | 控件类型 | 控件名称 | 说明 |
|---------|---------|---------|------|
| `timestamp` | DateTimeEdit | `dateTimeEdit` | 时间戳 |
| `device_id` | ComboBox | `comboBox_model` | 设备ID |
| `department` | ComboBox | `comboBox_apt` | 部门 |
| `temp` | DoubleSpinBox | `doubleSpinBox_temp` | 温度 |
| `vibration` | DoubleSpinBox | `doubleSpinBox_vibration` | 振动 |
| `oil_pressure` | DoubleSpinBox | `doubleSpinBox_oil` | 油压 |
| `voltage` | DoubleSpinBox | `doubleSpinBox_voltage` | 电压 |
| `rpm` | DoubleSpinBox | `doubleSpinBox_rpm` | 转速 |

**重要按钮**：
- `pushButton_solely`: 故障概率评估 (单次预测)
- `pushButton_assessment`: 质量评估 (批量预测)
- `pushButton_import`: 导入测试数据

**结果显示**：
- `textEdit_solely`: 单次预测结果显示区域
- `textEdit_3`: 批量预测结果显示区域

---

### 典型业务流程 (以 Page 4 单次预测为例)

```
1. 用户操作
   ↓
   用户在 Page4 界面输入数据
   ├── dateTimeEdit: 时间戳
   ├── comboBox_model: 设备ID
   ├── comboBox_apt: 部门
   ├── doubleSpinBox_temp: 温度
   ├── doubleSpinBox_vibration: 振动
   ├── doubleSpinBox_oil: 油压
   ├── doubleSpinBox_voltage: 电压
   └── doubleSpinBox_rpm: 转速
   ↓
   点击 "故障概率评估" 按钮 (pushButton_solely)

2. View 层 (page_4.py)
   ↓
   按钮点击事件触发
   ↓
   调用 handler.assess_single_instance()

3. Handler 层 (page_4_handler.py)
   ↓
   assess_single_instance() 方法
   ├── 从UI控件收集数据 → data_dict
   ├── 获取模型路径 → main_window.model_pkl_path
   ├── 禁用按钮，显示"正在预测..."
   └── 调用 _run_prediction(data_dict)

4. Worker 层 (prediction_worker.py)
   ↓
   创建 PredictionWorker
   ├── 创建 QThread
   ├── 将 Worker 移到线程
   └── 启动线程
   ↓
   Worker.run() 执行
   ├── 加载模型: model, bin_config = load_model(model_path)
   ├── 调用预测: predict_single(model, data_dict, bin_config)
   └── 发射信号: single_prediction_finished.emit(result, data_dict)

5. 核心算法层 (predict.py)
   ↓
   predict_single(model, data_dict, bin_config)
   ├── 将 data_dict 转为 DataFrame
   ├── 使用 bin_config 对连续变量分箱
   │   └── _discretize_single_value(value, bin_config[col])
   ├── 修改部门名称: '部门_' + department
   ├── 过滤模型节点
   └── 调用模型预测: model.predict(df)
   ↓
   返回预测结果: '故障类型'

6. 回调处理 (page_4_handler.py)
   ↓
   on_single_assessment_finished(prediction_result, input_data)
   ├── 格式化输出文本
   ├── 显示在 textEdit_solely
   ├── 清理线程
   └── 重新启用按钮
```

---

## 📊 数据流向

### Page 1 → Page 2 → Page 3 → Page 4 数据传递

```
Page 1 (数据导入)
   ↓ file_selected 信号
MainWindow.on_file_path_changed()
   ↓ 保存 dataset_path
   
Page 2 (Apriori规则挖掘)
   ↓ 读取 MainWindow.dataset_path
   ↓ 执行 Apriori 算法
   ↓ initial_rules_ready 信号
MainWindow.on_initial_rules_ready()
   ↓ 保存 initial_rules_df
   ↓ optimized_rules_ready 信号
MainWindow.on_optimized_rules_ready()
   ↓ 保存 optimized_rules_df

Page 3 (贝叶斯网络构建)
   ↓ 读取 MainWindow.dataset_path
   ↓ 构建并训练贝叶斯网络
   ↓ 保存模型到 MainWindow.model_pkl_path
   ↓ 保存 (model, bin_config) 到 .pkl 文件

Page 4 (故障预测)
   ↓ 读取 MainWindow.model_pkl_path
   ↓ 加载 (model, bin_config)
   ↓ 执行预测
   └── 显示结果
```

---

## 🎯 关键设计模式

### 1. **MVC 模式**
- **Model**: 核心算法层 (apriori/, new_bayesian/)
- **View**: 视图层 (view/pages/*.py)
- **Controller**: Handler层 (view/pages/*_handler.py)

### 2. **Handler 分层架构**
```python
# View 只负责界面
class Page4(QWidget, Ui_page_4):
    def __init__(self):
        self.handler = PageFourHandler(self)
        self.bind_event()
    
    def bind_event(self):
        self.pushButton_solely.clicked.connect(
            self.handler.assess_single_instance
        )

# Handler 负责业务逻辑
class PageFourHandler(QObject):
    def assess_single_instance(self):
        # 收集数据
        # 调用 Worker
        # 处理回调
```

### 3. **异步任务模式**
```python
# 创建线程和Worker
self.thread = QThread()
self.worker = PredictionWorker(model_path, data)
self.worker.moveToThread(self.thread)

# 连接信号
self.thread.started.connect(self.worker.run)
self.worker.finished.connect(self.on_finished)

# 启动线程
self.thread.start()
```

### 4. **Signal/Slot 通信**
```python
# 页面间通信
class PageOne(QWidget):
    file_selected = Signal(str)  # 定义信号
    
    def select_file(self):
        self.file_selected.emit(file_path)  # 发射信号

class MainWindow(FluentWindow):
    def __init__(self):
        self.pageOne.file_selected.connect(
            self.on_file_path_changed  # 连接槽函数
        )
```

---

## 🔑 核心文件说明

### 最重要的文件

1. **entry.py**: 程序入口
2. **view/main_window.py**: 主窗口，管理所有页面和共享数据
3. **view/pages/page_4_handler.py**: Page4业务逻辑
4. **workers/prediction_worker.py**: 预测异步任务
5. **new_bayesian/predict/predict.py**: 预测核心算法
6. **new_bayesian/BN_new/bn_bayesian.py**: 贝叶斯网络训练

### 配置文件

- **config.json**: 用户配置 (主题、语言、自动登录等)
- **requirements.txt**: Python依赖包

---

## 📝 开发建议

### 修改界面
1. 使用 Qt Designer 编辑 `ui_page/*.ui`
2. 运行 `python pack_resources.py`
3. 在对应的 `view/pages/*.py` 中使用

### 添加新功能
1. 在 Handler 中添加业务逻辑
2. 如需异步处理，创建 Worker
3. 通过 Signal/Slot 更新界面

### 调试技巧
- 查看控制台输出 (print/logger)
- 检查 `logs/` 目录下的日志文件
- 使用 DEBUG 标记追踪数据流

---

## 🐛 历史问题与解决方案

### 问题：单次预测总是返回"正常运行"

#### 问题现象
在 Page 4 中进行单次故障预测时，无论输入什么参数值，预测结果总是"正常运行"，模型不敏感。

#### 根本原因
```python
# ❌ 错误的做法 (旧代码)
def predict_single(model, data_dict):
    df = pd.DataFrame([data_dict])
    # 对单个值调用 std_based_binning
    for col in ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']:
        df[col] = std_based_binning(df[col], num_bins=5, var_name=col)
    # 结果：所有值都变成 NaN！
```

**为什么会变成 NaN？**
- `std_based_binning` 需要计算均值和标准差
- 对单个值：`mean = 58.0`, `std = 0.0`
- 生成的分箱边界：`[58.0, 58.0, 58.0, ...]` (全部相同)
- `pd.cut` 无法处理重复边界 → 返回 `NaN`
- 模型接收 `NaN` → 默认预测最常见类别 → "正常运行"

#### 解决方案

**核心思想**：使用训练时的分箱边界，而不是重新计算

```python
# ✅ 正确的做法 (新代码)

# 1. 训练时保存分箱配置
# bn_bayesian.py
pickle.dump((model, bin_config), f)

# 2. 预测时加载分箱配置
# predict.py
model, bin_config = load_model(model_path)

# 3. 使用预设边界对单值分箱
def _discretize_single_value(value, bin_config_for_feature):
    bins = bin_config_for_feature['bins']  # 使用训练时的边界
    labels = bin_config_for_feature['labels']
    
    # 确保值在范围内
    if value < bins[0]:
        value = bins[0]
    elif value > bins[-1]:
        value = bins[-1]
    
    # 使用预设边界分箱
    result = pd.cut(pd.Series([value]), bins=bins, labels=labels, include_lowest=True)
    return result.iloc[0]

# 4. 在 predict_single 中使用
for col_name, config in bin_config.items():
    if col_name in df.columns:
        df[col_name] = _discretize_single_value(df[col_name].iloc[0], config)
```

#### 修改的文件

1. **`new_bayesian/predict/predict.py`**
   - 修改 `load_model()`: 返回 `(model, bin_config)`
   - 新增 `_discretize_single_value()`: 使用预设边界分箱
   - 修改 `predict_single()`: 接收并使用 `bin_config`

2. **`workers/prediction_worker.py`**
   - 修改 `run()`: 加载并传递 `bin_config`

3. **`new_bayesian/BN_new/bn_bayesian.py`**
   - 已经正确保存 `(model, bin_config)` ✅

#### 关键数据流

```
训练阶段 (Page 3):
  数据 → 计算分箱边界 → bin_config
       → 训练模型 → model
       → 保存 (model, bin_config) → .pkl

预测阶段 (Page 4):
  加载 .pkl → (model, bin_config)
       → 使用 bin_config 对输入分箱
       → model.predict()
       → 返回预测结果
```

---

## 🎓 总结

这个项目采用了**清晰的分层架构**：

1. **UI层** (ui_page/) - Qt Designer设计
2. **视图层** (view/) - 界面显示和事件绑定
3. **控制层** (Handler) - 业务逻辑处理
4. **异步层** (workers/) - 后台任务执行
5. **算法层** (apriori/, new_bayesian/) - 核心算法实现

**优势**：
- ✅ 职责分离，易于维护
- ✅ 异步处理，界面流畅
- ✅ 模块化设计，易于扩展
- ✅ 信号槽机制，松耦合

**关键点**：
- 所有耗时操作都在 Worker 中异步执行
- 页面间通过 MainWindow 共享数据
- **bin_config 确保训练和预测时分箱一致** ⭐ (核心！)
