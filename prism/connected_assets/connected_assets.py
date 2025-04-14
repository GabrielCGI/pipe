import os
import re
import sys

def make_relative_path(payload_path, usd_file_dir):
    return payload_path
    match = re.match(r'@([^@]+)@<(.+)>', payload_path)
    if not match:
        return payload_path
    abs_path, prim_path = match.groups()
    rel_path = os.path.relpath(abs_path, start=usd_file_dir).replace('\\', '/')
    return f"@{rel_path}@<{prim_path}>"

def process_usda(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    usd_file_dir = os.path.dirname(os.path.abspath(input_file))
    new_lines = []

    for line in lines:
        payload_match = re.search(r'prepend payload\s*=\s*@[^@]+@<[^>]+>', line)
        if payload_match:
            path_match = re.search(r'@[^@]+@<[^>]+>', line)
            if path_match:
                original_path = path_match.group()
                relative_path = make_relative_path(original_path, usd_file_dir)
                line = line.replace(original_path, relative_path)
        new_lines.append(line)

    output_lines = []
    for i, line in enumerate(new_lines):
        if line.strip().startswith('def "assets"'):
            output_lines.append('def "world"\n')
            output_lines.append('{\n')
            output_lines.append(line)
        else:
            output_lines.append(line)

    if output_lines[-1].strip() == "}":
        output_lines[-1] = '    ' + output_lines[-1]
        output_lines.append('}\n')
    else:
        output_lines.append('}\n')

    with open(output_file, 'w') as f:
        f.writelines(output_lines)

    print(f"✔️ Processed USDA saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wrap_usda.py <path_to_usda>")
        sys.exit(1)

    input_usda = sys.argv[1]
    base, ext = os.path.splitext(input_usda)
    output_usda = input_usda
    process_usda(input_usda, output_usda)
