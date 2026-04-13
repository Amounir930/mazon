# Extract actual conversation from chat JSONL - Full extraction
import json

input_file = r"C:\Users\Dell\.qwen\projects\c--users-dell-desktop-learn-amazon\chats\d720819f-9c31-46a1-88c3-0d6315912866.jsonl"
output_file = r"c:\Users\Dell\Desktop\learn\amazon\chat_clean.txt"

messages = []

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
        except:
            continue
        
        entry_type = entry.get('type', '')
        
        # Assistant messages (text only, no thoughts/tool calls)
        if entry_type == 'assistant':
            parts = entry.get('message', {}).get('parts', [])
            text = ''
            for part in parts:
                if isinstance(part, dict):
                    # Get text that's NOT a thought
                    if 'text' in part and not part.get('thought', False):
                        text += part.get('text', '')
            if text:
                timestamp = entry.get('timestamp', '')
                messages.append(f"\n{'='*80}")
                messages.append(f"🤖 ASSISTANT [{timestamp}]")
                messages.append(f"{'='*80}")
                messages.append(text)

print(f"\nExtracted {len([m for m in messages if 'ASSISTANT' in m])} messages")

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(messages))

print(f"Saved to: {output_file}")
