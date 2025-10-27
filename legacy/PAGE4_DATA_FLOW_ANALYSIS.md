# Page 4 - textEdit_solely 数据流向完整分析

## 📊 概览

`textEdit_solely` 是 Page 4 页面用于显示**单次故障预测结果**的文本展示框。

---

## 🔄 完整数据流向图

```
┌─────────────────────────────────────────────────────────────────┐
│                    1️⃣ 用户操作 (View 层)                         │
│                      page_4.py                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        用户在界面输入数据并点击"故障概率评估"按钮
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 2️⃣ 数据收集 (Handler 层)                         │
│              page_4_handler.py                                   │
│          assess_single_instance()                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        收集 UI 控件数据 → data_dict
        {
            'timestamp': '2023-06-01T00:00:00',
            'device_id': 'DEV-001',
            'department': '生产部',
            'temp': 58.0,
            'vibration': 1.4,
            'oil_pressure': 11.0,
            'voltage': 220.0,
            'rpm': 2020.0
        }
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              3️⃣ 启动异步任务 (Handler 层)                        │
│              page_4_handler.py                                   │
│            _run_prediction(data_dict)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        创建 PredictionWorker(model_path, data_dict)
        启动独立线程执行预测
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                4️⃣ 异步执行 (Worker 层)                           │
│              prediction_worker.py                                │
│                 PredictionWorker.run()                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ├─ 10%: 初始化
        ├─ 20%: 开始加载模型
        ├─ 50%: 加载 model, bin_config = load_model(model_path)
        ├─ 60%: 准备预测
        ├─ 90%: 执行 prediction_result, probability_dist = predict_single(...)
        └─ 100%: 完成
                              ↓
        发射信号: single_prediction_finished.emit(
            prediction_result,    # 预测结果，如 "散热系统故障"
            data_dict,            # 原始输入数据
            probability_dist      # 概率分布字典
        )
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               5️⃣ 核心预测逻辑 (算法层)                           │
│            new_bayesian/predict/predict.py                       │
│                 predict_single()                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        A. 极端值检测
           _detect_extreme_values(data_dict)
           ├─ 检查是否有极端值（如 temp > 95）
           └─ 如果有极端值 → _predict_extreme_case()
                              ↓
        B. 正常预测流程
           ├─ 数据预处理（分箱）
           │  └─ 使用 bin_config 对连续值分箱
           ├─ 模型预测
           │  └─ model.predict(df)
           └─ 概率查询
              └─ _get_probability_distribution(model, df)
                              ↓
        返回: (prediction_result, probability_dist)
        
        例如:
        prediction_result = "散热系统故障"
        probability_dist = {
            "散热系统故障": 0.75,
            "正常运行": 0.15,
            "传动系统异常": 0.08,
            "润滑系统异常": 0.015,
            "电力供应故障": 0.005
        }
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              6️⃣ 回调处理 (Handler 层)                            │
│              page_4_handler.py                                   │
│        on_single_assessment_finished()                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        接收三个参数:
        - prediction_result: "散热系统故障"
        - input_data_dict: 原始输入数据
        - probability_dist: 概率分布字典
                              ↓
        构建 HTML 字符串:
        ├─ 标题: "⚡ 单次故障概率评估结果"
        ├─ 输入数据表格
        ├─ 预测结果（根据结果选择颜色）
        │  ├─ 正常运行 → 绿色 🟢
        │  └─ 异常 → 红色 🔴
        ├─ 低置信度警告（如果最高概率 < 60%）
        └─ 概率分布条形图
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                7️⃣ 显示结果 (View 层)                             │
│                    page_4.py                                     │
│              textEdit_solely.setHtml(output)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    用户看到美观的结果展示
```

---

## 📝 详细步骤说明

### 1️⃣ 用户操作 (View 层)

**文件**: `view/pages/page_4.py`

```python
# 用户在界面上:
# - 输入时间戳 (dateTimeEdit)
# - 选择设备ID (comboBox_model)
# - 选择部门 (comboBox_apt)
# - 输入温度 (doubleSpinBox_temp)
# - 输入振动 (doubleSpinBox_vibration)
# - 输入油压 (doubleSpinBox_oil)
# - 输入电压 (doubleSpinBox_voltage)
# - 输入转速 (doubleSpinBox_rpm)
# 
# 点击 "故障概率评估" 按钮 (pushButton_solely)
# ↓ 触发事件
# handler.assess_single_instance()
```

---

### 2️⃣ 数据收集 (Handler 层)

**文件**: `view/pages/page_4_handler.py`  
**方法**: `assess_single_instance()`

```python
def assess_single_instance(self):
    """对UI界面上输入的数据进行单次评估"""
    
    # 从UI控件收集数据
    data_dict = {
        'timestamp': self._parent.dateTimeEdit.dateTime().toString(Qt.DateFormat.ISODate),
        'device_id': self._parent.comboBox_model.currentText(),
        'department': self._parent.comboBox_apt.currentText(),
        'temp': self._parent.doubleSpinBox_temp.value(),
        'vibration': self._parent.doubleSpinBox_vibration.value(),
        'oil_pressure': self._parent.doubleSpinBox_oil.value(),
        'voltage': self._parent.doubleSpinBox_voltage.value(),
        'rpm': self._parent.doubleSpinBox_rpm.value()
    }
    
    # 调用预测函数
    self._run_prediction(data_dict)
```

**输出**: `data_dict` 字典

---

### 3️⃣ 启动异步任务 (Handler 层)

**文件**: `view/pages/page_4_handler.py`  
**方法**: `_run_prediction(data_payload)`

```python
def _run_prediction(self, data_payload):
    """通用的预测执行函数"""
    
    # 获取模型路径
    model_path = main_window.model_pkl_path
    # 例如: "new_bayesian/pkl/bn_bayesian_model.pkl"
    
    # 创建 Worker 和线程
    self.thread = QThread()
    self.worker = PredictionWorker(model_path, data_payload)
    self.worker.moveToThread(self.thread)
    
    # 连接信号
    self.worker.single_prediction_finished.connect(
        self.on_single_assessment_finished  # ⭐ 关键回调
    )
    self.worker.progress_updated.connect(self.on_progress_updated)
    
    # 启动线程
    self.thread.start()
```

---

### 4️⃣ 异步执行 (Worker 层)

**文件**: `workers/prediction_worker.py`  
**方法**: `PredictionWorker.run()`

```python
def run(self):
    # 单次预测模式
    if isinstance(self.data, dict):
        # 进度更新
        self.progress_updated.emit(10)   # 初始化
        self.progress_updated.emit(20)   # 开始加载
        
        # 加载模型和分箱配置
        model, bin_config = load_model(self.model_path)
        self.progress_updated.emit(50)   # 加载完成
        
        # 执行预测 ⭐ 核心步骤
        prediction_result, probability_dist = predict_single(
            model, 
            self.data,      # data_dict
            bin_config
        )
        self.progress_updated.emit(90)   # 预测完成
        
        # 发射完成信号 ⭐ 传递三个参数
        self.single_prediction_finished.emit(
            prediction_result,    # 如 "散热系统故障"
            self.data,            # 原始 data_dict
            probability_dist      # 概率分布字典
        )
```

**输出**: 
- `prediction_result`: 字符串，如 `"散热系统故障"`
- `probability_dist`: 字典，如 `{"散热系统故障": 0.75, "正常运行": 0.15, ...}`

---

### 5️⃣ 核心预测逻辑 (算法层)

**文件**: `new_bayesian/predict/predict.py`  
**方法**: `predict_single(model, data_dict, bin_config)`

```python
def predict_single(model, data_dict, bin_config):
    """对单条数据进行预测"""
    
    # A. 极端值检测
    extreme_detected, extreme_values = _detect_extreme_values(data_dict)
    
    if extreme_detected:
        extreme_prediction = _predict_extreme_case(data_dict)
        if extreme_prediction != "正常运行":
            # 极端情况，直接返回 100% 概率
            return extreme_prediction, {extreme_prediction: 1.0}
    
    # B. 正常预测流程
    df = pd.DataFrame([data_dict])
    
    # 数据预处理：使用训练时的分箱边界
    for col_name, config in bin_config.items():
        if col_name in df.columns:
            df[col_name] = _discretize_single_value(
                df[col_name].iloc[0], 
                config
            )
    
    # 修改部门名称
    df['department'] = '部门_' + df['department']
    
    # 过滤模型节点
    model_nodes = model.nodes()
    df = df[[col for col in df.columns if col in model_nodes]]
    
    # 执行预测
    prediction = model.predict(df)
    prediction_result = prediction['故障类型'].iloc[0]
    
    # 获取概率分布 ⭐ 重要
    probability_dist = _get_probability_distribution(model, df)
    
    return prediction_result, probability_dist
```

**关键函数**: `_get_probability_distribution()`

```python
def _get_probability_distribution(model, evidence_df):
    """获取故障类型的概率分布"""
    from pgmpy.inference import VariableElimination
    
    # 创建推理引擎
    inference = VariableElimination(model)
    
    # 准备证据
    evidence = {}
    for col in evidence_df.columns:
        if col != '故障类型':
            evidence[col] = evidence_df[col].iloc[0]
    
    # 查询概率分布
    query_result = inference.query(['故障类型'], evidence=evidence)
    
    # 提取概率
    prob_dist = {}
    for state in query_result.state_names['故障类型']:
        prob = query_result.values[...]
        prob_dist[state] = float(prob)
    
    # 按概率从大到小排序
    return dict(sorted(prob_dist.items(), key=lambda x: x[1], reverse=True))
```

**输出示例**:
```python
prediction_result = "散热系统故障"
probability_dist = {
    "散热系统故障": 0.75,
    "正常运行": 0.15,
    "传动系统异常": 0.08,
    "润滑系统异常": 0.015,
    "电力供应故障": 0.005
}
```

---

### 6️⃣ 回调处理 (Handler 层)

**文件**: `view/pages/page_4_handler.py`  
**方法**: `on_single_assessment_finished(prediction_result, input_data_dict, probability_dist)`

```python
def on_single_assessment_finished(self, prediction_result, input_data_dict, probability_dist):
    """单次评估成功的回调 - 构建 HTML 显示"""
    
    # 1. 开始构建 HTML
    output = '<div style="font-size: 10pt; line-height: 1.6;">'
    
    # 2. 标题
    output += '<p style="font-size: 11pt; font-weight: bold;">⚡ 单次故障概率评估结果</p>'
    
    # 3. 输入数据表格
    output += '<table>...'
    for key, value in input_data_dict.items():
        output += f'<tr><td>{key}</td><td>{value}</td></tr>'
    output += '</table>'
    
    # 4. 预测结果 - 根据结果选择颜色 ⭐ 你的优化
    if prediction_result == "正常运行":
        result_color = "#27ae60"  # 绿色
        result_icon = "🟢"
    else:
        result_color = "#e74c3c"  # 红色
        result_icon = "🔴"
    
    # 5. 低置信度警告 ⭐ 你的优化
    max_prob = max(probability_dist.values())
    if max_prob < 0.6:
        output += '<div>⚠️ 低置信度警告</div>'
    
    # 6. 显示预测结果
    output += f'<p style="color: {result_color};">{result_icon} 预测故障类型：{prediction_result}</p>'
    
    # 7. 概率分布条形图 ⭐ 你的优化
    output += '<div>📈 故障类型概率分布：</div>'
    for fault_type, prob in probability_dist.items():
        bar_width = prob * 100
        output += f'<div>{fault_type}: {prob:.1%}</div>'
        output += f'<div style="width: {bar_width}%; background-color: ..."></div>'
    
    output += '</div>'
    
    # 8. 渲染到 textEdit_solely ⭐ 最终显示
    self._parent.textEdit_solely.setHtml(output)
    
    # 9. 清理线程
    self.cleanup_thread()
```

---

### 7️⃣ 显示结果 (View 层)

**文件**: `view/pages/page_4.py`  
**控件**: `textEdit_solely`

```python
# Handler 调用
self._parent.textEdit_solely.setHtml(output)

# textEdit_solely 渲染 HTML，用户看到:
# ⚡ 单次故障概率评估结果
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 
# 📊 输入数据：
# ┌──────────────────────────────────────┐
# │ ⏰ 时间戳      │ 2023-06-01T00:00:00  │
# │ 🛠️ 设备ID      │ DEV-001              │
# │ ...                                   │
# └──────────────────────────────────────┘
# 
# 🔴 预测故障类型：散热系统故障
# 
# 📈 故障类型概率分布：
# 散热系统故障  75.0% ████████████████
# 正常运行      15.0% ███
# ...
```

---

## 🔑 关键数据来源总结

### `textEdit_solely` 显示的数据来自：

| 数据项 | 来源 | 说明 |
|--------|------|------|
| **输入数据** | `input_data_dict` | Handler 从 UI 控件收集 |
| **预测结果** | `prediction_result` | `predict_single()` 返回 |
| **概率分布** | `probability_dist` | `_get_probability_distribution()` 计算 |
| **颜色样式** | Handler 逻辑 | 根据 `prediction_result` 动态选择 |
| **置信度警告** | Handler 逻辑 | 根据 `max(probability_dist.values())` 判断 |

---

## 🎯 你的优化点

根据你的修改，你添加了以下功能：

### 1. **极端值检测** (`predict.py`)
```python
def _detect_extreme_values(data_dict):
    # 检测是否有极端值
    if temp > 95:
        return "散热系统故障", {prediction: 1.0}
```

### 2. **概率分布显示** (`page_4_handler.py`)
```python
# 显示每个故障类型的概率
probability_dist = {
    "散热系统故障": 0.75,
    "正常运行": 0.15,
    ...
}
# 渲染为条形图
```

### 3. **动态颜色** (`page_4_handler.py`)
```python
if prediction_result == "正常运行":
    color = "绿色" 🟢
else:
    color = "红色" 🔴
```

### 4. **低置信度警告** (`page_4_handler.py`)
```python
if max(probability_dist.values()) < 0.6:
    显示警告 ⚠️
```

---

## 📌 总结

**数据流向**：
```
UI 控件 → data_dict → Worker → predict_single() → 
(prediction_result, probability_dist) → Handler → HTML → textEdit_solely
```

**关键文件**：
1. `page_4_handler.py` - 数据收集和显示格式化
2. `prediction_worker.py` - 异步执行
3. `predict.py` - 核心预测逻辑和概率计算

**显示内容**：
- ✅ 输入数据（来自 UI 控件）
- ✅ 预测结果（来自贝叶斯模型或极端值规则）
- ✅ 概率分布（来自贝叶斯推理引擎）
- ✅ 动态样式（Handler 根据结果动态生成）

希望这个分析对你有帮助！🎉
