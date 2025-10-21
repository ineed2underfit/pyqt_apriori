import json

with open('gemini-conversation-1761028240941.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total messages: {len(data)}')
print('\nLast 5 exchanges:')

# Get last 10 messages (5 exchanges)
for i, msg in enumerate(data[-10:]):
    role = msg['role']
    if 'text' in msg['parts'][0]:
        text = msg['parts'][0]['text'][:800] if len(msg['parts'][0]['text']) > 800 else msg['parts'][0]['text']
    else:
        text = str(msg['parts'][0])[:800]
    print(f'\n{"="*60}')
    print(f'{role.upper()} (message {len(data)-10+i+1}/{len(data)}):')
    print(f'{"="*60}')
    print(text)
