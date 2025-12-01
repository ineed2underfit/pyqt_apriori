import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random


def generate_multi_device_data(device_model, device_units, department_pool, sensors_config, faults_config,
                               total_points=100):
    """
    生成多设备多部门的数据
    :param device_model: 设备型号
    :param device_units: 设备个体列表
    :param department_pool: 部门池，设备从中分配部门
    :param sensors_config: 传感器配置
    :param faults_config: 故障配置
    :param total_points: 总数据点数
    :return: DataFrame
    """
    # 为每个设备分配部门
    device_departments = {}
    for unit in device_units:
        device_departments[unit] = random.choice(department_pool)

    # 计算每个设备的数据点数（大致平均分配）
    points_per_device = total_points // len(device_units)
    remaining_points = total_points % len(device_units)

    all_data = []

    for i, unit in enumerate(device_units):
        # 分配数据点数（处理不能整除的情况）
        unit_points = points_per_device + (1 if i < remaining_points else 0)

        # 生成时间序列（每个设备的时间独立）
        start_time = datetime(2023, 1, 1, 0, 0, 0) + timedelta(days=random.randint(0, 30))
        times = [start_time + timedelta(hours=j) for j in range(unit_points)]

        # 初始化数据字典
        data = {
            'department': [device_departments[unit]] * unit_points,
            '设备型号': [device_model] * unit_points,
            '设备名称': [unit] * unit_points,
            'time': times
        }

        # 添加传感器列
        for sensor in sensors_config['sensors']:
            data[sensor] = np.zeros(unit_points)

        data['status'] = ['正常'] * unit_points

        # 生成正常数据
        for j in range(unit_points):
            for sensor in sensors_config['sensors']:
                low, high = sensors_config['normal_ranges'][sensor]
                # 添加小幅随机波动，使每个设备的数据略有不同
                fluctuation = random.uniform(-0.05, 0.05) * (high - low)
                base_value = random.uniform(low, high)
                data[sensor][j] = max(0, base_value + fluctuation)  # 确保非负

        # 插入故障事件
        fault_percentage = 0.12  # 12%故障数据
        num_faults = int(unit_points * fault_percentage)
        fault_types = list(faults_config.keys())
        fault_duration_min = 3
        fault_duration_max = 8

        j = 0
        faults_inserted = 0
        while j < unit_points - fault_duration_max and faults_inserted < num_faults:
            if np.random.random() < fault_percentage:  # 决定是否插入故障
                fault_type = np.random.choice(fault_types)
                duration = np.random.randint(fault_duration_min, fault_duration_max + 1)
                if j + duration >= unit_points:
                    break

                # 应用故障
                for k in range(j, j + duration):
                    data['status'][k] = fault_type
                    # 根据故障类型调整传感器值
                    for sensor, adjustment in faults_config[fault_type].items():
                        if isinstance(adjustment, tuple):  # 如果是范围
                            min_val, max_val = adjustment
                            data[sensor][k] = random.uniform(min_val, max_val)
                        elif adjustment == 'low':
                            data[sensor][k] = random.uniform(0, sensors_config['normal_ranges'][sensor][0] * 0.6)
                        elif adjustment == 'high':
                            data[sensor][k] = random.uniform(
                                sensors_config['normal_ranges'][sensor][1] * 1.2,
                                sensors_config['normal_ranges'][sensor][1] * 1.8
                            )
                        elif adjustment == 'zero':
                            data[sensor][k] = 0
                        elif adjustment == 'slightly_low':
                            data[sensor][k] = random.uniform(
                                sensors_config['normal_ranges'][sensor][0] * 0.7,
                                sensors_config['normal_ranges'][sensor][0] * 0.9
                            )
                        elif adjustment == 'slightly_high':
                            data[sensor][k] = random.uniform(
                                sensors_config['normal_ranges'][sensor][1] * 1.05,
                                sensors_config['normal_ranges'][sensor][1] * 1.15
                            )
                        elif adjustment == 'very_high':
                            data[sensor][k] = random.uniform(
                                sensors_config['normal_ranges'][sensor][1] * 1.5,
                                sensors_config['normal_ranges'][sensor][1] * 2.5
                            )
                        elif adjustment == 'unstable':
                            # 不稳定的波动
                            base = sensors_config['normal_ranges'][sensor][0] + \
                                   (sensors_config['normal_ranges'][sensor][1] -
                                    sensors_config['normal_ranges'][sensor][0]) * 0.5
                            data[sensor][k] = base + random.uniform(-0.3, 0.3) * base

                j += duration
                faults_inserted += 1
            else:
                j += 1

        # 转换为DataFrame并添加到总数据
        df_unit = pd.DataFrame(data)
        all_data.append(df_unit)

    # 合并所有设备的数据
    result_df = pd.concat(all_data, ignore_index=True)

    # 按时间排序
    result_df = result_df.sort_values('time').reset_index(drop=True)

    return result_df


# 设备1: HP-30 配置 (液压系统)
hp30_units = ['HP-30-001', 'HP-30-002', 'HP-30-003', 'HP-30-004']
hp30_departments = ['液压部A', '液压部B', '生产部A', '维修部C']
sensors_config_hp30 = {
    'sensors': ['液压压力', '流量', '油温', '振动频率', '油液清洁度'],
    'normal_ranges': {
        '液压压力': (100, 200),  # bar
        '流量': (50, 150),  # L/min
        '油温': (30, 70),  # °C
        '振动频率': (5, 25),  # Hz
        '油液清洁度': (80, 100)  # %
    }
}
faults_config_hp30 = {
    '液压泄漏': {'液压压力': 'low', '流量': 'high'},
    '泵磨损': {'液压压力': 'unstable', '振动频率': 'high'},
    '油温过高': {'油温': 'high', '油液清洁度': 'low'},
    '阀门故障': {'液压压力': (50, 80), '流量': (20, 40)},
    '污染故障': {'油液清洁度': (10, 40), '油温': 'slightly_high'}
}

# 设备2: VA-25 配置 (振动分析系统)
va25_units = ['VA-25-001', 'VA-25-002', 'VA-25-003', 'VA-25-004', 'VA-25-005']
va25_departments = ['振动分析部', '设备监测部', '维修部A', '生产部B', '研发部']
sensors_config_va25 = {
    'sensors': ['振动频率', '振幅', '相位角', '温度', '转速'],
    'normal_ranges': {
        '振动频率': (10, 50),  # Hz
        '振幅': (0.1, 2.0),  # mm
        '相位角': (0, 360),  # 度
        '温度': (20, 60),  # °C
        '转速': (800, 1800)  # RPM
    }
}
faults_config_va25 = {
    '轴承故障': {'振动频率': 'high', '振幅': 'high', '温度': 'slightly_high'},
    '不平衡': {'振幅': 'high', '相位角': 'unstable'},
    '不对中': {'振动频率': (60, 100), '相位角': (100, 150)},
    '松动': {'振幅': 'very_high', '振动频率': 'unstable'},
    '共振': {'振动频率': (80, 120), '振幅': 'very_high'}
}

# 设备3: PA-40 配置 (气压系统)
pa40_units = ['PA-40-001', 'PA-40-002', 'PA-40-003', 'PA-40-004', 'PA-40-005', 'PA-40-006']
pa40_departments = ['气压部A', '气压部B', '生产部C', '维修部D', '装配部', '测试部']
sensors_config_pa40 = {
    'sensors': ['气压', '流量', '温度', '湿度', '露点'],
    'normal_ranges': {
        '气压': (5, 10),  # bar
        '流量': (100, 300),  # L/min
        '温度': (15, 35),  # °C
        '湿度': (30, 60),  # %
        '露点': (5, 15)  # °C
    }
}
faults_config_pa40 = {
    '泄漏故障': {'气压': 'low', '流量': 'high'},
    '过滤器堵塞': {'气压': 'slightly_low', '流量': 'low'},
    '干燥器故障': {'湿度': 'high', '露点': 'high'},
    '冷凝故障': {'湿度': 'very_high', '温度': 'low'},
    '压力调节故障': {'气压': 'unstable', '流量': 'unstable'}
}

# 生成三个数据集
df_hp30 = generate_multi_device_data('HP-30', hp30_units, hp30_departments, sensors_config_hp30, faults_config_hp30)
df_va25 = generate_multi_device_data('VA-25', va25_units, va25_departments, sensors_config_va25, faults_config_va25)
df_pa40 = generate_multi_device_data('PA-40', pa40_units, pa40_departments, sensors_config_pa40, faults_config_pa40)

# 保存为CSV文件
df_hp30.to_csv('device_HP30_testdata.csv', index=False)
df_va25.to_csv('device_VA25_testdata.csv', index=False)
df_pa40.to_csv('device_PA40_testdata.csv', index=False)

# 显示每个数据集的基本信息
print("HP-30数据集信息 (液压系统):")
print(f"总数据量: {len(df_hp30)}")
print(f"设备数量: {df_hp30['设备名称'].nunique()}")
print(f"部门数量: {df_hp30['department'].nunique()}")
print("设备分布:")
print(df_hp30['设备名称'].value_counts())
print("部门分布:")
print(df_hp30['department'].value_counts())
print("故障类型分布:")
print(df_hp30['status'].value_counts())
print("\n" + "=" * 60)

print("VA-25数据集信息 (振动分析系统):")
print(f"总数据量: {len(df_va25)}")
print(f"设备数量: {df_va25['设备名称'].nunique()}")
print(f"部门数量: {df_va25['department'].nunique()}")
print("设备分布:")
print(df_va25['设备名称'].value_counts())
print("部门分布:")
print(df_va25['department'].value_counts())
print("故障类型分布:")
print(df_va25['status'].value_counts())
print("\n" + "=" * 60)

print("PA-40数据集信息 (气压系统):")
print(f"总数据量: {len(df_pa40)}")
print(f"设备数量: {df_pa40['设备名称'].nunique()}")
print(f"部门数量: {df_pa40['department'].nunique()}")
print("设备分布:")
print(df_pa40['设备名称'].value_counts())
print("部门分布:")
print(df_pa40['department'].value_counts())
print("故障类型分布:")
print(df_pa40['status'].value_counts())

# 显示每个数据集的前几行数据作为示例
print("\nHP-30数据集示例 (前10行):")
print(df_hp30.head(10).to_string(index=False))

print("\nVA-25数据集示例 (前10行):")
print(df_va25.head(10).to_string(index=False))

print("\nPA-40数据集示例 (前10行):")
print(df_pa40.head(10).to_string(index=False))