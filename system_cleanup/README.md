# System Cleanup & Performance Booster

This toolkit provides a comprehensive solution for automating system cleanup, monitoring disk space, and optimizing system performance on Linux systems.

## Features

- Automatic cleanup of temporary files, cache, and logs
- Disk space monitoring with configurable threshold alerts
- System performance optimization
- Safe mode to preview files before deletion
- Scheduling via cron jobs for automated maintenance
- Customizable configuration

## Requirements

- Python 3.6 or higher
- psutil Python module
- Linux operating system

## Installation

1. Clone or download this repository to your local machine
2. Make the scripts executable:
   ```
   chmod +x system_cleanup.py cleanup.sh
   ```
3. Install the required Python modules:
   ```
   pip3 install psutil
   ```

## Usage

### Basic Usage

Run the cleanup script with default settings:

```bash
./cleanup.sh
```

### Command Line Options

The script supports several command line options:

- `-d, --dry-run`: Preview files to be deleted without removing them
- `-a, --age DAYS`: Delete files older than DAYS days (default: 7)
- `-t, --threshold PERCENT`: Disk space threshold percentage (default: 80)
- `-o, --optimize`: Optimize system performance
- `-c, --config FILE`: Use custom configuration file
- `-s, --schedule`: Schedule script to run as a cron job
- `-h, --help`: Show help message

### Examples

1. Preview files that would be deleted without actually deleting them:
   ```bash
   ./cleanup.sh --dry-run
   ```

2. Delete files older than 14 days:
   ```bash
   ./cleanup.sh --age 14
   ```

3. Set disk space threshold to 90%:
   ```bash
   ./cleanup.sh --threshold 90
   ```

4. Run cleanup and system optimization:
   ```bash
   ./cleanup.sh --optimize
   ```

5. Use a custom configuration file:
   ```bash
   ./cleanup.sh --config my_config.json
   ```

6. Schedule the script to run automatically:
   ```bash
   ./cleanup.sh --schedule
   ```

## Configuration

You can customize the script's behavior by editing the `cleanup_config.json` file. The configuration allows you to specify:

- Paths to clean up
- File extensions to target
- Disk space threshold
- Directories to exclude from cleanup

## Scheduling with Cron

To schedule the script to run automatically, you can use the `--schedule` option:

```bash
./cleanup.sh --schedule
```

This will prompt you to enter the frequency (daily, weekly, or monthly) and the time to run the script.

## Logs

The script creates a log file named `system_cleanup.log` in the same directory. This log contains detailed information about the cleanup process, including files deleted and disk space freed.

## Safety Features

- The script includes a dry-run mode to preview files before deletion
- It excludes important system directories by default
- It logs all actions for audit purposes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.