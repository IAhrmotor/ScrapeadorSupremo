"""Desktop GUI application for Cochesnet scraper using tkinter."""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional, List
import sys
import subprocess
import socket
import time
from pathlib import Path
from datetime import datetime

# HeadlessX configuration
HEADLESSX_URL = "http://localhost:3000"
HEADLESSX_PORT = 3000
HEADLESSX_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "HeadlessX"

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.cochesnet.app.scraper_agent import CochesnetScraperAgent, ScrapeResult


class CochesnetApp:
    """
    Desktop GUI application for Cochesnet scraping.

    Features:
    - Year selection (2007-2025) with checkboxes
    - Progress tracking
    - Real-time log output
    - Database statistics
    - Export functionality
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cochesnet Scraper")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Agent instance
        self.agent = CochesnetScraperAgent()

        # State
        self.is_running = False
        self.selected_years = []

        # HeadlessX state
        self.headlessx_process = None  # Subprocess if we started it
        self.headlessx_managed = False  # True if we manage the process

        # Create UI
        self._create_widgets()
        self._load_initial_data()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Coches.net Scraper",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Scraping
        scrape_frame = ttk.Frame(notebook, padding="10")
        notebook.add(scrape_frame, text="Scraping")
        self._create_scrape_tab(scrape_frame)

        # Tab 2: Statistics
        stats_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stats_frame, text="Statistics")
        self._create_stats_tab(stats_frame)

        # Tab 3: Export
        export_frame = ttk.Frame(notebook, padding="10")
        notebook.add(export_frame, text="Export")
        self._create_export_tab(export_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def _create_scrape_tab(self, parent):
        """Create the scraping tab."""
        # Left panel - Year selection
        left_frame = ttk.LabelFrame(parent, text="Select Years", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Year list with scrollbar
        year_container = ttk.Frame(left_frame)
        year_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(year_container, width=200)
        scrollbar = ttk.Scrollbar(year_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Year checkboxes (2007-2025)
        self.year_vars = {}
        years = list(range(2007, 2026))  # 2007 to 2025

        for year in years:
            var = tk.BooleanVar()
            self.year_vars[year] = var

            cb = ttk.Checkbutton(
                scrollable_frame,
                text=str(year),
                variable=var,
                command=self._on_year_selection_changed
            )
            cb.pack(anchor=tk.W, pady=2)

        # Select/Deselect buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            button_frame,
            text="Select All",
            command=self._select_all_years
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Deselect All",
            command=self._deselect_all_years
        ).pack(side=tk.LEFT, padx=2)

        # Select recent years button
        ttk.Button(
            button_frame,
            text="2020-2025",
            command=lambda: self._select_year_range(2020, 2025)
        ).pack(side=tk.LEFT, padx=2)

        # Right panel - Progress and logs
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # HeadlessX Server section
        server_frame = ttk.LabelFrame(right_frame, text="HeadlessX Server", padding="5")
        server_frame.pack(fill=tk.X, pady=(0, 5))

        server_status_frame = ttk.Frame(server_frame)
        server_status_frame.pack(fill=tk.X)

        self.server_status_label = ttk.Label(
            server_status_frame,
            text="Server: Checking...",
            font=("Helvetica", 10, "bold")
        )
        self.server_status_label.pack(side=tk.LEFT, padx=(0, 10))

        self.start_server_button = ttk.Button(
            server_status_frame,
            text="Start Server",
            command=self._start_headlessx,
            width=12
        )
        self.start_server_button.pack(side=tk.LEFT)

        ttk.Button(
            server_status_frame,
            text="Refresh",
            command=self._refresh_server_status,
            width=8
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Progress section
        progress_frame = ttk.LabelFrame(right_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.X, pady=(0, 5))

        # Progress info frame
        progress_info_frame = ttk.Frame(progress_frame)
        progress_info_frame.pack(fill=tk.X, pady=(0, 5))

        # Progress percentage label (left)
        self.progress_percent_label = ttk.Label(progress_info_frame, text="0%", font=("Arial", 10, "bold"))
        self.progress_percent_label.pack(side=tk.LEFT)

        # Progress detail label (right)
        self.progress_detail_label = ttk.Label(progress_info_frame, text="", font=("Arial", 9))
        self.progress_detail_label.pack(side=tk.RIGHT)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Progress label (main status)
        self.progress_label = ttk.Label(progress_frame, text="Listo para scrapear", font=("Arial", 9))
        self.progress_label.pack()

        # Scraping mode options
        parallel_frame = ttk.LabelFrame(progress_frame, text="Modo de Scrapeo", padding="5")
        parallel_frame.pack(fill=tk.X, pady=(5, 5))

        # Mode selector: 0=sequential, 1=sequential+parallel_pages, 2=full_parallel
        self.mode_var = tk.IntVar(value=0)

        ttk.Radiobutton(
            parallel_frame,
            text="Secuencial puro (1 año, 1 página a la vez)",
            variable=self.mode_var,
            value=0
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            parallel_frame,
            text="Secuencial + Workers (1 año, N páginas en paralelo)",
            variable=self.mode_var,
            value=1
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            parallel_frame,
            text="Paralelo total (N años simultáneos)",
            variable=self.mode_var,
            value=2
        ).pack(anchor=tk.W)

        # Workers selector
        workers_frame = ttk.Frame(parallel_frame)
        workers_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(workers_frame, text="Workers:").pack(side=tk.LEFT)
        self.workers_var = tk.IntVar(value=3)
        workers_spinbox = ttk.Spinbox(
            workers_frame,
            from_=2,
            to=5,
            width=5,
            textvariable=self.workers_var
        )
        workers_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(workers_frame, text="(páginas o años según modo)").pack(side=tk.LEFT)

        # Control buttons
        control_frame = ttk.Frame(progress_frame)
        control_frame.pack(fill=tk.X, pady=(5, 0))

        self.start_button = ttk.Button(
            control_frame,
            text="Start Scraping",
            command=self._start_scraping
        )
        self.start_button.pack(side=tk.LEFT, padx=2)

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop",
            command=self._stop_scraping,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=2)

        # Logs section
        logs_frame = ttk.LabelFrame(right_frame, text="Logs", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=15,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Clear logs button
        ttk.Button(
            logs_frame,
            text="Clear Logs",
            command=self._clear_logs
        ).pack(pady=(5, 0))

    def _create_stats_tab(self, parent):
        """Create the statistics tab."""
        stats_container = ttk.Frame(parent)
        stats_container.pack(fill=tk.BOTH, expand=True)

        # Stats display
        self.stats_text = scrolledtext.ScrolledText(
            stats_container,
            height=20,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Refresh button
        ttk.Button(
            stats_container,
            text="Refresh Statistics",
            command=self._refresh_stats
        ).pack()

    def _create_export_tab(self, parent):
        """Create the export tab."""
        export_container = ttk.Frame(parent)
        export_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Export info
        info_text = """
Export scraped data to different formats.

Available formats:
- CSV: Comma-separated values
- JSON: JavaScript Object Notation
- Excel: Microsoft Excel format

The export will include all scraped listings from the database.
        """

        ttk.Label(
            export_container,
            text=info_text,
            justify=tk.LEFT
        ).pack(pady=(0, 20))

        # Export buttons
        button_frame = ttk.Frame(export_container)
        button_frame.pack()

        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: self._export_data("csv")
        ).pack(pady=5, fill=tk.X)

        ttk.Button(
            button_frame,
            text="Export to JSON",
            command=lambda: self._export_data("json")
        ).pack(pady=5, fill=tk.X)

        ttk.Button(
            button_frame,
            text="Export to Excel",
            command=lambda: self._export_data("excel")
        ).pack(pady=5, fill=tk.X)

    def _load_initial_data(self):
        """Load initial data when app starts."""
        self._log("Application started")
        self._refresh_server_status()
        self._refresh_stats()

    def _refresh_server_status(self):
        """Check and update HeadlessX server status."""
        is_online = self._check_headlessx_status()
        self._update_server_status(is_online)
        if not is_online:
            self._log("HeadlessX server is offline - click 'Start Server' to start it")

    def _on_year_selection_changed(self):
        """Called when year selection changes."""
        self.selected_years = [
            year for year, var in self.year_vars.items()
            if var.get()
        ]
        self._log(f"Selected {len(self.selected_years)} years")

    def _select_all_years(self):
        """Select all years."""
        for var in self.year_vars.values():
            var.set(True)
        self._on_year_selection_changed()

    def _deselect_all_years(self):
        """Deselect all years."""
        for var in self.year_vars.values():
            var.set(False)
        self._on_year_selection_changed()

    def _select_year_range(self, start_year: int, end_year: int):
        """Select a range of years."""
        for year, var in self.year_vars.items():
            var.set(start_year <= year <= end_year)
        self._on_year_selection_changed()

    def _start_scraping(self):
        """Start the scraping process."""
        if not self.selected_years:
            messagebox.showwarning(
                "No Years Selected",
                "Please select at least one year to scrape."
            )
            return

        if self.is_running:
            messagebox.showwarning(
                "Already Running",
                "Scraping is already in progress."
            )
            return

        # Check HeadlessX server
        if not self._check_headlessx_status():
            self._update_server_status(False)
            if messagebox.askyesno(
                "Server Offline",
                "HeadlessX server is not running.\n\nDo you want to start it now?"
            ):
                self._start_headlessx()
                self._log("Please wait for server to start, then try again.")
            return

        # Confirm
        mode = self.mode_var.get()
        workers = self.workers_var.get()

        mode_names = {
            0: "SECUENCIAL PURO",
            1: f"SECUENCIAL + {workers} WORKERS (páginas en paralelo)",
            2: f"PARALELO TOTAL ({workers} años simultáneos)"
        }
        mode_str = mode_names.get(mode, "DESCONOCIDO")

        msg = f"Start scraping {len(self.selected_years)} years?\n\n"
        msg += f"Mode: {mode_str}\n"
        msg += f"Years: {', '.join(map(str, sorted(self.selected_years)))}"

        if not messagebox.askyesno("Confirm", msg):
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # Reset progress indicators
        self.progress_var.set(0)
        self.progress_percent_label.config(text="0%")
        self.progress_detail_label.config(text="Iniciando...")
        self.progress_label.config(text="Preparando scraping...")

        # Start scraping in background thread
        threading.Thread(
            target=self._run_scraping_thread,
            daemon=True
        ).start()

    def _run_scraping_thread(self):
        """Run scraping in a background thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Get mode settings
            mode = self.mode_var.get()
            max_workers = self.workers_var.get()

            # Run scraping based on mode
            if mode == 0:
                # Secuencial puro
                self._log("Mode: SECUENCIAL PURO (1 año, 1 página a la vez)")
                result = loop.run_until_complete(
                    self.agent.scrape_years(
                        years=self.selected_years,
                        progress_callback=self._update_progress,
                        log_callback=self._log,
                        parallel=False,
                        max_workers=1
                    )
                )

            elif mode == 1:
                # Secuencial + Workers (páginas en paralelo)
                self._log(f"Mode: SECUENCIAL + {max_workers} WORKERS (páginas en paralelo)")
                result = loop.run_until_complete(
                    self.agent.scrape_years_sequential_parallel_pages(
                        years=self.selected_years,
                        progress_callback=self._update_progress,
                        log_callback=self._log,
                        max_workers=max_workers
                    )
                )

            else:  # mode == 2
                # Paralelo total (años simultáneos)
                self._log(f"Mode: PARALELO TOTAL ({max_workers} años simultáneos)")
                result = loop.run_until_complete(
                    self.agent.scrape_years(
                        years=self.selected_years,
                        progress_callback=self._update_progress,
                        log_callback=self._log,
                        parallel=True,
                        max_workers=max_workers
                    )
                )

            # Show results
            self.root.after(0, lambda: self._show_results(result))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

        finally:
            self.root.after(0, self._scraping_finished)

    def _stop_scraping(self):
        """Stop the scraping process."""
        if messagebox.askyesno("Confirm", "Stop scraping?"):
            self.agent.stop()
            self._log("Stop requested...")

    def _update_progress(self, current: int, total: int, message: str):
        """Update progress bar and labels with detailed info."""
        def update():
            progress = (current / total * 100) if total > 0 else 0
            self.progress_var.set(progress)

            # Update percentage label
            self.progress_percent_label.config(text=f"{progress:.1f}%")

            # Update detail label (pages info)
            self.progress_detail_label.config(text=f"{current}/{total} páginas")

            # Update main status label
            self.progress_label.config(text=message)
            self.status_var.set(message)

        self.root.after(0, update)

    def _log(self, message: str):
        """Add message to log."""
        def add_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)

        self.root.after(0, add_log)

    def _clear_logs(self):
        """Clear the log text."""
        self.log_text.delete(1.0, tk.END)

    def _scraping_finished(self):
        """Called when scraping finishes."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set(100)
        self.progress_percent_label.config(text="100%")
        self.progress_detail_label.config(text="Completado")
        self.progress_label.config(text="Scraping finalizado")
        self._refresh_stats()

    def _show_results(self, result: ScrapeResult):
        """Show scraping results."""
        msg = f"""
Scraping Completed!

Total Listings: {result.total_listings}
New Listings: {result.new_listings}
Updated Listings: {result.updated_listings}
Errors: {result.errors}

Time Taken: {result.duration:.1f} seconds
        """

        messagebox.showinfo("Results", msg.strip())
        self._log("Scraping completed successfully")

    def _show_error(self, error: str):
        """Show error message."""
        messagebox.showerror("Error", f"Scraping failed:\n\n{error}")
        self._log(f"ERROR: {error}")

    def _refresh_stats(self):
        """Refresh database statistics."""
        self._log("Refreshing statistics...")

        try:
            stats = self.agent.get_statistics()

            stats_text = f"""
DATABASE STATISTICS
{"="*50}

Total Listings: {stats.get('total_listings', 0):,}
By Year:
"""

            # Add year breakdown
            year_counts = stats.get('by_year', {})
            for year in sorted(year_counts.keys(), reverse=True):
                count = year_counts[year]
                stats_text += f"  {year}: {count:,} listings\n"

            stats_text += f"""
{"="*50}

Parsing Quality:
Average Confidence: {stats.get('avg_confidence', 0):.2f}
Perfect Matches: {stats.get('perfect_matches', 0):,} ({stats.get('perfect_pct', 0):.1f}%)

Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text.strip())

            self._log("Statistics refreshed")

        except Exception as e:
            self._log(f"Error refreshing stats: {e}")
            messagebox.showerror("Error", f"Failed to load statistics:\n\n{e}")

    def _export_data(self, format: str):
        """Export data to file."""
        # File dialog
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "json": [("JSON files", "*.json")],
            "excel": [("Excel files", "*.xlsx")]
        }

        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=filetypes.get(format, [("All files", "*.*")])
        )

        if not filename:
            return

        try:
            self._log(f"Exporting to {format.upper()}...")
            self.agent.export_data(filename, format)
            self._log(f"Export completed: {filename}")
            messagebox.showinfo("Success", f"Data exported to:\n{filename}")

        except Exception as e:
            self._log(f"Export failed: {e}")
            messagebox.showerror("Error", f"Export failed:\n\n{e}")

    # ==================== HeadlessX Management ====================

    def _check_headlessx_status(self) -> bool:
        """Check if HeadlessX server is running on localhost:3000."""
        import urllib.request
        try:
            # Try HTTP request to health endpoint
            req = urllib.request.Request(
                f"{HEADLESSX_URL}/api/health",
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status == 200
        except Exception:
            # Fallback: try socket connection (IPv4 and IPv6)
            for family in [socket.AF_INET, socket.AF_INET6]:
                try:
                    sock = socket.socket(family, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    host = '127.0.0.1' if family == socket.AF_INET else '::1'
                    result = sock.connect_ex((host, HEADLESSX_PORT))
                    sock.close()
                    if result == 0:
                        return True
                except Exception:
                    continue
            return False

    def _start_headlessx(self):
        """Start HeadlessX server in background."""
        if self._check_headlessx_status():
            self._log("HeadlessX already running")
            self._update_server_status(True)
            return True

        if not HEADLESSX_PATH.exists():
            self._log(f"ERROR: HeadlessX not found at {HEADLESSX_PATH}")
            messagebox.showerror(
                "HeadlessX Not Found",
                f"HeadlessX directory not found at:\n{HEADLESSX_PATH}\n\nPlease install HeadlessX first."
            )
            return False

        self._log("Starting HeadlessX server...")
        self.server_status_label.config(text="Server: Starting...", foreground="orange")
        self.start_server_button.config(state=tk.DISABLED)

        def start_server():
            try:
                # On Windows, use cmd /c to run npm start properly
                if sys.platform == 'win32':
                    cmd = f'cd /d "{HEADLESSX_PATH}" && npm start'
                    self.headlessx_process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    self.headlessx_process = subprocess.Popen(
                        ['npm', 'start'],
                        cwd=str(HEADLESSX_PATH),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                self.headlessx_managed = True

                # Wait for server to be ready (max 30 seconds)
                for i in range(30):
                    time.sleep(1)
                    if self._check_headlessx_status():
                        self.root.after(0, lambda: self._on_headlessx_started(True))
                        return
                    if self.headlessx_process.poll() is not None:
                        # Process died
                        self.root.after(0, lambda: self._on_headlessx_started(False, "Process terminated"))
                        return

                self.root.after(0, lambda: self._on_headlessx_started(False, "Timeout"))

            except Exception as e:
                self.root.after(0, lambda: self._on_headlessx_started(False, str(e)))

        threading.Thread(target=start_server, daemon=True).start()
        return True

    def _on_headlessx_started(self, success: bool, error: str = None):
        """Called when HeadlessX startup completes."""
        if success:
            self._log("HeadlessX server started successfully")
            self._update_server_status(True)
        else:
            self._log(f"Failed to start HeadlessX: {error}")
            self._update_server_status(False)
            self.headlessx_process = None
            self.headlessx_managed = False
            messagebox.showerror(
                "Server Error",
                f"Failed to start HeadlessX server:\n\n{error}"
            )

    def _stop_headlessx(self):
        """Stop HeadlessX server if we started it."""
        if self.headlessx_process and self.headlessx_managed:
            self._log("Stopping HeadlessX server...")
            try:
                self.headlessx_process.terminate()
                self.headlessx_process.wait(timeout=5)
            except Exception:
                self.headlessx_process.kill()
            self.headlessx_process = None
            self.headlessx_managed = False
            self._log("HeadlessX server stopped")
            self._update_server_status(False)

    def _update_server_status(self, is_online: bool):
        """Update the server status indicator in UI."""
        if is_online:
            self.server_status_label.config(text="Server: Online", foreground="green")
            self.start_server_button.config(text="Stop Server", state=tk.NORMAL)
            self.start_server_button.config(command=self._stop_headlessx)
        else:
            self.server_status_label.config(text="Server: Offline", foreground="red")
            self.start_server_button.config(text="Start Server", state=tk.NORMAL)
            self.start_server_button.config(command=self._start_headlessx)

    def _on_closing(self):
        """Handle window close event."""
        if self.headlessx_managed and self.headlessx_process:
            if messagebox.askyesno(
                "Stop Server?",
                "HeadlessX server is running.\nDo you want to stop it before closing?"
            ):
                self._stop_headlessx()
        self.root.destroy()

    def run(self):
        """Start the application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()


def main():
    """Entry point for the application."""
    app = CochesnetApp()
    app.run()


if __name__ == "__main__":
    main()
