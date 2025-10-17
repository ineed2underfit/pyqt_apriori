import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 读取CSV文件
df = pd.read_csv("dataset/data_info/training_dataset.csv")

# 2. 筛选数值型特征列
numeric_cols = ['temp', 'vibration', 'oil_pressure', 'voltage', 'rpm']

# 3. 绘制每个数值特征的分布图
plt.figure(figsize=(15, 10))

for i, col in enumerate(numeric_cols, 1):
    plt.subplot(2, 3, i)
    sns.histplot(df[col], kde=True, bins=30, stat='density', color='skyblue')
    plt.title(f'Distribution of {col}')
    plt.xlabel('Value')
    plt.ylabel('Density')

plt.tight_layout()
plt.show()

# 4. 附加统计信息输出
print("\n数据统计描述:")
print(df[numeric_cols].describe())