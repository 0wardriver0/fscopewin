#!/usr/bin/env python3
"""
System Overview - Hackerish CLI System Monitor
Combines htop, nvidia-smi, and network monitoring into one real-time dashboard
"""

import asyncio
import time
import platform
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional

import psutil
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich import box

try:
    import pynvml

    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False


class SystemMonitor:
    def __init__(self):
        self.console = Console()
        self.start_time = time.time()
        self.network_stats_prev = psutil.net_io_counters()
        self.network_update_time = time.time()

        # Initialize NVIDIA if available
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
            except Exception:
                self.gpu_count = 0
        else:
            self.gpu_count = 0

    def get_ascii_header(self) -> Text:
        """Generate cool ASCII header"""
        header = """
███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗     ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗██╗███████╗██╗    ██╗
██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║    ██╔═══██╗██║   ██║██╔════╝██╔══██╗██║   ██║██║██╔════╝██║    ██║
███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║    ██║   ██║██║   ██║█████╗  ██████╔╝██║   ██║██║█████╗  ██║ █╗ ██║
╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║    ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗╚██╗ ██╔╝██║██╔══╝  ██║███╗██║
███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║ ╚████╔╝ ██║███████╗╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝
        """
        return Text(header, style="bold bright_green")

    def get_system_info(self) -> Panel:
        """Get basic system information"""
        uptime = time.time() - self.start_time
        uptime_str = (
            f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}"
        )

        info_table = Table(show_header=False, box=box.SIMPLE)
        info_table.add_column("Property", style="bright_cyan")
        info_table.add_column("Value", style="green")

        info_table.add_row("🖥️  System", f"{platform.system()} {platform.machine()}")
        info_table.add_row("🐍 Python", f"{platform.python_version()}")
        info_table.add_row("⏱️  Uptime", uptime_str)
        info_table.add_row(
            "👤 User", psutil.users()[0].name if psutil.users() else "Unknown"
        )
        info_table.add_row("🕐 Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return Panel(
            info_table,
            title="[bold bright_cyan]System Info[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    def get_cpu_memory_info(self) -> Panel:
        """Get CPU and memory usage information"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Memory usage
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Metric", style="bright_cyan")
        table.add_column("Usage", style="green")
        table.add_column("Bar", style="yellow")

        # CPU info
        cpu_bar = "█" * int(cpu_percent // 5) + "░" * (20 - int(cpu_percent // 5))
        table.add_row(
            f"🔥 CPU ({cpu_count} cores)",
            f"{cpu_percent:5.1f}%",
            f"[{'red' if cpu_percent > 80 else 'yellow' if cpu_percent > 60 else 'green'}]{cpu_bar}[/]",
        )

        if cpu_freq:
            table.add_row("⚡ CPU Freq", f"{cpu_freq.current:.0f} MHz", "")

        # Memory info
        mem_percent = memory.percent
        mem_bar = "█" * int(mem_percent // 5) + "░" * (20 - int(mem_percent // 5))
        table.add_row(
            "💾 Memory",
            f"{mem_percent:5.1f}%",
            f"[{'red' if mem_percent > 80 else 'yellow' if mem_percent > 60 else 'green'}]{mem_bar}[/]",
        )
        table.add_row(
            "",
            f"{self.bytes_to_human(memory.used)} / {self.bytes_to_human(memory.total)}",
            "",
        )

        # Swap info
        if swap.total > 0:
            swap_percent = swap.percent
            swap_bar = "█" * int(swap_percent // 5) + "░" * (
                20 - int(swap_percent // 5)
            )
            table.add_row(
                "💿 Swap",
                f"{swap_percent:5.1f}%",
                f"[{'red' if swap_percent > 50 else 'yellow' if swap_percent > 20 else 'green'}]{swap_bar}[/]",
            )

        return Panel(
            table,
            title="[bold bright_cyan]CPU & Memory[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    def get_gpu_info(self) -> Panel:
        """Get GPU information using nvidia-smi"""
        if self.gpu_count == 0:
            no_gpu_table = Table(show_header=False, box=box.SIMPLE)
            no_gpu_table.add_column("Status", style="yellow")
            no_gpu_table.add_row("🚫 No NVIDIA GPUs detected")
            return Panel(
                no_gpu_table,
                title="[bold bright_cyan]GPU Status[/]",
                border_style="bright_green",
                box=box.SQUARE,
            )

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("GPU", style="bright_cyan", width=12)
        table.add_column("Usage", style="green", width=8)
        table.add_column("Memory", style="green", width=12)
        table.add_column("Temp", style="green", width=8)
        table.add_column("Power", style="green", width=10)

        try:
            for i in range(self.gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                # Handle both string and bytes return types for GPU name
                name_raw = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name_raw, bytes):
                    name = name_raw.decode()
                else:
                    name = str(name_raw)

                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = int(util.gpu)

                # Memory info
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_used = int(mem_info.used) // 1024**2  # MB
                mem_total = int(mem_info.total) // 1024**2  # MB
                mem_percent = (mem_used / mem_total) * 100

                # Temperature
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                except:
                    temp = 0

                # Power
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) // 1000  # Watts
                    power_limit = (
                        pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1]
                        // 1000
                    )
                    power_str = f"{power}W/{power_limit}W"
                except:
                    power_str = "N/A"

                gpu_name = name.replace("NVIDIA ", "").replace("GeForce ", "")[:12]
                temp_color = "red" if temp > 80 else "yellow" if temp > 65 else "green"
                util_color = (
                    "red" if gpu_util > 90 else "yellow" if gpu_util > 70 else "green"
                )

                table.add_row(
                    f"🎮 {gpu_name}",
                    f"[{util_color}]{gpu_util}%[/]",
                    f"{mem_used}MB/{mem_total}MB",
                    f"[{temp_color}]{temp}°C[/]",
                    power_str,
                )
        except Exception as e:
            table.add_row("❌ Error", str(e)[:50], "", "", "")

        return Panel(
            table,
            title="[bold bright_cyan]GPU Status[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    def get_network_info(self) -> Panel:
        """Get network traffic information"""
        current_stats = psutil.net_io_counters()
        current_time = time.time()
        time_delta = current_time - self.network_update_time

        if time_delta > 0:
            bytes_sent_delta = (
                current_stats.bytes_sent - self.network_stats_prev.bytes_sent
            )
            bytes_recv_delta = (
                current_stats.bytes_recv - self.network_stats_prev.bytes_recv
            )

            upload_speed = bytes_sent_delta / time_delta
            download_speed = bytes_recv_delta / time_delta
        else:
            upload_speed = download_speed = 0

        self.network_stats_prev = current_stats
        self.network_update_time = current_time

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Interface", style="bright_cyan")
        table.add_column("Value", style="green")

        table.add_row("📡 Upload Speed", f"{self.bytes_to_human(upload_speed)}/s")
        table.add_row("📥 Download Speed", f"{self.bytes_to_human(download_speed)}/s")
        table.add_row("📤 Total Sent", self.bytes_to_human(current_stats.bytes_sent))
        table.add_row(
            "📨 Total Received", self.bytes_to_human(current_stats.bytes_recv)
        )
        table.add_row("📊 Packets Sent", f"{current_stats.packets_sent:,}")
        table.add_row("📊 Packets Received", f"{current_stats.packets_recv:,}")

        # Get active network interfaces
        interfaces = psutil.net_if_stats()
        active_interfaces = [name for name, stats in interfaces.items() if stats.isup]
        table.add_row("🌐 Active Interfaces", ", ".join(active_interfaces[:3]))

        return Panel(
            table,
            title="[bold bright_cyan]Network Traffic[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    def get_top_processes(self) -> Panel:
        """Get top processes by CPU usage"""
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent", "status"]
        ):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x["cpu_percent"] or 0, reverse=True)

        table = Table(show_header=True, box=box.SIMPLE)
        table.add_column("PID", style="bright_cyan", width=8)
        table.add_column("Process", style="green", width=20)
        table.add_column("CPU%", style="yellow", width=8)
        table.add_column("MEM%", style="magenta", width=8)
        table.add_column("Status", style="blue", width=10)

        for proc in processes[:10]:  # Top 10 processes
            cpu_color = (
                "red"
                if (proc["cpu_percent"] or 0) > 50
                else "yellow" if (proc["cpu_percent"] or 0) > 20 else "white"
            )
            mem_color = (
                "red"
                if (proc["memory_percent"] or 0) > 20
                else "yellow" if (proc["memory_percent"] or 0) > 10 else "white"
            )

            table.add_row(
                str(proc["pid"]),
                (proc["name"] or "N/A")[:20],
                f"[{cpu_color}]{proc['cpu_percent'] or 0:.1f}[/]",
                f"[{mem_color}]{proc['memory_percent'] or 0:.1f}[/]",
                (proc["status"] or "N/A")[:10],
            )

        return Panel(
            table,
            title="[bold bright_cyan]Top Processes[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    def get_disk_usage(self) -> Panel:
        """Get disk usage information"""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Disk", style="bright_cyan", width=15)
        table.add_column("Usage", style="green", width=10)
        table.add_column("Free/Total", style="green", width=15)
        table.add_column("Bar", style="yellow", width=20)

        disk_partitions = psutil.disk_partitions()
        for partition in disk_partitions[:5]:  # Show top 5 partitions
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                percent = (usage.used / usage.total) * 100
                disk_bar = "█" * int(percent // 5) + "░" * (20 - int(percent // 5))

                table.add_row(
                    f"💽 {partition.device}",
                    f"{percent:.1f}%",
                    f"{self.bytes_to_human(usage.free)} / {self.bytes_to_human(usage.total)}",
                    f"[{'red' if percent > 90 else 'yellow' if percent > 75 else 'green'}]{disk_bar}[/]",
                )
            except PermissionError:
                continue

        return Panel(
            table,
            title="[bold bright_cyan]Disk Usage[/]",
            border_style="bright_green",
            box=box.SQUARE,
        )

    @staticmethod
    def bytes_to_human(bytes_val: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}PB"

    def create_layout(self) -> Layout:
        """Create the main layout"""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=10),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(Layout(name="left"), Layout(name="right"))

        layout["left"].split_column(
            Layout(name="system_info", ratio=1),
            Layout(name="cpu_mem", ratio=1),
            Layout(name="gpu", ratio=1),
        )

        layout["right"].split_column(
            Layout(name="network", ratio=1),
            Layout(name="processes", ratio=2),
            Layout(name="disk", ratio=1),
        )

        return layout

    def update_layout(self, layout: Layout):
        """Update all panels in the layout"""
        layout["header"].update(Align.center(self.get_ascii_header()))
        layout["system_info"].update(self.get_system_info())
        layout["cpu_mem"].update(self.get_cpu_memory_info())
        layout["gpu"].update(self.get_gpu_info())
        layout["network"].update(self.get_network_info())
        layout["processes"].update(self.get_top_processes())
        layout["disk"].update(self.get_disk_usage())

        footer_text = Text(
            "🚀 System Overview - Press Ctrl+C to exit 🚀", style="bold bright_green"
        )
        layout["footer"].update(Align.center(footer_text))

    async def run(self):
        """Main run loop"""
        layout = self.create_layout()

        with Live(layout, refresh_per_second=2, screen=True) as live:
            while True:
                try:
                    self.update_layout(layout)
                    await asyncio.sleep(1)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(1)


def main():
    """Main entry point"""
    try:
        monitor = SystemMonitor()
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
