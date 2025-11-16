import os
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import json

# 基于脚本位置构建相对路径
script_dir = os.path.dirname(__file__)
datas_dir = os.path.join(script_dir, "datas")
os.makedirs(datas_dir, exist_ok=True)

# 初始化 Tkinter 文件选择器（隐藏主窗口）
root = tk.Tk()
root.withdraw()

# 打开文件选择对话框，默认目录为 datas/
csv_path = filedialog.askopenfilename(
    title="请选择一个 CSV 文件",
    initialdir=datas_dir,
    filetypes=[("CSV files", "*.csv")],
    parent=root
)

if not csv_path:
    print("未选择文件，程序退出。")
else:
    try:
        # 读取 CSV（支持中文）
        df = pd.read_csv(csv_path, encoding='utf-8')
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        exit(1)

    base_path = os.path.splitext(csv_path)[0]  # 去掉 .csv 后缀

    # 1. 保存为格式化 JSON（整个文件是一个数组）
    json_path = base_path + ".json"
    df.to_json(json_path, orient='records', indent=2, force_ascii=False)

    # 2. 保存为 TXT（JSONL：每行一个 JSON 对象）
    txt_path = base_path + ".txt"
    records = df.to_dict(orient='records')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"✅ 转换成功！\n"
          f"输入: {csv_path}\n"
          f"输出: {json_path}\n"
          f"      {txt_path}")