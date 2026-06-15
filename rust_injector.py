import sys
import re
import os

# ---------------------------------------------------------
# PART 1: ASSERTION LOGIC
# ---------------------------------------------------------
def synthesize_assertions(condition):
    cond = condition.strip()
    if cond.startswith("(") and cond.endswith(")"):
        cond = cond[1:-1]
    
    # Kani Assertions
    s1 = f'\t// KANI INJECTION: Check Reachability'
    s2 = f'\tassert!(!({cond}), "REACHABLE_TRUE");'
    s3 = f'\tassert!(({cond}), "REACHABLE_FALSE");'
    return [s1, s2, s3]

def inject_assertions(line):
    # Match if/while statements more flexibly
    pattern = r'^\s*(if|while)\s+(.+?)\s*\{' 
    match = re.search(pattern, line)
    
    injections = []
    if match:
        condition = match.group(2).strip()
        if "let " not in condition:
            injections = synthesize_assertions(condition)
    return injections

def is_smart_contract_file(content):
    return "#[smart_contract]" in content or "smart_contract_macros" in content

# ---------------------------------------------------------
# PART 2: HARNESS GENERATOR
# ---------------------------------------------------------
def find_smart_contract_impl(content):
    regex = r'#\[smart_contract\]\s*.*?\s*impl\s+([a-zA-Z0-9_]+)\s*\{'
    match = re.search(regex, content, re.DOTALL)
    
    if not match:
        print("DEBUG: No #[smart_contract] impl block found.")
        return None, None
        
    struct_name = match.group(1)
    print(f"DEBUG: Found Smart Contract Struct: {struct_name}")
    
    start_index = match.end() - 1 
    open_braces = 0
    block_content = ""
    found_start = False
    
    for i in range(start_index, len(content)):
        char = content[i]
        block_content += char
        if char == '{':
            open_braces += 1
            found_start = True
        elif char == '}':
            open_braces -= 1
        
        if found_start and open_braces == 0:
            break
            
    return struct_name, block_content

def extract_functions_from_block(block_content):
    funcs = []
    pattern = r'fn\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*(?:->.*?)?\{'
    matches = re.finditer(pattern, block_content)
    for match in matches:
        name = match.group(1)
        args = match.group(2)
        if name not in ["init", "main", "fmt", "default"]:
            funcs.append((name, args))
    return funcs

def strip_comments_and_tests(content):
    content = re.sub(r'//.*', '', content)
    content = re.sub(r'#\[cfg\(test\)\]\s*mod\s+tests\s*\{.*?\n\}', '', content, flags=re.DOTALL)
    return content

def find_matching_brace(content, open_index):
    depth = 0
    for index in range(open_index, len(content)):
        char = content[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1

def extract_custom_types(content):
    structs = {}
    enums = {}

    for match in re.finditer(r'(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', content):
        name = match.group(1)
        open_index = content.find("{", match.end() - 1)
        close_index = find_matching_brace(content, open_index)
        if close_index == -1:
            continue
        body = content[open_index + 1:close_index]
        fields = []
        for field_match in re.finditer(r'(?:pub\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([^,\n]+)', body):
            fields.append((field_match.group(1), field_match.group(2).strip()))
        if fields:
            structs[name] = fields

    for match in re.finditer(r'(?:pub\s+)?enum\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{', content):
        name = match.group(1)
        open_index = content.find("{", match.end() - 1)
        close_index = find_matching_brace(content, open_index)
        if close_index == -1:
            continue
        body = content[open_index + 1:close_index]
        variants = []
        for part in body.split(","):
            variant = part.strip()
            if not variant or "(" in variant or "{" in variant:
                continue
            variant = re.sub(r'\s*=.*', '', variant).strip()
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', variant):
                variants.append(variant)
        if variants:
            enums[name] = variants

    return structs, enums

def split_args(args_str):
    args = []
    current = []
    depth = 0

    for char in args_str:
        if char in "([<":
            depth += 1
        elif char in ")]>" and depth > 0:
            depth -= 1
        elif char == "," and depth == 0:
            arg = "".join(current).strip()
            if arg:
                args.append(arg)
            current = []
            continue
        current.append(char)

    arg = "".join(current).strip()
    if arg:
        args.append(arg)
    return args

def parse_arg(arg):
    arg = arg.strip()
    if arg in ["self", "&self", "&mut self"] or ":" not in arg:
        return None
    name, type_name = arg.split(":", 1)
    name = name.strip().replace("mut ", "")
    type_name = type_name.strip()
    return name, type_name

def extract_standalone_functions(content):
    funcs = []
    clean = strip_comments_and_tests(content)
    pattern = re.compile(r'pub\s+fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')

    for match in pattern.finditer(clean):
        prefix = clean[:match.start()]
        if prefix.count("{") != prefix.count("}"):
            continue

        name = match.group(1)
        if name in ["main", "fmt", "default"]:
            continue

        args_start = match.end()
        depth = 1
        index = args_start
        while index < len(clean) and depth > 0:
            if clean[index] == "(":
                depth += 1
            elif clean[index] == ")":
                depth -= 1
            index += 1

        if depth == 0:
            funcs.append((name, clean[args_start:index - 1].strip()))

    return funcs

def sanitize_identifier(value):
    return re.sub(r'[^A-Za-z0-9_]', '_', value)

def base_type(type_name):
    return type_name.strip().replace("mut ", "").replace("&mut ", "").replace("&", "").strip()

def is_supported_primitive(type_name):
    return base_type(type_name) in [
        "bool", "usize", "u8", "u16", "u32", "u64", "u128",
        "isize", "i8", "i16", "i32", "i64", "i128",
    ]

def value_expr(type_name, var_name, structs, enums, setup_lines):
    type_name = type_name.strip()
    normalized = base_type(type_name)

    if type_name.startswith("&mut "):
        inner = base_type(type_name)
        local_name = f"{var_name}_value"
        setup_lines.append(f"    let mut {local_name} = {value_expr(inner, local_name, structs, enums, setup_lines)};")
        return f"&mut {local_name}"

    if type_name.startswith("&[") and type_name.endswith("]"):
        inner = type_name[2:-1].strip()
        array_name = f"{var_name}_items"
        setup_lines.append(f"    let {array_name} = [")
        for _ in range(3):
            setup_lines.append(f"        {value_expr(inner, f'{var_name}_item', structs, enums, setup_lines)},")
        setup_lines.append("    ];")
        return f"&{array_name}"

    if type_name.startswith("&"):
        inner = base_type(type_name)
        local_name = f"{var_name}_value"
        setup_lines.append(f"    let {local_name} = {value_expr(inner, local_name, structs, enums, setup_lines)};")
        return f"&{local_name}"

    vec_match = re.match(r'Vec\s*<\s*(.+)\s*>', normalized)
    if vec_match:
        inner = vec_match.group(1).strip()
        return (
            f"vec![{value_expr(inner, var_name + '_0', structs, enums, setup_lines)}, "
            f"{value_expr(inner, var_name + '_1', structs, enums, setup_lines)}, "
            f"{value_expr(inner, var_name + '_2', structs, enums, setup_lines)}]"
        )

    if is_supported_primitive(normalized):
        return f"kani::any::<{normalized}>()"

    if normalized in enums:
        helper = f"kani_any_{normalized}"
        return f"{helper}()"

    if normalized in structs:
        helper = f"kani_any_{normalized}"
        return f"{helper}()"

    return None

def generate_custom_type_helpers(structs, enums):
    lines = []

    for enum_name, variants in enums.items():
        helper = f"kani_any_{enum_name}"
        lines.append("#[cfg(kani)]")
        lines.append(f"fn {helper}() -> {enum_name} {{")
        lines.append("    let choice: u8 = kani::any();")
        lines.append(f"    match choice % {len(variants)} {{")
        for index, variant in enumerate(variants[:-1]):
            lines.append(f"        {index} => {enum_name}::{variant},")
        lines.append(f"        _ => {enum_name}::{variants[-1]},")
        lines.append("    }")
        lines.append("}")
        lines.append("")

    for struct_name, fields in structs.items():
        helper = f"kani_any_{struct_name}"
        lines.append("#[cfg(kani)]")
        lines.append(f"fn {helper}() -> {struct_name} {{")
        lines.append(f"    {struct_name} {{")
        for field_name, field_type in fields:
            setup_lines = []
            expr = value_expr(field_type, field_name, structs, enums, setup_lines)
            if expr is None:
                return []
            for setup_line in setup_lines:
                lines.append(setup_line)
            lines.append(f"        {field_name}: {expr},")
        lines.append("    }")
        lines.append("}")
        lines.append("")

    return lines

def generate_standalone_harness(func_name, args_str, structs, enums):
    setup_lines = []
    call_args = []

    for index, arg in enumerate(split_args(args_str)):
        parsed = parse_arg(arg)
        if not parsed:
            continue
        name, type_name = parsed
        safe_name = sanitize_identifier(name or f"arg_{index}")
        expr = value_expr(type_name, safe_name, structs, enums, setup_lines)
        if expr is None:
            print(f"DEBUG: Skipping harness for '{func_name}' due to unsupported argument type '{type_name}'")
            return None
        call_args.append(expr)

    lines = []
    lines.append("")
    lines.append("#[cfg(kani)]")
    lines.append("#[kani::proof]")
    lines.append(f"fn kani_harness_{func_name}() {{")
    lines.extend(setup_lines)
    lines.append(f"    let _ = {func_name}({', '.join(call_args)});")
    lines.append("}")
    return "\n".join(lines)

def generate_harness(struct_name, func_name, args_str):
    lines = []
    lines.append(f"\n#[cfg(kani)]")
    lines.append(f"#[kani::proof]")
    lines.append(f"fn kani_harness_{func_name}() {{")

    # FIX: Use unsafe transmute_copy to bypass Arbitrary trait check
    # We create 256 bytes of symbolic data and cast it to Parameters.
    if "Parameters" in args_str:
        lines.append(f"    let mut params: smart_contract::payload::Parameters = unsafe {{")
        lines.append(f"        let raw_bytes: [u8; 256] = kani::any();")
        lines.append(f"        std::mem::transmute_copy(&raw_bytes)")
        lines.append(f"    }};")

    if "self" in args_str:
        lines.append(f"    let mut contract = {struct_name}::init(&mut params);")
        lines.append(f"    let _ = contract.{func_name}(&mut params);")

    lines.append("}")
    return "\n".join(lines)

def generate_all_harnesses(code_content):
    harnesses = []
    if is_smart_contract_file(code_content):
        struct_name, block_content = find_smart_contract_impl(code_content)
        if struct_name and block_content:
            funcs = extract_functions_from_block(block_content)
            for func_name, args_str in funcs:
                print(f"DEBUG: Generating harness for function '{func_name}'")
                harness = generate_harness(struct_name, func_name, args_str)
                harnesses.append(harness)
    else:
        structs, enums = extract_custom_types(code_content)
        funcs = extract_standalone_functions(code_content)
        helpers = generate_custom_type_helpers(structs, enums)
        if helpers:
            harnesses.append("\n".join(helpers))
        for func_name, args_str in funcs:
            print(f"DEBUG: Generating standalone harness for function '{func_name}'")
            harness = generate_standalone_harness(func_name, args_str, structs, enums)
            if harness:
                harnesses.append(harness)
    return harnesses

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    if len(sys.argv) < 2: return
    input_file = sys.argv[1]
    temp_file = input_file + ".temp"
    
    condition_count = 0
    full_content = ""
    
    with open(input_file, 'r') as f_in:
        lines = f_in.readlines()
        full_content = "".join(lines)
        
    with open(temp_file, 'w') as f_out:
        for line in lines:
            f_out.write(line)
            injections = inject_assertions(line)
            if injections:
                for inj in injections:
                    f_out.write(inj + "\n")
                condition_count += 1
        
        harnesses = generate_all_harnesses(full_content)
        if harnesses:
            f_out.write("\n\n// --- AUTO-GENERATED KANI HARNESSES ---\n")
            for h in harnesses:
                f_out.write(h + "\n")
                
        f_out.flush() 

    print(condition_count * 2)
    os.replace(temp_file, input_file)

if __name__ == "__main__":
    main()
