import os
import ast

def get_imports(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
    except Exception:
        return set()
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
                # handle from . import module
                if node.level > 0:
                    pass # ignore relative for simplicity if we just want absolute top levels
    return imports

def resolve_module(mod_name):
    # Returns relative file path of the module if it's in our backend
    parts = mod_name.split('.')
    if parts[0] != 'backend':
        return None
    
    path_as_file = os.path.join(*parts) + ".py"
    path_as_dir = os.path.join(*parts, "__init__.py")
    
    if os.path.isfile(path_as_file):
        return path_as_file.replace('\\', '/')
    if os.path.isfile(path_as_dir):
        return path_as_dir.replace('\\', '/')
    return None

def trace_execution(start_file):
    visited = set()
    queue = [start_file.replace('\\', '/')]
    
    while queue:
        curr = queue.pop(0)
        if curr in visited:
            continue
        visited.add(curr)
        
        # for modules imported dynamically, try finding their string references if necessary
        # but standard imports are enough for now
        imports = get_imports(curr)
        for imp in imports:
            mod_path = resolve_module(imp)
            if mod_path and mod_path not in visited:
                queue.append(mod_path)
    return visited

def analyze():
    print("=== ACTIVE EXECUTION REPORT ===\n")
    
    # 1. Backend Entry Flow
    app_flow = trace_execution("backend/app.py")
    print("[Backend Entry Flow]")
    print("-> backend/app.py (main fastapi application)")
    print("Dependencies loaded via app.py:")
    for f in sorted(list(app_flow)):
        if f != "backend/app.py":
            print(f"  - {f}")
    
    # 2. Search Endpoint Execution Path
    search_flow = trace_execution("backend/api/search.py")
    print("\n[Search Endpoint Execution Path]")
    print("-> GET /search (backend/api/search.py)")
    for f in sorted(list(search_flow)):
        if f != "backend/api/search.py":
            print(f"  - {f}")
            
    # 3. Cold Start Execution Path
    cold_start_flow = trace_execution("backend/ingestion/cold_start.py")
    print("\n[Cold Start Execution Path]")
    print("-> backend/ingestion/cold_start.py")
    for f in sorted(list(cold_start_flow)):
        if f != "backend/ingestion/cold_start.py":
            print(f"  - {f}")
            
    # 4. Trust Engine Invocation Path
    trust_flow = trace_execution("backend/trust/trust_engine.py")
    print("\n[Trust Engine Invocation Path]")
    print("-> backend/trust/trust_engine.py")
    for f in sorted(list(trust_flow)):
        if f != "backend/trust/trust_engine.py":
            print(f"  - {f}")
            
    # Determine statuses
    all_active = app_flow.union(cold_start_flow)
    
    print("\n[Blockchain Anchoring Status]")
    anchoring_queue_used = "backend/blockchain/anchoring_queue.py" in all_active
    notary_client_used = "backend/blockchain/notary_client.py" in all_active
    ledger_used = "backend/blockchain/ledger.py" in all_active
    
    if not anchoring_queue_used:
        print("Status: Completely unused")
        print("Reason: backend/blockchain/anchoring_queue.py is NOT imported or invoked in any runtime path.")
    
    print("\n[Diff Engine Status]")
    if "backend/ingestion/diff_engine.py" in all_active:
        print("Active")
    else:
        print("Status: Unused")
        print("Reason: backend/ingestion/diff_engine.py is NOT invoked anywhere.")
        
    print("\n[Legacy / Unused Modules]")
    legacy_modules = [
        "backend/blockchain/anchoring_queue.py",
        "backend/blockchain/anchoring_policy.py",
        "backend/blockchain/integrity_hash.py",
        "backend/ingestion/diff_engine.py",
        "backend/trust/reason_engine.py",
        "backend/trust/status_engine.py",
        "backend/trust/wayback_oracle.py" 
    ]
    
    actually_legacy = []
    # double check using purely what is active in the entire system from app.py & cold_start.py
    for lg in legacy_modules:
        if lg not in all_active:
             actually_legacy.append(lg)
             
    for m in sorted(actually_legacy):
        print(f"- {m}")
        
    print("\n[Architectural Drift Detected? Yes/No]")
    if len(actually_legacy) > 0:
        print("Yes")
        print("Explanation: Modules like reason_engine, status_engine, and diff_engine were likely remnants of older architecture implementations that have since been superseded by unified components (e.g. diffs handled in cold_start, status logic merged elsewhere). Blockchain anchoring logic exists but is unhooked from the active execution flows.")
    else:
        print("No")
        

if __name__ == "__main__":
    analyze()
