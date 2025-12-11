"""
Unified Desktop GUI for managing Autocasion and Cochesnet scrapers.

This application combines both scrapers into a single interface with separate tabs
for each platform, plus unified statistics and export functionality.
"""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional, List, Dict
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent, ScrapeResult as AutocasionResult
from scraping.sites.cochesnet.app.scraper_agent import CochesnetScraperAgent, ScrapeResult as CochesnetResult


class UnifiedScraperApp:
    """
    Unified desktop application for managing multiple car listing scrapers.

    Features:
    - Autocasion scraper (by brand)
    - Cochesnet scraper (by year)
    - Unified statistics
    - Combined export
    - Real-time logs
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Car Scrapers - Unified Manager")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)

        # Agent instances
        self.autocasion_agent = AutocasionScraperAgent()
        self.cochesnet_agent = CochesnetScraperAgent()

        # State
        self.is_running = {"autocasion": False, "cochesnet": False}

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
            text="🚗 Car Listing Scrapers - Unified Manager",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Create main notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Autocasion
        autocasion_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(autocasion_frame, text="📋 Autocasion")
        self._create_autocasion_tab(autocasion_frame)

        # Tab 2: Cochesnet
        cochesnet_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(cochesnet_frame, text="🌐 Cochesnet")
        self._create_cochesnet_tab(cochesnet_frame)

        # Tab 3: Unified Statistics
        stats_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(stats_frame, text="📊 Statistics")
        self._create_unified_stats_tab(stats_frame)

        # Tab 4: Export
        export_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(export_frame, text="💾 Export")
        self._create_export_tab(export_frame)

        # Tab 5: Logs
        logs_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(logs_frame, text="📝 Logs")
        self._create_logs_tab(logs_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a scraper to begin")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("Helvetica", 9)
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def _create_autocasion_tab(self, parent):
        """Create the Autocasion scraping tab."""
        # Info label
        info_label = ttk.Label(
            parent,
            text="Autocasion.com - Scraping by Brand",
            font=("Helvetica", 12, "bold")
        )
        info_label.pack(pady=(0, 10))

        # Main layout
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Brand selection
        left_frame = ttk.LabelFrame(content_frame, text="Select Brands", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Scrollable brand list
        brand_container = ttk.Frame(left_frame)
        brand_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(brand_container, width=200)
        scrollbar = ttk.Scrollbar(brand_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Brand checkboxes (common Spanish brands)
        self.autocasion_brand_vars = {}
        brands = [
            "Audi", "BMW", "Citroen", "Dacia", "Fiat", "Ford",
            "Honda", "Hyundai", "Kia", "Land Rover", "Mazda",
            "Mercedes-Benz", "Mini", "Nissan", "Opel", "Peugeot",
            "Renault", "SEAT", "Skoda", "Tesla", "Toyota", "Volkswagen", "Volvo"
        ]

        for brand in brands:
            var = tk.BooleanVar()
            self.autocasion_brand_vars[brand] = var
            ttk.Checkbutton(
                scrollable_frame,
                text=brand,
                variable=var
            ).pack(anchor=tk.W, pady=1)

        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="All", command=self._autocasion_select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="None", command=self._autocasion_deselect_all).pack(side=tk.LEFT, padx=2)

        # Right: Progress and controls
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Progress
        progress_frame = ttk.LabelFrame(right_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.X)

        self.autocasion_progress_var = tk.DoubleVar()
        self.autocasion_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.autocasion_progress_var,
            maximum=100
        )
        self.autocasion_progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.autocasion_progress_label = ttk.Label(progress_frame, text="Ready")
        self.autocasion_progress_label.pack()

        # Controls
        control_frame = ttk.Frame(progress_frame)
        control_frame.pack(pady=(5, 0))

        self.autocasion_start_btn = ttk.Button(
            control_frame,
            text="Start Scraping",
            command=lambda: self._start_scraping("autocasion")
        )
        self.autocasion_start_btn.pack(side=tk.LEFT, padx=2)

        self.autocasion_stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=lambda: self._stop_scraping("autocasion"),
            state=tk.DISABLED
        )
        self.autocasion_stop_btn.pack(side=tk.LEFT, padx=2)

        # Mini stats
        stats_frame = ttk.LabelFrame(right_frame, text="Quick Stats", padding="5")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.autocasion_stats_text = scrolledtext.ScrolledText(
            stats_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.autocasion_stats_text.pack(fill=tk.BOTH, expand=True)

    def _create_cochesnet_tab(self, parent):
        """Create the Cochesnet scraping tab."""
        # Info label
        info_label = ttk.Label(
            parent,
            text="Coches.net - Scraping by Year",
            font=("Helvetica", 12, "bold")
        )
        info_label.pack(pady=(0, 10))

        # Main layout
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Year selection
        left_frame = ttk.LabelFrame(content_frame, text="Select Years (2007-2025)", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Scrollable year list
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

        # Year checkboxes
        self.cochesnet_year_vars = {}
        for year in range(2007, 2026):
            var = tk.BooleanVar()
            self.cochesnet_year_vars[year] = var
            ttk.Checkbutton(
                scrollable_frame,
                text=str(year),
                variable=var
            ).pack(anchor=tk.W, pady=1)

        # Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="All", command=self._cochesnet_select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="None", command=self._cochesnet_deselect_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="2020-2025", command=lambda: self._cochesnet_select_range(2020, 2025)).pack(side=tk.LEFT, padx=2)

        # Right: Progress and controls
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Progress
        progress_frame = ttk.LabelFrame(right_frame, text="Progress", padding="5")
        progress_frame.pack(fill=tk.X)

        self.cochesnet_progress_var = tk.DoubleVar()
        self.cochesnet_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.cochesnet_progress_var,
            maximum=100
        )
        self.cochesnet_progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.cochesnet_progress_label = ttk.Label(progress_frame, text="Ready")
        self.cochesnet_progress_label.pack()

        # Controls
        control_frame = ttk.Frame(progress_frame)
        control_frame.pack(pady=(5, 0))

        self.cochesnet_start_btn = ttk.Button(
            control_frame,
            text="Start Scraping",
            command=lambda: self._start_scraping("cochesnet")
        )
        self.cochesnet_start_btn.pack(side=tk.LEFT, padx=2)

        self.cochesnet_stop_btn = ttk.Button(
            control_frame,
            text="Stop",
            command=lambda: self._stop_scraping("cochesnet"),
            state=tk.DISABLED
        )
        self.cochesnet_stop_btn.pack(side=tk.LEFT, padx=2)

        # Mini stats
        stats_frame = ttk.LabelFrame(right_frame, text="Quick Stats", padding="5")
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.cochesnet_stats_text = scrolledtext.ScrolledText(
            stats_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.cochesnet_stats_text.pack(fill=tk.BOTH, expand=True)

    def _create_unified_stats_tab(self, parent):
        """Create unified statistics tab."""
        title = ttk.Label(
            parent,
            text="Combined Statistics - All Sources",
            font=("Helvetica", 12, "bold")
        )
        title.pack(pady=(0, 10))

        # Stats display
        self.unified_stats_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.unified_stats_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Refresh button
        ttk.Button(
            parent,
            text="Refresh All Statistics",
            command=self._refresh_all_stats
        ).pack()

    def _create_export_tab(self, parent):
        """Create export tab."""
        title = ttk.Label(
            parent,
            text="Export Data from Both Sources",
            font=("Helvetica", 12, "bold")
        )
        title.pack(pady=(0, 20))

        # Export by source
        for source in ["Autocasion", "Cochesnet"]:
            frame = ttk.LabelFrame(parent, text=f"Export {source}", padding="10")
            frame.pack(fill=tk.X, pady=(0, 10))

            btn_frame = ttk.Frame(frame)
            btn_frame.pack()

            ttk.Button(
                btn_frame,
                text="CSV",
                command=lambda s=source.lower(): self._export_source(s, "csv")
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="JSON",
                command=lambda s=source.lower(): self._export_source(s, "json")
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Excel",
                command=lambda s=source.lower(): self._export_source(s, "excel")
            ).pack(side=tk.LEFT, padx=5)

    def _create_logs_tab(self, parent):
        """Create unified logs tab."""
        title = ttk.Label(
            parent,
            text="Activity Logs - All Scrapers",
            font=("Helvetica", 12, "bold")
        )
        title.pack(pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        ttk.Button(
            parent,
            text="Clear Logs",
            command=self._clear_logs
        ).pack()

    def _load_initial_data(self):
        """Load initial data."""
        self._log("Application started")
        self._refresh_all_stats()

    def _autocasion_select_all(self):
        for var in self.autocasion_brand_vars.values():
            var.set(True)

    def _autocasion_deselect_all(self):
        for var in self.autocasion_brand_vars.values():
            var.set(False)

    def _cochesnet_select_all(self):
        for var in self.cochesnet_year_vars.values():
            var.set(True)

    def _cochesnet_deselect_all(self):
        for var in self.cochesnet_year_vars.values():
            var.set(False)

    def _cochesnet_select_range(self, start: int, end: int):
        for year, var in self.cochesnet_year_vars.items():
            var.set(start <= year <= end)

    def _start_scraping(self, source: str):
        """Start scraping for specified source."""
        if source == "autocasion":
            selected_brands = [
                brand for brand, var in self.autocasion_brand_vars.items()
                if var.get()
            ]

            if not selected_brands:
                messagebox.showwarning("No Selection", "Please select at least one brand")
                return

            msg = f"Scrape {len(selected_brands)} brands from Autocasion?"
            if not messagebox.askyesno("Confirm", msg):
                return

            self.is_running["autocasion"] = True
            self.autocasion_start_btn.config(state=tk.DISABLED)
            self.autocasion_stop_btn.config(state=tk.NORMAL)

            threading.Thread(
                target=self._run_autocasion_thread,
                args=(selected_brands,),
                daemon=True
            ).start()

        elif source == "cochesnet":
            selected_years = [
                year for year, var in self.cochesnet_year_vars.items()
                if var.get()
            ]

            if not selected_years:
                messagebox.showwarning("No Selection", "Please select at least one year")
                return

            msg = f"Scrape {len(selected_years)} years from Cochesnet?"
            if not messagebox.askyesno("Confirm", msg):
                return

            self.is_running["cochesnet"] = True
            self.cochesnet_start_btn.config(state=tk.DISABLED)
            self.cochesnet_stop_btn.config(state=tk.NORMAL)

            threading.Thread(
                target=self._run_cochesnet_thread,
                args=(selected_years,),
                daemon=True
            ).start()

    def _stop_scraping(self, source: str):
        """Stop scraping."""
        if source == "autocasion":
            self.autocasion_agent.stop()
        elif source == "cochesnet":
            self.cochesnet_agent.stop()

        self._log(f"{source.capitalize()} - Stop requested")

    def _run_autocasion_thread(self, brands: List[str]):
        """Run Autocasion scraping in thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # TODO: Implement multi-brand scraping
            self._log("Autocasion scraping not yet implemented")
            messagebox.showinfo("Info", "Autocasion multi-brand scraping coming soon")

        except Exception as e:
            self._log(f"Autocasion ERROR: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.root.after(0, lambda: self._scraping_finished("autocasion"))

    def _run_cochesnet_thread(self, years: List[int]):
        """Run Cochesnet scraping in thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.cochesnet_agent.scrape_years(
                    years=years,
                    progress_callback=lambda c, t, m: self._update_progress("cochesnet", c, t, m),
                    log_callback=lambda msg: self._log(f"Cochesnet: {msg}")
                )
            )

            self.root.after(0, lambda: self._show_results("cochesnet", result))

        except Exception as e:
            self._log(f"Cochesnet ERROR: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        finally:
            self.root.after(0, lambda: self._scraping_finished("cochesnet"))

    def _update_progress(self, source: str, current: int, total: int, message: str):
        """Update progress."""
        def update():
            progress = (current / total * 100) if total > 0 else 0

            if source == "autocasion":
                self.autocasion_progress_var.set(progress)
                self.autocasion_progress_label.config(text=f"{message} ({current}/{total})")
            elif source == "cochesnet":
                self.cochesnet_progress_var.set(progress)
                self.cochesnet_progress_label.config(text=f"{message} ({current}/{total})")

            self.status_var.set(f"{source.capitalize()}: {message}")

        self.root.after(0, update)

    def _log(self, message: str):
        """Add log message."""
        def add():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)

        self.root.after(0, add)

    def _clear_logs(self):
        self.log_text.delete(1.0, tk.END)

    def _scraping_finished(self, source: str):
        """Called when scraping finishes."""
        self.is_running[source] = False

        if source == "autocasion":
            self.autocasion_start_btn.config(state=tk.NORMAL)
            self.autocasion_stop_btn.config(state=tk.DISABLED)
            self.autocasion_progress_var.set(0)
            self.autocasion_progress_label.config(text="Finished")
        elif source == "cochesnet":
            self.cochesnet_start_btn.config(state=tk.NORMAL)
            self.cochesnet_stop_btn.config(state=tk.DISABLED)
            self.cochesnet_progress_var.set(0)
            self.cochesnet_progress_label.config(text="Finished")

        self._refresh_all_stats()

    def _show_results(self, source: str, result):
        """Show results."""
        msg = f"""
{source.capitalize()} Scraping Completed!

Total Listings: {result.total_listings}
New: {result.new_listings}
Updated: {result.updated_listings}
Errors: {result.errors}

Duration: {result.duration:.1f}s
        """

        messagebox.showinfo("Results", msg.strip())

    def _refresh_all_stats(self):
        """Refresh all statistics."""
        self._log("Refreshing statistics...")

        # Autocasion stats
        # TODO: Implement
        self.autocasion_stats_text.delete(1.0, tk.END)
        self.autocasion_stats_text.insert(1.0, "Autocasion stats coming soon...")

        # Cochesnet stats
        stats = self.cochesnet_agent.get_statistics()
        text = f"""Total: {stats.get('total_listings', 0):,}

By Year:
"""
        for year in sorted(stats.get('by_year', {}).keys(), reverse=True)[:10]:
            count = stats['by_year'][year]
            text += f"  {year}: {count:,}\n"

        text += f"\nAvg Confidence: {stats.get('avg_confidence', 0):.2f}"

        self.cochesnet_stats_text.delete(1.0, tk.END)
        self.cochesnet_stats_text.insert(1.0, text)

        # Unified stats
        unified_text = f"""
UNIFIED STATISTICS
{"="*60}

AUTOCASION:
  Total: Coming soon...

COCHESNET:
  Total: {stats.get('total_listings', 0):,}
  Perfect Matches: {stats.get('perfect_matches', 0):,} ({stats.get('perfect_pct', 0):.1f}%)

Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """

        self.unified_stats_text.delete(1.0, tk.END)
        self.unified_stats_text.insert(1.0, unified_text.strip())

    def _export_source(self, source: str, format: str):
        """Export data from source."""
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "json": [("JSON files", "*.json")],
            "excel": [("Excel files", "*.xlsx")]
        }

        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=filetypes.get(format, [])
        )

        if not filename:
            return

        try:
            if source == "cochesnet":
                self.cochesnet_agent.export_data(filename, format)
            else:
                # TODO: Implement autocasion export
                messagebox.showinfo("Info", "Autocasion export coming soon")
                return

            messagebox.showinfo("Success", f"Exported to:\n{filename}")
            self._log(f"Exported {source} to {format}: {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{e}")
            self._log(f"Export ERROR: {e}")

    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Entry point."""
    app = UnifiedScraperApp()
    app.run()


if __name__ == "__main__":
    main()
