"""Desktop GUI application for OcasionPlus scraper using tkinter."""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional, List
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.ocasionplus.app.scraper_agent import OcasionPlusScraperAgent, ScrapeResult


class OcasionPlusApp:
    """
    Desktop GUI application for OcasionPlus scraping.

    Features:
    - Year range selection (2007-2025)
    - Scroll iterations configuration
    - HeadlessX / Playwright method selection
    - Progress tracking
    - Real-time log output
    - Database statistics
    - Export functionality
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OcasionPlus Scraper")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Set app icon color scheme (blue theme for OcasionPlus)
        style = ttk.Style()
        style.theme_use('clam')

        # Agent instance (will be created based on settings)
        self.agent: Optional[OcasionPlusScraperAgent] = None

        # State
        self.is_running = False
        self.stop_requested = False

        # Create UI
        self._create_widgets()
        self._load_initial_data()

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            title_frame,
            text="OcasionPlus Scraper",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Method indicator
        self.method_label = ttk.Label(
            title_frame,
            text="[HeadlessX]",
            font=("Helvetica", 10),
            foreground="green"
        )
        self.method_label.pack(side=tk.RIGHT, padx=10)

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
        # Top config panel
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Year range
        year_frame = ttk.Frame(config_frame)
        year_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(year_frame, text="Year Range:").pack(side=tk.LEFT)

        self.year_from_var = tk.IntVar(value=2007)
        year_from_spin = ttk.Spinbox(
            year_frame,
            from_=2000,
            to=2025,
            width=6,
            textvariable=self.year_from_var
        )
        year_from_spin.pack(side=tk.LEFT, padx=(10, 5))

        ttk.Label(year_frame, text="to").pack(side=tk.LEFT)

        self.year_to_var = tk.IntVar(value=2025)
        year_to_spin = ttk.Spinbox(
            year_frame,
            from_=2000,
            to=2025,
            width=6,
            textvariable=self.year_to_var
        )
        year_to_spin.pack(side=tk.LEFT, padx=(5, 20))

        # Quick year buttons
        ttk.Button(
            year_frame,
            text="2020-2025",
            command=lambda: self._set_years(2020, 2025)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            year_frame,
            text="2015-2025",
            command=lambda: self._set_years(2015, 2025)
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            year_frame,
            text="All",
            command=lambda: self._set_years(2007, 2025)
        ).pack(side=tk.LEFT, padx=2)

        # Row 2: Scroll iterations and method
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(options_frame, text="Max Scroll Iterations:").pack(side=tk.LEFT)

        self.iterations_var = tk.IntVar(value=200)
        iterations_spin = ttk.Spinbox(
            options_frame,
            from_=5,
            to=500,
            width=6,
            textvariable=self.iterations_var
        )
        iterations_spin.pack(side=tk.LEFT, padx=(10, 10))

        # Quick iteration buttons
        ttk.Button(
            options_frame,
            text="50",
            command=lambda: self.iterations_var.set(50),
            width=4
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            options_frame,
            text="100",
            command=lambda: self.iterations_var.set(100),
            width=4
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            options_frame,
            text="MAX",
            command=lambda: self.iterations_var.set(500),
            width=5
        ).pack(side=tk.LEFT, padx=(2, 20))

        # Method selection
        ttk.Label(options_frame, text="Method:").pack(side=tk.LEFT)

        self.method_var = tk.StringVar(value="headlessx")
        ttk.Radiobutton(
            options_frame,
            text="HeadlessX (Anti-detection)",
            variable=self.method_var,
            value="headlessx",
            command=self._on_method_changed
        ).pack(side=tk.LEFT, padx=(10, 5))

        ttk.Radiobutton(
            options_frame,
            text="Playwright (Fallback)",
            variable=self.method_var,
            value="playwright",
            command=self._on_method_changed
        ).pack(side=tk.LEFT, padx=5)

        # Row 3: Save to DB option
        db_frame = ttk.Frame(config_frame)
        db_frame.pack(fill=tk.X, pady=(5, 0))

        self.save_to_db_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            db_frame,
            text="Save to Database (Supabase)",
            variable=self.save_to_db_var
        ).pack(side=tk.LEFT)

        self.headless_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            db_frame,
            text="Headless Mode (no visible browser)",
            variable=self.headless_var
        ).pack(side=tk.LEFT, padx=(20, 0))

        # Progress section
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Progress label
        self.progress_label = ttk.Label(
            progress_frame,
            text="Ready to scrape",
            font=("Helvetica", 10)
        )
        self.progress_label.pack()

        # Control buttons
        control_frame = ttk.Frame(progress_frame)
        control_frame.pack(pady=(10, 0))

        self.start_button = ttk.Button(
            control_frame,
            text="Start Scraping",
            command=self._start_scraping,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Full scrape button (max iterations, all years)
        self.full_scrape_button = ttk.Button(
            control_frame,
            text="SCRAPEO TOTAL",
            command=self._start_full_scraping,
            width=18
        )
        self.full_scrape_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop",
            command=self._stop_scraping,
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Logs section
        logs_frame = ttk.LabelFrame(parent, text="Logs", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=12,
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

        # Info section
        info_frame = ttk.LabelFrame(stats_container, text="About OcasionPlus Scraper", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_text = """
OcasionPlus.com uses an INFINITE SCROLL pattern:
- Single URL with all cars loaded dynamically
- Scroll to bottom repeatedly to load more listings
- Uses HeadlessX for anti-detection (fingerprint spoofing, behavioral simulation)
- Falls back to Playwright if HeadlessX fails
- Marca/Modelo validation against database reference table
        """

        ttk.Label(
            info_frame,
            text=info_text.strip(),
            justify=tk.LEFT,
            font=("Helvetica", 9)
        ).pack(anchor=tk.W)

        # Stats display
        stats_display_frame = ttk.LabelFrame(stats_container, text="Database Statistics", padding="10")
        stats_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.stats_text = scrolledtext.ScrolledText(
            stats_display_frame,
            height=15,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)

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
- CSV: Comma-separated values (Excel compatible)
- JSON: JavaScript Object Notation (API compatible)
- Excel: Microsoft Excel format (.xlsx)

The export will include all scraped listings from the OcasionPlus table.

Fields exported:
- listing_id, url, marca, modelo, version
- potencia_cv, precio_contado, precio_financiado, cuota_mensual
- year, kilometros, combustible, transmision
- etiqueta_ambiental, ubicacion, imagen_url
        """

        ttk.Label(
            export_container,
            text=info_text.strip(),
            justify=tk.LEFT,
            font=("Helvetica", 9)
        ).pack(pady=(0, 20), anchor=tk.W)

        # Export buttons
        button_frame = ttk.Frame(export_container)
        button_frame.pack()

        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: self._export_data("csv"),
            width=20
        ).pack(pady=5)

        ttk.Button(
            button_frame,
            text="Export to JSON",
            command=lambda: self._export_data("json"),
            width=20
        ).pack(pady=5)

        ttk.Button(
            button_frame,
            text="Export to Excel",
            command=lambda: self._export_data("excel"),
            width=20
        ).pack(pady=5)

    def _load_initial_data(self):
        """Load initial data when app starts."""
        self._log("OcasionPlus Scraper initialized")
        self._log("Using HeadlessX for anti-detection")
        self._refresh_stats()

    def _set_years(self, year_from: int, year_to: int):
        """Set year range."""
        self.year_from_var.set(year_from)
        self.year_to_var.set(year_to)
        self._log(f"Year range set: {year_from} - {year_to}")

    def _on_method_changed(self):
        """Called when scraping method changes."""
        method = self.method_var.get()
        if method == "headlessx":
            self.method_label.config(text="[HeadlessX]", foreground="green")
            self._log("Method changed to HeadlessX (anti-detection)")
        else:
            self.method_label.config(text="[Playwright]", foreground="orange")
            self._log("Method changed to Playwright (fallback)")

    def _start_full_scraping(self):
        """Start a full scrape using segmented strategy for all 14,000+ cars."""
        if self.is_running:
            messagebox.showwarning(
                "Already Running",
                "Scraping is already in progress."
            )
            return

        # Set maximum settings for full scrape
        self.save_to_db_var.set(True)
        self.headless_var.set(True)

        # Confirm full segmented scrape
        msg = """SCRAPEO TOTAL SEGMENTADO de OcasionPlus

Estrategia: Divide el scrapeo en 7 segmentos por anio
para obtener los 14,000+ coches disponibles.

Segmentos:
- 2007-2010, 2011-2014, 2015-2017
- 2018-2019, 2020-2021, 2022-2023, 2024-2025

Configuracion:
- 100 iteraciones por segmento
- 10 segundos de delay entre segmentos
- Guardar en BD: Si

Tiempo estimado: 35-50 minutos
Continuar?"""

        if not messagebox.askyesno("Scrapeo Total Segmentado", msg):
            return

        # Start the segmented scraping process
        self._execute_segmented_scraping()

    def _start_scraping(self):
        """Start the scraping process."""
        if self.is_running:
            messagebox.showwarning(
                "Already Running",
                "Scraping is already in progress."
            )
            return

        # Validate year range
        year_from = self.year_from_var.get()
        year_to = self.year_to_var.get()

        if year_from > year_to:
            messagebox.showerror(
                "Invalid Range",
                "Start year must be less than or equal to end year."
            )
            return

        # Confirm
        iterations = self.iterations_var.get()
        method = self.method_var.get()
        save_db = self.save_to_db_var.get()

        msg = f"""Start scraping OcasionPlus?

Year Range: {year_from} - {year_to}
Max Iterations: {iterations}
Method: {method.upper()}
Save to DB: {'Yes' if save_db else 'No'}
"""

        if not messagebox.askyesno("Confirm", msg):
            return

        self._execute_scraping()

    def _execute_scraping(self):
        """Execute the scraping with current settings."""
        self.is_running = True
        self.stop_requested = False
        self.start_button.config(state=tk.DISABLED)
        self.full_scrape_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)

        # Create agent with selected method
        method = self.method_var.get()
        use_headlessx = (method == "headlessx")
        headless = self.headless_var.get()
        self.agent = OcasionPlusScraperAgent(
            headless=headless,
            use_headlessx=use_headlessx
        )

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

            year_from = self.year_from_var.get()
            year_to = self.year_to_var.get()
            max_iterations = self.iterations_var.get()
            save_to_db = self.save_to_db_var.get()

            self._log(f"\nStarting scrape: {year_from}-{year_to}")
            self._log(f"Max iterations: {max_iterations}")
            self._log(f"Mode: PROGRESSIVE SAVE (every 10 iterations)")

            # Run scraping with progressive saves
            result = loop.run_until_complete(
                self.agent.scrape_all_progressive(
                    max_iterations=max_iterations,
                    save_to_db=save_to_db,
                    year_from=year_from,
                    year_to=year_to,
                    save_every=10,  # Save every 10 iterations
                    log_callback=self._log
                )
            )

            # Show results
            self.root.after(0, lambda: self._show_results(result))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

        finally:
            self.root.after(0, self._scraping_finished)

    def _execute_segmented_scraping(self):
        """Execute the segmented scraping strategy."""
        self.is_running = True
        self.stop_requested = False
        self.start_button.config(state=tk.DISABLED)
        self.full_scrape_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)

        # Create agent
        headless = self.headless_var.get()
        self.agent = OcasionPlusScraperAgent(headless=headless, use_headlessx=True)

        # Start segmented scraping in background thread
        threading.Thread(
            target=self._run_segmented_scraping_thread,
            daemon=True
        ).start()

    def _run_segmented_scraping_thread(self):
        """Run segmented scraping in a background thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self._log("\nStarting SEGMENTED scraping...")
            self._log("This will scrape 7 year segments to get all 14,000+ cars")

            # Run segmented scraping
            result = loop.run_until_complete(
                self.agent.scrape_by_segments(
                    max_iterations_per_segment=100,
                    save_to_db=True,
                    delay_between_segments=10.0,
                    log_callback=self._log
                )
            )

            # Show results
            self.root.after(0, lambda: self._show_segmented_results(result))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

        finally:
            self.root.after(0, self._scraping_finished)

    def _show_segmented_results(self, result):
        """Show segmented scraping results."""
        msg = f"""
SCRAPEO SEGMENTADO COMPLETADO!

Total Listings Scraped: {result.total_listings:,}
Total Saved to DB: {result.total_saved:,}
Duplicates: {result.total_duplicates:,}

Segments Completed: {result.segments_completed}/7
Segments Failed: {result.segments_failed}

Duration: {result.duration_seconds:.1f} seconds ({result.duration_seconds/60:.1f} min)
"""

        if result.errors:
            msg += f"\nWarnings/Errors: {len(result.errors)}"

        messagebox.showinfo("Segmented Scraping Results", msg.strip())
        self._log("Segmented scraping completed successfully")

    def _stop_scraping(self):
        """Stop the scraping process."""
        if messagebox.askyesno("Confirm", "Stop scraping?"):
            self.stop_requested = True
            self._log("Stop requested... (will stop after current operation)")

    def _log(self, message: str):
        """Add message to log."""
        def add_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Clean up message (remove extra newlines at start)
            msg = message.lstrip('\n')
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
            self.log_text.see(tk.END)

        self.root.after(0, add_log)

    def _clear_logs(self):
        """Clear the log text."""
        self.log_text.delete(1.0, tk.END)

    def _scraping_finished(self):
        """Called when scraping finishes."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.full_scrape_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set(0)
        self.progress_label.config(text="Scraping finished")
        self._refresh_stats()

    def _show_results(self, result: ScrapeResult):
        """Show scraping results."""
        msg = f"""
Scraping Completed!

Total Listings Found: {result.total_listings}
Saved to Database: {result.saved_to_db}
Scroll Iterations: {result.scroll_iterations}
Method Used: {result.method_used.upper()}

Duration: {result.duration_seconds:.1f} seconds
"""

        if result.errors:
            msg += f"\nWarnings/Errors: {len(result.errors)}"

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
            # Create temporary agent to get stats
            if self.agent is None:
                self.agent = OcasionPlusScraperAgent()

            stats = self.agent.get_stats()

            stats_text = f"""
OCASIONPLUS DATABASE STATISTICS
{'='*50}

Total Listings: {stats.get('total_listings', 0):,}

Scraping Pattern: {stats.get('scraping_pattern', 'infinite_scroll')}
Current Method: {stats.get('method', 'headlessx').upper()}

{'='*50}

Site Info:
- URL: https://www.ocasionplus.com/coches-segunda-mano
- Pattern: Infinite Scroll
- Anti-detection: HeadlessX with fingerprint spoofing

Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text.strip())

            self._log("Statistics refreshed")

        except Exception as e:
            self._log(f"Error refreshing stats: {e}")
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, f"Error loading statistics:\n{e}")

    def _export_data(self, format: str):
        """Export data to file."""
        # File dialog
        filetypes = {
            "csv": [("CSV files", "*.csv")],
            "json": [("JSON files", "*.json")],
            "excel": [("Excel files", "*.xlsx")]
        }

        default_name = f"ocasionplus_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format}" if format != "excel" else ".xlsx",
            filetypes=filetypes.get(format, [("All files", "*.*")]),
            initialfile=default_name
        )

        if not filename:
            return

        try:
            self._log(f"Exporting to {format.upper()}...")

            # Get data from Supabase
            if self.agent is None:
                self.agent = OcasionPlusScraperAgent()

            # Fetch all data
            result = self.agent.supabase.client.table('ocasionplus').select('*').execute()
            data = result.data

            if not data:
                messagebox.showwarning("No Data", "No data to export.")
                return

            if format == "csv":
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

            elif format == "json":
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            elif format == "excel":
                try:
                    import pandas as pd
                    df = pd.DataFrame(data)
                    df.to_excel(filename, index=False)
                except ImportError:
                    messagebox.showerror(
                        "Missing Dependency",
                        "Excel export requires pandas and openpyxl.\n\n"
                        "Install with: pip install pandas openpyxl"
                    )
                    return

            self._log(f"Export completed: {filename}")
            messagebox.showinfo("Success", f"Data exported to:\n{filename}\n\n{len(data)} records")

        except Exception as e:
            self._log(f"Export failed: {e}")
            messagebox.showerror("Error", f"Export failed:\n\n{e}")

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point for the application."""
    app = OcasionPlusApp()
    app.run()


if __name__ == "__main__":
    main()
