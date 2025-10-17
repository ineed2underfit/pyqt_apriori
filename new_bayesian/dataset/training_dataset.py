import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建输出目录
os.makedirs('dataset/data_info', exist_ok=True)

# 基础参数设置
np.random.seed(42)
DEVICE_COUNT = 100
DEPARTMENTS = ["生产部", "研发部", "质检部", "维修部"]
FAULT_TYPES = [
    "散热系统故障",
    "润滑系统异常",
    "电力供应故障",
    "传动系统异常"
]
TOTAL_RECORDS = 100000
FAULT_RATE = 0.05
FAULT_RECORDS = int(TOTAL_RECORDS * FAULT_RATE)
NORMAL_RECORDS = TOTAL_RECORDS - FAULT_RECORDS

# 传感器物理极限（防止负数）
PHYSICAL_LIMITS = {
    'temp': (0, 100),  # 温度物理极限
    'vibration': (0, 5),  # 振动物理极限
    'oil_pressure': (0, 20),  # 油压物理极限
    'voltage': (0, 300),  # 电压物理极限
    'rpm': (0, 3500)  # 转速物理极限
}

# 传感器正常范围
NORMAL_RANGES = {
    'temp': (40, 75),  # 温度
    'vibration': (0, 2.8),  # 振动
    'voltage': (200, 240),  # 电压
    'rpm': (1600, 2400),  # 转速
    'oil_pressure': (5, 15)  # 油压
}

# 专业故障规则定义
FAULT_RULES = {
    1: {
        'type': FAULT_TYPES[0],
        'department': "生产部",
        'conditions': [
            lambda row: row['temp'] > 80,  # 过热特征
            lambda row: row['vibration'] > 3.2  # 异常振动
        ]
    },
    2: {
        'type': FAULT_TYPES[1],
        'department': "研发部",
        'conditions': [
            lambda row: row['temp'] > 75,  # 温度异常
            lambda row: row['oil_pressure'] < 4  # 油压不足
        ]
    },
    3: {
        'type': FAULT_TYPES[2],
        'department': "质检部",
        'conditions': [
            lambda row: row['voltage'] < 190,  # 电压不稳
            lambda row: row['oil_pressure'] > 16  # 油压过高
        ]
    },
    4: {
        'type': FAULT_TYPES[3],
        'department': "维修部",
        'conditions': [
            lambda row: (row['rpm'] < 1500) | (row['rpm'] > 2500),  # 转速异常
            lambda row: row['oil_pressure'] < 4  # 油压异常
        ]
    }
}


def generate_timestamps(n):
    start = datetime(2022, 1, 1)
    end = datetime(2024, 12, 31)
    return [start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
            for _ in range(n)]


def generate_sensor_data(sensor_type, fault_type=0):
    """专业传感器数据生成器（带物理极限保护）"""
    if fault_type == 0:
        # 正常数据生成
        value = np.random.uniform(*NORMAL_RANGES[sensor_type])
    else:
        # 故障数据生成
        if sensor_type == 'temp':
            value = np.random.uniform(80, 95) if fault_type in [1, 2] else np.random.uniform(40, 75)
        elif sensor_type == 'vibration':
            value = np.random.uniform(3.2, 4.0) if fault_type == 1 else np.random.uniform(0, 2.8)
        elif sensor_type == 'oil_pressure':
            if fault_type in [2, 4]:
                value = np.random.uniform(0, 4)
            elif fault_type == 3:
                value = np.random.uniform(16, 20)
            else:
                value = np.random.uniform(5, 15)
        elif sensor_type == 'voltage':
            value = np.random.uniform(180, 190) if fault_type == 3 else np.random.uniform(200, 240)
        elif sensor_type == 'rpm':
            value = np.random.uniform(2500, 3000) if fault_type == 4 else np.random.uniform(1600, 2400)

    # 添加物理极限保护
    return np.clip(value, PHYSICAL_LIMITS[sensor_type][0], PHYSICAL_LIMITS[sensor_type][1])


def add_measurement_noise(value, sensor_type):
    """添加测量噪声（带物理极限保护）"""
    noise_level = {
        'temp': 1.5,  # ±1.5℃
        'vibration': 0.15,  # ±0.15mm/s
        'oil_pressure': 0.3,  # ±0.3MPa
        'voltage': 3,  # ±3V
        'rpm': 25  # ±25RPM
    }
    noisy_value = value + np.random.normal(0, noise_level[sensor_type])
    return np.clip(noisy_value, PHYSICAL_LIMITS[sensor_type][0], PHYSICAL_LIMITS[sensor_type][1])


def generate_normal_data(n):
    """生成正常数据"""
    data = []
    for _ in range(n):
        device_id = random.randint(1, DEVICE_COUNT)
        department = random.choice(DEPARTMENTS)
        record = {
            'timestamp': generate_timestamps(1)[0],
            'device_id': f"DEV-{device_id:03d}",
            'department': department,
            'temp': add_measurement_noise(generate_sensor_data('temp'), 'temp'),
            'vibration': add_measurement_noise(generate_sensor_data('vibration'), 'vibration'),
            'oil_pressure': add_measurement_noise(generate_sensor_data('oil_pressure'), 'oil_pressure'),
            'voltage': add_measurement_noise(generate_sensor_data('voltage'), 'voltage'),
            'rpm': add_measurement_noise(generate_sensor_data('rpm'), 'rpm'),
            '故障类型': '正常运行'
        }
        data.append(record)
    return data


def generate_fault_data(n):
    """生成故障数据"""
    fault_counts = {name: 0 for name in FAULT_TYPES}
    data = []

    while len(data) < n:
        fault_code = random.choice(list(FAULT_RULES.keys()))
        rule = FAULT_RULES[fault_code]

        # 生成符合故障特征的数据
        record = {
            'timestamp': generate_timestamps(1)[0],
            'device_id': f"DEV-{random.randint(1, DEVICE_COUNT):03d}",
            'department': rule['department'],
            'temp': add_measurement_noise(generate_sensor_data('temp', fault_code), 'temp'),
            'vibration': add_measurement_noise(generate_sensor_data('vibration', fault_code), 'vibration'),
            'oil_pressure': add_measurement_noise(generate_sensor_data('oil_pressure', fault_code), 'oil_pressure'),
            'voltage': add_measurement_noise(generate_sensor_data('voltage', fault_code), 'voltage'),
            'rpm': add_measurement_noise(generate_sensor_data('rpm', fault_code), 'rpm'),
            '故障类型': rule['type']
        }

        # 验证故障条件
        if all(condition(record) for condition in rule['conditions']):
            data.append(record)
            fault_counts[rule['type']] += 1

    return data, fault_counts


# 生成数据集
normal_data = generate_normal_data(NORMAL_RECORDS)
fault_data, fault_counts = generate_fault_data(FAULT_RECORDS)

# 合并并打乱数据
dataset = pd.DataFrame(normal_data + fault_data)
dataset = dataset.sample(frac=1, random_state=42).reset_index(drop=True)

# 验证数据范围
for col in ['vibration', 'oil_pressure']:
    assert dataset[col].ge(0).all(), f"{col}存在负数"

# 生成统计报告
fault_dist = dataset['故障类型'].value_counts()
print("=" * 40)
print(f"总记录数: {len(dataset)} | 正常记录: {NORMAL_RECORDS} | 故障记录: {FAULT_RECORDS}")
print("-" * 40)
for fault, count in fault_counts.items():
    print(f"{fault:10s}: {count} 条 ({count / FAULT_RECORDS * 100:.1f}%)")

# 保存数据
dataset.to_csv('dataset/data_info/training_dataset.csv', index=False)

# 生成可视化
plt.figure(figsize=(12, 6))
fault_dist.plot(kind='bar', color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
plt.title('设备故障类型分布分析', fontsize=14)
plt.xlabel('故障类型', fontsize=12)
plt.ylabel('记录数量', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('dataset/data_info/故障分布柱状图.png')
plt.show()