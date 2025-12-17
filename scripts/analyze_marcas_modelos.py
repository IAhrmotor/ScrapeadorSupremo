"""
Script para analizar todas las marcas_norm y modelos_norm de vehiculos_combinados_v4
"""
import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_all_brands_and_models():
    """Obtiene todas las marcas y sus modelos de vehiculos_combinados_v4"""

    print("=" * 80)
    print("ANALISIS DE MARCAS Y MODELOS - vehiculos_combinados_v4")
    print("=" * 80)

    # Obtener todas las marcas unicas
    response = supabase.table('vehiculos_combinados_v4')\
        .select('marca_norm')\
        .not_.is_('marca_norm', 'null')\
        .execute()

    marcas = set(r['marca_norm'] for r in response.data if r.get('marca_norm'))
    marcas_sorted = sorted(marcas)

    print(f"\nTotal marcas unicas: {len(marcas_sorted)}")
    print("-" * 80)

    # Para cada marca, obtener sus modelos
    brand_models = {}

    for marca in marcas_sorted:
        response = supabase.table('vehiculos_combinados_v4')\
            .select('modelo_norm')\
            .eq('marca_norm', marca)\
            .not_.is_('modelo_norm', 'null')\
            .execute()

        modelos = defaultdict(int)
        for r in response.data:
            if r.get('modelo_norm'):
                modelos[r['modelo_norm']] += 1

        brand_models[marca] = modelos

    # Mostrar resultados
    for marca in marcas_sorted:
        modelos = brand_models[marca]
        total_vehiculos = sum(modelos.values())

        print(f"\n{'=' * 80}")
        print(f"MARCA: {marca} ({total_vehiculos} vehiculos, {len(modelos)} modelos)")
        print(f"{'=' * 80}")

        # Ordenar modelos por cantidad
        modelos_sorted = sorted(modelos.items(), key=lambda x: -x[1])

        for modelo, count in modelos_sorted[:30]:  # Top 30 modelos
            print(f"  {modelo}: {count}")

        if len(modelos) > 30:
            print(f"  ... y {len(modelos) - 30} modelos mas")

    return brand_models


def find_problematic_models():
    """Busca modelos problematicos"""

    print("\n" + "=" * 80)
    print("MODELOS PROBLEMATICOS")
    print("=" * 80)

    # Modelos que contienen la marca
    response = supabase.rpc('execute_sql', {
        'query': """
        SELECT marca_norm, modelo_norm, COUNT(*) as total
        FROM vehiculos_combinados_v4
        WHERE modelo_norm IS NOT NULL
          AND (
            modelo_norm LIKE '%' || marca_norm || '%'
            OR modelo_norm LIKE '%  %'
            OR modelo_norm LIKE '%--%'
            OR LENGTH(modelo_norm) > 40
          )
        GROUP BY marca_norm, modelo_norm
        ORDER BY total DESC
        LIMIT 100
        """
    }).execute()

    if response.data:
        print("\nModelos con marca duplicada, espacios dobles o muy largos:")
        for row in response.data:
            print(f"  {row['marca_norm']}: '{row['modelo_norm']}' ({row['total']})")


def export_to_csv():
    """Exporta marcas y modelos a CSV"""
    import csv

    response = supabase.table('vehiculos_combinados_v4')\
        .select('marca_norm, modelo_norm')\
        .not_.is_('marca_norm', 'null')\
        .execute()

    # Contar combinaciones
    combinations = defaultdict(int)
    for r in response.data:
        marca = r.get('marca_norm', '')
        modelo = r.get('modelo_norm', '')
        combinations[(marca, modelo)] += 1

    # Exportar
    with open('marcas_modelos_v4.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['marca_norm', 'modelo_norm', 'count'])
        for (marca, modelo), count in sorted(combinations.items()):
            writer.writerow([marca, modelo, count])

    print(f"\nExportado a marcas_modelos_v4.csv ({len(combinations)} combinaciones)")


if __name__ == "__main__":
    brand_models = get_all_brands_and_models()
    # find_problematic_models()  # Descomentar si quieres buscar problemas
    # export_to_csv()  # Descomentar para exportar a CSV
