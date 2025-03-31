#!/usr/bin/env python3
"""
System Cleanup & Performance Booster Script
-------------------------------------------
This script automates system cleanup by removing temporary files,
cache, and logs, while monitoring disk space and optimizing system performance.
"""

import os
import sys
import shutil
import subprocess
import logging
import argparse
import time
import psutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_cleanup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default locations for cleanup
DEFAULT_CLEANUP_PATHS = {
    "temp_files": [
        "/tmp",
        "/var/tmp",
        os.path.expanduser("~/.cache"),
        os.path.expanduser("~/Downloads"),
    ],
    "log_files": [
        "/var/log",
    ],
    "cache_files": [
        os.path.expanduser("~/.cache/thumbnails"),
        os.path.expanduser("~/.cache/mozilla"),
        os.path.expanduser("~/.cache/google-chrome"),
    ]
}

# File extensions to target for cleanup
TARGET_EXTENSIONS = {
    "temp": [".tmp", ".temp", ".swp", ".bak", ".old"],
    "logs": [".log", ".log.1", ".log.gz"],
    "cache": [".cache"]
}

# Disk space threshold (in percentage)
DISK_THRESHOLD = 80


def get_size(path):
    """Calculate the total size of a directory or file."""
    total_size = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp) and not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    pass
    return total_size


def format_size(size_bytes):
    """Format size in bytes to a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"


def check_disk_space():
    """Monitor disk space and return True if above threshold."""
    disk_usage = psutil.disk_usage('/')
    percent_used = disk_usage.percent
    
    logger.info(f"Current disk usage: {percent_used:.2f}%")
    logger.info(f"Total: {format_size(disk_usage.total)}, Used: {format_size(disk_usage.used)}, Free: {format_size(disk_usage.free)}")
    
    return percent_used > DISK_THRESHOLD


def get_files_to_delete(paths, age_days=7, extensions=None, exclude_dirs=None):
    """
    Get a list of files to delete based on age and extensions.
    
    Args:
        paths (list): List of paths to scan
        age_days (int): Files older than this many days will be marked for deletion
        extensions (list): List of file extensions to target
        exclude_dirs (list): List of directories to exclude
        
    Returns:
        list: List of files to delete
    """
    files_to_delete = []
    current_time = time.time()
    age_seconds = age_days * 86400  # Convert days to seconds
    
    exclude_dirs = exclude_dirs or []
    extensions = extensions or []
    
    for path in paths:
        if not os.path.exists(path):
            logger.warning(f"Path does not exist: {path}")
            continue
            
        try:
            if os.path.isfile(path):
                file_stats = os.stat(path)
                if (current_time - file_stats.st_mtime) > age_seconds:
                    if not extensions or any(path.endswith(ext) for ext in extensions):
                        files_to_delete.append(path)
            else:
                for root, dirs, files in os.walk(path, topdown=True):
                    # Exclude directories
                    dirs[:] = [d for d in dirs if os.path.join(root, d) not in exclude_dirs]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.islink(file_path):
                            continue
                            
                        try:
                            file_stats = os.stat(file_path)
                            if (current_time - file_stats.st_mtime) > age_seconds:
                                if not extensions or any(file.endswith(ext) for ext in extensions):
                                    files_to_delete.append(file_path)
                        except (FileNotFoundError, PermissionError) as e:
                            logger.debug(f"Error accessing file {file_path}: {e}")
        except (PermissionError, OSError) as e:
            logger.warning(f"Error accessing path {path}: {e}")
    
    return files_to_delete


def cleanup_files(files_list, dry_run=False):
    """
    Delete files in the provided list.
    
    Args:
        files_list (list): List of files to delete
        dry_run (bool): If True, only preview files that would be deleted
        
    Returns:
        tuple: (number of files deleted, total size freed)
    """
    deleted_count = 0
    total_size_freed = 0
    
    for file_path in files_list:
        try:
            file_size = os.path.getsize(file_path)
            if dry_run:
                logger.info(f"Would delete: {file_path} ({format_size(file_size)})")
            else:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path} ({format_size(file_size)})")
                deleted_count += 1
                total_size_freed += file_size
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.warning(f"Error deleting file {file_path}: {e}")
    
    return deleted_count, total_size_freed


def cleanup_empty_dirs(paths, dry_run=False):
    """
    Remove empty directories in the provided paths.
    
    Args:
        paths (list): List of paths to scan for empty directories
        dry_run (bool): If True, only preview directories that would be deleted
        
    Returns:
        int: Number of directories deleted
    """
    deleted_count = 0
    
    for path in paths:
        if not os.path.exists(path) or not os.path.isdir(path):
            continue
            
        for root, dirs, files in os.walk(path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if len(os.listdir(dir_path)) == 0:
                        if dry_run:
                            logger.info(f"Would remove empty directory: {dir_path}")
                        else:
                            os.rmdir(dir_path)
                            logger.info(f"Removed empty directory: {dir_path}")
                            deleted_count += 1
                except (PermissionError, OSError) as e:
                    logger.debug(f"Error removing directory {dir_path}: {e}")
    
    return deleted_count


def optimize_system():
    """Optimize system performance by clearing unused processes."""
    logger.info("Starting system optimization...")
    
    # Get current memory usage
    memory = psutil.virtual_memory()
    logger.info(f"Current memory usage: {memory.percent}%")
    logger.info(f"Available memory: {format_size(memory.available)}")
    
    # Clear system cache (requires root privileges)
    try:
        if os.geteuid() == 0:  # Check if running as root
            logger.info("Clearing system cache...")
            subprocess.run(["sync"], check=True)
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("3")
            logger.info("System cache cleared successfully")
        else:
            logger.warning("Skipping system cache clearing (requires root privileges)")
    except (subprocess.SubprocessError, IOError, PermissionError) as e:
        logger.error(f"Error clearing system cache: {e}")
    
    # Check for memory-intensive processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            process_info = proc.info
            memory_usage = process_info['memory_info'].rss
            cpu_usage = process_info['cpu_percent']
            
            if memory_usage > 100 * 1024 * 1024:  # More than 100MB
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'memory': memory_usage,
                    'cpu': cpu_usage
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort processes by memory usage (descending)
    processes.sort(key=lambda x: x['memory'], reverse=True)
    
    # Display top memory-consuming processes
    logger.info("Top memory-consuming processes:")
    for i, process in enumerate(processes[:10], 1):
        logger.info(f"{i}. PID: {process['pid']}, Name: {process['name']}, "
                   f"Memory: {format_size(process['memory'])}, CPU: {process['cpu']}%")
    
    # Refresh memory usage after optimization
    memory = psutil.virtual_memory()
    logger.info(f"Memory usage after optimization: {memory.percent}%")
    logger.info(f"Available memory: {format_size(memory.available)}")


def main():
    """Main function to run the system cleanup script."""
    parser = argparse.ArgumentParser(description="System Cleanup & Performance Booster")
    parser.add_argument("--dry-run", action="store_true", help="Preview files to be deleted without removing them")
    parser.add_argument("--age", type=int, default=7, help="Delete files older than specified days (default: 7)")
    parser.add_argument("--threshold", type=int, default=DISK_THRESHOLD, 
                        help=f"Disk space threshold percentage (default: {DISK_THRESHOLD})")
    parser.add_argument("--optimize", action="store_true", help="Optimize system performance")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"Starting system cleanup at {start_time}")
    
    # Load custom configuration if provided
    cleanup_paths = DEFAULT_CLEANUP_PATHS
    if args.config and os.path.exists(args.config):
        import json
        try:
            with open(args.config, 'r') as f:
                custom_config = json.load(f)
                cleanup_paths = custom_config.get('cleanup_paths', DEFAULT_CLEANUP_PATHS)
                logger.info(f"Loaded custom configuration from {args.config}")
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file: {args.config}")
    
    # Check disk space
    if check_disk_space():
        logger.warning(f"Disk usage above threshold ({args.threshold}%)!")
    
    total_files_deleted = 0
    total_size_freed = 0
    
    # Process temporary files
    logger.info("Processing temporary files...")
    temp_files = get_files_to_delete(
        cleanup_paths["temp_files"], 
        age_days=args.age,
        extensions=TARGET_EXTENSIONS["temp"]
    )
    
    count, size = cleanup_files(temp_files, dry_run=args.dry_run)
    total_files_deleted += count
    total_size_freed += size
    
    # Process log files
    logger.info("Processing log files...")
    log_files = get_files_to_delete(
        cleanup_paths["log_files"], 
        age_days=args.age,
        extensions=TARGET_EXTENSIONS["logs"]
    )
    
    count, size = cleanup_files(log_files, dry_run=args.dry_run)
    total_files_deleted += count
    total_size_freed += size
    
    # Process cache files
    logger.info("Processing cache files...")
    cache_files = get_files_to_delete(
        cleanup_paths["cache_files"], 
        age_days=args.age,
        extensions=TARGET_EXTENSIONS["cache"]
    )
    
    count, size = cleanup_files(cache_files, dry_run=args.dry_run)
    total_files_deleted += count
    total_size_freed += size
    
    # Clean up empty directories
    logger.info("Cleaning up empty directories...")
    dirs_deleted = cleanup_empty_dirs(
        cleanup_paths["temp_files"] + cleanup_paths["cache_files"],
        dry_run=args.dry_run
    )
    
    # Optimize system if requested
    if args.optimize:
        optimize_system()
    
    # Final report
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("Cleanup completed!")
    logger.info(f"Time taken: {duration}")
    
    if args.dry_run:
        logger.info(f"Would delete {total_files_deleted} files, freeing {format_size(total_size_freed)}")
        logger.info(f"Would remove {dirs_deleted} empty directories")
    else:
        logger.info(f"Deleted {total_files_deleted} files, freed {format_size(total_size_freed)}")
        logger.info(f"Removed {dirs_deleted} empty directories")
    
    # Check disk space after cleanup
    if not args.dry_run:
        check_disk_space()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)