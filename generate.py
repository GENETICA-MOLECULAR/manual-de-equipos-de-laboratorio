#!/usr/bin/env python3
"""
Generador principal del sitio de Inventario de Equipos.
Lee el CSV de inventario, los instructivos y manuales existentes,
y genera el HTML estático del sitio.

Uso:
    python3 generate.py
"""

import csv
import os
import re
import json

# ─── Configuración ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.expanduser("~/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv")
OUTPUT_DIR = BASE_DIR
EQUIPOS_DIR = os.path.join(OUTPUT_DIR, "equipos")
INSTRUCTIVOS_MAP = os.path.join(OUTPUT_DIR, "instructivos_map.json")
INSTRUCTIVOS_PDF_DIR = "instructivos_pdf"
PDFS_DIR = "pdfs"

EXCLUDE_KEYWORDS = [
    "silla", "mesa", "escritorio", "extintor", "teclado", "monitor",
    "munition", "cpu", "estabilizador", "camara domo", "camara de tubo",
    "monitor de camaras", "rodadora de video", "pantalla", "impresora"
]

# Mapeo nombre del equipo → archivo PDF manual
PDF_MAP = {
    "autoclave": "AUTOCLAVE  BENCHMARK.pdf",
    "balanza de precisión": "BALANZA FX-500i.pdf",
    "baño maría": "BAÑO MARIA MEMMERT.pdf",
    "homogeneizador": "HOMOGENEIZADOR- MANUAL ESPAÑOL.pdf",
    "incubadora de co2": "INCUBADORA DE CO2.pdf",
    "incubadora convencional": "MANUAL DE LA INCUBADORA MARCA MEMMERT MODELO IF55.pdf",
}


# ─── Utilidades ─────────────────────────────────────────────────

def slugify(text):
    """Convierte texto a slug URL-friendly: 'Centrifuga 1' → 'centrifuga-1'."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def should_exclude(nombre):
    """Determina si un equipo debe excluirse del inventario (mobiliario, etc.)."""
    nombre_lower = nombre.lower()
    return any(kw in nombre_lower for kw in EXCLUDE_KEYWORDS)


def find_manual_pdf(nombre):
    """Busca si existe un manual PDF para el equipo dado."""
    nombre_lower = nombre.lower()
    for key, pdf in PDF_MAP.items():
        if key in nombre_lower:
            return pdf
    return None


def find_instructivo_pdf(slug, nombre):
    """Busca si existe un instructivo PDF para el equipo dado."""
    pdf_dir = os.path.join(OUTPUT_DIR, INSTRUCTIVOS_PDF_DIR)
    
    # Buscar por slug exacto
    path = os.path.join(pdf_dir, f"{slug}.pdf")
    if os.path.exists(path):
        return f"../{INSTRUCTIVOS_PDF_DIR}/{slug}.pdf"
    
    # Buscar por nombre (sin código)
    nombre_slug = slugify(nombre)
    path = os.path.join(pdf_dir, f"{nombre_slug}.pdf")
    if os.path.exists(path):
        return f"../{INSTRUCTIVOS_PDF_DIR}/{nombre_slug}.pdf"
    
    return None


def load_instructivos():
    """Carga el mapa de instructivos en texto plano."""
    if os.path.exists(INSTRUCTIVOS_MAP):
        with open(INSTRUCTIVOS_MAP, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def format_instructivo_html(text):
    """Convierte texto de instructivo a HTML formateado."""
    lines = text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append('</ol>')
                in_list = False
            html_lines.append('')
            continue
        
        if line.startswith(('MARCA:', 'MODELO:', 'SERIE:')):
            key, val = line.split(':', 1)
            html_lines.append(f'<p class="inst-meta"><strong>{key}:</strong> {val.strip()}</p>')
        elif re.match(r'^\d+\.?\s', line):
            if not in_list:
                html_lines.append('<ol class="inst-pasos">')
                in_list = True
            step = re.sub(r'^\d+\.?\s*', '', line)
            html_lines.append(f'  <li>{step}</li>')
        else:
            if in_list:
                html_lines.append('</ol>')
                in_list = False
            html_lines.append(f'<p>{line}</p>')
    
    if in_list:
        html_lines.append('</ol>')
    
    return '\n'.join(html_lines)


# ─── Lectura de datos ──────────────────────────────────────────

def read_csv():
    """Lee el CSV de inventario y retorna lista de equipos."""
    equipos = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            nombre = row.get('Nombre', '').strip()
            if not nombre or should_exclude(nombre):
                continue
            codigo = row.get('Codigo Actual', '').strip()
            if not codigo:
                continue
            equipos.append({
                'nombre': nombre,
                'codigo': codigo,
                'codigo_antiguo': row.get('Codigo Antiguo', '').strip(),
                'modelo': row.get('Modelo', '').strip(),
                'marca': row.get('Marca 2', '').strip(),
                'color': row.get('Color', '').strip(),
                'serie': row.get('Serie', '').strip(),
                'estado': row.get('Estado', '').strip(),
                'situacion': row.get('Situaciòn', '').strip().strip('"'),
                'importe': row.get('Importe', '').strip(),
                'area': row.get('Area', '').strip(),
                'pdf': find_manual_pdf(nombre),
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos


def get_areas(equipos):
    """Retorna lista ordenada de áreas únicas."""
    return sorted(set(e['area'] for e in equipos if e['area']))


# ─── Generación de HTML ────────────────────────────────────────

THEME_SCRIPT = """<script>
  const getSystemTheme = () => window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null;
  const initialTheme = savedTheme || getSystemTheme();
  document.documentElement.setAttribute('data-theme', initialTheme);
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
      document.documentElement.setAttribute('data-theme', e.matches ? 'light' : 'dark');
    }
  });
</script>"""

SVG_SUN = '<svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>'
SVG_MOON = '<svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>'
SVG_DOWNLOAD = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'
SVG_BACK = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>'
SVG_SEARCH = '<svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'


def generate_index(equipos, areas):
    """Genera el HTML de la página principal."""
    total = len(equipos)
    con_manual = sum(1 for e in equipos if e['pdf'])
    
    # Botones de filtro
    filter_btns = '\n'.join([
        f'            <button class="filter-btn active" data-area="todos">Todos ({total})</button>',
        f'            <button class="filter-btn" data-area="con-manual">📄 Con Manual ({con_manual})</button>'
    ] + [
        f'            <button class="filter-btn" data-area="{a}">{a} ({sum(1 for e in equipos if e["area"]==a)})</button>'
        for a in areas
    ])
    
    # Tarjetas de equipos
    cards = []
    for e in equipos:
        estado_class = 'bueno' if 'bueno' in e['estado'].lower() else 'malo' if 'malo' in e['estado'].lower() else 'desuso'
        pdf_badge = '<span class="equipo-pdf">📄 Manual</span>' if e['pdf'] else ''
        
        card = f'''        <a href="equipos/{e['slug']}.html" class="equipo-card" data-area="{e['area']}" data-pdf="{'si' if e['pdf'] else 'no'}">
          <div class="equipo-nombre">{e['nombre']}</div>
          <div class="equipo-codigo">Código: {e['codigo']}</div>
          <div class="equipo-info">
            <span>Modelo: {e['modelo'] or 'N/A'}</span>
            <span>Marca: {e['marca'] or 'N/A'}</span>
            <span>Serie: {e['serie'] or 'N/A'}</span>
          </div>
          <span class="equipo-area">{e['area']}</span>
          <span class="equipo-estado {estado_class}">{e['estado']}</span>
          {pdf_badge}
        </a>'''
        cards.append(card)
    
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Inventario de Equipos - Laboratorio de Genética Molecular UNSAAC">
  <meta name="theme-color" content="#0a1628">
  <link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
  <title>Inventario de Equipos - Lab. Genética Molecular UNSAAC</title>
  {THEME_SCRIPT}
</head>
<body>
  <main class="container">
    <div class="glass-panel">
      <button id="themeToggle" class="theme-toggle" aria-label="Cambiar tema">
        {SVG_SUN}
        {SVG_MOON}
      </button>

      <header class="header">
        <div class="logo-container">
          <img src="assets/logo.png" alt="Logo Laboratorio Genética" class="logo-icon">
        </div>
        <div class="titles">
          <h1>Inventario de Equipos</h1>
          <h2>Laboratorio de Genética Molecular</h2>
          <p>Facultad de Ciencias Biológicas, UNSAAC</p>
        </div>
      </header>

      <div class="stats">
        <div class="stat-card">
          <span class="stat-value">{total}</span>
          <span class="stat-label">Equipos</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{con_manual}</span>
          <span class="stat-label">Con Manual</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{len(areas)}</span>
          <span class="stat-label">Áreas</span>
        </div>
      </div>

      <div class="search-bar">
        {SVG_SEARCH}
        <input type="text" id="searchInput" placeholder="Buscar equipo por nombre, código, marca o modelo...">
      </div>

      <div class="filters">
{filter_btns}
      </div>

      <div class="equipos-grid" id="equiposGrid">
{chr(10).join(cards)}
      </div>

      <div class="no-results" id="noResults" style="display:none">
        <h3>No se encontraron equipos</h3>
        <p>Intenta con otros términos de búsqueda</p>
      </div>

      <footer class="footer">
        <p>Laboratorio de Genética Molecular - Facultad de Ciencias Biológicas, UNSAAC</p>
      </footer>
    </div>
  </main>

  <script>
    document.getElementById('themeToggle').addEventListener('click', () => {{
      const c = document.documentElement.getAttribute('data-theme');
      const n = c === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', n);
      localStorage.setItem('theme', n);
    }});

    const searchInput = document.getElementById('searchInput');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.equipo-card');
    const noResults = document.getElementById('noResults');
    let currentArea = 'todos';

    filterBtns.forEach(btn => btn.addEventListener('click', () => {{
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentArea = btn.dataset.area;
      filterCards();
    }}));

    searchInput.addEventListener('input', filterCards);

    function filterCards() {{
      const q = searchInput.value.toLowerCase();
      let visible = 0;
      cards.forEach(card => {{
        const match = (!q || card.textContent.toLowerCase().includes(q)) &&
          (currentArea === 'todos' || card.dataset.area === currentArea ||
           (currentArea === 'con-manual' && card.dataset.pdf === 'si'));
        card.style.display = match ? '' : 'none';
        if (match) visible++;
      }});
      noResults.style.display = visible === 0 ? '' : 'none';
    }}
  </script>
</body>
</html>'''


def generate_equipo_page(e, instructivos):
    """Genera el HTML de la página individual de un equipo."""
    slug = e['slug']
    inst_path = find_instructivo_pdf(slug, e['nombre'])
    manual_path = f"../{PDFS_DIR}/{e['pdf']}" if e['pdf'] else None
    
    has_manual = manual_path is not None
    has_inst = inst_path is not None
    
    # Sección de documentación
    doc_section = _build_doc_section(has_manual, has_inst, manual_path, inst_path, e['nombre'])
    
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{e['nombre']} - Inventario de Equipos - Lab. Genética Molecular UNSAAC">
  <meta name="theme-color" content="#0a1628">
  <link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/styles.css">
  <title>{e['nombre']} - Inventario de Equipos</title>
  {THEME_SCRIPT}
</head>
<body>
  <main class="container">
    <div class="glass-panel">
      <button id="themeToggle" class="theme-toggle" aria-label="Cambiar tema">
        {SVG_SUN}
        {SVG_MOON}
      </button>

      <a href="../index.html" class="back-btn">
        {SVG_BACK}
        Volver al inventario
      </a>

      <header class="header">
        <div class="logo-container">
          <img src="../assets/logo.png" alt="Logo Laboratorio Genética" class="logo-icon">
        </div>
        <div class="titles">
          <h1>{e['nombre']}</h1>
          <h2>Código: {e['codigo']}</h2>
          <p>{e['area']}</p>
        </div>
      </header>

      <div class="detail-info">
        {_info_item("Código Actual", e['codigo'])}
        {_info_item("Código Antiguo", e['codigo_antiguo'] or 'N/A')}
        {_info_item("Modelo", e['modelo'] or 'N/A')}
        {_info_item("Marca", e['marca'] or 'N/A')}
        {_info_item("Serie", e['serie'] or 'N/A')}
        {_info_item("Color", e['color'] or 'N/A')}
        {_info_item("Estado", e['estado'])}
        {_info_item("Situación", e['situacion'] or 'N/A')}
        {_info_item("Importe", e['importe'] or 'N/A')}
        {_info_item("Área", e['area'])}
      </div>

{doc_section}

      <footer class="footer">
        <p>Laboratorio de Genética Molecular - Facultad de Ciencias Biológicas, UNSAAC</p>
      </footer>
    </div>
  </main>

  <script>
    document.getElementById('themeToggle').addEventListener('click', () => {{
      const c = document.documentElement.getAttribute('data-theme');
      const n = c === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', n);
      localStorage.setItem('theme', n);
    }});

    function showDoc(type) {{
      document.getElementById('doc-inst').style.display = type === 'inst' ? 'block' : 'none';
      document.getElementById('doc-manual').style.display = type === 'manual' ? 'block' : 'none';
      document.querySelectorAll('.doc-tab').forEach(t =>
        t.classList.toggle('active', t.dataset.doc === type)
      );
    }}
  </script>
</body>
</html>'''


def _info_item(label, value):
    """Genera HTML de un item de información."""
    return f'''        <div class="info-item">
          <div class="info-label">{label}</div>
          <div class="info-value">{value}</div>
        </div>'''


def _build_doc_section(has_manual, has_inst, manual_path, inst_path, nombre):
    """Genera la sección de documentación según los archivos disponibles."""
    
    if has_manual and has_inst:
        return f'''      <div class="doc-section">
        <div class="doc-toggle">
          <button class="doc-tab active" data-doc="inst" onclick="showDoc('inst')">📋 Instructivo</button>
          <button class="doc-tab" data-doc="manual" onclick="showDoc('manual')">📖 Manual Original</button>
        </div>
        <div class="doc-viewer" id="doc-inst"><iframe src="{inst_path}" title="Instructivo de {nombre}"></iframe></div>
        <div class="doc-viewer" id="doc-manual" style="display:none"><iframe src="{manual_path}" title="Manual de {nombre}"></iframe></div>
        <div class="doc-actions">
          <a href="{inst_path}" download class="pdf-download">{SVG_DOWNLOAD} Descargar Instructivo</a>
          <a href="{manual_path}" download class="pdf-download pdf-download--secondary">{SVG_DOWNLOAD} Descargar Manual</a>
        </div>
      </div>'''
    
    if has_inst:
        return f'''      <div class="doc-section">
        <div class="doc-viewer"><iframe src="{inst_path}" title="Instructivo de {nombre}"></iframe></div>
        <div class="doc-actions">
          <a href="{inst_path}" download class="pdf-download">{SVG_DOWNLOAD} Descargar Instructivo</a>
        </div>
      </div>'''
    
    if has_manual:
        return f'''      <div class="doc-section">
        <div class="doc-viewer"><iframe src="{manual_path}" title="Manual de {nombre}"></iframe></div>
        <div class="doc-actions">
          <a href="{manual_path}" download class="pdf-download">{SVG_DOWNLOAD} Descargar Manual</a>
        </div>
      </div>'''
    
    return '''      <div class="doc-section">
        <div class="placeholder-msg">
          <h3>📄 Documentación pendiente</h3>
          <p>El instructivo de uso y manual para este equipo están pendientes de carga.</p>
        </div>
      </div>'''


# ─── Main ──────────────────────────────────────────────────────

def main():
    os.makedirs(EQUIPOS_DIR, exist_ok=True)
    
    equipos = read_csv()
    areas = get_areas(equipos)
    instructivos = load_instructivos()
    
    print(f"Equipos: {len(equipos)} | Áreas: {len(areas)} | Instructivos: {sum(len(v) for v in instructivos.values())}")
    
    with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(generate_index(equipos, areas))
    
    for e in equipos:
        filepath = os.path.join(EQUIPOS_DIR, f"{e['slug']}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(generate_equipo_page(e, instructivos))
    
    print(f"Generadas: index.html + {len(equipos)} páginas en equipos/")


if __name__ == "__main__":
    main()
