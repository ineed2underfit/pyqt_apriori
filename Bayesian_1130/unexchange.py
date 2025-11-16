import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import json

# 相对路径：exchange 目录（相对于脚本所在位置）
script_dir = os.path.dirname(__file__)
exchange_dir = os.path.join(script_dir, "exchange")
os.makedirs(exchange_dir, exist_ok=True)

# 初始化文件选择器
root = tk.Tk()
root.withdraw()

# 选择 JSON 或 TXT 文件
file_path = filedialog.askopenfilename(
    title="请选择一个 JSON 或 TXT 文件（JSONL 格式）",
    initialdir=exchange_dir,
    filetypes=[("JSON or TXT files", "*.json *.txt")],
    parent=root
)

if not file_path:
    print("未选择文件，程序退出。")
    exit(0)

_, ext = os.path.splitext(file_path)
ext = ext.lower()

try:
    if ext == ".json":
        # 直接读取标准 JSON 数组
        df = pd.read_json(file_path, encoding='utf-8')
    elif ext == ".txt":
        # 逐行读取 JSONL
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        df = pd.DataFrame(records)
    else:
        raise ValueError("仅支持 .json 或 .txt 文件")

    # 输出 CSV（同名，同目录）
    csv_path = os.path.splitext(file_path)[0] + ".csv"
    df.to_csv(csv_path, index=False, encoding='utf-8')

    print(f"✅ 转换成功！\n"
          f"输入: {file_path}\n"
          f"输出: {csv_path}")

except Exception as e:
    print(f"❌ 转换失败: {e}")