# Clean JSONL - remove execute-output and telemetry garbage
import json
import sys

input_file = r"C:\Users\Dell\.qwen\projects\c--users-dell-desktop-learn-amazon\chats\d720819f-9c31-46a1-88c3-0d6315912866.jsonl"
backup_file = r"C:\Users\Dell\.qwen\projects\c--users-dell-desktop-learn-amazon\chats\d720819f-9c31-46a1-88c3-0d6315912866.jsonl.bak"
output_file = r"C:\Users\Dell\.qwen\projects\c--users-dell-desktop-learn-amazon\chats\d720819f-9c31-46a1-88c3-0d6315912866_clean.jsonl"

# Backup first
import shutil
shutil.copy(input_file, backup_file)
print(f"Backup created: {backup_file}")

# Read and filter
original_count = 0
kept_count = 0
removed_types = {}

with open(output_file, 'w', encoding='utf-8') as out:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            original_count += 1
            
            try:
                entry = json.loads(line)
            except:
                continue
            
            entry_type = entry.get('type', '')
            subtype = entry.get('subtype', '')
            
            # KEEP: assistant messages (actual responses)
            # KEEP: user messages (actual questions)
            # REMOVE: system/telemetry/tool_result/execute-output
            
            if entry_type == 'assistant':
                # Keep only if it has actual text content
                parts = entry.get('message', {}).get('parts', [])
                has_text = any(
                    isinstance(p, dict) and 'text' in p 
                    for p in parts
                )
                if has_text:
                    out.write(line + '\n')
                    kept_count += 1
                else:
                    removed_types['assistant (no text)'] = removed_types.get('assistant (no text)', 0) + 1
            elif entry_type == 'user':
                # Keep user text messages
                parts = entry.get('message', {}).get('parts', [])
                has_text = any(
                    isinstance(p, dict) and 'text' in p 
                    for p in parts
                )
                if has_text:
                    out.write(line + '\n')
                    kept_count += 1
                else:
                    removed_types['user (no text)'] = removed_types.get('user (no text)', 0) + 1
            else:
                # Remove system/telemetry/tool_result
                key = f"{entry_type}/{subtype or 'no-subtype'}"
                removed_types[key] = removed_types.get(key, 0) + 1

print(f"\nOriginal entries: {original_count}")
print(f"Kept entries: {kept_count}")
print(f"Removed entries: {original_count - kept_count}")
print(f"\nRemoved breakdown:")
for k, v in sorted(removed_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"\nClean file saved to: {output_file}")
