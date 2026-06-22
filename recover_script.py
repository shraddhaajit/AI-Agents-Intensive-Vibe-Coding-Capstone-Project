import json
import re

log_path = r"C:\Users\shrad\.gemini\antigravity-ide\brain\9cb70efd-c670-4030-b9a5-c09cde426bac\.system_generated\logs\transcript.jsonl"
recovered_files = {}

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except:
            continue
            
        if 'tool_calls' in obj and obj['tool_calls']:
            tool = obj['tool_calls'][0]
            name = tool.get('name') or tool.get('toolName')
            if name == 'view_file':
                try:
                    args = tool.get('tool_args') or tool.get('args', {})
                    path = args.get('AbsolutePath')
                    response = tool.get('response', {}) or {}
                    output = response.get('output', '')
                    
                    if not path or not path.endswith('.py'): continue
                    
                    cleaned_lines = []
                    lines = output.split('\n')
                    is_code = False
                    for l in lines:
                        if l.startswith('1: '): is_code = True
                        if is_code:
                            m = re.match(r'^\d+:\s?(.*)', l)
                            if m:
                                cleaned_lines.append(m.group(1))
                            elif l == "The above content shows the entire, complete file contents of the requested file.":
                                break
                    if is_code:
                        recovered_files[path] = '\n'.join(cleaned_lines)
                except Exception as e:
                    pass

for p, c in recovered_files.items():
    print(f"Recovered {p}")
    with open(p, 'w', encoding='utf-8') as out:
        out.write(c)
