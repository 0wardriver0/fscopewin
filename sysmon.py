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
import signal
import threading
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
        self.selected_process = 0
        self.top_processes = []
        self.input_mode = "normal"  # normal, select, confirm
        self.pending_kill_pid = None
        self.message = ""
        self.message_color = "white"

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
        return Text(header, style="bold green")

    def get_system_info(self) -> Panel:
        """Get basic system information"""
        uptime = time.time() - self.start_time
        uptime_str = (
            f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}"
        )

        info_table = Table(show_header=False, box=box.SIMPLE)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="bright_green")

        info_table.add_row("🖥️  System", f"{platform.system()} {platform.machine()}")
        info_table.add_row("🐍 Python", f"{platform.python_version()}")
        info_table.add_row("⏱️  Uptime", uptime_str)
        info_table.add_row(
            "👤 User", psutil.users()[0].name if psutil.users() else "Unknown"
        )
        info_table.add_row("🕐 Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return Panel(
            info_table, title="[bold cyan]System Info[/]", border_style="green"
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
        table.add_column("Metric", style="cyan")
        table.add_column("Usage", style="bright_green")
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

        return Panel(table, title="[bold cyan]CPU & Memory[/]", border_style="green")

    def get_gpu_info(self) -> Panel:
        """Get GPU information using nvidia-smi"""
        if self.gpu_count == 0:
            no_gpu_table = Table(show_header=False, box=box.SIMPLE)
            no_gpu_table.add_column("Status", style="yellow")
            no_gpu_table.add_row("🚫 No NVIDIA GPUs detected")
            return Panel(
                no_gpu_table, title="[bold cyan]GPU Status[/]", border_style="green"
            )

        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("GPU", style="cyan", width=12)
        table.add_column("Usage", style="bright_green", width=8)
        table.add_column("Memory", style="bright_green", width=12)
        table.add_column("Temp", style="bright_green", width=8)
        table.add_column("Power", style="bright_green", width=10)

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
                mem_used = int(mem_info.used) // 1024**2
                mem_total = int(mem_info.total) // 1024**2
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

        return Panel(table, title="[bold cyan]GPU Status[/]", border_style="green")

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
        table.add_column("Interface", style="cyan")
        table.add_column("Value", style="bright_green")

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

        return Panel(table, title="[bold cyan]Network Traffic[/]", border_style="green")

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
        self.top_processes = processes[:10]  # Store for killing

        table = Table(show_header=True, box=box.SIMPLE)
        table.add_column("#", style="cyan", width=3)
        table.add_column("PID", style="cyan", width=8)
        table.add_column("Process", style="bright_green", width=18)
        table.add_column("CPU%", style="yellow", width=8)
        table.add_column("MEM%", style="magenta", width=8)
        table.add_column("Status", style="blue", width=8)

        for i, proc in enumerate(self.top_processes):
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

            # Highlight selected process
            row_style = ""
            number_display = str(i + 1)
            if self.input_mode == "select" and i == self.selected_process:
                row_style = "on bright_blue"
                number_display = f"► {i + 1}"

            table.add_row(
                number_display,
                str(proc["pid"]),
                (proc["name"] or "N/A")[:18],
                f"[{cpu_color}]{proc['cpu_percent'] or 0:.1f}[/]",
                f"[{mem_color}]{proc['memory_percent'] or 0:.1f}[/]",
                (proc["status"] or "N/A")[:8],
                style=row_style,
            )

        title_text = "[bold cyan]Top Processes"
        if self.input_mode == "select":
            title_text += " - Select with ↑↓, Kill with K, Esc to cancel"
        elif self.input_mode == "normal":
            title_text += " - Press K to kill mode"
        title_text += "[/]"

        return Panel(table, title=title_text, border_style="green")

    def get_disk_usage(self) -> Panel:
        """Get disk usage information"""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Disk", style="cyan", width=15)
        table.add_column("Usage", style="bright_green", width=10)
        table.add_column("Free/Total", style="bright_green", width=15)
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

        return Panel(table, title="[bold cyan]Disk Usage[/]", border_style="green")

    @staticmethod
    def bytes_to_human(bytes_val: float) -> str:
        """Convert bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}PB"

    def handle_keyboard_input(self, key: str):
        """Handle keyboard input for process interaction"""
        if self.input_mode == "normal":
            if key.lower() == "k":
                self.input_mode = "select"
                self.selected_process = 0
                self.message = ""

        elif self.input_mode == "select":
            if key == "up" and self.selected_process > 0:
                self.selected_process -= 1
            elif key == "down" and self.selected_process < len(self.top_processes) - 1:
                self.selected_process += 1
            elif key.lower() == "k":
                if self.top_processes and self.selected_process < len(
                    self.top_processes
                ):
                    self.pending_kill_pid = self.top_processes[self.selected_process][
                        "pid"
                    ]
                    self.input_mode = "confirm"
            elif key == "escape":
                self.input_mode = "normal"
                self.message = "Cancelled process selection"
                self.message_color = "yellow"

        elif self.input_mode == "confirm":
            if key.lower() == "y":
                if self.pending_kill_pid is not None:
                    self.kill_process(self.pending_kill_pid)
                self.input_mode = "normal"
                self.pending_kill_pid = None
            elif key.lower() == "n" or key == "escape":
                self.input_mode = "normal"
                self.pending_kill_pid = None
                self.message = "Kill cancelled"
                self.message_color = "yellow"

    def kill_process(self, pid: int):
        """Kill a process by PID"""
        try:
            process = psutil.Process(pid)
            process_name = process.name()

            # Try graceful termination first
            process.terminate()

            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=2)
                self.message = f"Successfully terminated {process_name} (PID: {pid})"
                self.message_color = "green"
            except psutil.TimeoutExpired:
                # Force kill if graceful termination failed
                process.kill()
                self.message = f"Force killed {process_name} (PID: {pid})"
                self.message_color = "red"

        except psutil.NoSuchProcess:
            self.message = f"Process {pid} no longer exists"
            self.message_color = "yellow"
        except psutil.AccessDenied:
            self.message = f"Permission denied to kill process {pid}"
            self.message_color = "red"
        except Exception as e:
            self.message = f"Error killing process {pid}: {str(e)[:30]}"
            self.message_color = "red"

    def clear_message_after_delay(self):
        """Clear message after a delay"""

        def clear():
            time.sleep(3)
            self.message = ""
            self.message_color = "white"

        threading.Thread(target=clear, daemon=True).start()

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

        # Dynamic footer based on mode and messages
        if self.input_mode == "confirm":
            footer_text = Text(
                f"⚠️  Kill process {self.pending_kill_pid}? (Y/N) ⚠️", style="bold red"
            )
        elif self.input_mode == "select":
            footer_text = Text(
                "🎯 Use ↑↓ arrows to select, K to kill, Esc to cancel",
                style="bold yellow",
            )
        elif self.message:
            footer_text = Text(f"💬 {self.message}", style=f"bold {self.message_color}")
        else:
            footer_text = Text(
                "🚀 System Overview - Press K for kill mode, Ctrl+C to exit 🚀",
                style="bold bright_green",
            )

        layout["footer"].update(Align.center(footer_text))

    async def run(self):
        """Main run loop with simple keyboard input"""
        import select
        import sys
        import termios
        import tty

        layout = self.create_layout()

        # Set terminal to non-blocking mode
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())

            with Live(layout, refresh_per_second=2, screen=True) as live:
                while True:
                    try:
                        # Check for keyboard input
                        if select.select([sys.stdin], [], [], 0) == (
                            [sys.stdin],
                            [],
                            [],
                        ):
                            char = sys.stdin.read(1)
                            if char == "\x03":  # Ctrl+C
                                break
                            elif char == "\x1b":  # ESC sequence for arrow keys
                                try:
                                    char = sys.stdin.read(2)
                                    if char == "[A":
                                        self.handle_keyboard_input("up")
                                    elif char == "[B":
                                        self.handle_keyboard_input("down")
                                    else:
                                        self.handle_keyboard_input("escape")
                                except:
                                    self.handle_keyboard_input("escape")
                            else:
                                self.handle_keyboard_input(char)
                                if self.message and self.message_color != "white":
                                    self.clear_message_after_delay()

                        self.update_layout(layout)
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        self.console.print(f"[red]Error: {e}[/red]")
                        await asyncio.sleep(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


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
