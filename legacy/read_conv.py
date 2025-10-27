import json
import sys

# 设置输出编码
sys.stdout.reconfigure(encoding='utf-8')

with open('gemini-conversation-1761028240941.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total messages: {len(data)}')

# 查找关键信息
user_messages = [m for m in data if m['role'] == 'user']
print(f'User messages: {len(user_messages)}')

# 搜索关键词
keywords = ['page_4', 'Page4', 'Page 4', '单次预测', '故障概率评估', 'bin_config', '分箱']
print('\n=== 搜索关键信息 ===')
for keyword in keywords:
    count = 0
    for msg in data:
        if 'text' in msg['parts'][0]:
            if keyword in msg['parts'][0]['text']:
                count += 1
    print(f'{keyword}: {count} 次提及')

# 显示最后几条用户消息
print('\n=== 最后5条用户消息 ===')
for i, msg in enumerate(user_messages[-5:]):
    if 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text'][:500]
        print(f'\n--- User message {len(user_messages)-5+i+1} ---')
        print(text)
