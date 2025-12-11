"""Supabase client for storing scraped car listings."""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from supabase import create_client, Client
from dotenv import load_dotenv

from ..base.parser import CarListing


class SupabaseClient:
    """Client for persisting scraped data to Supabase."""

    # Mapping from site name to table name
    TABLE_MAPPING = {
        "cochesnet": "cochesnet",
        "autocasion": "autocasion",
        "clicars": "clicars",
        "ocasionplus": "ocasionplus"
    }

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        load_dotenv()
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")

        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Lazy initialization of Supabase client."""
        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client

    def _listing_to_cochesnet(self, listing: CarListing) -> Dict[str, Any]:
        """Convert CarListing to cochesnet table format."""
        now = datetime.utcnow().isoformat()

        # Parse numeric values
        km_numeric = None
        if listing.kilometers:
            km_clean = listing.kilometers.replace(".", "").replace(" km", "").replace("km", "").strip()
            try:
                km_numeric = int(km_clean)
            except ValueError:
                pass

        price_numeric = None
        if listing.price:
            price_clean = listing.price.replace(".", "").replace("€", "").replace(" ", "").strip()
            try:
                price_numeric = int(price_clean)
            except ValueError:
                pass

        power_numeric = None
        if listing.power:
            power_clean = listing.power.replace(" CV", "").replace("CV", "").strip()
            try:
                power_numeric = int(power_clean)
            except ValueError:
                pass

        return {
            "ad_id": listing.ad_id,
            "url": listing.url,
            "title": listing.title,
            "marca": listing.marca,
            "marca_normalizada": listing.marca.lower() if listing.marca else None,
            "modelo": listing.modelo,
            "modelo_base": listing.modelo,
            "modelo_completo": listing.modelo,
            "version": listing.version,
            "year": str(listing.year) if listing.year else None,
            "kilometers": listing.kilometers,
            "kilometers_numeric": km_numeric,
            "fuel": listing.fuel,
            "combustible_normalizado": self._normalize_fuel(listing.fuel),
            "price": listing.price,
            "price_numeric": price_numeric,
            "power": listing.power,
            "power_numeric": power_numeric,
            "location": listing.location,
            "provincia": listing.provincia,
            "scraped_at": now,
            "created_at": now,
            "activo": True,
            "parsing_version": 1
        }

    def _listing_to_autocasion(self, listing: CarListing) -> Dict[str, Any]:
        """Convert CarListing to autocasion table format."""
        now = datetime.utcnow().isoformat()

        # Parse numeric values - handle both int and str
        km_numeric = None
        km_str = None
        if listing.kilometers is not None:
            if isinstance(listing.kilometers, int):
                km_numeric = listing.kilometers
                km_str = f"{listing.kilometers:,}".replace(",", ".") + " km"
            else:
                km_str = str(listing.kilometers)
                km_clean = km_str.replace(".", "").replace(" km", "").replace("km", "").strip()
                try:
                    km_numeric = int(km_clean)
                except ValueError:
                    pass

        price_numeric = None
        price_str = None
        if listing.price is not None:
            if isinstance(listing.price, int):
                price_numeric = listing.price
                price_str = f"{listing.price} €"
            else:
                price_str = str(listing.price)
                price_clean = price_str.replace(".", "").replace("€", "").replace(" ", "").strip()
                try:
                    price_numeric = int(price_clean)
                except ValueError:
                    pass

        # Power fields
        power_numeric = None
        power_str = None
        if listing.power_cv is not None:
            if isinstance(listing.power_cv, int):
                power_numeric = listing.power_cv
                power_str = f"{listing.power_cv} CV"
            else:
                power_str = str(listing.power_cv)
                power_clean = power_str.replace(" CV", "").replace("CV", "").replace("cv", "").strip()
                try:
                    power_numeric = int(power_clean)
                except ValueError:
                    pass

        return {
            "ad_id": listing.ad_id,
            "url": listing.url,
            "title": listing.title,
            "marca": listing.marca,
            "modelo": listing.modelo,
            "version": listing.version,
            "year": listing.year,
            "kilometers": km_str,
            "kilometers_numeric": km_numeric,
            "fuel": listing.fuel,
            "power": power_str,
            "power_numeric": power_numeric,
            "transmission": listing.transmission,
            "price": price_str,
            "price_numeric": price_numeric,
            "location": listing.location,
            "scraped_at": now,
            "created_at": now,
            "updated_at": now
        }

    def _listing_to_clicars(self, listing: CarListing) -> Dict[str, Any]:
        """Convert CarListing to clicars table format (same as autocasion)."""
        now = datetime.utcnow().isoformat()

        # Parse numeric values - handle both int and str
        km_numeric = None
        km_str = None
        if listing.kilometers is not None:
            if isinstance(listing.kilometers, int):
                km_numeric = listing.kilometers
                km_str = f"{listing.kilometers:,}".replace(",", ".") + " km"
            else:
                km_str = str(listing.kilometers)
                km_clean = km_str.replace(".", "").replace(" km", "").replace("km", "").strip()
                try:
                    km_numeric = int(km_clean)
                except ValueError:
                    pass

        price_numeric = None
        price_str = None
        if listing.price is not None:
            if isinstance(listing.price, int):
                price_numeric = listing.price
                price_str = f"{listing.price} €"
            else:
                price_str = str(listing.price)
                price_clean = price_str.replace(".", "").replace("€", "").replace(" ", "").strip()
                try:
                    price_numeric = int(price_clean)
                except ValueError:
                    pass

        # Power fields
        power_numeric = None
        power_str = None
        if listing.power_cv is not None:
            if isinstance(listing.power_cv, int):
                power_numeric = listing.power_cv
                power_str = f"{listing.power_cv} CV"
            else:
                power_str = str(listing.power_cv)
                power_clean = power_str.replace(" CV", "").replace("CV", "").replace("cv", "").strip()
                try:
                    power_numeric = int(power_clean)
                except ValueError:
                    pass

        return {
            "ad_id": listing.ad_id,
            "url": listing.url,
            "title": listing.title,
            "marca": listing.marca,
            "modelo": listing.modelo,
            "version": listing.version,
            "year": listing.year,
            "kilometers": km_str,
            "kilometers_numeric": km_numeric,
            "fuel": listing.fuel,
            "power": power_str,
            "power_numeric": power_numeric,
            "transmission": listing.transmission,
            "price": price_str,
            "price_numeric": price_numeric,
            "location": listing.location,
            "scraped_at": now,
            "created_at": now,
            "updated_at": now
        }

    def _dict_to_ocasionplus(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert OcasionPlus listing dict to ocasionplus table format.

        Args:
            data: Dictionary from OcasionPlusListing.to_dict()

        Returns:
            Dict ready for Supabase insert
        """
        now = datetime.utcnow().isoformat()

        # Format kilometers string
        km_str = None
        km_numeric = data.get("kilometros")
        if km_numeric:
            km_str = f"{km_numeric:,}".replace(",", ".") + " Km"

        # Format potencia string
        potencia_str = None
        potencia_cv = data.get("potencia_cv")
        if potencia_cv:
            potencia_str = f"{potencia_cv} CV"

        # Format precio string
        precio_str = None
        precio_contado = data.get("precio_contado")
        if precio_contado:
            precio_str = f"{precio_contado:,}".replace(",", ".") + "€"

        return {
            "listing_id": data.get("listing_id"),
            "url": data.get("url"),
            "marca": data.get("marca"),
            "modelo": data.get("modelo"),
            "version": data.get("version"),
            "titulo_completo": data.get("titulo_completo"),
            "potencia": potencia_str,
            "potencia_cv": potencia_cv,
            "precio": precio_str,
            "precio_contado": precio_contado,
            "precio_financiado": data.get("precio_financiado"),
            "cuota_mensual": data.get("cuota_mensual"),
            "year": data.get("year"),
            "kilometros": km_str,
            "kilometros_numeric": km_numeric,
            "combustible": data.get("combustible"),
            "transmision": data.get("transmision"),
            "etiqueta_ambiental": data.get("etiqueta_ambiental"),
            "ubicacion": data.get("ubicacion"),
            "imagen_url": data.get("imagen_url"),
            "scraped_at": now,
            "created_at": now,
            "updated_at": now
        }

    def save_ocasionplus_listings(self, listings_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Save OcasionPlus listings to database.

        Args:
            listings_data: List of dicts from OcasionPlusListing.to_dict()

        Returns:
            Stats dict with count saved
        """
        stats = {"ocasionplus": 0, "errors": 0, "duplicates_in_batch": 0}

        if not listings_data:
            return stats

        # Convert to table format
        data = [self._dict_to_ocasionplus(l) for l in listings_data]

        # Remove duplicates within the same batch (keep last occurrence)
        seen_ids = {}
        for item in data:
            listing_id = item.get("listing_id")
            if listing_id:
                seen_ids[listing_id] = item

        unique_data = list(seen_ids.values())
        stats["duplicates_in_batch"] = len(data) - len(unique_data)

        if not unique_data:
            return stats

        try:
            result = self.client.table("ocasionplus").upsert(
                unique_data,
                on_conflict="listing_id"
            ).execute()

            stats["ocasionplus"] = len(result.data) if result.data else 0
        except Exception as e:
            print(f"Error saving to ocasionplus: {e}")
            stats["errors"] = len(unique_data)

        return stats

    def _normalize_fuel(self, fuel: Optional[str]) -> Optional[str]:
        """Normalize fuel type to standard values."""
        if not fuel:
            return None

        fuel_lower = fuel.lower()

        if "diesel" in fuel_lower or "diésel" in fuel_lower:
            return "diesel"
        elif "gasolina" in fuel_lower or "petrol" in fuel_lower:
            return "gasolina"
        elif "eléctrico" in fuel_lower or "electrico" in fuel_lower or "electric" in fuel_lower:
            return "electrico"
        elif "híbrido" in fuel_lower or "hibrido" in fuel_lower or "hybrid" in fuel_lower:
            return "hibrido"
        elif "glp" in fuel_lower or "gas" in fuel_lower:
            return "gas"

        return fuel_lower

    def save_listing(self, listing: CarListing) -> Dict[str, Any]:
        """Save a single car listing to the appropriate table."""
        table_name = self.TABLE_MAPPING.get(listing.source)
        if not table_name:
            raise ValueError(f"Unknown source: {listing.source}")

        if listing.source == "cochesnet":
            data = self._listing_to_cochesnet(listing)
        elif listing.source == "clicars":
            data = self._listing_to_clicars(listing)
        else:
            data = self._listing_to_autocasion(listing)

        # Upsert based on ad_id
        result = self.client.table(table_name).upsert(
            data,
            on_conflict="ad_id"
        ).execute()

        return result.data[0] if result.data else {}

    def save_listings(self, listings: List[CarListing]) -> Dict[str, int]:
        """Save multiple listings, grouped by source."""
        stats = {"cochesnet": 0, "autocasion": 0, "clicars": 0, "ocasionplus": 0, "errors": 0}

        # Group by source
        by_source: Dict[str, List[CarListing]] = {}
        for listing in listings:
            source = listing.source
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(listing)

        # Save each group
        for source, source_listings in by_source.items():
            table_name = self.TABLE_MAPPING.get(source)
            if not table_name:
                stats["errors"] += len(source_listings)
                continue

            # Convert to table format
            if source == "cochesnet":
                data = [self._listing_to_cochesnet(l) for l in source_listings]
            elif source == "clicars":
                data = [self._listing_to_clicars(l) for l in source_listings]
            else:
                data = [self._listing_to_autocasion(l) for l in source_listings]

            try:
                # Batch upsert
                result = self.client.table(table_name).upsert(
                    data,
                    on_conflict="ad_id"
                ).execute()

                stats[source] = len(result.data) if result.data else 0
            except Exception as e:
                print(f"Error saving to {table_name}: {e}")
                stats["errors"] += len(source_listings)

        return stats

    def get_existing_ad_ids(self, source: str, ad_ids: List[str]) -> set:
        """Get set of ad_ids that already exist in the database."""
        table_name = self.TABLE_MAPPING.get(source)
        if not table_name:
            return set()

        result = self.client.table(table_name).select("ad_id").in_("ad_id", ad_ids).execute()

        return {row["ad_id"] for row in result.data} if result.data else set()

    def count_by_source(self, source: str) -> int:
        """Count total listings for a source."""
        table_name = self.TABLE_MAPPING.get(source)
        if not table_name:
            return 0

        result = self.client.table(table_name).select("id", count="exact").execute()
        return result.count or 0

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all tables."""
        stats = {}
        for source, table in self.TABLE_MAPPING.items():
            try:
                result = self.client.table(table).select("id", count="exact").execute()
                stats[source] = {
                    "total": result.count or 0,
                    "table": table
                }
            except Exception as e:
                stats[source] = {"error": str(e)}

        return stats

    # =====================
    # OBJETIVO TABLES
    # =====================

    OBJETIVO_MAPPING = {
        "cochesnet": "objetivo_coches_net",
        "autocasion": "objetivo_autocasion"
    }

    def get_objetivos(self, source: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get scraping objectives for a source."""
        table_name = self.OBJETIVO_MAPPING.get(source)
        if not table_name:
            return []

        result = self.client.table(table_name).select("*").limit(limit).execute()
        return result.data if result.data else []

    def get_pending_objetivos(self, source: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get objectives that haven't been scraped or failed."""
        table_name = self.OBJETIVO_MAPPING.get(source)
        if not table_name:
            return []

        # Get objectives ordered by priority (autocasion) or attempts
        if source == "autocasion":
            result = self.client.table(table_name).select("*")\
                .order("prioridad", desc=True)\
                .order("scraping_attempts")\
                .limit(limit).execute()
        else:
            result = self.client.table(table_name).select("*")\
                .order("scraping_attempts")\
                .limit(limit).execute()

        return result.data if result.data else []

    def get_objetivo_by_marca(self, source: str, marca: str) -> Optional[Dict[str, Any]]:
        """Get objective for a specific brand."""
        table_name = self.OBJETIVO_MAPPING.get(source)
        if not table_name:
            return None

        result = self.client.table(table_name).select("*")\
            .eq("marca", marca.lower()).limit(1).execute()

        return result.data[0] if result.data else None

    def update_objetivo_status(
        self,
        source: str,
        marca: str,
        status: str,
        cars_scraped: int = 0,
        pages_scraped: int = 0,
        duration_seconds: Optional[float] = None
    ) -> bool:
        """Update scraping status for an objective."""
        table_name = self.OBJETIVO_MAPPING.get(source)
        if not table_name:
            return False

        now = datetime.utcnow().isoformat()

        update_data = {
            "last_scraped": now,
            "last_status": status,
            "updated_at": now
        }

        if source == "cochesnet":
            # cochesnet has different column names
            objetivo = self.get_objetivo_by_marca(source, marca)
            if objetivo:
                update_data["total_cars_scraped"] = objetivo.get("total_cars_scraped", 0) + cars_scraped
                update_data["total_pages_scraped"] = objetivo.get("total_pages_scraped", 0) + pages_scraped
                update_data["scraping_attempts"] = objetivo.get("scraping_attempts", 0) + 1
                if duration_seconds:
                    update_data["last_scraping_duration_seconds"] = duration_seconds
        else:
            # autocasion
            objetivo = self.get_objetivo_by_marca(source, marca)
            if objetivo:
                update_data["scraping_attempts"] = objetivo.get("scraping_attempts", 0) + 1

        try:
            self.client.table(table_name).update(update_data)\
                .eq("marca", marca.lower()).execute()
            return True
        except Exception as e:
            print(f"Error updating objetivo: {e}")
            return False

    def get_all_marcas(self, source: str) -> List[str]:
        """Get all brands from objectives table."""
        table_name = self.OBJETIVO_MAPPING.get(source)
        if not table_name:
            return []

        result = self.client.table(table_name).select("marca").execute()
        return [row["marca"] for row in result.data] if result.data else []

    def get_objetivo_url(self, source: str, marca: str) -> Optional[str]:
        """Get the scraping URL for a brand."""
        objetivo = self.get_objetivo_by_marca(source, marca)
        if not objetivo:
            return None

        if source == "cochesnet":
            return objetivo.get("url_general")
        else:
            return objetivo.get("url")


# Global client instance
_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client
