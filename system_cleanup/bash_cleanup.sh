#!/bin/bash
# System Cleanup & Performance Booster Wrapper Script

# Script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLEANUP_SCRIPT="$SCRIPT_DIR/system_cleanup.py"
CONFIG_FILE="$SCRIPT_DIR/cleanup_config.json"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check if required Python modules are installed
python3 -c "import psutil" &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing required Python modules...${NC}"
    pip3 install psutil
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to install required Python modules. Please install them manually:${NC}"
        echo "pip3 install psutil"
        exit 1
    fi
fi

# Check if the Python script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo -e "${RED}Error: Cleanup script not found at $CLEANUP_SCRIPT${NC}"
    exit 1
fi

# Make sure the Python script is executable
chmod +x "$CLEANUP_SCRIPT"

# Function to display usage
function show_usage {
    echo -e "${GREEN}System Cleanup & Performance Booster${NC}"
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -d, --dry-run     Preview files to be deleted without removing them"
    echo "  -a, --age DAYS    Delete files older than DAYS days (default: 7)"
    echo "  -t, --threshold PERCENT  Disk space threshold percentage (default: 80)"
    echo "  -o, --optimize    Optimize system performance"
    echo "  -c, --config FILE Use custom configuration file"
    echo "  -s, --schedule    Schedule script to run as a cron job"
    echo "  -h, --help        Show this help message"
}

# Function to schedule the script as a cron job
function schedule_cron {
    echo -e "${GREEN}Scheduling cleanup script to run as a cron job...${NC}"
    
    # Check if we're root
    if [ "$(id -u)" != "0" ]; then
        echo -e "${YELLOW}Warning: Not running as root. Scheduling for current user only.${NC}"
    fi
    
    read -p "Enter frequency (daily, weekly, monthly): " frequency
    case $frequency in
        daily)
            read -p "Enter time (HH:MM): " time
            hour=$(echo $time | cut -d: -f1)
            minute=$(echo $time | cut -d: -f2)
            cron_schedule="$minute $hour * * *"
            ;;
        weekly)
            read -p "Enter day (0-6, where 0 is Sunday): " day
            read -p "Enter time (HH:MM): " time
            hour=$(echo $time | cut -d: -f1)
            minute=$(echo $time | cut -d: -f2)
            cron_schedule="$minute $hour * * $day"
            ;;
        monthly)
            read -p "Enter day of month (1-31): " day
            read -p "Enter time (HH:MM): " time
            hour=$(echo $time | cut -d: -f1)
            minute=$(echo $time | cut -d: -f2)
            cron_schedule="$minute $hour $day * *"
            ;;
        *)
            echo -e "${RED}Invalid frequency. Please enter daily, weekly, or monthly.${NC}"
            exit 1
            ;;
    esac
    
    # Create cron job
    cron_cmd="$cron_schedule $SCRIPT_DIR/cleanup.sh --optimize"
    
    # Check if user wants to run as root
    if [ "$(id -u)" == "0" ]; then
        (crontab -l 2>/dev/null; echo "$cron_cmd") | crontab -
        echo -e "${GREEN}Cron job scheduled for root user.${NC}"
    else
        (crontab -l 2>/dev/null; echo "$cron_cmd") | crontab -
        echo -e "${GREEN}Cron job scheduled for current user.${NC}"
    fi
    
    echo -e "${GREEN}Script will run: $cron_schedule${NC}"
}

# Parse command line arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -d|--dry-run)
            ARGS+=("--dry-run")
            shift
            ;;
        -a|--age)
            ARGS+=("--age" "$2")
            shift 2
            ;;
        -t|--threshold)
            ARGS+=("--threshold" "$2")
            shift 2
            ;;
        -o|--optimize)
            ARGS+=("--optimize")
            shift
            ;;
        -c|--config)
            ARGS+=("--config" "$2")
            shift 2
            ;;
        -s|--schedule)
            schedule_cron
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $key${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Run the cleanup script
echo -e "${GREEN}Running system cleanup script...${NC}"
python3 "$CLEANUP_SCRIPT" "${ARGS[@]}"

# Check the exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Cleanup completed successfully!${NC}"
else
    echo -e "${RED}Cleanup failed. Check the log file for details.${NC}"
fi