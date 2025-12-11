"""Desktop GUI application for Clicars scraper using tkinter."""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from scraping.sites.clicars.app.scraper_agent import ClicarsScraperAgent, ScrapeResult


class ClicarsApp:
    """
    Desktop GUI application for Clicars scraping.

    Features:
    - Scroll iterations configuration
    - Headless mode toggle
    - Progress tracking
    - Real-time log output
    - Database statistics
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Clicars Scraper")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Set app icon color scheme (orange theme for Clicars)
        style = ttk.Style()
        style.theme_use('clam')

        # Agent instance
        self.agent: Optional[ClicarsScraperAgent] = None

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
            text="Clicars Scraper",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Method indicator
        self.method_label = ttk.Label(
            title_frame,
            text="[Playwright]",
            font=("Helvetica", 10),
            foreground="orange"
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
        notebook.add(stats_frame, text="Estadisticas")
        self._create_stats_tab(stats_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Listo")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def _create_scrape_tab(self, parent):
        """Create the scraping configuration tab."""
        # Configuration frame
        config_frame = ttk.LabelFrame(parent, text="Configuracion", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Iterations
        iter_frame = ttk.Frame(config_frame)
        iter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(iter_frame, text="Iteraciones de scroll:").pack(side=tk.LEFT)
        self.iterations_var = tk.StringVar(value="200")
        iterations_spin = ttk.Spinbox(
            iter_frame,
            from_=10,
            to=500,
            textvariable=self.iterations_var,
            width=10
        )
        iterations_spin.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(iter_frame, text="(~12 coches por iteracion)").pack(side=tk.LEFT, padx=(10, 0))

        # Headless mode
        headless_frame = ttk.Frame(config_frame)
        headless_frame.pack(fill=tk.X, pady=5)

        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(
            headless_frame,
            text="Modo headless (navegador invisible)",
            variable=self.headless_var
        )
        headless_check.pack(side=tk.LEFT)

        # Save to DB
        db_frame = ttk.Frame(config_frame)
        db_frame.pack(fill=tk.X, pady=5)

        self.save_db_var = tk.BooleanVar(value=True)
        save_db_check = ttk.Checkbutton(
            db_frame,
            text="Guardar en Supabase",
            variable=self.save_db_var
        )
        save_db_check.pack(side=tk.LEFT)

        # Presets
        preset_frame = ttk.Frame(config_frame)
        preset_frame.pack(fill=tk.X, pady=10)

        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT)

        ttk.Button(
            preset_frame,
            text="Rapido (50)",
            command=lambda: self.iterations_var.set("50")
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_frame,
            text="Normal (200)",
            command=lambda: self.iterations_var.set("200")
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_frame,
            text="Completo (400)",
            command=lambda: self.iterations_var.set("400")
        ).pack(side=tk.LEFT, padx=5)

        # Buttons frame
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(
            btn_frame,
            text="Iniciar Scraping",
            command=self._start_scraping
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            btn_frame,
            text="Detener",
            command=self._stop_scraping,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Progreso", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="0 / 0 iteraciones")
        self.progress_label.pack()

        # Log frame
        log_frame = ttk.LabelFrame(parent, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure log colors
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("error", foreground="red")

    def _create_stats_tab(self, parent):
        """Create the statistics tab."""
        # Stats display
        stats_frame = ttk.LabelFrame(parent, text="Estadisticas de Base de Datos", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # Stats labels
        self.stats_labels = {}

        stats_items = [
            ("total", "Total en Clicars:"),
            ("last_scrape", "Ultimo scrapeo:"),
        ]

        for key, label_text in stats_items:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label_text, width=20).pack(side=tk.LEFT)
            self.stats_labels[key] = ttk.Label(frame, text="--")
            self.stats_labels[key].pack(side=tk.LEFT)

        # Refresh button
        ttk.Button(
            stats_frame,
            text="Actualizar Estadisticas",
            command=self._refresh_stats
        ).pack(pady=10)

        # Last scrape results
        results_frame = ttk.LabelFrame(parent, text="Ultimo Resultado", padding="10")
        results_frame.pack(fill=tk.X)

        self.result_labels = {}

        result_items = [
            ("listings", "Listings encontrados:"),
            ("saved", "Guardados en DB:"),
            ("duration", "Duracion:"),
            ("method", "Metodo:"),
        ]

        for key, label_text in result_items:
            frame = ttk.Frame(results_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label_text, width=20).pack(side=tk.LEFT)
            self.result_labels[key] = ttk.Label(frame, text="--")
            self.result_labels[key].pack(side=tk.LEFT)

    def _load_initial_data(self):
        """Load initial statistics."""
        self._refresh_stats()

    def _refresh_stats(self):
        """Refresh database statistics."""
        try:
            # Create temporary agent to get stats
            agent = ClicarsScraperAgent()
            stats = agent.get_stats()

            self.stats_labels["total"].config(text=str(stats.get("total_listings", 0)))
            self.stats_labels["last_scrape"].config(text=datetime.now().strftime("%Y-%m-%d %H:%M"))

            self._log("Estadisticas actualizadas", "info")
        except Exception as e:
            self._log(f"Error obteniendo estadisticas: {e}", "error")

    def _log(self, message: str, level: str = "info"):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _start_scraping(self):
        """Start the scraping process."""
        if self.is_running:
            return

        self.is_running = True
        self.stop_requested = False

        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Scrapeando...")

        # Get configuration
        max_iterations = int(self.iterations_var.get())
        headless = self.headless_var.get()
        save_to_db = self.save_db_var.get()

        self._log(f"Iniciando scraping: {max_iterations} iteraciones, headless={headless}", "info")

        # Run in thread
        thread = threading.Thread(
            target=self._run_scraping,
            args=(max_iterations, headless, save_to_db),
            daemon=True
        )
        thread.start()

    def _run_scraping(self, max_iterations: int, headless: bool, save_to_db: bool):
        """Run scraping in background thread."""
        try:
            # Create agent
            self.agent = ClicarsScraperAgent(headless=headless)

            # Create event loop for async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Define log callback
            def log_callback(msg: str):
                # Schedule log update on main thread
                self.root.after(0, lambda: self._log(msg, "info"))

                # Update progress if iteration info
                if "[Iteration" in msg:
                    try:
                        parts = msg.split("/")
                        current = int(parts[0].split()[-1])
                        total = int(parts[1].split("]")[0])
                        progress = (current / total) * 100
                        self.root.after(0, lambda: self._update_progress(current, total, progress))
                    except:
                        pass

            # Run scraping
            result = loop.run_until_complete(
                self.agent.scrape_all(
                    max_iterations=max_iterations,
                    save_to_db=save_to_db,
                    log_callback=log_callback
                )
            )

            # Update UI with results
            self.root.after(0, lambda: self._scraping_complete(result))

        except Exception as e:
            self.root.after(0, lambda: self._scraping_error(str(e)))
        finally:
            loop.close()

    def _update_progress(self, current: int, total: int, progress: float):
        """Update progress bar."""
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{current} / {total} iteraciones")

    def _scraping_complete(self, result: ScrapeResult):
        """Handle scraping completion."""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        if result.errors:
            self.status_var.set("Completado con errores")
            self._log(f"Errores: {result.errors}", "warning")
        else:
            self.status_var.set("Completado")

        self._log(f"Scraping completado: {result.total_listings} listings, {result.saved_to_db} guardados", "success")

        # Update result labels
        self.result_labels["listings"].config(text=str(result.total_listings))
        self.result_labels["saved"].config(text=str(result.saved_to_db))
        self.result_labels["duration"].config(text=f"{result.duration_seconds:.1f}s")
        self.result_labels["method"].config(text=result.method_used)

        # Refresh stats
        self._refresh_stats()

    def _scraping_error(self, error: str):
        """Handle scraping error."""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Error")
        self._log(f"Error: {error}", "error")
        messagebox.showerror("Error", f"Error durante el scraping:\n{error}")

    def _stop_scraping(self):
        """Request stop of scraping."""
        self.stop_requested = True
        self._log("Deteniendo scraping...", "warning")
        self.status_var.set("Deteniendo...")

    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Entry point."""
    app = ClicarsApp()
    app.run()


if __name__ == "__main__":
    main()
