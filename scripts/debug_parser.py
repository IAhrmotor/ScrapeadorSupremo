"""
Script de debugging para identificar fisuras en el parseo de modelos.

Este script analiza el proceso de normalización y matching para entender
por qué algunos modelos no se están encontrando en la base de datos.

Usage:
    python scripts/debug_parser.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.base.title_parser import get_title_parser
from scraping.storage.supabase_client import get_supabase_client


def debug_normalization(parser, text):
    """Debug the normalization process."""
    normalized = parser._normalize(text)
    print(f"  Original: '{text}'")
    print(f"  Normalized: '{normalized}'")
    return normalized


def debug_marca_matching(parser, title):
    """Debug marca matching process."""
    print(f"\n[DEBUG] Marca matching for: '{title}'")

    title_norm = parser._normalize(title)
    print(f"  Title normalized: '{title_norm}'")

    print(f"\n  Checking against {len(parser._marcas_normalized)} marcas...")

    # Show first 10 marcas in cache
    print("\n  Top 10 marcas (by length):")
    for i, (marca_norm, marca_orig) in enumerate(parser._marcas_normalized[:10], 1):
        match_status = "OK MATCH" if title_norm.startswith(marca_norm) else "NO"
        print(f"    {i}. '{marca_orig}' (normalized: '{marca_norm}') {match_status}")

    # Find the actual match
    for marca_norm, marca_orig in parser._marcas_normalized:
        if title_norm.startswith(marca_norm):
            print(f"\n  OK FOUND MARCA: '{marca_orig}' (normalized: '{marca_norm}')")
            return marca_norm, marca_orig, len(marca_norm)

    print(f"\n  NO MARCA MATCH FOUND")
    return None, None, 0


def debug_modelo_matching(parser, marca_norm, remaining_text):
    """Debug modelo matching process."""
    print(f"\n[DEBUG] Modelo matching")
    print(f"  Marca found: '{marca_norm}'")
    print(f"  Remaining text: '{remaining_text}'")

    remaining_norm = parser._normalize(remaining_text)
    print(f"  Remaining normalized: '{remaining_norm}'")

    modelos = parser._marca_modelos_cache.get(marca_norm, [])
    print(f"\n  Available modelos for this marca: {len(modelos)}")
    print(f"  Top 10 modelos (by length):")

    for i, modelo in enumerate(modelos[:10], 1):
        modelo_norm = parser._normalize(modelo)

        # Check different matching strategies
        starts_with = remaining_norm.startswith(modelo_norm)
        word_boundary = remaining_norm.startswith(modelo_norm + ' ') or remaining_norm == modelo_norm

        match_status = "OK" if starts_with or word_boundary else "NO"

        print(f"    {i}. '{modelo}' (normalized: '{modelo_norm}') {match_status}")
        print(f"        starts_with: {starts_with}, word_boundary: {word_boundary}")

    # Find actual match
    for modelo in modelos:
        modelo_norm = parser._normalize(modelo)

        if remaining_norm.startswith(modelo_norm):
            print(f"\n  OK FOUND MODELO: '{modelo}' (normalized: '{modelo_norm}')")
            return modelo, len(modelo_norm)

    print(f"\n  NO MODELO MATCH FOUND - Will use heuristic fallback")
    return None, 0


def test_specific_titles():
    """Test specific problematic titles with detailed debugging."""

    print("="*80)
    print("PARSER DEBUGGING - Identificando fisuras en el matching")
    print("="*80)

    # Initialize parser
    client = get_supabase_client()
    parser = get_title_parser(client, force_reload=True)

    # Problematic titles from test
    problematic_titles = [
        ("BMW Serie 3 320d 140 kW (190 CV)", "Should match: BMW / Serie 3"),
        ("Volkswagen Golf 2.0 TDI 110kW", "Should match: Volkswagen / Golf"),
        ("Audi A4 2.0 TDI 110kW", "Should match: Audi / A4"),
        ("Renault Clio 1.5 dCi Energy", "Should match: Renault / Clio"),
        ("Land Rover Range Rover Evoque 2.0D", "Should match: Land Rover / Range Rover"),
    ]

    for title, expected in problematic_titles:
        print("\n" + "="*80)
        print(f"TESTING: {title}")
        print(f"EXPECTED: {expected}")
        print("="*80)

        # Step 1: Debug marca matching
        marca_norm, marca_orig, marca_end_pos = debug_marca_matching(parser, title)

        if not marca_norm:
            print("\nFISURA: No se encontro la marca")
            continue

        # Step 2: Debug modelo matching
        remaining = title[marca_end_pos:].strip()
        modelo, modelo_end_pos = debug_modelo_matching(parser, marca_norm, remaining)

        if not modelo:
            print("\nFISURA: Marca encontrada pero modelo no")

            # Show what heuristic would do
            words = remaining.split()
            if words:
                print(f"\n  Heuristic would use: '{words[0]}'")
                if len(words) >= 2:
                    print(f"  Or maybe: '{words[0]} {words[1]}'")

        # Step 3: Parse and compare
        print("\n[ACTUAL PARSE RESULT]")
        parsed = parser.parse(title)
        print(f"  Marca: {parsed.marca}")
        print(f"  Modelo: {parsed.modelo}")
        print(f"  Version: {parsed.version}")
        print(f"  Confidence: {parsed.confidence}")

        # Analysis
        if parsed.confidence == 1.0:
            print("\nPERFECT MATCH - No fisura aqui")
        elif parsed.confidence >= 0.7:
            print("\nFISURA PARCIAL - Marca OK, modelo con heuristica")
        else:
            print("\nFISURA TOTAL - Parseo completamente heuristico")


def analyze_normalization_issues():
    """Analyze specific normalization edge cases."""

    print("\n" + "="*80)
    print("ANALISIS DE NORMALIZACION")
    print("="*80)

    client = get_supabase_client()
    parser = get_title_parser(client)

    test_cases = [
        ("Serie 3", "serie3 or serie 3?"),
        ("Clase A", "clasea or clase a?"),
        ("Range Rover", "rangerover or range rover?"),
        ("T-Roc", "troc or t-roc?"),
        ("Q4 e-tron", "q4etron or q4 e-tron?"),
        ("500X", "500x?"),
        ("C3 Aircross", "c3aircross or c3 aircross?"),
    ]

    print("\nCasos especiales de normalización:\n")

    for text, question in test_cases:
        normalized = parser._normalize(text)
        print(f"  '{text}' -> '{normalized}' ({question})")

    # Check if these exist in DB
    print("\n\nVerificando en cache de modelos:")

    for marca_norm, modelos in list(parser._marca_modelos_cache.items())[:5]:
        print(f"\n  Marca: '{marca_norm}'")
        for modelo in modelos[:3]:
            modelo_norm = parser._normalize(modelo)
            print(f"    - '{modelo}' -> '{modelo_norm}'")


def check_database_content():
    """Check actual database content for common models."""

    print("\n" + "="*80)
    print("VERIFICACION DE CONTENIDO EN BD")
    print("="*80)

    client = get_supabase_client()

    # Check specific marca-modelo combinations
    test_combinations = [
        ("BMW", "Serie 3"),
        ("Volkswagen", "Golf"),
        ("Audi", "A4"),
        ("Renault", "Clio"),
        ("Land Rover", "Range Rover"),
        ("Mercedes-Benz", "Clase A"),
    ]

    print("\nBuscando combinaciones específicas en BD:\n")

    for marca, modelo in test_combinations:
        try:
            result = client.client.table('marcas_modelos_validos').select('*').eq('marca', marca).eq('modelo', modelo).execute()

            if result.data:
                print(f"  OK '{marca}' / '{modelo}' - EXISTE en BD")
            else:
                print(f"  NO '{marca}' / '{modelo}' - NO EXISTE en BD")
        except Exception as e:
            print(f"  ? '{marca}' / '{modelo}' - ERROR: {e}")

    # Check variations
    print("\n\nBuscando variaciones de 'Golf':")
    try:
        result = client.client.table('marcas_modelos_validos').select('*').ilike('modelo', '%golf%').execute()
        print(f"  Encontrados {len(result.data)} registros:")
        for row in result.data[:5]:
            print(f"    - {row['marca']} / {row['modelo']}")
    except Exception as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    print("\nINICIANDO ANALISIS DE FISURAS EN EL PARSER\n")

    # 1. Check database content first
    check_database_content()

    # 2. Analyze normalization
    analyze_normalization_issues()

    # 3. Test specific problematic titles
    test_specific_titles()

    print("\n" + "="*80)
    print("ANALISIS COMPLETADO")
    print("="*80)
