import json

with open('gemini-conversation-1761028240941.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查找问题描述
print("=== 查找核心问题 ===\n")
problem_keywords = ['问题', '错误', '不对', '失败', '总是', '不敏感', '正常运行']

for i, msg in enumerate(data):
    if i < 300:  # 跳过早期消息
        continue
    if msg['role'] == 'user' and 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text']
        # 查找包含问题关键词的消息
        if any(kw in text for kw in problem_keywords) and len(text) > 50:
            if '单次' in text or 'page_4' in text or '预测' in text:
                print(f"=== Message {i} ===")
                print(text[:800])
                print("\n" + "="*60 + "\n")

# 查找解决方案
print("\n=== 查找解决方案 ===\n")
for i, msg in enumerate(data):
    if i < 300:
        continue
    if msg['role'] == 'model' and 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text']
        if 'bin_config' in text and '解决' in text:
            print(f"=== Model Response {i} ===")
            print(text[:800])
            print("\n" + "="*60 + "\n")
            break
