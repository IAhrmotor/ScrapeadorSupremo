"""Desktop GUI application for Autocasion scraper using tkinter."""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent, ScrapeResult


class AutocasionApp:
    """
    Desktop GUI application for Autocasion scraping.

    Features:
    - Brand selection with checkboxes
    - Progress tracking
    - Real-time log output
    - Database statistics
    - Export functionality
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Autocasion Scraper")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Agent instance
        self.agent = AutocasionScraperAgent()

        # State
        self.is_running = False
        self.selected_brands = []

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
            text="Autocasion.com Scraper",
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
        # Left panel - Brand selection
        left_frame = ttk.LabelFrame(parent, text="Select Brands", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Brand list with scrollbar
        brand_container = ttk.Frame(left_frame)
        brand_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(brand_container, width=200)
        scrollbar = ttk.Scrollbar(brand_container, orient="vertical", command=canvas.yview)
        self.brands_frame = ttk.Frame(canvas)

        self.brands_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.brands_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Brand checkboxes will be added in _load_initial_data
        self.brand_vars = {}

        # Select all / none buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Select All", command=self._select_all_brands).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Select None", command=self._select_no_brands).pack(side=tk.LEFT, padx=2)

        # Right panel - Controls and log
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Controls
        controls_frame = ttk.LabelFrame(right_frame, text="Controls", padding="5")
        controls_frame.pack(fill=tk.X)

        # Max pages
        pages_frame = ttk.Frame(controls_frame)
        pages_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pages_frame, text="Max pages per brand:").pack(side=tk.LEFT)
        self.pages_var = tk.StringVar(value="5")
        self.pages_spin = ttk.Spinbox(pages_frame, from_=1, to=100, width=5, textvariable=self.pages_var)
        self.pages_spin.pack(side=tk.LEFT, padx=5)

        # All pages checkbox
        self.all_pages_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pages_frame,
            text="ALL PAGES",
            variable=self.all_pages_var,
            command=self._toggle_all_pages
        ).pack(side=tk.LEFT, padx=10)

        # Parallel mode options
        parallel_frame = ttk.LabelFrame(controls_frame, text="Modo de Scrapeo", padding="5")
        parallel_frame.pack(fill=tk.X, pady=5)

        self.parallel_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            parallel_frame,
            text="Secuencial (1 marca a la vez)",
            variable=self.parallel_var,
            value=False
        ).pack(anchor=tk.W)

        ttk.Radiobutton(
            parallel_frame,
            text="Paralelo (mas rapido)",
            variable=self.parallel_var,
            value=True
        ).pack(anchor=tk.W)

        # Workers selector
        workers_frame = ttk.Frame(parallel_frame)
        workers_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(workers_frame, text="Workers paralelos:").pack(side=tk.LEFT)
        self.workers_var = tk.IntVar(value=3)
        workers_spinbox = ttk.Spinbox(
            workers_frame,
            from_=2,
            to=5,
            width=5,
            textvariable=self.workers_var
        )
        workers_spinbox.pack(side=tk.LEFT, padx=5)
        ttk.Label(workers_frame, text="(2-5 recomendado)").pack(side=tk.LEFT)

        # Options
        self.save_to_db_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls_frame,
            text="Save to Supabase",
            variable=self.save_to_db_var
        ).pack(anchor=tk.W)

        # Action buttons
        action_frame = ttk.Frame(controls_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(
            action_frame,
            text="Start Scraping",
            command=self._start_scraping
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            action_frame,
            text="Stop",
            command=self._stop_scraping,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        ttk.Button(
            action_frame,
            text="Scrape from Objetivos",
            command=self._scrape_from_objetivos
        ).pack(side=tk.LEFT, padx=2)

        # Progress
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            controls_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(controls_frame, text="")
        self.progress_label.pack()

        # Log output
        log_frame = ttk.LabelFrame(right_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(log_frame, text="Clear Log", command=self._clear_log).pack(anchor=tk.E, pady=(5, 0))

    def _create_stats_tab(self, parent):
        """Create the statistics tab."""
        # Stats display
        stats_frame = ttk.LabelFrame(parent, text="Database Statistics", padding="10")
        stats_frame.pack(fill=tk.X)

        self.stats_labels = {}
        stats_items = [
            ("total_listings", "Total listings in DB:"),
            ("total_objetivos", "Total objetivos:"),
            ("brands_available", "Available brands:"),
        ]

        for key, label in stats_items:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label, width=25).pack(side=tk.LEFT)
            self.stats_labels[key] = ttk.Label(frame, text="--", font=("Helvetica", 10, "bold"))
            self.stats_labels[key].pack(side=tk.LEFT)

        ttk.Button(stats_frame, text="Refresh Stats", command=self._refresh_stats).pack(pady=10)

        # Objetivos table
        obj_frame = ttk.LabelFrame(parent, text="Objetivos Status", padding="10")
        obj_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        columns = ("marca", "attempts", "status", "last_scraped")
        self.obj_tree = ttk.Treeview(obj_frame, columns=columns, show="headings", height=15)

        self.obj_tree.heading("marca", text="Marca")
        self.obj_tree.heading("attempts", text="Attempts")
        self.obj_tree.heading("status", text="Status")
        self.obj_tree.heading("last_scraped", text="Last Scraped")

        self.obj_tree.column("marca", width=150)
        self.obj_tree.column("attempts", width=80)
        self.obj_tree.column("status", width=100)
        self.obj_tree.column("last_scraped", width=150)

        scrollbar = ttk.Scrollbar(obj_frame, orient=tk.VERTICAL, command=self.obj_tree.yview)
        self.obj_tree.configure(yscrollcommand=scrollbar.set)

        self.obj_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_export_tab(self, parent):
        """Create the export tab."""
        export_frame = ttk.LabelFrame(parent, text="Export Data", padding="10")
        export_frame.pack(fill=tk.X)

        # Format selection
        format_frame = ttk.Frame(export_frame)
        format_frame.pack(fill=tk.X, pady=5)
        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT)
        self.export_format = tk.StringVar(value="json")
        ttk.Radiobutton(format_frame, text="JSON", variable=self.export_format, value="json").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="CSV", variable=self.export_format, value="csv").pack(side=tk.LEFT, padx=10)

        # Export button
        ttk.Button(
            export_frame,
            text="Export to File...",
            command=self._export_data
        ).pack(pady=10)

        # Info
        info_text = """
Export Options:
- JSON: Full data with nested structures
- CSV: Flat format, suitable for Excel

The export will include all listings currently in the autocasion table.
        """
        ttk.Label(export_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

    def _load_initial_data(self):
        """Load initial data."""
        # Load brands
        brands = self.agent.site.get_brands_list()
        for brand in brands:
            var = tk.BooleanVar(value=False)
            self.brand_vars[brand] = var
            cb = ttk.Checkbutton(self.brands_frame, text=brand, variable=var)
            cb.pack(anchor=tk.W)

        # Load stats
        self._refresh_stats()

    def _refresh_stats(self):
        """Refresh statistics display."""
        try:
            stats = self.agent.get_stats()

            for key, label in self.stats_labels.items():
                value = stats.get(key, "--")
                label.config(text=str(value))

            # Refresh objetivos table
            for item in self.obj_tree.get_children():
                self.obj_tree.delete(item)

            objetivos = self.agent.supabase.get_objetivos("autocasion", limit=50)
            for obj in objetivos:
                self.obj_tree.insert("", tk.END, values=(
                    obj.get("marca", "?"),
                    obj.get("scraping_attempts", 0),
                    obj.get("last_status", "pending"),
                    obj.get("last_scraped", "")[:19] if obj.get("last_scraped") else ""
                ))

            self.status_var.set("Stats refreshed")

        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def _select_all_brands(self):
        """Select all brands."""
        for var in self.brand_vars.values():
            var.set(True)

    def _select_no_brands(self):
        """Deselect all brands."""
        for var in self.brand_vars.values():
            var.set(False)

    def _toggle_all_pages(self):
        """Toggle all pages mode - disable/enable spinbox."""
        if self.all_pages_var.get():
            self.pages_spin.config(state=tk.DISABLED)
            self.status_var.set("ALL PAGES mode: Will scrape every page for each brand")
        else:
            self.pages_spin.config(state=tk.NORMAL)
            self.status_var.set("Ready")

    def _log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def _clear_log(self):
        """Clear log output."""
        self.log_text.delete(1.0, tk.END)

    def _get_selected_brands(self) -> list:
        """Get list of selected brands."""
        return [brand for brand, var in self.brand_vars.items() if var.get()]

    def _start_scraping(self):
        """Start scraping selected brands."""
        brands = self._get_selected_brands()
        if not brands:
            messagebox.showwarning("No Selection", "Please select at least one brand")
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)

        # Run in background thread
        thread = threading.Thread(
            target=self._run_scraping,
            args=(brands,),
            daemon=True
        )
        thread.start()

    def _run_scraping(self, brands: list):
        """Run scraping in background thread."""
        # max_pages = 0 means ALL PAGES
        if self.all_pages_var.get():
            max_pages = 0
            self._log(f"Mode: ALL PAGES (auto-detect)")
        else:
            max_pages = int(self.pages_var.get())
        save_to_db = self.save_to_db_var.get()
        parallel = self.parallel_var.get()
        max_workers = self.workers_var.get()
        total = len(brands)

        # Thread-safe log callback for GUI
        def gui_log(msg: str):
            self.root.after(0, lambda m=msg: self._log(m))

        # Thread-safe progress callback for GUI
        def gui_progress(current: int, total: int, message: str):
            progress = (current / total * 100) if total > 0 else 0
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
            self.root.after(0, lambda m=message: self.progress_label.config(text=m))

        # Run async scrape
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            if parallel and len(brands) > 1:
                # PARALLEL MODE
                self._log(f"Starting PARALLEL scrape of {total} brands with {max_workers} workers...")
                results = loop.run_until_complete(
                    self.agent.scrape_batch_parallel(
                        marcas=brands,
                        max_pages=max_pages,
                        save_to_db=save_to_db,
                        max_workers=max_workers,
                        progress_callback=gui_progress,
                        log_callback=gui_log
                    )
                )
            else:
                # SEQUENTIAL MODE
                self._log(f"Starting SEQUENTIAL scrape of {total} brands...")
                results = []
                was_stopped = False

                for i, brand in enumerate(brands):
                    if not self.is_running:
                        self._log("Scraping stopped by user")
                        was_stopped = True
                        break

                    progress = (i / total) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda b=brand, n=i+1, t=total: self.progress_label.config(
                        text=f"Scraping {b} ({n}/{t})"
                    ))

                    self._log(f"[{i+1}/{total}] Scraping {brand}...")

                    result = loop.run_until_complete(
                        self.agent.scrape_marca(brand, max_pages, save_to_db, log_callback=gui_log)
                    )
                    results.append(result)

                    self._log(f"  DONE {brand}: {result.total_listings} listings, "
                             f"{result.pages_scraped} pages, {result.duration_seconds:.1f}s")

                    if result.errors:
                        for err in result.errors:
                            self._log(f"  ERROR: {err}")

                if was_stopped:
                    self.root.after(0, lambda: self.progress_label.config(text="Stopped"))
                    self._log(f"\nScraping stopped: {len(results)} brands completed")
                    self.root.after(0, self._scraping_complete)
                    return

            # Complete
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.progress_label.config(text="Complete"))
            total_listings = sum(r.total_listings for r in results)
            total_saved = sum(r.saved_to_db for r in results)
            mode_str = f"PARALLEL ({max_workers} workers)" if parallel else "SEQUENTIAL"
            self._log(f"\nScraping complete ({mode_str}): {total_listings} listings, {total_saved} saved")

        except Exception as e:
            self._log(f"Error during scraping: {e}")
        finally:
            loop.close()

        self.root.after(0, self._scraping_complete)

    def _scraping_complete(self):
        """Called when scraping completes."""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Scraping complete")
        self._refresh_stats()

    def _stop_scraping(self):
        """Stop current scraping operation."""
        self.is_running = False
        self.agent.stop()  # Signal agent to stop
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopping...")
        self._log("Stop requested by user")

    def _scrape_from_objetivos(self):
        """Scrape brands from objetivos table."""
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        thread = threading.Thread(
            target=self._run_objetivos_scraping,
            daemon=True
        )
        thread.start()

    def _run_objetivos_scraping(self):
        """Run objetivos scraping in background."""
        # max_pages = 0 means ALL PAGES
        if self.all_pages_var.get():
            max_pages = 0
        else:
            max_pages = int(self.pages_var.get())

        parallel = self.parallel_var.get()
        max_workers = self.workers_var.get()

        self._log("Fetching objetivos from database...")

        try:
            # Fetch objetivos
            objetivos = self.agent.supabase.get_pending_objetivos("autocasion", limit=10)

            if not objetivos:
                self._log("No pending objetivos found")
                self.root.after(0, self._scraping_complete)
                return

            brands = [obj["marca"] for obj in objetivos]
            self._log(f"Found {len(brands)} pending objetivos: {', '.join(brands)}")

            # Thread-safe callbacks for GUI
            def gui_log(msg: str):
                self.root.after(0, lambda m=msg: self._log(m))

            def gui_progress(current: int, total: int, message: str):
                progress = (current / total * 100) if total > 0 else 0
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda m=message: self.progress_label.config(text=m))

            save_to_db = self.save_to_db_var.get()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                if parallel and len(brands) > 1:
                    # PARALLEL MODE
                    self._log(f"Starting PARALLEL objetivos scrape with {max_workers} workers...")
                    results = loop.run_until_complete(
                        self.agent.scrape_batch_parallel(
                            marcas=brands,
                            max_pages=max_pages,
                            save_to_db=save_to_db,
                            max_workers=max_workers,
                            progress_callback=gui_progress,
                            log_callback=gui_log
                        )
                    )
                else:
                    # SEQUENTIAL MODE
                    results = []
                    total = len(brands)

                    for i, brand in enumerate(brands):
                        if not self.is_running:
                            self._log("Scraping stopped by user")
                            break

                        progress = (i / total) * 100
                        self.root.after(0, lambda p=progress: self.progress_var.set(p))
                        self.root.after(0, lambda b=brand, n=i+1, t=total: self.progress_label.config(
                            text=f"Scraping {b} ({n}/{t})"
                        ))

                        self._log(f"[{i+1}/{total}] Scraping {brand}...")

                        result = loop.run_until_complete(
                            self.agent.scrape_marca(brand, max_pages, save_to_db, log_callback=gui_log)
                        )
                        results.append(result)

                        self._log(f"  DONE {brand}: {result.total_listings} listings")

                # Complete
                self.root.after(0, lambda: self.progress_var.set(100))
                self.root.after(0, lambda: self.progress_label.config(text="Complete"))
                total_listings = sum(r.total_listings for r in results)
                total_saved = sum(r.saved_to_db for r in results)
                mode_str = f"PARALLEL ({max_workers} workers)" if parallel else "SEQUENTIAL"
                self._log(f"\nObjetivos scraping complete ({mode_str}): {total_listings} listings, {total_saved} saved")

            finally:
                loop.close()

        except Exception as e:
            self._log(f"Error: {e}")

        self.root.after(0, self._scraping_complete)

    def _export_data(self):
        """Export data to file."""
        format = self.export_format.get()
        ext = ".json" if format == "json" else ".csv"

        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{format.upper()} files", f"*{ext}"), ("All files", "*.*")],
            initialfilename=f"autocasion_export_{datetime.now().strftime('%Y%m%d')}{ext}"
        )

        if not filename:
            return

        try:
            from scraping.sites.autocasion.app.runner import AutocasionRunner
            runner = AutocasionRunner()
            runner.run_export(filename, format)
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def run(self):
        """Run the application."""
        self.root.mainloop()

    def close(self):
        """Clean up on close."""
        self.agent.close()


def main():
    """Main entry point for GUI."""
    app = AutocasionApp()
    try:
        app.run()
    finally:
        app.close()


if __name__ == "__main__":
    main()
