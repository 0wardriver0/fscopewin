# 🚀 System Overview - Hackerish CLI Monitor for Windows

A comprehensive real-time system monitoring tool that combines the functionality of `htop`, `nvidia-smi`, and network monitoring into one sleek, hackerish terminal dashboard.

Perfect for developers working on AI projects who need to monitor system resources, GPU usage, and network activity all in one place.

![System Overview Screenshot](https://raw.githubusercontent.com/0wardriver0/fscopewin/main/terminal.png)

## ✨ Features

- **🔥 CPU & Memory Monitoring**: Real-time CPU usage, memory consumption, and swap usage with visual bars
- **🎮 GPU Monitoring**: NVIDIA GPU utilization, memory usage, temperature, and power consumption
- **📡 Network Traffic**: Upload/download speeds, total data transferred, and active interfaces
- **📊 Interactive Process Monitoring**: Top 10 processes by CPU usage with ability to kill processes
- **💽 Disk Usage**: Storage usage across all mounted drives
- **🖥️ System Information**: OS details, uptime, current user, and timestamp
- **🎨 Hackerish UI**: Matrix-style green color scheme with ASCII art header
- **⚡ Real-time Updates**: Refreshes every second for live monitoring

## 🛠️ Installation

### 🚀 Quick Setup

1. Clone or download this repository
2. Run the setup script:
   ```batch
   ./setup.bat
   ```
**Press `Ctrl+C` to exit the monitor**

### 🎮 Keyboard Controls

- **`K`** - Enter process kill mode
- **`↑/↓`** - Navigate through processes (when in kill mode)
- **`K`** - Kill selected process (when in kill mode)
- **`Y`** - Confirm process kill
- **`N`** or **`Esc`** - Cancel process kill/exit kill mode
- **`Ctrl+C`** - Exit the application

## 📋 Requirements

- **Python 3.7+**
- **NVIDIA drivers** (optional, for GPU monitoring)
- Terminal with Unicode support for best visual experience

## 📦 Dependencies

- `rich` - Beautiful terminal UI and formatting
- `psutil` - System and process monitoring
- `pynvml` - NVIDIA GPU monitoring (optional)
- `asyncio-throttle` - Async utilities

## 🎯 Features Breakdown

### CPU & Memory Panel

- Real-time CPU usage percentage
- CPU frequency information
- Memory usage with visual bars
- Swap usage monitoring
- Color-coded alerts (green/yellow/red)

### GPU Status Panel

- GPU utilization percentage
- VRAM usage (used/total)
- GPU temperature with thermal warnings
- Power consumption vs limits
- Support for multiple GPUs

### Network Traffic Panel

- Real-time upload/download speeds
- Total bytes sent/received
- Packet statistics
- Active network interfaces

### Top Processes Panel

- Top 10 processes by CPU usage
- Process ID, name, and status
- CPU and memory usage per process
- Color-coded resource usage
- **Interactive process killing**:
  - Press `K` to enter kill mode
  - Use ↑↓ arrow keys to select process
  - Press `K` again to kill selected process
  - Press `Y` to confirm or `N`/`Esc` to cancel

### Disk Usage Panel

- Usage percentage for all mounted drives
- Free space vs total capacity
- Visual usage bars
- Storage alerts for near-full drives

## 🎨 Visual Design

The interface features:

- **Matrix-style green theme** for that authentic hacker aesthetic
- **ASCII art header** with the tool name
- **Color-coded metrics** (green = good, yellow = warning, red = critical)
- **Unicode symbols and emojis** for visual clarity
- **Clean panel layout** that scales to your terminal size

## 🔧 Troubleshooting

### GPU Monitoring Not Working

- Ensure NVIDIA drivers are installed
- Install `nvidia-ml-py3`: `pip3 install pynvml`
- The tool will gracefully fall back if GPU monitoring fails

### Permission Errors

- Some system metrics may require elevated permissions
- Try running with `sudo` if you encounter permission issues

### Terminal Display Issues

- Ensure your terminal supports Unicode characters
- Use a modern terminal emulator for best results
- Resize your terminal if the layout appears cramped

## 🎮 Perfect for AI Development

This tool is specifically designed for AI developers who need to monitor:

- **GPU utilization** during model training
- **Memory usage** for large datasets
- **Network traffic** during data downloads
- **CPU usage** during preprocessing
- **Storage space** for model checkpoints

## 🚀 Future Enhancements

Potential features for future versions:

- Temperature monitoring for CPU
- Docker container monitoring
- Custom alert thresholds
- Historical data graphs
- Export monitoring data
- AMD GPU support

## 📄 License

This project is open source and available under the MIT License.

---

**Happy monitoring! 🎯**
