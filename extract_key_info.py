import json

with open('gemini-conversation-1761028240941.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查找包含"物件名为"的消息
print("=== 查找控件名称信息 ===\n")
for i, msg in enumerate(data):
    if msg['role'] == 'user' and 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text']
        if '物件名为' in text or 'doubleSpinBox' in text or 'comboBox' in text:
            print(f"Message {i}:")
            # 提取相关段落
            lines = text.split('\n')
            for line in lines:
                if '物件名为' in line or 'doubleSpinBox' in line or 'comboBox' in line or 'dateTimeEdit' in line:
                    print(f"  {line.strip()}")
            print()
            if i > 350:  # 只看最近的
                break

# 查找问题描述
print("\n=== 查找问题描述 ===\n")
for i, msg in enumerate(data):
    if msg['role'] == 'user' and 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text']
        if '总是' in text and ('正常运行' in text or '不敏感' in text):
            print(f"Message {i}:")
            print(text[:600])
            print()
