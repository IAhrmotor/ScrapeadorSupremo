"""Desktop GUI application for Coordinated Multi-Scraper with DNS Protection."""

import asyncio
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.orchestrator import OrchestratorAgent
from core.network import CoordinatorConfig
from core.dns import DNSHealthStatus


class CoordinatedScraperApp:
    """
    Desktop GUI application for Coordinated Multi-Scraper.

    Features:
    - Select which scrapers to run (Coches.net, Autocasion, OcasionPlus)
    - Configure workers per scraper
    - DNS health monitoring display
    - Real-time progress and logs
    - Coordinator statistics
    - Auto-pause on DNS issues
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Scraper Coordinado - Multi-Scraper con Proteccion DNS")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)

        # Style
        style = ttk.Style()
        style.theme_use('clam')

        # Configure custom colors
        style.configure("DNS.TLabel", font=("Helvetica", 11, "bold"))
        style.configure("Healthy.TLabel", foreground="green")
        style.configure("Degraded.TLabel", foreground="orange")
        style.configure("Unhealthy.TLabel", foreground="red")
        style.configure("Unknown.TLabel", foreground="gray")

        # State
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.is_running = False
        self.stop_requested = False
        self.dns_monitor_task = None

        # Create UI
        self._create_widgets()
        self._log("Scraper Coordinado inicializado")
        self._log("Sistema de proteccion DNS activo")

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title section
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            title_frame,
            text="Scraper Coordinado",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)

        subtitle = ttk.Label(
            title_frame,
            text="Multi-Scraper con Proteccion DNS",
            font=("Helvetica", 10)
        )
        subtitle.pack(side=tk.LEFT, padx=(10, 0))

        # DNS Status indicator
        self.dns_status_frame = ttk.Frame(title_frame)
        self.dns_status_frame.pack(side=tk.RIGHT)

        ttk.Label(self.dns_status_frame, text="DNS:", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self.dns_status_label = ttk.Label(
            self.dns_status_frame,
            text="UNKNOWN",
            font=("Helvetica", 10, "bold")
        )
        self.dns_status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Scraping Configuration
        scrape_frame = ttk.Frame(notebook, padding="10")
        notebook.add(scrape_frame, text="Scraping")
        self._create_scrape_tab(scrape_frame)

        # Tab 2: DNS Monitor
        dns_frame = ttk.Frame(notebook, padding="10")
        notebook.add(dns_frame, text="DNS Monitor")
        self._create_dns_tab(dns_frame)

        # Tab 3: Statistics
        stats_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stats_frame, text="Estadisticas")
        self._create_stats_tab(stats_frame)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="Listo")
        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)

        self.connection_label = ttk.Label(
            status_frame,
            text="Conexiones: 0/6",
            relief=tk.SUNKEN,
            width=20
        )
        self.connection_label.pack(side=tk.RIGHT, padx=(5, 0))

    def _create_scrape_tab(self, parent):
        """Create the scraping configuration tab."""
        # Scrapers selection
        scrapers_frame = ttk.LabelFrame(parent, text="Scrapers", padding="10")
        scrapers_frame.pack(fill=tk.X, pady=(0, 10))

        # Scraper checkboxes and worker spinboxes
        self.scraper_vars = {}
        self.worker_vars = {}

        scrapers_config = [
            ("cochesnet", "Coches.net", 3, "Paginacion por anios"),
            ("autocasion", "Autocasion", 2, "Paginacion por marcas"),
            ("ocasionplus", "OcasionPlus", 1, "Infinite scroll")
        ]

        for i, (key, name, default_workers, desc) in enumerate(scrapers_config):
            row_frame = ttk.Frame(scrapers_frame)
            row_frame.pack(fill=tk.X, pady=2)

            # Checkbox
            var = tk.BooleanVar(value=True)
            self.scraper_vars[key] = var
            cb = ttk.Checkbutton(
                row_frame,
                text=name,
                variable=var,
                width=15
            )
            cb.pack(side=tk.LEFT)

            # Workers label and spinbox
            ttk.Label(row_frame, text="Workers:").pack(side=tk.LEFT, padx=(20, 5))

            worker_var = tk.IntVar(value=default_workers)
            self.worker_vars[key] = worker_var
            worker_spin = ttk.Spinbox(
                row_frame,
                from_=1,
                to=5,
                width=4,
                textvariable=worker_var
            )
            worker_spin.pack(side=tk.LEFT)

            # Description
            ttk.Label(row_frame, text=f"({desc})", foreground="gray").pack(side=tk.LEFT, padx=(15, 0))

        # Global configuration
        config_frame = ttk.LabelFrame(parent, text="Configuracion Global", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        config_row1 = ttk.Frame(config_frame)
        config_row1.pack(fill=tk.X, pady=2)

        ttk.Label(config_row1, text="Max Conexiones Globales:").pack(side=tk.LEFT)
        self.max_connections_var = tk.IntVar(value=6)
        ttk.Spinbox(
            config_row1,
            from_=3,
            to=10,
            width=5,
            textvariable=self.max_connections_var
        ).pack(side=tk.LEFT, padx=(10, 30))

        self.save_to_db_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            config_row1,
            text="Guardar en Base de Datos (Supabase)",
            variable=self.save_to_db_var
        ).pack(side=tk.LEFT)

        config_row2 = ttk.Frame(config_frame)
        config_row2.pack(fill=tk.X, pady=2)

        self.auto_pause_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            config_row2,
            text="Auto-pausar si DNS falla",
            variable=self.auto_pause_var
        ).pack(side=tk.LEFT)

        self.dns_rotation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            config_row2,
            text="Rotacion DNS (Cloudflare, Google, Quad9, OpenDNS)",
            variable=self.dns_rotation_var
        ).pack(side=tk.LEFT, padx=(30, 0))

        # Quick presets
        preset_frame = ttk.Frame(config_frame)
        preset_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT)

        ttk.Button(
            preset_frame,
            text="Conservador (4 conn)",
            command=lambda: self._apply_preset("conservative"),
            width=18
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_frame,
            text="Balanceado (6 conn)",
            command=lambda: self._apply_preset("balanced"),
            width=18
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            preset_frame,
            text="Agresivo (8 conn)",
            command=lambda: self._apply_preset("aggressive"),
            width=18
        ).pack(side=tk.LEFT, padx=5)

        # Progress section
        progress_frame = ttk.LabelFrame(parent, text="Progreso", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        # Overall progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(
            progress_frame,
            text="Listo para scrapear",
            font=("Helvetica", 10)
        )
        self.progress_label.pack()

        # Per-scraper progress
        self.scraper_status_labels = {}
        scraper_status_frame = ttk.Frame(progress_frame)
        scraper_status_frame.pack(fill=tk.X, pady=(10, 0))

        for key, name, _, _ in scrapers_config:
            frame = ttk.Frame(scraper_status_frame)
            frame.pack(fill=tk.X, pady=1)

            ttk.Label(frame, text=f"{name}:", width=12).pack(side=tk.LEFT)
            status_label = ttk.Label(frame, text="Inactivo", foreground="gray")
            status_label.pack(side=tk.LEFT)
            self.scraper_status_labels[key] = status_label

        # Control buttons
        control_frame = ttk.Frame(progress_frame)
        control_frame.pack(pady=(10, 0))

        self.start_button = ttk.Button(
            control_frame,
            text="INICIAR SCRAPEO",
            command=self._start_scraping,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="DETENER",
            command=self._stop_scraping,
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = ttk.Button(
            control_frame,
            text="PAUSAR",
            command=self._toggle_pause,
            state=tk.DISABLED,
            width=15
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        # Logs section
        logs_frame = ttk.LabelFrame(parent, text="Logs", padding="5")
        logs_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure log tags for colors
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("error", foreground="red")

        log_buttons = ttk.Frame(logs_frame)
        log_buttons.pack(pady=(5, 0))

        ttk.Button(
            log_buttons,
            text="Limpiar Logs",
            command=self._clear_logs
        ).pack(side=tk.LEFT, padx=5)

    def _create_dns_tab(self, parent):
        """Create the DNS monitor tab."""
        # DNS Status section
        status_frame = ttk.LabelFrame(parent, text="Estado DNS", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Big status indicator
        self.dns_big_status = ttk.Label(
            status_frame,
            text="DNS STATUS: UNKNOWN",
            font=("Helvetica", 16, "bold")
        )
        self.dns_big_status.pack(pady=10)

        # Status details
        details_frame = ttk.Frame(status_frame)
        details_frame.pack(fill=tk.X)

        # Left column - Providers
        left_col = ttk.Frame(details_frame)
        left_col.pack(side=tk.LEFT, padx=20, anchor=tk.N)

        ttk.Label(left_col, text="DNS Providers:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        self.provider_labels = {}
        providers = [
            ("1.1.1.1", "Cloudflare"),
            ("8.8.8.8", "Google"),
            ("9.9.9.9", "Quad9"),
            ("208.67.222.222", "OpenDNS")
        ]
        for ip, name in providers:
            frame = ttk.Frame(left_col)
            frame.pack(fill=tk.X, pady=1)
            ttk.Label(frame, text=f"{name} ({ip}):", width=25).pack(side=tk.LEFT)
            status = ttk.Label(frame, text="--", width=10)
            status.pack(side=tk.LEFT)
            self.provider_labels[ip] = status

        # Right column - Stats
        right_col = ttk.Frame(details_frame)
        right_col.pack(side=tk.RIGHT, padx=20, anchor=tk.N)

        ttk.Label(right_col, text="DNS Cache:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        self.cache_stats_labels = {
            "entries": self._create_stat_row(right_col, "Entradas:"),
            "hits": self._create_stat_row(right_col, "Hits:"),
            "misses": self._create_stat_row(right_col, "Misses:"),
            "hit_rate": self._create_stat_row(right_col, "Hit Rate:")
        }

        # DNS Health Monitor
        monitor_frame = ttk.LabelFrame(parent, text="Monitor de Salud", padding="10")
        monitor_frame.pack(fill=tk.X, pady=(0, 10))

        monitor_row1 = ttk.Frame(monitor_frame)
        monitor_row1.pack(fill=tk.X, pady=2)

        self.health_labels = {
            "checks": self._create_stat_row(monitor_row1, "Health Checks:", inline=True),
            "failures": self._create_stat_row(monitor_row1, "Fallos Consecutivos:", inline=True),
            "recoveries": self._create_stat_row(monitor_row1, "Recuperaciones:", inline=True)
        }

        # Test domains
        test_frame = ttk.LabelFrame(parent, text="Test de Resolucion DNS", padding="10")
        test_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(test_frame, text="Probar resolucion de dominio:").pack(anchor=tk.W)

        test_row = ttk.Frame(test_frame)
        test_row.pack(fill=tk.X, pady=5)

        self.test_domain_var = tk.StringVar(value="supabase.co")
        ttk.Entry(test_row, textvariable=self.test_domain_var, width=40).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            test_row,
            text="Probar DNS",
            command=self._test_dns
        ).pack(side=tk.LEFT)

        # Quick test buttons
        quick_test_frame = ttk.Frame(test_frame)
        quick_test_frame.pack(fill=tk.X, pady=(5, 0))

        for domain in ["coches.net", "autocasion.com", "ocasionplus.com", "supabase.co"]:
            ttk.Button(
                quick_test_frame,
                text=domain,
                command=lambda d=domain: self._quick_test_dns(d),
                width=15
            ).pack(side=tk.LEFT, padx=2)

        self.dns_test_result = ttk.Label(test_frame, text="", font=("Courier", 9))
        self.dns_test_result.pack(anchor=tk.W, pady=(10, 0))

        # Refresh button
        ttk.Button(
            parent,
            text="Actualizar Estado DNS",
            command=self._refresh_dns_status
        ).pack(pady=10)

    def _create_stats_tab(self, parent):
        """Create the statistics tab."""
        # Coordinator stats
        coord_frame = ttk.LabelFrame(parent, text="Estadisticas del Coordinador", padding="10")
        coord_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_text = scrolledtext.ScrolledText(
            coord_frame,
            height=20,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Actualizar Estadisticas",
            command=self._refresh_stats
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Exportar Estadisticas",
            command=self._export_stats
        ).pack(side=tk.LEFT, padx=5)

    def _create_stat_row(self, parent, label: str, inline: bool = False) -> ttk.Label:
        """Create a labeled stat row."""
        if inline:
            ttk.Label(parent, text=label).pack(side=tk.LEFT, padx=(0, 5))
            value = ttk.Label(parent, text="--")
            value.pack(side=tk.LEFT, padx=(0, 20))
        else:
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=1)
            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)
            value = ttk.Label(frame, text="--")
            value.pack(side=tk.LEFT)
        return value

    def _apply_preset(self, preset: str):
        """Apply a configuration preset."""
        presets = {
            "conservative": {"max_conn": 4, "cochesnet": 2, "autocasion": 1, "ocasionplus": 1},
            "balanced": {"max_conn": 6, "cochesnet": 3, "autocasion": 2, "ocasionplus": 1},
            "aggressive": {"max_conn": 8, "cochesnet": 4, "autocasion": 3, "ocasionplus": 1}
        }

        config = presets.get(preset, presets["balanced"])
        self.max_connections_var.set(config["max_conn"])
        self.worker_vars["cochesnet"].set(config["cochesnet"])
        self.worker_vars["autocasion"].set(config["autocasion"])
        self.worker_vars["ocasionplus"].set(config["ocasionplus"])

        self._log(f"Preset aplicado: {preset} (max {config['max_conn']} conexiones)")

    def _start_scraping(self):
        """Start the coordinated scraping process."""
        if self.is_running:
            messagebox.showwarning("Ya en ejecucion", "El scraping ya esta en progreso.")
            return

        # Get selected scrapers
        selected = [key for key, var in self.scraper_vars.items() if var.get()]

        if not selected:
            messagebox.showerror("Sin scrapers", "Selecciona al menos un scraper.")
            return

        # Confirm
        workers_info = "\n".join([
            f"  - {key}: {self.worker_vars[key].get()} workers"
            for key in selected
        ])

        msg = f"""Iniciar Scrapeo Coordinado?

Scrapers seleccionados:
{workers_info}

Max Conexiones: {self.max_connections_var.get()}
Guardar en BD: {'Si' if self.save_to_db_var.get() else 'No'}
Auto-pausa DNS: {'Si' if self.auto_pause_var.get() else 'No'}
"""

        if not messagebox.askyesno("Confirmar", msg):
            return

        self._execute_scraping(selected)

    def _execute_scraping(self, scrapers: List[str]):
        """Execute the coordinated scraping."""
        self.is_running = True
        self.stop_requested = False

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)

        # Update scraper status labels
        for key in scrapers:
            self.scraper_status_labels[key].config(text="Iniciando...", foreground="blue")

        # Start scraping in background thread
        threading.Thread(
            target=self._run_scraping_thread,
            args=(scrapers,),
            daemon=True
        ).start()

        # Start DNS status monitor
        self._start_dns_monitor()

    def _run_scraping_thread(self, scrapers: List[str]):
        """Run scraping in background thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self._log("Iniciando scraping coordinado...")

            # Build configuration
            config = {
                "max_global_connections": self.max_connections_var.get(),
                "scrapers": {
                    name: {
                        "max_concurrent": self.worker_vars[name].get(),
                        "save_to_db": self.save_to_db_var.get()
                    }
                    for name in scrapers
                }
            }

            # Add specific configs
            if "cochesnet" in config["scrapers"]:
                config["scrapers"]["cochesnet"]["max_pages"] = 0  # All pages

            if "autocasion" in config["scrapers"]:
                config["scrapers"]["autocasion"]["max_pages"] = 0

            if "ocasionplus" in config["scrapers"]:
                config["scrapers"]["ocasionplus"]["max_iterations"] = 200

            # Create orchestrator
            self.orchestrator = OrchestratorAgent()
            self.orchestrator.setup_coordinator(
                max_global_connections=config["max_global_connections"],
                scraper_slots={
                    name: cfg["max_concurrent"]
                    for name, cfg in config["scrapers"].items()
                }
            )

            # Import and create scraper functions
            scraper_funcs = {}

            for name in scrapers:
                self.root.after(0, lambda n=name: self._update_scraper_status(n, "Cargando...", "orange"))

                try:
                    if name == "cochesnet":
                        from scraping.sites.cochesnet.app.scraper_agent import CochesnetScraperAgent
                        agent = CochesnetScraperAgent()

                        async def run_cochesnet(a=agent, c=config["scrapers"]["cochesnet"]):
                            self.root.after(0, lambda: self._update_scraper_status("cochesnet", "Scrapeando...", "green"))
                            self._log("Coches.net: Iniciando scrapeo...")
                            try:
                                # Scrape years 2015-2025 in parallel
                                years = list(range(2015, 2026))
                                result = await a.scrape_years(
                                    years=years,
                                    parallel=True,
                                    max_workers=c.get("max_concurrent", 3),
                                    log_callback=lambda msg: self._log(f"Coches.net: {msg}")
                                )
                                self._log(f"Coches.net: Completado - {result.total_listings} listings, {result.saved_to_db} guardados")
                                return {"total": result.total_listings, "saved": result.saved_to_db}
                            except Exception as e:
                                self._log(f"Coches.net ERROR: {e}", "error")
                                raise

                        scraper_funcs["cochesnet"] = run_cochesnet

                    elif name == "autocasion":
                        from scraping.sites.autocasion.app.scraper_agent import AutocasionScraperAgent
                        agent = AutocasionScraperAgent()

                        async def run_autocasion(a=agent, c=config["scrapers"]["autocasion"]):
                            self.root.after(0, lambda: self._update_scraper_status("autocasion", "Scrapeando...", "green"))
                            self._log("Autocasion: Iniciando scrapeo...")
                            try:
                                brands = a.site.get_brands_list()
                                results = await a.scrape_batch_parallel(
                                    marcas=brands,
                                    max_pages=c.get("max_pages", 0),
                                    save_to_db=c.get("save_to_db", True),
                                    max_workers=c.get("max_concurrent", 2)
                                )
                                total = sum(r.total_listings for r in results)
                                saved = sum(r.saved_to_db for r in results)
                                self._log(f"Autocasion: Completado - {total} listings, {saved} guardados")
                                return {"total": total, "saved": saved}
                            except Exception as e:
                                self._log(f"Autocasion ERROR: {e}", "error")
                                raise

                        scraper_funcs["autocasion"] = run_autocasion

                    elif name == "ocasionplus":
                        from scraping.sites.ocasionplus.app.scraper_agent import OcasionPlusScraperAgent
                        agent = OcasionPlusScraperAgent()

                        async def run_ocasionplus(a=agent, c=config["scrapers"]["ocasionplus"]):
                            self.root.after(0, lambda: self._update_scraper_status("ocasionplus", "Scrapeando...", "green"))
                            self._log("OcasionPlus: Iniciando scrapeo (infinite scroll)...")
                            try:
                                result = await a.scrape_all(
                                    max_iterations=c.get("max_iterations", 200),
                                    save_to_db=c.get("save_to_db", True),
                                    log_callback=lambda msg: self._log(f"OcasionPlus: {msg}")
                                )
                                self._log(f"OcasionPlus: Completado - {result.total_listings} listings, {result.saved_to_db} guardados")
                                return {"total": result.total_listings, "saved": result.saved_to_db}
                            except Exception as e:
                                self._log(f"OcasionPlus ERROR: {e}", "error")
                                raise

                        scraper_funcs["ocasionplus"] = run_ocasionplus

                except ImportError as e:
                    self._log(f"Error importando {name}: {e}", "error")
                    self.root.after(0, lambda n=name: self._update_scraper_status(n, "Error import", "red"))

            if not scraper_funcs:
                raise Exception("No se pudo cargar ningun scraper")

            # Run coordinated scrape
            self._log(f"Ejecutando {len(scraper_funcs)} scrapers en paralelo...")

            results = loop.run_until_complete(
                self.orchestrator.coordinate_scrapers(
                    scrapers=list(scraper_funcs.keys()),
                    scraper_funcs=scraper_funcs,
                    config=config
                )
            )

            # Show results
            self.root.after(0, lambda: self._show_results(results))

        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

        finally:
            # Cleanup
            if self.orchestrator:
                try:
                    loop.run_until_complete(self.orchestrator.close_coordinator())
                except:
                    pass

            self.root.after(0, self._scraping_finished)

    def _update_scraper_status(self, name: str, status: str, color: str):
        """Update scraper status label."""
        if name in self.scraper_status_labels:
            self.scraper_status_labels[name].config(text=status, foreground=color)

    def _stop_scraping(self):
        """Stop the scraping process."""
        if messagebox.askyesno("Confirmar", "Detener el scraping?"):
            self.stop_requested = True
            self._log("Detencion solicitada...", "warning")

    def _toggle_pause(self):
        """Toggle pause state."""
        if self.orchestrator and self.orchestrator.coordinator:
            if self.orchestrator.coordinator.is_paused:
                self.orchestrator.coordinator.resume_all()
                self.pause_button.config(text="PAUSAR")
                self._log("Scrapers reanudados", "success")
            else:
                self.orchestrator.coordinator.pause_all()
                self.pause_button.config(text="REANUDAR")
                self._log("Scrapers pausados", "warning")

    def _start_dns_monitor(self):
        """Start background DNS status monitoring."""
        def monitor():
            while self.is_running:
                self.root.after(0, self._update_dns_display)
                time.sleep(2)

        self.dns_monitor_task = threading.Thread(target=monitor, daemon=True)
        self.dns_monitor_task.start()

    def _update_dns_display(self):
        """Update DNS status display."""
        if not self.orchestrator or not self.orchestrator.coordinator:
            return

        try:
            status = self.orchestrator.get_dns_status()
            stats = self.orchestrator.get_coordinator_stats()

            if status:
                status_text = status.value.upper()
                color_map = {
                    "healthy": ("green", "HEALTHY"),
                    "degraded": ("orange", "DEGRADED"),
                    "unhealthy": ("red", "UNHEALTHY"),
                    "unknown": ("gray", "UNKNOWN")
                }
                color, text = color_map.get(status.value, ("gray", status_text))
                self.dns_status_label.config(text=text, foreground=color)
                self.dns_big_status.config(text=f"DNS STATUS: {text}", foreground=color)

            if stats:
                # Update connection count
                global_conn = stats.get("global_connections", {})
                current = global_conn.get("current", 0)
                max_conn = global_conn.get("max", 6)
                self.connection_label.config(text=f"Conexiones: {current}/{max_conn}")

                # Update DNS cache stats
                dns_stats = stats.get("dns", {})
                cache_stats = dns_stats.get("cache", {})
                self.cache_stats_labels["entries"].config(text=str(cache_stats.get("size", 0)))
                self.cache_stats_labels["hits"].config(text=str(cache_stats.get("hits", 0)))
                self.cache_stats_labels["misses"].config(text=str(cache_stats.get("misses", 0)))
                self.cache_stats_labels["hit_rate"].config(text=cache_stats.get("hit_rate", "--"))

                # Update health monitor stats
                monitor_stats = stats.get("dns_monitor", {})
                self.health_labels["checks"].config(text=str(monitor_stats.get("total_checks", 0)))
                self.health_labels["failures"].config(text=str(monitor_stats.get("consecutive_failures", 0)))
                self.health_labels["recoveries"].config(text=str(monitor_stats.get("recoveries", 0)))

        except Exception:
            pass

    def _scraping_finished(self):
        """Called when scraping finishes."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set(0)
        self.progress_label.config(text="Scrapeo finalizado")

        # Reset scraper status labels
        for label in self.scraper_status_labels.values():
            label.config(text="Inactivo", foreground="gray")

        self._refresh_stats()

    def _show_results(self, results: Dict[str, Any]):
        """Show scraping results."""
        success = results.get("success", False)
        duration = results.get("duration_seconds", 0)
        scraper_results = results.get("results", {})
        errors = results.get("errors", {})

        msg = f"""Scrapeo Coordinado {'COMPLETADO' if success else 'con errores'}

Duracion: {duration:.1f} segundos ({duration/60:.1f} min)

Resultados por scraper:
"""
        for name, data in scraper_results.items():
            if isinstance(data, dict):
                msg += f"\n{name}:"
                msg += f"\n  - Total: {data.get('total', 0):,}"
                msg += f"\n  - Guardados: {data.get('saved', 0):,}"

        if errors:
            msg += "\n\nErrores:"
            for name, error in errors.items():
                msg += f"\n{name}: {error}"

        # DNS stats
        coord_stats = results.get("coordinator_stats", {})
        dns_cache = coord_stats.get("dns", {}).get("cache", {})
        msg += f"\n\nDNS Cache Hit Rate: {dns_cache.get('hit_rate', 'N/A')}"

        messagebox.showinfo("Resultados", msg)
        self._log("Scrapeo completado exitosamente", "success")

    def _show_error(self, error: str):
        """Show error message."""
        messagebox.showerror("Error", f"Scrapeo fallido:\n\n{error}")
        self._log(f"ERROR: {error}", "error")

    def _log(self, message: str, level: str = "info"):
        """Add message to log."""
        def add_log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
            self.log_text.insert(tk.END, f"{message}\n", level)
            self.log_text.see(tk.END)

        self.root.after(0, add_log)

    def _clear_logs(self):
        """Clear the log text."""
        self.log_text.delete(1.0, tk.END)

    def _test_dns(self):
        """Test DNS resolution."""
        domain = self.test_domain_var.get().strip()
        if not domain:
            return

        self._quick_test_dns(domain)

    def _quick_test_dns(self, domain: str):
        """Quick test DNS for a domain."""
        self.test_domain_var.set(domain)
        self.dns_test_result.config(text=f"Probando {domain}...")

        def test():
            import socket
            try:
                start = time.time()
                ip = socket.gethostbyname(domain)
                elapsed = (time.time() - start) * 1000

                result = f"OK: {domain} -> {ip} ({elapsed:.0f}ms)"
                color = "green"
                self._log(f"DNS Test: {result}", "success")
            except socket.gaierror as e:
                result = f"FALLO: {domain} - {e}"
                color = "red"
                self._log(f"DNS Test: {result}", "error")

            self.root.after(0, lambda: self.dns_test_result.config(text=result, foreground=color))

        threading.Thread(target=test, daemon=True).start()

    def _refresh_dns_status(self):
        """Refresh DNS status display."""
        self._update_dns_display()
        self._log("Estado DNS actualizado")

    def _refresh_stats(self):
        """Refresh coordinator statistics."""
        self.stats_text.delete(1.0, tk.END)

        if self.orchestrator:
            stats = self.orchestrator.get_coordinator_stats()
            if stats:
                self._display_stats(stats)
            else:
                self.stats_text.insert(1.0, "No hay estadisticas disponibles (scraper no iniciado)")
        else:
            self.stats_text.insert(1.0, "Coordinador no inicializado.\nInicia un scrapeo para ver estadisticas.")

    def _display_stats(self, stats: Dict):
        """Display formatted statistics."""
        text = f"""ESTADISTICAS DEL COORDINADOR
{'='*50}

Tiempo Activo: {stats.get('uptime_seconds', 0):.1f} segundos
Estado Pausado: {'Si' if stats.get('is_paused', False) else 'No'}

CONEXIONES GLOBALES
{'-'*30}
Actuales: {stats.get('global_connections', {}).get('current', 0)}
Maximo: {stats.get('global_connections', {}).get('max', 6)}
Slots Adquiridos: {stats.get('total_slots_acquired', 0)}
Slots Liberados: {stats.get('total_slots_released', 0)}

SCRAPERS
{'-'*30}
"""
        for name, scraper_stats in stats.get('scrapers', {}).items():
            if scraper_stats:
                text += f"\n{name}:"
                text += f"\n  Estado: {scraper_stats.get('status', 'unknown')}"
                text += f"\n  Conexiones: {scraper_stats.get('current', 0)}/{scraper_stats.get('max_concurrent', 0)}"
                text += f"\n  Total Requests: {scraper_stats.get('total_requests', 0)}"
                text += f"\n  Total Errores: {scraper_stats.get('total_errors', 0)}"
                text += f"\n  Tasa Error: {scraper_stats.get('error_rate', '0%')}"

        text += f"""

DNS CACHE
{'-'*30}
"""
        dns_stats = stats.get('dns', {})
        cache = dns_stats.get('cache', {})
        text += f"Entradas: {cache.get('size', 0)}/{cache.get('max_size', 1000)}\n"
        text += f"Hits: {cache.get('hits', 0)}\n"
        text += f"Misses: {cache.get('misses', 0)}\n"
        text += f"Hit Rate: {cache.get('hit_rate', 'N/A')}\n"
        text += f"Evictions: {cache.get('evictions', 0)}\n"

        text += f"""
DNS MONITOR
{'-'*30}
"""
        monitor = stats.get('dns_monitor', {})
        text += f"Estado: {monitor.get('status', 'unknown')}\n"
        text += f"Total Checks: {monitor.get('total_checks', 0)}\n"
        text += f"Fallos Consecutivos: {monitor.get('consecutive_failures', 0)}\n"
        text += f"Total Fallos: {monitor.get('total_failures', 0)}\n"
        text += f"Recuperaciones: {monitor.get('recoveries', 0)}\n"

        text += f"""
RATE LIMITER
{'-'*30}
"""
        rate = stats.get('rate_limiter', {})
        text += f"Dominios: {rate.get('total_domains', 0)}\n"
        text += f"Total Requests: {rate.get('total_requests', 0)}\n"
        text += f"Total Bloqueados: {rate.get('total_blocked', 0)}\n"

        text += f"\n\nActualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.stats_text.insert(1.0, text)

    def _export_stats(self):
        """Export statistics to file."""
        if not self.orchestrator:
            messagebox.showwarning("Sin datos", "No hay estadisticas para exportar.")
            return

        from tkinter import filedialog
        import json

        stats = self.orchestrator.get_coordinator_stats()
        if not stats:
            messagebox.showwarning("Sin datos", "No hay estadisticas para exportar.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"coordinator_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not filename:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False, default=str)

            messagebox.showinfo("Exito", f"Estadisticas exportadas a:\n{filename}")
            self._log(f"Estadisticas exportadas: {filename}", "success")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando:\n{e}")

    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Entry point for the application."""
    app = CoordinatedScraperApp()
    app.run()


if __name__ == "__main__":
    main()
