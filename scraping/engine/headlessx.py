"""
HeadlessX API Client - Unico motor de scraping para ScrapeadorSupremo.

HeadlessX v1.3.0 es un servidor Node.js que proporciona capacidades avanzadas
de anti-deteccion a traves de una API REST.

Caracteristicas:
- Canvas/WebGL fingerprint spoofing
- Simulacion conductual (mouse, scroll, typing)
- WAF bypass (Cloudflare, DataDome, Imperva, Akamai)
- Rotacion de perfiles de dispositivo
- Modo stealth avanzado

Requiere:
- Servidor HeadlessX corriendo en localhost:3000 (o remoto)
- HEADLESSX_AUTH_TOKEN en .env

Referencia: https://github.com/SaifyXPRO/HeadlessX
"""

import logging
import os
import time
import random
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HeadlessXConfig:
    """Configuracion del cliente HeadlessX."""

    api_url: str = "http://localhost:3000"
    auth_token: Optional[str] = None
    timeout: int = 180000  # ms

    # Profiles
    device_profile: str = "mid-range-desktop"
    geo_profile: str = "us-east"
    behavior_profile: str = "natural"

    # Anti-Detection
    enable_canvas_spoofing: bool = True
    enable_webgl_spoofing: bool = True
    enable_audio_spoofing: bool = True
    enable_webrtc_blocking: bool = True
    enable_advanced_stealth: bool = True

    # Behavioral
    simulate_mouse_movement: bool = True
    simulate_scrolling: bool = True
    human_delays: bool = True
    randomize_timings: bool = True

    # Page interaction
    scroll_to_bottom: bool = True
    extra_wait_time: int = 5000

    # Stealth
    use_stealth_endpoint: bool = False
    stealth_mode: str = "maximum"  # basic, advanced, maximum

    # Retry
    retry_on_block: bool = True
    max_retries: int = 3


class HeadlessXClient:
    """
    Cliente para la API HeadlessX v1.3.0.

    Es el unico motor de scraping de ScrapeadorSupremo.
    Todas las peticiones web pasan por este cliente.

    Ejemplo:
        client = HeadlessXClient()
        client.setup()
        html = client.get_page("https://www.coches.net/segunda-mano/bmw")
        client.cleanup()
    """

    def __init__(self, config: Optional[HeadlessXConfig] = None):
        """
        Inicializa el cliente HeadlessX.

        Args:
            config: Configuracion del cliente (usa defaults si no se proporciona)
        """
        self.config = config or HeadlessXConfig()
        self.config.auth_token = self.config.auth_token or os.getenv("HEADLESSX_AUTH_TOKEN")

        self.session: Optional[requests.Session] = None
        self._is_setup = False
        self._block_count = 0
        self._last_waf_detected: Optional[str] = None

    def setup(self) -> None:
        """
        Configura el cliente y verifica conexion con el servidor.

        Raises:
            ValueError: Si AUTH_TOKEN no esta configurado
            ConnectionError: Si el servidor no esta disponible
        """
        if not self.config.auth_token:
            raise ValueError(
                "HeadlessX AUTH_TOKEN no configurado. "
                "Configura HEADLESSX_AUTH_TOKEN en .env"
            )

        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ScrapeadorSupremo/1.0'
        })

        # Test connection
        health_url = f"{self.config.api_url}/api/health"
        try:
            response = self.session.get(health_url, timeout=10)
            response.raise_for_status()

            health = response.json()
            logger.info(
                f"HeadlessX conectado - Version: {health.get('version', '?')}"
            )

            self._is_setup = True

        except requests.RequestException as e:
            raise ConnectionError(
                f"No se pudo conectar a HeadlessX en {self.config.api_url}: {e}\n"
                f"Asegurate de que el servidor este corriendo: cd HeadlessX && npm start"
            )

    def get_page(self, url: str, use_stealth: Optional[bool] = None) -> str:
        """
        Obtiene el HTML de una URL.

        Args:
            url: URL a scrapear
            use_stealth: Forzar endpoint stealth (None = usar config)

        Returns:
            HTML de la pagina

        Raises:
            ValueError: URL invalida
            requests.RequestException: Error en la peticion
        """
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError(f"URL invalida: {url}")

        if not self._is_setup:
            self.setup()

        stealth = use_stealth if use_stealth is not None else self.config.use_stealth_endpoint

        # Select endpoint
        if stealth:
            endpoint = f"{self.config.api_url}/api/render/stealth"
        else:
            endpoint = f"{self.config.api_url}/api/render"

        # Build payload
        payload = self._build_payload(url, stealth)

        logger.info(f"Fetching: {url} [{'stealth' if stealth else 'standard'}]")

        try:
            start = time.time()

            response = self.session.post(
                endpoint,
                params={"token": self.config.auth_token},
                json=payload,
                timeout=self.config.timeout / 1000 + 30
            )
            response.raise_for_status()

            data = response.json()
            html = data.get("html", "")

            if not html:
                error = data.get("error", data.get("message", "Sin HTML"))
                raise requests.RequestException(f"API error: {error}")

            elapsed = time.time() - start

            # Check for WAF/block
            is_blocked, waf_type = self._detect_waf(html)

            if is_blocked:
                self._block_count += 1
                self._last_waf_detected = waf_type
                logger.warning(f"Bloqueo detectado: {waf_type} (count: {self._block_count})")

                if self.config.retry_on_block and self._block_count <= self.config.max_retries:
                    return self._retry_with_escalation(url, waf_type)
            else:
                self._block_count = 0

            logger.info(f"OK: {len(html):,} bytes en {elapsed:.2f}s")

            # Human-like delay
            self._random_delay(1.5, 3.0)

            return html

        except requests.Timeout:
            logger.error(f"Timeout: {url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Error: {url} - {e}")
            raise

    def get_page_stealth(self, url: str) -> str:
        """Shortcut para get_page con stealth forzado."""
        return self.get_page(url, use_stealth=True)

    def cleanup(self) -> None:
        """Limpia recursos."""
        if self.session:
            self.session.close()
            self.session = None
        self._is_setup = False
        logger.debug("HeadlessX client cleaned up")

    def _build_payload(self, url: str, stealth: bool) -> Dict[str, Any]:
        """Construye el payload para la API."""
        payload = {
            "url": url,
            "timeout": self.config.timeout,
            "waitUntil": "networkidle",
            "returnPartialOnTimeout": True,

            # Profiles
            "deviceProfile": self.config.device_profile,
            "geoProfile": self.config.geo_profile,
            "behaviorProfile": self.config.behavior_profile,

            # Anti-Detection
            "enableCanvasSpoofing": self.config.enable_canvas_spoofing,
            "enableWebGLSpoofing": self.config.enable_webgl_spoofing,
            "enableAudioSpoofing": self.config.enable_audio_spoofing,
            "enableWebRTCBlocking": self.config.enable_webrtc_blocking,
            "enableAdvancedStealth": self.config.enable_advanced_stealth,

            # Behavioral
            "simulateMouseMovement": self.config.simulate_mouse_movement,
            "simulateScrolling": self.config.simulate_scrolling,
            "humanDelays": self.config.human_delays,
            "randomizeTimings": self.config.randomize_timings,

            # Page interaction
            "scrollToBottom": self.config.scroll_to_bottom,
            "extraWaitTime": self.config.extra_wait_time,
            "waitForNetworkIdle": True,
        }

        if stealth:
            payload["stealthMode"] = self.config.stealth_mode
            payload["behaviorSimulation"] = True

        return payload

    def _detect_waf(self, html: str) -> tuple:
        """
        Detecta tipo de WAF/proteccion en el HTML.

        Returns:
            (is_blocked, waf_type)
        """
        html_lower = html.lower()

        # Cloudflare
        if any(x in html_lower for x in ['cf-browser-verification', 'cloudflare', 'cf_captcha_kind', 'cf-ray']):
            return True, 'cloudflare'

        # DataDome
        if any(x in html_lower for x in ['datadome', 'dd_', 'geo.captcha-delivery.com']):
            return True, 'datadome'

        # Akamai
        if any(x in html_lower for x in ['akamai', '_abck', 'ak_bmsc']):
            return True, 'akamai'

        # Imperva/Incapsula
        if any(x in html_lower for x in ['incapsula', 'imperva', 'incap_ses']):
            return True, 'incapsula'

        # Generic block
        if any(x in html_lower for x in ['captcha', 'blocked', 'forbidden', 'access denied', 'robot']):
            return True, 'generic'

        return False, None

    def _retry_with_escalation(self, url: str, waf_type: str) -> str:
        """Reintenta con parametros escalados."""
        waf_delays = {
            'cloudflare': (2.0, 8.0),
            'datadome': (1.5, 6.0),
            'akamai': (3.0, 10.0),
            'incapsula': (2.5, 7.0),
            'generic': (1.0, 5.0)
        }

        min_d, max_d = waf_delays.get(waf_type, (1.0, 5.0))
        multiplier = 1 + (self._block_count * 0.5)

        wait = random.uniform(min_d, max_d) * multiplier
        logger.info(f"Esperando {wait:.1f}s antes de reintentar (WAF: {waf_type})...")
        time.sleep(wait)

        # Rotate profiles
        profiles = ['high-end-desktop', 'mid-range-desktop', 'business-laptop']
        geos = ['us-east', 'us-west', 'uk', 'germany', 'france']

        old_device = self.config.device_profile
        old_geo = self.config.geo_profile

        self.config.device_profile = random.choice([p for p in profiles if p != old_device])
        self.config.geo_profile = random.choice([g for g in geos if g != old_geo])
        self.config.behavior_profile = 'cautious'
        self.config.extra_wait_time = int(self.config.extra_wait_time * multiplier)

        # Force stealth for retry
        return self.get_page(url, use_stealth=True)

    def _random_delay(self, min_s: float, max_s: float) -> None:
        """Delay aleatorio."""
        time.sleep(random.uniform(min_s, max_s))

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
