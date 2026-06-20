# clean_docs module
import os
import re

DESCRIPTIONS = {
    "main.py": "FastAPI application entry point",
    "__init__.py": "Package init",
    "health.py": "Health check endpoint",
    "version.py": "Version info endpoint",
    "exceptions.py": "Exception handlers",
    "logging.py": "Logging configuration",
    "lifespan.py": "Application lifespan",
    "cors.py": "CORS middleware",
    "loader.py": "Environment loader",
    "manager.py": "Configuration manager",
    "settings.py": "Application settings",
    "container.py": "Dependency injection container",
    "common.py": "Shared configuration types",
    "conftest.py": "Pytest configuration",
}


def get_description(filepath):
    filename = os.path.basename(filepath)
    dir_name = os.path.dirname(filepath)
    
    if filename in DESCRIPTIONS:
        return DESCRIPTIONS[filename]
    
    name = filename.replace('.py', '')
    if "config/sections" in dir_name:
        return f"{name} settings"
    elif "config" in dir_name:
        return f"{name} configuration"
    elif "core" in dir_name:
        return f"{name} core"
    elif "api" in dir_name:
        return f"{name} API"
    elif "middleware" in dir_name:
        return f"{name} middleware"
    elif "dependencies" in dir_name:
        return f"{name} dependencies"
    elif "schemas" in dir_name:
        return f"{name} schemas"
    elif "services" in dir_name:
        return f"{name} services"
    elif "repositories" in dir_name:
        return f"{name} repositories"
    elif "models" in dir_name:
        return f"{name} models"
    elif "tests" in dir_name:
        return f"{name} tests"
    elif "platform" in dir_name:
        return f"{name} platform"
    elif "plugins" in dir_name:
        return f"{name} plugins"
    else:
        return f"{name} module"


def remove_docstrings_and_comments(content):
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped == '' and not result:
            i += 1
            continue
        
        if stripped.startswith('#'):
            i += 1
            continue
        
        if not result and (stripped.startswith('"""') or stripped.startswith("'''")):
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                i += 1
            else:
                i += 1
                while i < len(lines) and '"""' not in lines[i] and "'''" not in lines[i]:
                    i += 1
                if i < len(lines):
                    i += 1
            continue
        
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                i += 1
            else:
                i += 1
                while i < len(lines) and '"""' not in lines[i] and "'''" not in lines[i]:
                    i += 1
                if i < len(lines):
                    i += 1
            continue
        
        code_part = line
        if '#' in line:
            in_string = False
            string_char = None
            for j, char in enumerate(line):
                if char in ('"', "'") and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                elif char == '#' and not in_string:
                    code_part = line[:j].rstrip()
                    break
        result.append(code_part)
        i += 1
    
    while result and result[-1].strip() == '':
        result.pop()
    
    return '\n'.join(result)


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned = remove_docstrings_and_comments(content)
    
    desc = get_description(filepath)
    
    final_content = f"# {desc}\n" + cleaned
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Processed: {filepath}")


def main():
    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                process_file(filepath)


if __name__ == '__main__':
    main()