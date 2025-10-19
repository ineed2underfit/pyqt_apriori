# bn_bayesian.py 工作流程详解

## 📋 完整执行链路

```
开始
  ↓
1. 初始化 BayesianNetworkBayesian 对象
  ├─ 设置数据路径: ../dataset/data_info/training_dataset.csv
  ├─ 设置规则路径: ../dataset/optimal_rules.csv
  └─ 创建输出目录: ../pkl, ../bayesian_result
  ↓
2. load_data() - 加载训练数据
  ├─ 读取 CSV 文件
  ├─ 验证数据完整性
  └─ 输出: 10万条记录，7个特征
  ↓
3. preprocess_data() - 数据预处理
  ├─ 保留关键列: department, temp, vibration, oil_pressure, voltage, rpm, 故障类型
  ├─ 连续变量离散化 (基于标准差分箱)
  │   ├─ temp → [极低温, 低温, 中温, 高温, 极高温]
  │   ├─ vibration → [极低振动, 低振动, 中振动, 高振动, 极高振动]
  │   ├─ oil_pressure → [极低油压, 低油压, 中油压, 高油压, 极高油压]
  │   ├─ voltage → [极低电力, 低电力, 中电力, 高电力, 极高电力]
  │   └─ rpm → [极低转速, 低转速, 中转速, 高转速, 极高转速]
  └─ 部门变量处理: department → 部门_生产部, 部门_研发部...
  ↓
4. load_rules() - 加载关联规则
  ├─ 读取 optimal_rules.csv
  └─ 输出: 4条优化规则
  ↓
5. process_rules() - 处理规则构建网络结构
  ├─ 解析规则格式: "前因 → 后果"
  │   例: "中电力 ∧ 极高转速 → 传动系统异常"
  ├─ 提取前因条件 (用 ∧ 分割)
  ├─ 映射状态值到变量名
  │   例: "中电力" → voltage
  │        "极高转速" → rpm
  └─ 构建边: (变量名, '故障类型')
      例: (voltage, '故障类型'), (rpm, '故障类型')
  ↓
6. build_network() - 构建贝叶斯网络
  ├─ 使用 pgmpy.BayesianNetwork
  ├─ 输入网络结构 (边的列表)
  └─ 创建有向无环图 (DAG)
  ↓
7. visualize_network() - 可视化网络结构
  ├─ 使用 networkx 绘制网络图
  ├─ 保存图片: ../bayesian_result/network_structure.png
  └─ 显示节点和边的关系
  ↓
8. estimate_parameters() - 贝叶斯参数估计 ⭐核心步骤
  ├─ 验证数据列与模型节点匹配
  ├─ 使用 BayesianEstimator 估计条件概率表 (CPD)
  ├─ 将 CPD 添加到模型
  ├─ 保存模型: ../pkl/bn_bayesian_model.pkl
  ├─ 模型预测 (在训练集上验证)
  ├─ 生成分类报告: ../bayesian_result/classification_report.txt
  └─ 绘制混淆矩阵: ../bayesian_result/confusion_matrix.png
  ↓
结束 - 输出总运行时间
```

---

## 🔍 详细步骤说明

### Step 1: 初始化
```python
bn = BayesianNetworkBayesian(data_path, rules_path)
```
- 设置分箱配置 (5个等级)
- 定义变量映射关系
- 创建必要的输出目录

### Step 2: 加载数据
```python
bn.load_data()
```
**输入**: `../dataset/data_info/training_dataset.csv`
**输出**: DataFrame (100,000 × 7)

### Step 3: 数据预处理
```python
bn.preprocess_data()
```
**关键操作**: 
- 基于标准差的分箱: `bins = [min, mean-2σ, mean-σ, mean+σ, mean+2σ, max]`
- 转换为类别变量

### Step 4-5: 规则处理
```python
bn.load_rules()
bn.process_rules()
```
**输入**: `../dataset/optimal_rules.csv`
**输出**: 网络结构边列表
```python
[
    ('voltage', '故障类型'),
    ('rpm', '故障类型'),
    ('vibration', '故障类型'),
    ('temp', '故障类型'),
    ('oil_pressure', '故障类型'),
    ('department', '故障类型')
]
```

### Step 6: 构建网络
```python
bn.build_network()
```
创建贝叶斯网络 DAG，所有特征指向故障类型

### Step 7: 可视化
```python
bn.visualize_network(save_path="../bayesian_result/network_structure.png")
```
生成网络结构图

### Step 8: 参数估计 ⭐
```python
bn.estimate_parameters()
```
**核心算法**: 贝叶斯估计
- 计算条件概率表 P(特征|故障类型)
- 使用先验分布平滑
- 保存训练好的模型

---

## 📤 输出文件

| 文件路径 | 说明 |
|---------|------|
| `../pkl/bn_bayesian_model.pkl` | 训练好的贝叶斯网络模型 |
| `../bayesian_result/network_structure.png` | 网络结构可视化图 |
| `../bayesian_result/classification_report.txt` | 分类性能报告 |
| `../bayesian_result/confusion_matrix.png` | 混淆矩阵热力图 |

---

## 🎯 关键代码片段

### 贝叶斯估计核心代码
```python
# 创建贝叶斯估计器
bayesian_estimator = BayesianEstimator(self.model, self.processed_data)

# 估计所有节点的条件概率表
cpd_list = bayesian_estimator.get_parameters()

# 将 CPD 添加到模型
self.model.add_cpds(*cpd_list)

# 预测
y_pred = self.model.predict(predict_data)[['故障类型']].values.flatten()
```

---

## ⏱️ 性能指标

- **数据加载**: ~1秒
- **数据预处理**: ~2秒
- **规则处理**: <1秒
- **网络构建**: <1秒
- **参数估计**: ~5-10秒
- **总运行时间**: ~10-15秒

---

## 🔄 与后续流程的衔接

训练完成后，使用 `predict/predict.py`:
```python
# 加载训练好的模型
model = pickle.load('bn_bayesian_model.pkl')

# 对新数据进行预测
predictions = model.predict(new_data)
```
