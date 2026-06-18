import os
import ast
import re

print("Deep Code Audit Report")
print("======================")

def check_file(filepath):
    if not filepath.endswith('.py'): return
    print(f"\nScanning: {filepath}")
    try:
        content = open(filepath, encoding='utf-8').read()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # Bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    print(f"  [Warning] Bare except on line {node.lineno}")
                    
            # Check for os.path.join with potentially unsafe inputs
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == 'join':
                    if isinstance(node.func.value, ast.Attribute) and node.func.value.attr == 'path':
                        print(f"  [Info] os.path.join used on line {node.lineno}. Check for path traversal vulnerabilities.")
                
                # Command execution
                if isinstance(node.func, ast.Attribute) and node.func.attr in ['system', 'popen', 'call', 'run', 'Popen']:
                    print(f"  [Warning] Subprocess/System execution on line {node.lineno}. Check for command injection.")

                if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                    print(f"  [Danger] eval/exec used on line {node.lineno}.")
                    
    except SyntaxError as e:
        print(f"  [Error] Syntax error in file: {e}")
    except Exception as e:
        pass

for root, _, files in os.walk(r'd:\code iwan\EPUB'):
    if 'venv' in root or '__pycache__' in root or '.git' in root or 'scratch' in root:
        continue
    for file in files:
        check_file(os.path.join(root, file))

print("\nScanning app.js for common issues...")
js_content = open(r'd:\code iwan\EPUB\static\app.js', encoding='utf-8').read()
if re.search(r'innerHTML\s*=', js_content):
    print("  [Warning] 'innerHTML' is used. Check for XSS vulnerabilities.")
if re.search(r'eval\(', js_content):
    print("  [Danger] 'eval' is used in JavaScript.")
