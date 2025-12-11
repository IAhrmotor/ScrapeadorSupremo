"""
Title parser using marca_modelos reference table.

Estrategia de parsing inteligente:
1. Cargar tabla marca_modelos en cache
2. Normalizar título (lowercase, sin acentos)
3. Buscar marca (longest match first)
4. Buscar modelo (longest match first dentro de modelos de esa marca)
5. Version = resto del título
"""

import re
import unicodedata
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedTitle:
    """Resultado del parsing de título."""
    marca: Optional[str] = None
    modelo: Optional[str] = None
    version: Optional[str] = None
    confidence: float = 0.0  # 0-1, qué tan seguro estamos


class TitleParser:
    """
    Parser de títulos usando tabla de referencia marca_modelos.

    Ejemplos:
        "OPEL Corsa 1.5D DT 74kW 100CV Edition 5p."
        → marca="OPEL", modelo="Corsa", version="1.5D DT 74kW 100CV Edition 5p."

        "BMW Serie 3 320d 140 kW (190 CV)"
        → marca="BMW", modelo="Serie 3", version="320d 140 kW (190 CV)"

        "Mercedes-Benz Clase A A 200 CDI"
        → marca="Mercedes-Benz", modelo="Clase A", version="A 200 CDI"
    """

    def __init__(self, supabase_client=None):
        """
        Initialize parser.

        Args:
            supabase_client: Optional Supabase client to load marca_modelos
        """
        self._supabase = supabase_client
        self._marca_modelos_cache: Optional[Dict[str, List[str]]] = None
        self._marcas_normalized: Optional[List[Tuple[str, str]]] = None  # (normalized, original)

    def load_marca_modelos(self) -> bool:
        """
        Load marca_modelos from Supabase and build cache.

        Expected table structure:
            marcas_modelos_validos (
                id BIGSERIAL PRIMARY KEY,
                marca TEXT,           -- "OPEL", "BMW", "Mercedes-Benz"
                modelo TEXT,          -- "Corsa", "Serie 3", "Clase A"
                modelo_normalized TEXT -- "corsa", "serie3", "clasea" (optional)
            )

        Returns:
            True if loaded successfully
        """
        if not self._supabase:
            logger.warning("No Supabase client provided, using fallback parsing")
            return False

        try:
            # Fetch all marcas_modelos_validos with pagination
            # Supabase has a 1000 row limit by default, so we need to fetch all pages
            all_data = []
            page_size = 1000
            offset = 0

            while True:
                result = self._supabase.client.table('marcas_modelos_validos')\
                    .select('marca, modelo')\
                    .range(offset, offset + page_size - 1)\
                    .execute()

                if not result.data:
                    break

                all_data.extend(result.data)
                logger.debug(f"Fetched {len(result.data)} rows (offset {offset})")

                # If we got less than page_size rows, we're done
                if len(result.data) < page_size:
                    break

                offset += page_size

            if not all_data:
                logger.warning("marca_modelos table is empty")
                return False

            logger.info(f"Fetched {len(all_data)} total marca-modelo records from database")

            # Build cache: {marca_normalized: [modelo1, modelo2, ...]}
            cache = {}
            marcas_set = set()

            for row in all_data:
                marca = row.get('marca')
                modelo = row.get('modelo')

                if not marca or not modelo:
                    continue

                marca_norm = self._normalize(marca)
                marcas_set.add((marca_norm, marca))  # (normalized, original)

                if marca_norm not in cache:
                    cache[marca_norm] = []

                cache[marca_norm].append(modelo)

            # Sort modelos by length (longest first) for better matching
            for marca_norm in cache:
                cache[marca_norm].sort(key=len, reverse=True)

            # Sort marcas by length (longest first)
            self._marcas_normalized = sorted(marcas_set, key=lambda x: len(x[0]), reverse=True)
            self._marca_modelos_cache = cache

            logger.info(f"Loaded {len(self._marcas_normalized)} brands and {sum(len(v) for v in cache.values())} models")
            return True

        except Exception as e:
            logger.error(f"Error loading marca_modelos: {e}")
            return False

    def parse(self, title: str) -> ParsedTitle:
        """
        Parse title into marca, modelo, version.

        Strategy:
        1. Try database-based parsing (if marca_modelos loaded)
        2. Fall back to heuristic parsing

        Args:
            title: Car title like "OPEL Corsa 1.5D DT 74kW 100CV Edition 5p."

        Returns:
            ParsedTitle with marca, modelo, version, confidence
        """
        if not title:
            return ParsedTitle()

        # Try database parsing first
        if self._marca_modelos_cache:
            result = self._parse_with_db(title)
            if result.confidence > 0.5:
                return result

        # Fallback to heuristic
        return self._parse_heuristic(title)

    def _parse_with_db(self, title: str) -> ParsedTitle:
        """
        Parse using marca_modelos database.

        Algorithm:
        1. Normalize title
        2. Find marca (longest match first)
        3. Find modelo (longest match first within marca's modelos)
        4. Version = rest of title
        """
        title_norm = self._normalize(title)
        title_lower = title.lower()

        # 1. Find marca
        marca_found = None
        marca_original = None
        marca_end_pos = 0

        for marca_norm, marca_orig in self._marcas_normalized:
            # Check if marca is at start of title
            if title_norm.startswith(marca_norm):
                marca_found = marca_norm
                marca_original = marca_orig
                marca_end_pos = len(marca_norm)
                break

            # Also check with space/hyphen boundaries
            pattern = rf'\b{re.escape(marca_norm)}\b'
            match = re.match(pattern, title_norm)
            if match:
                marca_found = marca_norm
                marca_original = marca_orig
                marca_end_pos = match.end()
                break

        if not marca_found:
            return ParsedTitle(confidence=0.0)

        # 2. Find modelo
        # Get remaining text after marca
        remaining = title_norm[marca_end_pos:].strip()
        remaining_original = title[marca_end_pos:].strip()

        modelos = self._marca_modelos_cache.get(marca_found, [])
        modelo_found = None
        modelo_end_pos = 0

        for modelo in modelos:
            modelo_norm = self._normalize(modelo)

            # Check if modelo is at start of remaining text
            if remaining.startswith(modelo_norm):
                modelo_found = modelo
                modelo_end_pos = len(modelo_norm)
                break

            # Check with word boundaries
            pattern = rf'\b{re.escape(modelo_norm)}\b'
            match = re.match(pattern, remaining)
            if match:
                modelo_found = modelo
                modelo_end_pos = match.end()
                break

        if not modelo_found:
            # If no modelo found, use heuristic: first 1-2 words
            words = remaining_original.split()
            if len(words) >= 2 and self._looks_like_modelo(words[0], words[1]):
                modelo_found = f"{words[0]} {words[1]}"
                modelo_end_pos = len(modelo_found)
            elif words:
                modelo_found = words[0]
                modelo_end_pos = len(words[0])
            else:
                return ParsedTitle(
                    marca=marca_original,
                    confidence=0.5  # Found marca but no modelo
                )

        # 3. Version = rest of text
        version = remaining_original[modelo_end_pos:].strip()

        confidence = 1.0 if modelo_found in modelos else 0.7

        return ParsedTitle(
            marca=marca_original,
            modelo=modelo_found,
            version=version if version else None,
            confidence=confidence
        )

    def _parse_heuristic(self, title: str) -> ParsedTitle:
        """
        Fallback heuristic parsing when database not available.

        Rules:
        1. First word = marca
        2. Next 1-2 words = modelo (if uppercase or common patterns)
        3. Rest = version

        Examples:
            "OPEL Corsa 1.5D" → marca="OPEL", modelo="Corsa", version="1.5D"
            "BMW Serie 3 320d" → marca="BMW", modelo="Serie 3", version="320d"
            "Mercedes-Benz Clase A A 200" → marca="Mercedes-Benz", modelo="Clase A", version="A 200"
        """
        parts = title.split()
        if not parts:
            return ParsedTitle(confidence=0.0)

        # 1. Marca = first word (or first 2 if hyphenated)
        if len(parts) >= 2 and '-' in parts[0]:
            marca = f"{parts[0]} {parts[1]}" if not parts[1][0].islower() else parts[0]
            start_idx = 2 if marca.endswith(parts[1]) else 1
        else:
            marca = parts[0]
            start_idx = 1

        if start_idx >= len(parts):
            return ParsedTitle(marca=marca, confidence=0.3)

        # 2. Modelo = next 1-2 words
        # Check if next word is capitalized or common modelo pattern
        modelo_parts = []
        current_idx = start_idx

        # First word of modelo
        if current_idx < len(parts):
            modelo_parts.append(parts[current_idx])
            current_idx += 1

        # Second word if it looks like part of modelo
        if current_idx < len(parts):
            next_word = parts[current_idx]
            if self._looks_like_modelo_part(next_word):
                modelo_parts.append(next_word)
                current_idx += 1

        modelo = ' '.join(modelo_parts) if modelo_parts else None

        # 3. Version = rest
        version_parts = parts[current_idx:]
        version = ' '.join(version_parts) if version_parts else None

        return ParsedTitle(
            marca=marca,
            modelo=modelo,
            version=version,
            confidence=0.5  # Lower confidence for heuristic
        )

    def _normalize(self, text: str) -> str:
        """
        Normalize text for matching.

        Transformations:
        - Lowercase
        - Remove accents
        - Remove special chars except space/hyphen
        - Collapse multiple spaces
        """
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Remove accents
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )

        # Keep only alphanumeric, space, hyphen
        text = re.sub(r'[^a-z0-9\s\-]', '', text)

        # Collapse spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _looks_like_modelo_part(self, word: str) -> bool:
        """Check if word looks like part of modelo name."""
        # Common modelo patterns
        patterns = [
            r'^[A-Z]',              # Starts uppercase
            r'^Serie',              # "Serie 3"
            r'^Clase',              # "Clase A"
            r'^\d+$',               # Pure number "3", "5"
        ]

        return any(re.match(p, word) for p in patterns)

    def _looks_like_modelo(self, word1: str, word2: str) -> bool:
        """Check if two words together look like a modelo."""
        combined = f"{word1} {word2}"

        # Common two-word modelo patterns
        two_word_patterns = [
            r'^Serie\s+\d+',        # "Serie 3"
            r'^Clase\s+[A-Z]',      # "Clase A"
            r'^[A-Z]+\s+\d+',       # "X5", "Q7"
        ]

        return any(re.match(p, combined, re.IGNORECASE) for p in two_word_patterns)


# Global instance
_parser: Optional[TitleParser] = None


def get_title_parser(supabase_client=None, force_reload: bool = False) -> TitleParser:
    """
    Get global title parser instance.

    Args:
        supabase_client: Supabase client to load marca_modelos
        force_reload: Force reload of marca_modelos from DB

    Returns:
        TitleParser instance
    """
    global _parser

    if _parser is None or force_reload:
        _parser = TitleParser(supabase_client)
        if supabase_client:
            _parser.load_marca_modelos()

    return _parser
