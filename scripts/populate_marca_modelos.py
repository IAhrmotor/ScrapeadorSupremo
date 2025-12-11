"""
Script para poblar la tabla marca_modelos con marcas y modelos comunes en España.

Este script inserta las combinaciones más comunes de marca-modelo para mejorar
el parseo automático de títulos de anuncios.

Usage:
    python scripts/populate_marca_modelos.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.storage.supabase_client import get_supabase_client


# Marcas y modelos más comunes en España (2024)
MARCA_MODELOS = [
    # SEAT (marca española más vendida)
    ("SEAT", "Ibiza"),
    ("SEAT", "León"),
    ("SEAT", "Arona"),
    ("SEAT", "Ateca"),
    ("SEAT", "Tarraco"),
    ("SEAT", "Alhambra"),
    ("SEAT", "Mii"),
    ("SEAT", "Toledo"),

    # OPEL (muy popular en España)
    ("OPEL", "Corsa"),
    ("OPEL", "Astra"),
    ("OPEL", "Insignia"),
    ("OPEL", "Crossland"),
    ("OPEL", "Grandland"),
    ("OPEL", "Mokka"),
    ("OPEL", "Combo"),
    ("OPEL", "Zafira"),

    # Volkswagen
    ("Volkswagen", "Golf"),
    ("Volkswagen", "Polo"),
    ("Volkswagen", "Passat"),
    ("Volkswagen", "Tiguan"),
    ("Volkswagen", "T-Roc"),
    ("Volkswagen", "T-Cross"),
    ("Volkswagen", "Touareg"),
    ("Volkswagen", "Arteon"),
    ("Volkswagen", "Touran"),
    ("Volkswagen", "Caddy"),

    # BMW
    ("BMW", "Serie 1"),
    ("BMW", "Serie 2"),
    ("BMW", "Serie 3"),
    ("BMW", "Serie 4"),
    ("BMW", "Serie 5"),
    ("BMW", "Serie 6"),
    ("BMW", "Serie 7"),
    ("BMW", "X1"),
    ("BMW", "X2"),
    ("BMW", "X3"),
    ("BMW", "X4"),
    ("BMW", "X5"),
    ("BMW", "X6"),
    ("BMW", "X7"),
    ("BMW", "Z4"),
    ("BMW", "i3"),
    ("BMW", "i4"),
    ("BMW", "iX"),

    # Mercedes-Benz
    ("Mercedes-Benz", "Clase A"),
    ("Mercedes-Benz", "Clase B"),
    ("Mercedes-Benz", "Clase C"),
    ("Mercedes-Benz", "Clase E"),
    ("Mercedes-Benz", "Clase S"),
    ("Mercedes-Benz", "CLA"),
    ("Mercedes-Benz", "CLS"),
    ("Mercedes-Benz", "GLA"),
    ("Mercedes-Benz", "GLB"),
    ("Mercedes-Benz", "GLC"),
    ("Mercedes-Benz", "GLE"),
    ("Mercedes-Benz", "GLS"),
    ("Mercedes-Benz", "EQA"),
    ("Mercedes-Benz", "EQB"),
    ("Mercedes-Benz", "EQC"),
    ("Mercedes-Benz", "EQE"),
    ("Mercedes-Benz", "EQS"),

    # Audi
    ("Audi", "A1"),
    ("Audi", "A3"),
    ("Audi", "A4"),
    ("Audi", "A5"),
    ("Audi", "A6"),
    ("Audi", "A7"),
    ("Audi", "A8"),
    ("Audi", "Q2"),
    ("Audi", "Q3"),
    ("Audi", "Q4 e-tron"),
    ("Audi", "Q5"),
    ("Audi", "Q7"),
    ("Audi", "Q8"),
    ("Audi", "TT"),
    ("Audi", "e-tron"),

    # Renault
    ("Renault", "Clio"),
    ("Renault", "Megane"),
    ("Renault", "Captur"),
    ("Renault", "Kadjar"),
    ("Renault", "Koleos"),
    ("Renault", "Scenic"),
    ("Renault", "Talisman"),
    ("Renault", "Zoe"),
    ("Renault", "Twingo"),

    # Peugeot
    ("Peugeot", "208"),
    ("Peugeot", "308"),
    ("Peugeot", "508"),
    ("Peugeot", "2008"),
    ("Peugeot", "3008"),
    ("Peugeot", "5008"),
    ("Peugeot", "Rifter"),
    ("Peugeot", "Partner"),

    # Citroën
    ("Citroën", "C3"),
    ("Citroën", "C4"),
    ("Citroën", "C5"),
    ("Citroën", "C3 Aircross"),
    ("Citroën", "C5 Aircross"),
    ("Citroën", "Berlingo"),
    ("Citroën", "SpaceTourer"),

    # Ford
    ("Ford", "Fiesta"),
    ("Ford", "Focus"),
    ("Ford", "Mondeo"),
    ("Ford", "Kuga"),
    ("Ford", "Puma"),
    ("Ford", "Explorer"),
    ("Ford", "Mustang"),
    ("Ford", "Transit"),
    ("Ford", "Ranger"),

    # Nissan
    ("Nissan", "Micra"),
    ("Nissan", "Juke"),
    ("Nissan", "Qashqai"),
    ("Nissan", "X-Trail"),
    ("Nissan", "Leaf"),
    ("Nissan", "Ariya"),

    # Toyota
    ("Toyota", "Yaris"),
    ("Toyota", "Corolla"),
    ("Toyota", "Camry"),
    ("Toyota", "RAV4"),
    ("Toyota", "C-HR"),
    ("Toyota", "Highlander"),
    ("Toyota", "Prius"),
    ("Toyota", "Aygo"),

    # Hyundai
    ("Hyundai", "i10"),
    ("Hyundai", "i20"),
    ("Hyundai", "i30"),
    ("Hyundai", "Kona"),
    ("Hyundai", "Tucson"),
    ("Hyundai", "Santa Fe"),
    ("Hyundai", "Ioniq"),

    # Kia
    ("Kia", "Picanto"),
    ("Kia", "Rio"),
    ("Kia", "Ceed"),
    ("Kia", "Stonic"),
    ("Kia", "Niro"),
    ("Kia", "Sportage"),
    ("Kia", "Sorento"),
    ("Kia", "EV6"),

    # Mazda
    ("Mazda", "Mazda2"),
    ("Mazda", "Mazda3"),
    ("Mazda", "Mazda6"),
    ("Mazda", "CX-3"),
    ("Mazda", "CX-5"),
    ("Mazda", "CX-30"),
    ("Mazda", "CX-60"),
    ("Mazda", "MX-5"),

    # Volvo
    ("Volvo", "XC40"),
    ("Volvo", "XC60"),
    ("Volvo", "XC90"),
    ("Volvo", "V40"),
    ("Volvo", "V60"),
    ("Volvo", "V90"),
    ("Volvo", "S60"),
    ("Volvo", "S90"),

    # Skoda
    ("Skoda", "Fabia"),
    ("Skoda", "Octavia"),
    ("Skoda", "Superb"),
    ("Skoda", "Kamiq"),
    ("Skoda", "Karoq"),
    ("Skoda", "Kodiaq"),
    ("Skoda", "Enyaq"),

    # Dacia
    ("Dacia", "Sandero"),
    ("Dacia", "Duster"),
    ("Dacia", "Jogger"),
    ("Dacia", "Spring"),

    # Fiat
    ("Fiat", "500"),
    ("Fiat", "Panda"),
    ("Fiat", "Tipo"),
    ("Fiat", "500X"),

    # Tesla
    ("Tesla", "Model 3"),
    ("Tesla", "Model S"),
    ("Tesla", "Model X"),
    ("Tesla", "Model Y"),

    # Otros modelos chinos populares
    ("BYD", "Seal"),
    ("BYD", "Dolphin"),
    ("BYD", "Atto 3"),
    ("MG", "ZS"),
    ("MG", "Marvel R"),
    ("MG", "MG4"),

    # Mini
    ("Mini", "Cooper"),
    ("Mini", "Countryman"),
    ("Mini", "Clubman"),

    # Land Rover
    ("Land Rover", "Discovery"),
    ("Land Rover", "Range Rover"),
    ("Land Rover", "Defender"),
    ("Land Rover", "Evoque"),

    # Jeep
    ("Jeep", "Renegade"),
    ("Jeep", "Compass"),
    ("Jeep", "Wrangler"),
    ("Jeep", "Grand Cherokee"),

    # Alfa Romeo
    ("Alfa Romeo", "Giulia"),
    ("Alfa Romeo", "Stelvio"),
    ("Alfa Romeo", "Tonale"),

    # DS
    ("DS", "DS 3"),
    ("DS", "DS 4"),
    ("DS", "DS 7"),

    # Honda
    ("Honda", "Civic"),
    ("Honda", "CR-V"),
    ("Honda", "Jazz"),
    ("Honda", "HR-V"),
    ("Honda", "e"),

    # Suzuki
    ("Suzuki", "Swift"),
    ("Suzuki", "Vitara"),
    ("Suzuki", "S-Cross"),
    ("Suzuki", "Ignis"),
]


def main():
    """Poblar tabla marca_modelos."""
    print("="*60)
    print("POBLANDO TABLA marca_modelos")
    print("="*60)

    # Conectar a Supabase
    client = get_supabase_client()

    print(f"\nTotal marcas-modelos a insertar: {len(MARCA_MODELOS)}")
    print("\nVerificando tabla marca_modelos...")

    # Verificar si la tabla existe
    try:
        result = client.client.table('marcas_modelos_validos').select('count', count='exact').execute()
        existing_count = result.count or 0
        print(f"Registros existentes en marcas_modelos_validos: {existing_count}")
    except Exception as e:
        print(f"Error accediendo a marcas_modelos_validos: {e}")
        print("\nAsegúrate de crear la tabla primero:")
        print("""
CREATE TABLE marca_modelos (
    id BIGSERIAL PRIMARY KEY,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(marca, modelo)
);

CREATE INDEX idx_marca_modelos_marca ON marca_modelos(marca);
CREATE INDEX idx_marca_modelos_modelo ON marca_modelos(modelo);
        """)
        return

    # Insertar uno por uno para evitar problemas con duplicados
    print("\nInsertando datos...")
    inserted = 0
    skipped = 0
    errors = 0

    for i, (marca, modelo) in enumerate(MARCA_MODELOS, 1):
        try:
            # Primero verificar si ya existe
            result = client.client.table('marcas_modelos_validos').select('id').eq('marca', marca).eq('modelo', modelo).execute()

            if result.data:
                skipped += 1
                if i % 50 == 0:
                    print(f"  Procesados {i}/{len(MARCA_MODELOS)} (insertados: {inserted}, ya exist\u00edan: {skipped})...")
                continue

            # Insertar si no existe
            client.client.table('marcas_modelos_validos').insert({
                "marca": marca,
                "modelo": modelo
            }).execute()

            inserted += 1
            if i % 50 == 0:
                print(f"  Procesados {i}/{len(MARCA_MODELOS)} (insertados: {inserted}, ya exist\u00edan: {skipped})...")

        except Exception as e:
            print(f"  Error con {marca} {modelo}: {e}")
            errors += 1

    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Total intentados: {len(MARCA_MODELOS)}")
    print(f"Nuevos insertados: {inserted}")
    print(f"Ya existian: {skipped}")
    print(f"Errores: {errors}")

    # Verificar resultado final
    try:
        result = client.client.table('marcas_modelos_validos').select('count', count='exact').execute()
        final_count = result.count or 0
        print(f"\nTotal en base de datos: {final_count}")

        # Mostrar algunas marcas como ejemplo
        result = client.client.table('marcas_modelos_validos').select('marca, modelo').limit(10).execute()
        print("\nEjemplos de registros:")
        for row in result.data:
            print(f"  - {row['marca']}: {row['modelo']}")

    except Exception as e:
        print(f"Error verificando resultado: {e}")

    print("\nPoblacion completada!")


if __name__ == "__main__":
    main()
