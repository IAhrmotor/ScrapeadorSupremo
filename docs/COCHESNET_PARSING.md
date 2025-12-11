# Cochesnet - Análisis de Parsing

Este documento explica cómo se parsea la información de un anuncio de Cochesnet.

---

## 1. Arquitectura del Parser

```python
class CochesNetParser(BaseParser):
    """
    Parser con estrategia dual:
    1. JSON embebido (window.__INITIAL_PROPS__) - RÁPIDO ⚡
    2. CSS selectors (fallback) - LENTO 🐢
    """
```

**Flujo de decisión:**
```
parse(html)
    ↓
┌─────────────────────────────┐
│ 1. Buscar JSON embebido     │
│    window.__INITIAL_PROPS__ │
└─────────────────────────────┘
    ↓
   JSON?
    ↓ SI
┌─────────────────────────────┐
│ _extract_from_json()         │ ← ⚡ 10x más rápido
│ - Parsear JSON               │
│ - Mapear a CarListing        │
│ - Return listings            │
└─────────────────────────────┘
    ↓
   Done!

    ↓ NO
┌─────────────────────────────┐
│ _extract_from_css()          │ ← 🐢 Fallback
│ - Buscar div[data-ad-id]    │
│ - Extraer con BeautifulSoup │
│ - Return listings            │
└─────────────────────────────┘
```

---

## 2. Estrategia 1: JSON Embebido (Preferida)

### 2.1 Estructura del JSON

Cochesnet embebe datos JSON en el HTML para acelerar la carga:

```html
<script>
window.__INITIAL_PROPS__ = JSON.parse("{
  \"props\": {
    \"pageProps\": {
      \"initialResults\": {
        \"items\": [
          {
            \"id\": \"61694366\",
            \"title\": \"OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.\",
            \"url\": \"/opel-corsa-15d-dt-74kw-100cv-edition-5p-diesel-2021-en-madrid-61694366-covo.aspx\",
            \"price\": 9950,
            \"year\": 2021,
            \"km\": 137000,
            \"fuelType\": \"Diesel\",
            \"hp\": 100,
            \"location\": \"Madrid\",
            \"images\": [\"...\"],
            \"dealer\": {...}
          },
          {
            \"id\": \"62103845\",
            \"title\": \"BMW Serie 3 320d\",
            \"url\": \"/bmw-serie-3-320d-...\",
            \"price\": 15900,
            \"year\": 2018,
            \"km\": 89500,
            \"fuelType\": \"Diesel\",
            \"hp\": 190,
            \"location\": \"Barcelona\"
          },
          ...
        ],
        \"totalItems\": 1234,
        \"pagination\": {...}
      }
    }
  }
}")
</script>
```

### 2.2 Código de Extracción JSON

```python
def _extract_from_json(self, soup: BeautifulSoup) -> List[CarListing]:
    """Extract cars from embedded JSON."""
    scripts = soup.find_all('script')

    for script in scripts:
        text = script.string
        if not text:
            continue

        # Buscar patrón: window.__INITIAL_PROPS__ = JSON.parse("...")
        match = re.search(
            r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.+?)"\)',
            text, re.DOTALL
        )
        if match:
            # Decodificar string escapado
            json_str = match.group(1).encode().decode('unicode_escape')
            data = json.loads(json_str)
            return self._parse_json_items(data)

    return []
```

### 2.3 Navegación del JSON

```python
def _parse_json_items(self, data: Dict) -> List[CarListing]:
    """Parse items from JSON data structure."""

    # Navegar estructura anidada
    items = None

    # Opción 1: data['initialResults']['items']
    if 'initialResults' in data and 'items' in data['initialResults']:
        items = data['initialResults']['items']

    # Opción 2: data['props']['pageProps']['initialResults']['items']
    elif 'props' in data:
        page_props = data.get('props', {}).get('pageProps', {})
        if 'initialResults' in page_props:
            items = page_props['initialResults'].get('items', [])

    if not items:
        return []

    # Mapear cada item a CarListing
    listings = []
    for item in items:
        listing = self._map_json_to_listing(item)
        if listing:
            listings.append(listing)

    return listings
```

### 2.4 Mapeo JSON → CarListing

```python
def _map_json_to_listing(self, item: Dict) -> Optional[CarListing]:
    """Map JSON item to CarListing."""

    ad_id = item.get('id')
    if not ad_id:
        return None

    title = item.get('title', '')
    url_path = item.get('url', '')

    return CarListing(
        # Identificación
        ad_id=str(ad_id),                    # "61694366"
        source="cochesnet",
        url=f"https://www.coches.net{url_path}",

        # Información básica
        title=title,                          # "OPEL Corsa 1.5D DT..."
        marca=self._extract_marca(title),     # "OPEL" (primera palabra)
        modelo=self._extract_modelo(title),   # "Corsa 1.5D DT..." (resto)

        # Características (directamente del JSON)
        year=item.get('year'),                # 2021 (int)
        kilometers=item.get('km'),            # 137000 (int)
        fuel=item.get('fuelType'),            # "Diesel"
        power_cv=item.get('hp'),              # 100 (int)

        # Precio
        price=item.get('price'),              # 9950 (int)
        price_text=f"{item.get('price'):,} EUR".replace(',', '.'),
                                              # "9.950 EUR"

        # Ubicación
        location=item.get('location'),        # "Madrid"

        # Raw data para debugging
        raw_data=item
    )
```

**Ventajas del método JSON:**
- ⚡ **10x más rápido** que parsear HTML
- ✅ **Datos limpios** ya estructurados
- ✅ **Tipos correctos** (int, no strings)
- ✅ **Sin regex** complicados
- ✅ **Menos errores** de parsing

---

## 3. Estrategia 2: CSS Selectors (Fallback)

### 3.1 Estructura HTML de Cochesnet

```html
<div class="mt-ListAds">
  <!-- Anuncio 1 -->
  <div class="mt-ListAds-item" data-ad-id="61694366">

    <!-- Título y URL -->
    <a class="mt-CardAd-infoHeaderTitleLink"
       href="/opel-corsa-15d-dt-74kw-100cv-edition-5p-diesel-2021-en-madrid-61694366-covo.aspx">
      OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.
    </a>

    <!-- Precio -->
    <p data-testid="card-adPrice-price" class="mt-CardAdPrice-cashAmount">
      9.950 €
    </p>

    <!-- Atributos -->
    <ul class="mt-CardAd-attr">
      <li class="mt-CardAd-attrItem">2021</li>
      <li class="mt-CardAd-attrItem">137.000 km</li>
      <li class="mt-CardAd-attrItem">100 CV</li>
      <li class="mt-CardAd-attrItem">Diesel</li>
      <li class="mt-CardAd-attrItem">Madrid</li>
    </ul>

    <!-- Imagen -->
    <img src="https://a.ccdn.es/cnet/vehicles/.../image.jpg"
         alt="OPEL Corsa 1.5D DT Edition">
  </div>

  <!-- Anuncio 2 -->
  <div class="mt-ListAds-item" data-ad-id="62103845">
    ...
  </div>
</div>
```

### 3.2 Código de Extracción CSS

```python
def _extract_from_css(self, soup: BeautifulSoup) -> List[CarListing]:
    """Extract cars using CSS selectors."""
    listings = []

    # 1. Encontrar contenedor principal
    container = soup.find('div', class_='mt-ListAds')
    if not container:
        logger.warning("No mt-ListAds container found")
        return []

    # 2. Encontrar todos los anuncios
    ad_items = container.find_all('div', attrs={'data-ad-id': True})
    logger.info(f"Found {len(ad_items)} ads via CSS")

    # 3. Parsear cada anuncio
    for ad in ad_items:
        try:
            listing = self._parse_ad_element(ad)
            if listing:
                listings.append(listing)
        except Exception as e:
            logger.debug(f"Error parsing ad: {e}")

    return listings
```

### 3.3 Parseo de Elemento Individual

```python
def _parse_ad_element(self, ad) -> Optional[CarListing]:
    """Parse single ad element."""

    # 1. Extraer ad_id
    ad_id = ad.get('data-ad-id')
    if not ad_id:
        return None

    # 2. Saltar placeholders y anuncios nativos
    if ad.find('div', class_='sui-PerfDynamicRendering-placeholder'):
        return None
    if 'mt-ListAds-item--native' in ad.get('class', []):
        return None

    # 3. Extraer título y URL
    title_link = ad.find('a', class_='mt-CardAd-infoHeaderTitleLink')
    if not title_link:
        return None

    title = title_link.get_text(strip=True)
    url_path = title_link.get('href', '')

    # 4. Extraer precio
    price_elem = ad.find('p', {'data-testid': 'card-adPrice-price'})
    price_text = price_elem.get_text(strip=True) if price_elem else None
    price_numeric = self._extract_number(price_text)  # "9.950 €" → 9950

    # 5. Extraer atributos (year, km, CV, fuel, location)
    attrs = self._parse_attributes(ad)

    # 6. Crear CarListing
    return CarListing(
        ad_id=str(ad_id),
        source="cochesnet",
        url=f"https://www.coches.net{url_path}",
        title=title,
        marca=self._extract_marca(title),
        modelo=self._extract_modelo(title),
        year=attrs.get('year'),
        kilometers=attrs.get('kilometers'),
        fuel=attrs.get('fuel'),
        power_cv=attrs.get('power'),
        price=price_numeric,
        price_text=price_text,
        location=attrs.get('location'),
    )
```

### 3.4 Parseo de Atributos (Lista)

```python
def _parse_attributes(self, ad) -> Dict[str, Any]:
    """Parse attributes list."""
    attrs = {}

    # Encontrar lista de atributos
    attr_list = ad.find('ul', class_='mt-CardAd-attr')
    if not attr_list:
        return attrs

    # Obtener items (excluir etiquetas ambientales)
    items = attr_list.find_all('li', class_='mt-CardAd-attrItem')
    items = [i for i in items
             if 'mt-CardAd-attrItemEnvironmentalLabel' not in i.get('class', [])]

    # Parsear cada item con heurísticas
    for item in items:
        text = item.get_text(strip=True)

        if self._is_fuel(text):              # "Diesel" → fuel
            attrs['fuel'] = text
        elif self._is_year(text):            # "2021" → year
            attrs['year'] = int(text)
        elif 'km' in text.lower():           # "137.000 km" → kilometers
            attrs['kilometers'] = self._extract_number(text)  # → 137000
        elif 'cv' in text.lower():           # "100 CV" → power
            attrs['power'] = self._extract_number(text)       # → 100
        else:                                # "Madrid" → location
            attrs['location'] = text

    return attrs
```

### 3.5 Funciones Auxiliares

```python
def _is_fuel(self, text: str) -> bool:
    """Check if text is fuel type."""
    fuels = ['diesel', 'gasolina', 'electrico', 'hibrido', 'gas']
    return any(f in text.lower() for f in fuels)

def _is_year(self, text: str) -> bool:
    """Check if text is a year."""
    return bool(re.match(r'^(19|20)\d{2}$', text))

def _extract_marca(self, title: str) -> Optional[str]:
    """Extract brand from title (first word)."""
    if not title:
        return None
    parts = title.split()
    return parts[0] if parts else None
    # "OPEL Corsa 1.5D..." → "OPEL"

def _extract_modelo(self, title: str) -> Optional[str]:
    """Extract model from title (rest after brand)."""
    if not title:
        return None
    parts = title.split(maxsplit=1)
    return parts[1] if len(parts) > 1 else None
    # "OPEL Corsa 1.5D..." → "Corsa 1.5D..."

def _extract_number(self, text: str) -> Optional[int]:
    """Extract first number from text."""
    if not text:
        return None
    digits = re.sub(r'[^\d]', '', text)  # "9.950 €" → "9950"
    return int(digits) if digits else None
```

**Desventajas del método CSS:**
- 🐢 **Lento** (parsear HTML con regex)
- ⚠️ **Frágil** (cambios en clases CSS rompen todo)
- 🤔 **Heurísticas** necesarias (¿"2021" es año o precio?)
- 🔧 **Más código** de limpieza y validación

---

## 4. Ejemplo Completo de Anuncio

### JSON (Entrada del método 1)
```json
{
  "id": "61694366",
  "title": "OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.",
  "url": "/opel-corsa-15d-dt-74kw-100cv-edition-5p-diesel-2021-en-madrid-61694366-covo.aspx",
  "price": 9950,
  "year": 2021,
  "km": 137000,
  "fuelType": "Diesel",
  "hp": 100,
  "location": "Madrid",
  "images": [
    "https://a.ccdn.es/cnet/vehicles/18714450/40303184-c5de-4dc1-b0f3-cbdf0dfb7d31.jpg"
  ],
  "dealer": {
    "name": "Automóviles Ejemplo",
    "type": "professional"
  },
  "highlights": ["Buen precio", "Garantía 3 años"]
}
```

### CarListing (Salida del parser)
```python
CarListing(
    # Identificación
    ad_id="61694366",
    source="cochesnet",
    url="https://www.coches.net/opel-corsa-15d-dt-74kw-100cv-edition-5p-diesel-2021-en-madrid-61694366-covo.aspx",

    # Información básica
    title="OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.",
    marca="OPEL",
    modelo="Corsa 1.5D DT 74kW 100CV Edition 5p.",
    version=None,  # No disponible en listado

    # Características
    year=2021,                 # int
    kilometers=137000,         # int (no string!)
    fuel="Diesel",
    power_cv=100,              # int
    transmission=None,         # No disponible en listado

    # Precio
    price=9950,                # int
    price_text="9.950 EUR",    # string para display

    # Ubicación
    location="Madrid",
    provincia=None,            # Extraído de location si es necesario

    # Metadata
    raw_data={...}             # JSON completo para debugging
)
```

### Guardado en Supabase (tabla `cochesnet`)
```sql
INSERT INTO cochesnet (
    ad_id,
    url,
    title,
    marca,
    marca_normalizada,
    modelo,
    modelo_base,
    modelo_completo,
    version,
    year,
    kilometers,
    kilometers_numeric,
    fuel,
    combustible_normalizado,
    price,
    price_numeric,
    power,
    power_numeric,
    location,
    provincia,
    scraped_at,
    created_at,
    activo,
    parsing_version
) VALUES (
    '61694366',
    'https://www.coches.net/opel-corsa-...',
    'OPEL Corsa 1.5D DT 74kW 100CV Edition 5p.',
    'OPEL',
    'opel',
    'Corsa 1.5D DT 74kW 100CV Edition 5p.',
    'Corsa',
    'Corsa 1.5D DT 74kW 100CV Edition 5p.',
    NULL,
    '2021',
    '137.000 km',              -- Format string
    137000,                    -- Numeric para queries
    'Diesel',
    'diesel',
    '9.950 €',                 -- Format string
    9950,                      -- Numeric para queries
    '100 CV',                  -- Format string
    100,                       -- Numeric para queries
    'Madrid',
    NULL,
    '2025-01-15T10:30:00Z',
    '2025-01-15T10:30:00Z',
    TRUE,
    1
) ON CONFLICT (ad_id) DO UPDATE SET
    price_numeric = EXCLUDED.price_numeric,
    kilometers_numeric = EXCLUDED.kilometers_numeric,
    scraped_at = EXCLUDED.scraped_at;
```

---

## 5. Comparación de Métodos

| Aspecto | JSON Embebido | CSS Selectors |
|---------|---------------|---------------|
| **Velocidad** | ⚡ 10x más rápido | 🐢 Lento |
| **Precisión** | ✅ 100% | ⚠️ 85-90% |
| **Tipos de datos** | ✅ Correctos (int) | 🔧 Strings (conversión manual) |
| **Mantenimiento** | ✅ Estable | ⚠️ Frágil (cambios CSS) |
| **Código** | ✅ Simple | 🔧 Complejo (heurísticas) |
| **Disponibilidad** | ⚠️ Solo en páginas modernas | ✅ Siempre funciona |
| **Debugging** | ✅ Fácil (JSON inspector) | 🔧 Difícil (inspeccionar HTML) |

---

## 6. Flujo Completo

```
1. HTTP Request
   GET https://www.coches.net/coches-segunda-mano/

2. Recibir HTML
   <html>
     <script>window.__INITIAL_PROPS__ = JSON.parse("...")</script>
     <div class="mt-ListAds">...</div>
   </html>

3. parse(html)
   ↓
   Buscar JSON embebido
   ↓
   ¿Encontrado?
   ↓ SÍ (90% casos)
   _extract_from_json()
     ↓
     Regex: window.__INITIAL_PROPS__ = JSON.parse("...")
     ↓
     Decode Unicode escape
     ↓
     json.loads()
     ↓
     Navegar: data['props']['pageProps']['initialResults']['items']
     ↓
     For each item:
       _map_json_to_listing(item)
       ↓
       CarListing(
         ad_id=item['id'],
         year=item['year'],    # Ya es int!
         km=item['km'],        # Ya es int!
         price=item['price']   # Ya es int!
       )
   ↓
   Return [CarListing, CarListing, ...]

   ↓ NO (10% casos)
   _extract_from_css()
     ↓
     BeautifulSoup(html, 'lxml')
     ↓
     soup.find('div', class_='mt-ListAds')
     ↓
     soup.find_all('div', attrs={'data-ad-id': True})
     ↓
     For each ad:
       _parse_ad_element(ad)
       ↓
       ad.get('data-ad-id')
       ad.find('a', class_='mt-CardAd-infoHeaderTitleLink')
       ad.find('p', {'data-testid': 'card-adPrice-price'})
       _parse_attributes(ad) → {year, km, fuel, power, location}
       ↓
       CarListing(
         ad_id=str(ad_id),
         year=int(attrs['year']),      # Conversión manual
         kilometers=_extract_number(),  # Conversión manual
         price=_extract_number()        # Conversión manual
       )
   ↓
   Return [CarListing, CarListing, ...]

4. Guardar en Supabase
   supabase.save_listings(listings)
   ↓
   _listing_to_cochesnet(listing)
   ↓
   INSERT INTO cochesnet (...) VALUES (...)
   ON CONFLICT (ad_id) DO UPDATE
```

---

## 7. Conclusión

**Cochesnet usa una estrategia dual inteligente:**

✅ **Primero JSON** (rápido, preciso, fácil)
⚠️ **Fallback CSS** (lento, frágil, pero siempre funciona)

**Ventajas principales:**
- **Performance**: JSON es 10x más rápido
- **Robustez**: Fallback asegura que siempre funcione
- **Calidad de datos**: Tipos correctos desde el inicio

**Diferencia con Clicars/Autocasion:**
- **Autocasion**: Solo HeadlessX + CSS (paginación)
- **Clicars**: Playwright + CSS (infinite scroll)
- **Cochesnet**: JSON embebido + CSS fallback (paginación)

Cada sitio requiere una estrategia diferente basada en su arquitectura web.
