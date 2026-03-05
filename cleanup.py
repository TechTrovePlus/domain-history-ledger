import os
import shutil

def main():
    base_dir = '.'
    
    scripts_dir = os.path.join(base_dir, 'scripts')
    tests_dir = os.path.join(base_dir, 'tests')
    archive_dir = os.path.join(base_dir, 'archive')
    
    # Step 1: Create folders
    for d in [scripts_dir, tests_dir, archive_dir]:
        os.makedirs(d, exist_ok=True)
        
    scripts_files = [
        'check.py',
        'check2.py',
        'check_db.py',
        'diagnostic.py',
        'phase4_e2e.py',
        'run_audit.py',
        'result_query.py',
        'wayback_audit.py',
        'wayback_audit_part2.py',
        'validate_refactor.py',
        # Additional standalone diagnostics found earlier
        'audit_urlhaus.py',
        'db_cleanup.py',
        'db_recovery_validation.py',
        'introspect.py',
        'exec_path.py'
    ]
    
    tests_files = [
        'test_dates.py',
        'test_db_read.py',
        'test_lifecycle_fusion.py',
        'test_online_offline.py',
        'test_score.py',
        'test_serialization.py',
        'test_urlhaus.py'
    ]
    
    # We also need to grab any file starting with test_
    for file in os.listdir(base_dir):
        if file.startswith('test_') and file.endswith('.py') and file not in tests_files:
            tests_files.append(file)
            
    archive_modules = [
        os.path.join('backend', 'trust', 'reason_engine.py'),
        os.path.join('backend', 'trust', 'status_engine.py'),
        os.path.join('backend', 'ingestion', 'diff_engine.py'),
        os.path.join('backend', 'blockchain', 'integrity_hash.py'),
        os.path.join('backend', 'blockchain', 'anchoring_policy.py')
    ]
    
    moved_to_scripts = []
    moved_to_tests = []
    moved_to_archive = []
    
    # Move to scripts
    for f in scripts_files:
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            shutil.move(src, os.path.join(scripts_dir, f))
            moved_to_scripts.append(f)
            
    # Move to tests
    for f in tests_files:
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            shutil.move(src, os.path.join(tests_dir, f))
            moved_to_tests.append(f)
            
    # Move to archive
    for mod in archive_modules:
        src = os.path.join(base_dir, mod)
        if os.path.exists(src):
            # preserve filename
            filename = os.path.basename(mod)
            shutil.move(src, os.path.join(archive_dir, filename))
            moved_to_archive.append(mod.replace('\\', '/'))
            
    print("=== PHASE 1 CLEANUP REPORT ===")
    print("\n[Folders Created]")
    print("/scripts")
    print("/tests")
    print("/archive")
    
    print("\n[Files Moved to /scripts]")
    for m in sorted(moved_to_scripts):
        print(f"- {m}")
        
    print("\n[Files Moved to /tests]")
    for m in sorted(moved_to_tests):
        print(f"- {m}")
        
    print("\n[Files Moved to /archive]")
    for m in sorted(moved_to_archive):
        print(f"- {m}")

if __name__ == '__main__':
    main()
