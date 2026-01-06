import csv
import random
import time
from datetime import datetime, timedelta

# --- 配置参数 ---
total_rows = 300  # 总数据条数
start_time = datetime(2024, 1, 1, 8, 0)  # 起始时间
time_interval = timedelta(minutes=10)  # 时间间隔
normal_ratio = 0.65  # 正常状态比例

# 机械状态列表 (1 正常 + 29 故障)
status_list = [
    "正常",
    "+24V最大电流超标故障", "-24V最大电流超标故障",
    "+24V稳定电流超标故障", "-24V稳定电流超标故障", "+9V稳定电流超标故障",
    "电路断开频率过低故障", "电路断开频率过高故障", "电路断开时间超标故障",
    "指令判断时间过短故障", "指令判断时间过长故障",
    "第一脉冲时间过短故障", "第一脉冲时间过长故障",
    "第二脉冲时间过短故障", "第二脉冲时间过长故障",
    "第三脉冲时间过短故障", "第三脉冲时间过长故障",
    "光电频率过低故障", "光电频率过高故障",
    "系统识别电压过低故障", "系统识别电压过高故障",
    "模式1电平过低故障", "模式1电平过高故障",
    "模式2电平过低故障", "模式2电平过高故障",
    "模式1脉宽过短故障", "模式1脉宽过长故障",
    "模式2脉宽过短故障", "模式2脉宽过长故障"
]

# 定义各字段的正常范围和故障范围
# 格式: (正常最小值, 正常最大值, (故障最小值, 故障最大值))
ranges = {
    '+24V_max_current': (2.0, 2.9, (3.1, 4.0)),
    '-24V_max_current': (2.0, 2.9, (3.1, 4.0)),
    '+24V_working_current': (200, 290, (310, 400)),
    '-24V_working_current': (200, 290, (310, 400)),
    '+9V_working_current': (70, 99, (101, 150)),
    'circuit_disconnect_freq': (100, 130, ((80, 99), (131, 150))), # 两个故障范围
    'circuit_disconnect_time': (3.0, 5.5, (5.7, 7.0)),
    'command_judge_time': (0.70, 0.80, ((0.60, 0.69), (0.81, 0.90))),
    'first_pulse_time': (0.82, 0.88, ((0.79, 0.81), (0.89, 0.92))),
    'second_pulse_time': (0.52, 0.58, ((0.49, 0.51), (0.59, 0.62))),
    'third_pulse_time': (0.52, 0.58, ((0.49, 0.51), (0.59, 0.62))),
    'photoelectric_freq': (1.0, 3.0, ((0.1, 0.9), (3.1, 4.0))),
    'system_recognition': (11.9, 12.1, ((11.5, 11.8), (12.2, 12.5))),
    'mode1_level': (4.5, 5.5, ((3.8, 4.4), (5.6, 6.3))),
    'mode2_level': (-5.5, -4.5, ((-6.3, -5.6), (-4.4, -3.8))),
    'mode1_pulse_width': (32.95, 33.05, ((32.85, 32.94), (33.06, 33.15))),
    'mode2_pulse_width': (34.95, 35.05, ((34.85, 34.94), (35.06, 35.15))),
}

# --- 数据生成逻辑 ---

def generate_normal_value(field_name):
    """生成一个字段的正常值"""
    min_val, max_val, _ = ranges[field_name]
    if isinstance(min_val, int):
        return random.randint(min_val, max_val)
    else:
        # 保留一位或两位小数
        if field_name in ['command_judge_time', 'first_pulse_time', 'second_pulse_time', 'third_pulse_time', 'mode1_pulse_width', 'mode2_pulse_width']:
            return round(random.uniform(min_val, max_val), 2)
        else:
            return round(random.uniform(min_val, max_val), 1)

def generate_faulty_value(field_name, status):
    """根据故障状态生成一个字段的故障值"""
    _, _, fault_ranges = ranges[field_name]

    # 对于有两个故障范围的字段，根据状态选择
    if isinstance(fault_ranges, tuple) and len(fault_ranges) == 2 and isinstance(fault_ranges[0], tuple):
        if "过低" in status or "过短" in status:
            fault_min, fault_max = fault_ranges[0]
        elif "过高" in status or "过长" in status:
            fault_min, fault_max = fault_ranges[1]
        else:
            # 默认选择第一个范围
            fault_min, fault_max = fault_ranges[0]
    else:
        fault_min, fault_max = fault_ranges

    if isinstance(fault_min, int):
        return random.randint(fault_min, fault_max)
    else:
        if field_name in ['command_judge_time', 'first_pulse_time', 'second_pulse_time', 'third_pulse_time', 'mode1_pulse_width', 'mode2_pulse_width']:
            return round(random.uniform(fault_min, fault_max), 2)
        else:
            return round(random.uniform(fault_min, fault_max), 1)

def get_field_name_from_status(status):
    """根据状态名称推断对应的字段名"""
    status_to_field = {
        "+24V最大电流超标故障": "+24V_max_current",
        "-24V最大电流超标故障": "-24V_max_current",
        "+24V稳定电流超标故障": "+24V_working_current",
        "-24V稳定电流超标故障": "-24V_working_current",
        "+9V稳定电流超标故障": "+9V_working_current",
        "电路断开频率过低故障": "circuit_disconnect_freq",
        "电路断开频率过高故障": "circuit_disconnect_freq",
        "电路断开时间超标故障": "circuit_disconnect_time",
        "指令判断时间过短故障": "command_judge_time",
        "指令判断时间过长故障": "command_judge_time",
        "第一脉冲时间过短故障": "first_pulse_time",
        "第一脉冲时间过长故障": "first_pulse_time",
        "第二脉冲时间过短故障": "second_pulse_time",
        "第二脉冲时间过长故障": "second_pulse_time",
        "第三脉冲时间过短故障": "third_pulse_time",
        "第三脉冲时间过长故障": "third_pulse_time",
        "光电频率过低故障": "photoelectric_freq",
        "光电频率过高故障": "photoelectric_freq",
        "系统识别电压过低故障": "system_recognition",
        "系统识别电压过高故障": "system_recognition",
        "模式1电平过低故障": "mode1_level",
        "模式1电平过高故障": "mode1_level",
        "模式2电平过低故障": "mode2_level",
        "模式2电平过高故障": "mode2_level",
        "模式1脉宽过短故障": "mode1_pulse_width",
        "模式1脉宽过长故障": "mode1_pulse_width",
        "模式2脉宽过短故障": "mode2_pulse_width",
        "模式2脉宽过长故障": "mode2_pulse_width",
    }
    return status_to_field.get(status, None)

# --- 主程序 ---
def main():
    output_filename = "device_OW24_testdata.csv"
    
    # 准备状态列表
    status_distribution = []
    normal_count = int(total_rows * normal_ratio)
    fault_count = total_rows - normal_count
    
    status_distribution.extend(["正常"] * normal_count)
    
    # 均匀分配故障类型
    faults_per_type = fault_count // (len(status_list) - 1)
    remaining_faults = fault_count % (len(status_list) - 1)
    
    for status in status_list[1:]: # 跳过 "正常"
        status_distribution.extend([status] * faults_per_type)
    
    # 处理剩余的故障
    for i in range(remaining_faults):
        status_distribution.append(status_list[i + 1])
        
    # 打乱状态列表
    random.shuffle(status_distribution)

    print(f"开始生成 {total_rows} 条数据...")
    
    with open(output_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        # 定义CSV头部
        fieldnames = ['id', 'record_time', 'status'] + list(ranges.keys())
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for i in range(total_rows):
            row_id = i + 1
            current_time = start_time + i * time_interval
            current_status = status_distribution[i]
            
            # 创建一行数据
            row_data = {
                'id': row_id,
                'record_time': current_time.strftime("%Y-%m-%d %H:%M"),
                'status': current_status
            }
            
            # 生成所有字段的数值
            if current_status == "正常":
                for field in ranges.keys():
                    row_data[field] = generate_normal_value(field)
            else:
                # 故障状态：找到对应的故障字段
                faulty_field = get_field_name_from_status(current_status)
                for field in ranges.keys():
                    if field == faulty_field:
                        row_data[field] = generate_faulty_value(field, current_status)
                    else:
                        row_data[field] = generate_normal_value(field)
            
            writer.writerow(row_data)
            
            # 打印进度
            if (i + 1) % 500 == 0:
                print(f"已生成 {i + 1} 条数据...")

    print(f"\n数据生成完成！文件已保存为: {output_filename}")

if __name__ == "__main__":
    main()