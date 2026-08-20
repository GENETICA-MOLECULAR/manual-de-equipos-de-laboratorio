# Inventario de Equipos — Laboratorio de Genética Molecular

Sitio web estático con el inventario de equipos del Laboratorio de Genética Molecular de la Facultad de Ciencias Biológicas, UNSAAC.

## Estructura del proyecto

```
inventario_equipos/
├── index.html                      # Página principal (generada)
├── css/
│   └── styles.css                  # Estilos (tema oscuro/claro)
├── assets/
│   ├── logo.png                    # Logo del laboratorio
│   └── favicon.svg                 # Icono del sitio
├── equipos/                        # Páginas individuales (generadas)
│   ├── centrifuga-convencional-011363.html
│   ├── autoclave-011384.html
│   └── ... (56 páginas)
├── pdfs/                           # Manuales originales (PDF)
│   ├── AUTOCLAVE BENCHMARK.pdf
│   ├── BALANZA FX-500i.pdf
│   └── ... (7 manuales)
├── instructivos_pdf/               # Instructivos generados (PDF)
│   ├── agitador-vortex.pdf
│   ├── autoclave.pdf
│   └── ... (71 instructivos)
├── instructivos/                   # Texto plano de instructivos
├── generate.py                     # Generador principal de HTML
├── generate_instructivo_pdfs.py    # Generador de PDFs de instructivos
├── extract_instructivos.py         # Extrae instructivos del PDF del profesor
├── update.sh                       # Script maestro de actualización
└── README.md                       # Este archivo
```

## Uso rápido

### Generar todo el sitio
```bash
./update.sh
```

### Generar solo los HTML
```bash
python3 generate.py
```

### Regenerar instructivos PDF
```bash
python3 generate_instructivo_pdfs.py
```

### Extraer instructivos del PDF del profesor
```bash
python3 extract_instructivos.py
```

## Funcionalidades

- **56 equipos** de laboratorio con detalles completos del inventario
- **Filtros** por área del laboratorio y por "Con Manual"
- **Búsqueda** por nombre, código, marca o modelo
- **Tema oscuro/claro** con toggle
- **71 instructivos de uso** generados como PDF con formato del profesor
- **7 manuales originales** embebidos
- **Sistema de toggle**: cuando un equipo tiene ambos documentos, permite alternar entre Instructivo y Manual
- **56 QR codes** en PDF para acceso rápido desde el celular
- **Diseño responsive** optimizado para móvil

## Equipos con documentación

| Equipo | Manual PDF | Instructivo PDF | Toggle |
|--------|:---:|:---:|:---:|
| Autoclave | ✓ | ✓ | ✓ |
| Incubadora de CO2 | ✓ | ✓ | ✓ |
| Incubadora convencional | ✓ | ✓ | ✓ |
| qPCR / Termociclador en tiempo real | ✓ | ✓ | ✓ |
| Termociclador convencional | ✓ | ✓ | ✓ |
| Agitador Vortex | - | ✓ | |
| Agitador Orbital | - | ✓ | |
| Balanzas (2) | ✓ | ✓ | ✓ |
| Baño María | ✓ | ✓ | |
| Baño Seco Digital | - | ✓ | |
| Cámaras de Electroforesis (3) | - | ✓ | |
| Cabina de Bioseguridad | - | ✓ | |
| Cabina de PCR | - | ✓ | |
| Centrifugas (6) | - | ✓ | |
| Destilador de Agua | - | ✓ | |
| Documentador de Geles | - | ✓ | |
| Espectofotrómetros (2) | - | ✓ | |
| Homogeneizador | ✓ | ✓ | |
| Lavador de Microplacas | - | ✓ | |
| Lector de Placas ELISA | - | ✓ | |
| Microscopios (3) | - | ✓ | |
| PCR Workstation | - | ✓ | |
| Refrigeradores (3) | - | ✓ | |
| Ultracentrífuga | - | ✓ | |
| Ultrapurificador de Agua | - | ✓ | |

## Cómo agregar un nuevo equipo

1. Agregar el equipo al CSV de inventario
2. Actualizar el mapeo en `generate.py` si es necesario
3. Ejecutar `./update.sh`

## Cómo agregar un instructivo

1. Crear el instructivo en texto plano siguiendo el formato:
   ```
   INSTRUCTIVO DE USO: NOMBRE DEL EQUIPO
   MARCA: ...
   MODELO: ...
   SERIE: ...
   1. Primer paso
   2. Segundo paso
   ```
2. Agregar el texto al PDF de instructivos del profesor
3. Ejecutar `python3 extract_instructivos.py`
4. Ejecutar `python3 generate_instructivo_pdfs.py`
5. Ejecutar `python3 generate.py`

## Despliegue

El sitio se despliega automáticamente en GitHub Pages al hacer push a la rama `main`:

```
https://genetica-molecular.github.io/manual-de-equipos-de-laboratorio/
```

## Tecnologías

- HTML5 estático (generado con Python)
- CSS3 (variables, grid, flexbox, glassmorphism)
- JavaScript vanilla (filtros, búsqueda, toggle de temas)
- Python 3 (scripts de generación)
- ReportLab (generación de PDFs)
- qrcode (generación de QR codes)

## Licencia

Uso interno — Laboratorio de Genética Molecular, UNSAAC
