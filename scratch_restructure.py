import os
import glob

# 1. Update chat providers imports and remove embeddings
chat_dir = r"d:\Python\chatdoc\backend\app\providers\chat"
for filepath in glob.glob(os.path.join(chat_dir, "*.py")):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Fix imports
    content = content.replace("app.providers.base", "app.providers.chat.base")
    
    # Remove embeddings method if present
    lines = content.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if line.strip().startswith("async def embeddings("):
            skip = True
        elif skip and line.strip().startswith("def ") or line.strip().startswith("async def ") or line.strip().startswith("@"):
            skip = False
        
        if not skip:
            new_lines.append(line)
            
    with open(filepath, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))

# 2. Fix chat/registry.py by removing EMBEDDING_PROVIDER_OPTIONS
registry_path = os.path.join(chat_dir, "registry.py")
with open(registry_path, "r", encoding="utf-8") as f:
    registry_content = f.read()

import re
registry_content = re.sub(r'# Available embedding providers.*?# DEFAULT_PROVIDERS', '# DEFAULT_PROVIDERS', registry_content, flags=re.DOTALL)
registry_content = registry_content.replace('from app.providers.chat.base', 'from app.providers.chat.base')

with open(registry_path, "w", encoding="utf-8") as f:
    f.write(registry_content)

print("Restructured chat providers")
