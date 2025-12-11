# Guía de Accesos Directos de Escritorio

Instrucciones para crear y usar accesos directos de escritorio para las aplicaciones de scraping.

## Windows

### Opción 1: Crear Accesos Directos Automáticamente (Recomendado)

1. **Ejecutar el script de creación**:
   - Navegar a la carpeta del proyecto
   - Doble click en `create_desktop_shortcuts.bat`
   - El script creará 3 accesos directos en tu escritorio

2. **Accesos directos creados**:
   - **Unified Scraper** - Gestiona Autocasion + Cochesnet
   - **Cochesnet Scraper** - Solo Cochesnet (por año)
   - **Autocasion Scraper** - Solo Autocasion (por marca)

3. **Usar los accesos directos**:
   - Doble click en cualquier acceso directo
   - La aplicación se iniciará automáticamente

### Opción 2: Ejecutar Directamente los Launchers

Si no quieres crear accesos directos, puedes ejecutar directamente:

- `launch_unified_app.bat` - App unificada
- `launch_cochesnet_app.bat` - Solo Cochesnet
- `launch_autocasion_app.bat` - Solo Autocasion

### Características de los Launchers

Todos los `.bat` launchers incluyen:
- ✅ Auto-detección de virtual environment
- ✅ Activación automática del venv
- ✅ Mensajes de error si falla
- ✅ Working directory correcto
- ✅ Ventana persistente en caso de error

## Linux / Mac

### Crear Accesos Directos

1. **Hacer ejecutables los scripts**:
   ```bash
   chmod +x launch_unified_app.sh
   chmod +x launch_cochesnet_app.sh
   chmod +x launch_autocasion_app.sh
   ```

2. **Crear .desktop files** (Linux):
   ```bash
   # Unified App
   cat > ~/Desktop/unified-scraper.desktop << 'EOF'
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=Unified Scraper
   Comment=Autocasion + Cochesnet Manager
   Exec=/path/to/ScrapeadorSupremo/launch_unified_app.sh
   Path=/path/to/ScrapeadorSupremo
   Icon=utilities-terminal
   Terminal=true
   Categories=Utility;
   EOF

   chmod +x ~/Desktop/unified-scraper.desktop
   ```

3. **Crear App Bundle** (Mac):
   - Usar Automator para crear aplicación
   - Tipo: Application
   - Agregar acción "Run Shell Script"
   - Script: `/path/to/launch_unified_app.sh`
   - Guardar como aplicación

### Ejecutar Directamente

```bash
# App unificada
./launch_unified_app.sh

# Solo Cochesnet
./launch_cochesnet_app.sh

# Solo Autocasion
./launch_autocasion_app.sh
```

## Requisitos Previos

Antes de usar los accesos directos, asegúrate de tener:

### 1. Python Instalado
```bash
python --version  # Debe ser 3.8+
```

### 2. Dependencias Instaladas
```bash
pip install -r requirements.txt
```

O manualmente:
```bash
pip install tkinter requests beautifulsoup4 lxml supabase python-dotenv
```

### 3. Variables de Entorno Configuradas

Crear archivo `.env` en la raíz del proyecto:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 4. Virtual Environment (Opcional pero Recomendado)

```bash
# Crear venv
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Activar (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

Los launchers detectarán y activarán automáticamente el venv si existe.

## Estructura de Archivos

```
ScrapeadorSupremo/
├── launch_unified_app.bat          # Launcher Windows - Unified
├── launch_cochesnet_app.bat        # Launcher Windows - Cochesnet
├── launch_autocasion_app.bat       # Launcher Windows - Autocasion
├── launch_unified_app.sh           # Launcher Linux/Mac - Unified
├── create_desktop_shortcuts.bat    # Script para crear accesos directos
├── scraping/
│   ├── unified_app/
│   │   ├── main.py                 # Entry point - Unified
│   │   └── gui.py                  # GUI - Unified
│   └── sites/
│       ├── cochesnet/
│       │   └── app/
│       │       ├── main.py         # Entry point - Cochesnet
│       │       └── gui.py          # GUI - Cochesnet
│       └── autocasion/
│           └── agent/
│               ├── main.py         # Entry point - Autocasion
│               └── gui.py          # GUI - Autocasion
└── docs/
    ├── DESKTOP_SHORTCUTS_GUIDE.md  # Esta guía
    ├── UNIFIED_APP_README.md       # Documentación app unificada
    └── COCHESNET_APP_README.md     # Documentación app Cochesnet
```

## Troubleshooting

### Windows: "Python no reconocido como comando"

**Causa**: Python no está en el PATH

**Solución**:
1. Reinstalar Python con opción "Add to PATH"
2. O editar `.bat` para usar ruta completa:
   ```bat
   C:\Python39\python.exe scraping\unified_app\main.py
   ```

### Windows: "No se puede ejecutar .bat"

**Causa**: Política de ejecución restrictiva

**Solución**:
- Click derecho → "Ejecutar como administrador"
- O cambiar extensión de archivos asociados

### Linux/Mac: "Permission denied"

**Causa**: Script no es ejecutable

**Solución**:
```bash
chmod +x launch_unified_app.sh
```

### "ModuleNotFoundError: No module named 'tkinter'"

**Causa**: tkinter no instalado

**Solución**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Mac (con brew)
brew install python-tk
```

### "Could not connect to Supabase"

**Causa**: Variables de entorno no configuradas o incorrectas

**Solución**:
1. Verificar que `.env` existe en raíz del proyecto
2. Verificar credenciales correctas
3. Verificar conexión a internet

### Acceso directo no funciona

**Causa**: Ruta incorrecta en el acceso directo

**Solución**:
1. Click derecho en acceso directo → Propiedades
2. Verificar que "Target" apunta a `.bat` correcto
3. Verificar que "Start in" apunta a carpeta del proyecto
4. Re-ejecutar `create_desktop_shortcuts.bat`

## Personalización

### Cambiar Icono del Acceso Directo (Windows)

1. Click derecho en acceso directo → Propiedades
2. Tab "Shortcut" → Botón "Change Icon"
3. Seleccionar icono de `C:\Windows\System32\SHELL32.dll`
4. O usar archivo `.ico` personalizado

### Cambiar Nombre del Acceso Directo

1. Click derecho en acceso directo
2. Rename → Nuevo nombre
3. Enter

### Ejecutar sin Ventana de Consola (Windows)

Editar `.bat` y cambiar primera línea:
```bat
@echo off
```
Por:
```bat
@echo off
if not "%1"=="am_admin" (powershell start -verb runas '%0' am_admin & exit)
```

O crear `.vbs` wrapper:
```vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "launch_unified_app.bat" & Chr(34), 0
Set WshShell = Nothing
```

## Ejemplos de Uso

### Uso Diario Típico

1. **Mañana**: Doble click en "Unified Scraper" desktop shortcut
2. Seleccionar años recientes en Cochesnet (2024-2025)
3. Seleccionar top brands en Autocasion
4. Click "Start Scraping" en ambas tabs
5. Ir a desayunar mientras scrapea (15-30 min)
6. Regresar, revisar estadísticas
7. Exportar CSV desde tab "Export"

### Scraping Rápido de Cochesnet

1. Doble click en "Cochesnet Scraper" desktop shortcut
2. Seleccionar solo 2025
3. Click "Start Scraping"
4. 2-3 minutos para completar
5. Ver resultados en logs

### Testing Parseo

1. Doble click en "Cochesnet Scraper"
2. Seleccionar un año con pocos anuncios (ej: 2007)
3. Scrape rápido
4. Revisar confidence en mini stats
5. Ajustar sistema si es necesario

## Recursos Adicionales

- **Documentación Completa**: [UNIFIED_APP_README.md](UNIFIED_APP_README.md)
- **Sistema de Parsing**: [TITLE_PARSER_INTEGRATION.md](TITLE_PARSER_INTEGRATION.md)
- **Bugs Corregidos**: [RESUMEN_FISURAS_Y_TEST_REAL.md](RESUMEN_FISURAS_Y_TEST_REAL.md)
- **App Cochesnet**: [COCHESNET_APP_README.md](COCHESNET_APP_README.md)

---

**Version**: 1.0.0
**Date**: 2025-12-05
**Plataformas**: Windows (completo), Linux/Mac (scripts disponibles)
