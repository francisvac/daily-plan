#!/usr/bin/env python3
"""
ZeroClaw Baby Planner - Codebase Cleanup Script
Cleans up and organizes the codebase after refactoring
"""

import os
import shutil
from pathlib import Path
from typing import List

def cleanup_codebase():
    """Clean up the codebase after refactoring"""
    
    # Files to keep (essential files)
    keep_files = {
        'config.py',
        'logger.py', 
        'base_classes.py',
        'generate-baby-plan-refactored.py',
        'email_integration_refactored.py',
        'email_command_processor_refactored.py',
        'patterns.json',
        'template.md',
        'README.md',
        'QUICKSTART.md',
        'BABY-IMPLEMENTATION-COMPLETE.md',
        'BABY-QUICKSTART.md'
    }
    
    # Files to remove (old/duplicated files)
    remove_files = {
        'generate-baby-plan.py',
        'email_integration.py',
        'email_command_processor.py',
        'email_feedback_processor.py',
        'generate-enhanced-plan.py',
        'generate-daily-plan.sh',
        'setup.sh',
        'daily-planner.sh',
        'baby-planner-remote.sh'
    }
    
    # Files to archive (old plan files and documentation)
    archive_dir = Path.home() / "daily-plans" / "archive"
    archive_files = {
        'IMPLEMENTATION-SUMMARY.md',
        '2026-03-13-plan.md',
        '2026-03-14-plan.md'
    }
    
    base_dir = Path.home() / "daily-plans"
    
    print("🧹 Cleaning up ZeroClaw Baby Planner codebase...")
    print(f"📁 Base directory: {base_dir}")
    print()
    
    # Create archive directory
    archive_dir.mkdir(exist_ok=True)
    print(f"📦 Created archive directory: {archive_dir}")
    
    # Archive old files
    archived_count = 0
    for file_name in archive_files:
        old_path = base_dir / file_name
        new_path = archive_dir / file_name
        
        if old_path.exists():
            shutil.move(str(old_path), str(new_path))
            print(f"📦 Archived: {file_name}")
            archived_count += 1
    
    if archived_count > 0:
        print(f"✅ Archived {archived_count} files")
    else:
        print("ℹ️ No files to archive")
    
    print()
    
    # Remove old files
    removed_count = 0
    for file_name in remove_files:
        file_path = base_dir / file_name
        
        if file_path.exists():
            file_path.unlink()
            print(f"🗑️ Removed: {file_name}")
            removed_count += 1
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} old files")
    else:
        print("ℹ️ No old files to remove")
    
    print()
    
    # Rename refactored files to final names
    rename_map = {
        'generate-baby-plan-refactored.py': 'generate-baby-plan.py',
        'email_integration_refactored.py': 'email_integration.py',
        'email_command_processor_refactored.py': 'email_command_processor.py'
    }
    
    renamed_count = 0
    for old_name, new_name in rename_map.items():
        old_path = base_dir / old_name
        new_path = base_dir / new_name
        
        if old_path.exists():
            if new_path.exists():
                new_path.unlink()  # Remove existing file
            shutil.move(str(old_path), str(new_path))
            print(f"🔄 Renamed: {old_name} → {new_name}")
            renamed_count += 1
    
    if renamed_count > 0:
        print(f"✅ Renamed {renamed_count} files")
    else:
        print("ℹ️ No files to rename")
    
    print()
    
    # Create directories structure
    directories = ['logs', 'templates', 'scripts']
    created_dirs = 0
    
    for dir_name in directories:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"📁 Created directory: {dir_name}")
        created_dirs += 1
    
    if created_dirs > 0:
        print(f"✅ Created {created_dirs} directories")
    
    print()
    
    # Show final file structure
    print("📋 Final file structure:")
    print("=" * 50)
    
    def print_tree(path: Path, prefix: str = "", is_last: bool = True):
        """Print directory tree"""
        if path.is_dir():
            print(f"{prefix}{'└── ' if is_last else '├── '}{path.name}/")
            
            children = sorted([p for p in path.iterdir() if not p.name.startswith('.')])
            for i, child in enumerate(children):
                is_child_last = i == len(children) - 1
                child_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(child, child_prefix, is_child_last)
        else:
            print(f"{prefix}{'└── ' if is_last else '├── '}{path.name}")
    
    # Show main directory structure
    main_items = sorted([p for p in base_dir.iterdir() 
                        if not p.name.startswith('.') and p.name != 'archive'])
    
    for i, item in enumerate(main_items):
        is_last = i == len(main_items) - 1
        print_tree(item, "", is_last)
    
    print()
    print("🎉 Codebase cleanup complete!")
    print()
    print("📊 Summary:")
    print(f"  📦 Archived: {archived_count} files")
    print(f"  🗑️ Removed: {removed_count} old files")
    print(f"  🔄 Renamed: {renamed_count} files")
    print(f"  📁 Created: {created_dirs} directories")
    print()
    print("✅ Codebase is now clean and organized!")

if __name__ == "__main__":
    cleanup_codebase()
