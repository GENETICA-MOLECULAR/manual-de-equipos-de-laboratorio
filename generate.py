#!/usr/bin/env python3
import csv
import os
import re
import json

CSV_PATH = "/home/sam/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv"
OUTPUT_DIR = "/home/sam/Projects/04_registros_equipos/inventario_equipos"
EQUIPOS_DIR = os.path.join(OUTPUT_DIR, "equipos")
INSTRUCTIVOS_MAP = os.path.join(OUTPUT_DIR, "instructivos_map.json")

# Equipment to exclude (furniture, non-lab equipment)
EXCLUDE_KEYWORDS = [
    "silla", "mesa", "escritorio", "extintor", "teclado", "monitor",
    "munition", "cpu", "estabilizador", "camara domo", "camara de tubo",
    "monitor de camaras", "rodadora de video", "pantalla", "impresora"
]

# Map equipment names to PDF files
PDF_MAP = {
    "autoclave": "AUTOCLAVE  BENCHMARK.pdf",
    "balanza de precisión": "BALANZA FX-500i.pdf",
    "baño maría": "BAÑO MARIA MEMMERT.pdf",
    "homogeneizador": "HOMOGENEIZADOR- MANUAL ESPAÑOL.pdf",
    "incubadora de co2": "INCUBADORA DE CO2.pdf",
    "incubadora convencional": "MANUAL DE LA INCUBADORA MARCA MEMMERT MODELO IF55.pdf",
}

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def has_pdf(nombre):
    nombre_lower = nombre.lower()
    for key, pdf in PDF_MAP.items():
        if key in nombre_lower:
            return pdf
    return None

def should_exclude(nombre):
    nombre_lower = nombre.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in nombre_lower:
            return True
    return False

def load_instructivos():
    if os.path.exists(INSTRUCTIVOS_MAP):
        with open(INSTRUCTIVOS_MAP, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def format_instructivo_html(text):
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
        
        if line.startswith('MARCA:') or line.startswith('MODELO:') or line.startswith('SERIE:'):
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

def read_csv():
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
                'pdf': has_pdf(nombre),
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos

def get_areas(equipos):
    areas = sorted(set(e['area'] for e in equipos if e['area']))
    return areas

def generate_index(equipos, areas):
    total = len(equipos)
    con_pdf = sum(1 for e in equipos if e['pdf'])
    
    filter_btns = '\n'.join([
        f'            <button class="filter-btn active" data-area="todos">Todos ({total})</button>',
        f'            <button class="filter-btn" data-area="con-manual">📄 Con Manual ({con_pdf})</button>'
    ] + [
        f'            <button class="filter-btn" data-area="{area}">{area} ({sum(1 for e in equipos if e["area"]==area)})</button>'
        for area in areas
    ])
    
    cards = []
    for e in equipos:
        pdf_badge = f'<span class="equipo-pdf">📄 Manual disponible</span>' if e['pdf'] else ''
        estado_class = e['estado'].lower().replace(' ', '-')
        if 'bueno' in estado_class:
            estado_class = 'bueno'
        elif 'malo' in estado_class:
            estado_class = 'malo'
        else:
            estado_class = 'desuso'
        
        card = f'''        <a href="equipos/{e['slug']}.html" class="equipo-card" data-area="{e['area']}" data-pdf="{ 'si' if e['pdf'] else 'no' }">
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
    
    cards_html = '\n'.join(cards)
    
    html = f'''<!DOCTYPE html>
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
  <script>
    const getSystemTheme = () => window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null;
    const initialTheme = savedTheme || getSystemTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {{
      if (!localStorage.getItem('theme')) {{
        document.documentElement.setAttribute('data-theme', e.matches ? 'light' : 'dark');
      }}
    }});
  </script>
</head>
<body>
  <main class="container">
    <div class="glass-panel">
      <button id="themeToggle" class="theme-toggle" aria-label="Cambiar tema">
        <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
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
          <span class="stat-value">{con_pdf}</span>
          <span class="stat-label">Con Manual</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{len(areas)}</span>
          <span class="stat-label">Áreas</span>
        </div>
      </div>

      <div class="search-bar">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" id="searchInput" placeholder="Buscar equipo por nombre, código, marca o modelo...">
      </div>

      <div class="filters">
{filter_btns}
      </div>

      <div class="equipos-grid" id="equiposGrid">
{cards_html}
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
    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }});

    const searchInput = document.getElementById('searchInput');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const grid = document.getElementById('equiposGrid');
    const cards = grid.querySelectorAll('.equipo-card');
    const noResults = document.getElementById('noResults');
    let currentArea = 'todos';

    filterBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentArea = btn.dataset.area;
        filterCards();
      }});
    }});

    searchInput.addEventListener('input', filterCards);

    function filterCards() {{
      const query = searchInput.value.toLowerCase();
      let visible = 0;
      cards.forEach(card => {{
        const text = card.textContent.toLowerCase();
        const area = card.dataset.area;
        const hasPdf = card.dataset.pdf === 'si';
        const matchSearch = !query || text.includes(query);
        const matchArea = currentArea === 'todos' || area === currentArea || (currentArea === 'con-manual' && hasPdf);
        if (matchSearch && matchArea) {{
          card.style.display = '';
          visible++;
        }} else {{
          card.style.display = 'none';
        }}
      }});
      noResults.style.display = visible === 0 ? '' : 'none';
    }}
  </script>
</body>
</html>'''
    
    return html

def generate_equipo_page(e, instructivos):
    slug = e['slug']
    inst_list = instructivos.get(slug, [])
    
    has_manual = e['pdf'] is not None
    has_inst = os.path.exists(os.path.join(OUTPUT_DIR, "instructivos_pdf", f"{slug}.pdf"))
    if not has_inst:
        nombre_slug = slugify(e['nombre'])
        has_inst = os.path.exists(os.path.join(OUTPUT_DIR, "instructivos_pdf", f"{nombre_slug}.pdf"))
        if has_inst:
            inst_path = f"../instructivos_pdf/{nombre_slug}.pdf"
        else:
            inst_path = None
    else:
        inst_path = f"../instructivos_pdf/{slug}.pdf"
    manual_path = f"../pdfs/{e['pdf']}" if has_manual else None
    
    doc_section = ""
    
    if has_manual and has_inst:
        doc_section = f'''
      <div class="doc-section">
        <div class="doc-toggle">
          <button class="doc-tab active" data-doc="inst" onclick="showDoc('inst')">📋 Instructivo</button>
          <button class="doc-tab" data-doc="manual" onclick="showDoc('manual')">📖 Manual Original</button>
        </div>
        <div class="doc-viewer" id="doc-inst" style="display:block">
          <iframe src="{inst_path}" title="Instructivo de {e['nombre']}"></iframe>
        </div>
        <div class="doc-viewer" id="doc-manual" style="display:none">
          <iframe src="{manual_path}" title="Manual de {e['nombre']}"></iframe>
        </div>
        <div class="doc-actions">
          <a href="{inst_path}" download class="pdf-download">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Descargar Instructivo
          </a>
          <a href="{manual_path}" download class="pdf-download pdf-download--secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Descargar Manual
          </a>
        </div>
      </div>'''
    elif has_inst:
        doc_section = f'''
      <div class="doc-section">
        <div class="doc-viewer" style="display:block">
          <iframe src="{inst_path}" title="Instructivo de {e['nombre']}"></iframe>
        </div>
        <div class="doc-actions">
          <a href="{inst_path}" download class="pdf-download">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Descargar Instructivo
          </a>
        </div>
      </div>'''
    elif has_manual:
        doc_section = f'''
      <div class="doc-section">
        <div class="doc-viewer" style="display:block">
          <iframe src="{manual_path}" title="Manual de {e['nombre']}"></iframe>
        </div>
        <div class="doc-actions">
          <a href="{manual_path}" download class="pdf-download">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Descargar Manual
          </a>
        </div>
      </div>'''
    else:
        doc_section = '''
      <div class="doc-section">
        <div class="placeholder-msg">
          <h3>📄 Documentación pendiente</h3>
          <p>El instructivo de uso y manual para este equipo están pendientes de carga.</p>
        </div>
      </div>'''
    
    html = f'''<!DOCTYPE html>
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
  <script>
    const getSystemTheme = () => window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    const savedTheme = typeof localStorage !== 'undefined' ? localStorage.getItem('theme') : null;
    const initialTheme = savedTheme || getSystemTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {{
      if (!localStorage.getItem('theme')) {{
        document.documentElement.setAttribute('data-theme', e.matches ? 'light' : 'dark');
      }}
    }});
  </script>
</head>
<body>
  <main class="container">
    <div class="glass-panel">
      <button id="themeToggle" class="theme-toggle" aria-label="Cambiar tema">
        <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
        <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
      </button>

      <a href="../index.html" class="back-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
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
        <div class="info-item">
          <div class="info-label">Código Actual</div>
          <div class="info-value">{e['codigo']}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Código Antiguo</div>
          <div class="info-value">{e['codigo_antiguo'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Modelo</div>
          <div class="info-value">{e['modelo'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Marca</div>
          <div class="info-value">{e['marca'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Serie</div>
          <div class="info-value">{e['serie'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Color</div>
          <div class="info-value">{e['color'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Estado</div>
          <div class="info-value">{e['estado']}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Situación</div>
          <div class="info-value">{e['situacion'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Importe</div>
          <div class="info-value">{e['importe'] or 'N/A'}</div>
        </div>
        <div class="info-item">
          <div class="info-label">Área</div>
          <div class="info-value">{e['area']}</div>
        </div>
        </div>
{doc_section}

      <footer class="footer">
        <p>Laboratorio de Genética Molecular - Facultad de Ciencias Biológicas, UNSAAC</p>
      </footer>
    </div>
  </main>

  <script>
    document.getElementById('themeToggle').addEventListener('click', () => {{
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    }});

    function showDoc(type) {{
      document.getElementById('doc-inst').style.display = type === 'inst' ? 'block' : 'none';
      document.getElementById('doc-manual').style.display = type === 'manual' ? 'block' : 'none';
      document.querySelectorAll('.doc-tab').forEach(tab => {{
        tab.classList.toggle('active', tab.dataset.doc === type);
      }});
    }}
  </script>
</body>
</html>'''
    
    return html

def main():
    os.makedirs(EQUIPOS_DIR, exist_ok=True)
    
    equipos = read_csv()
    areas = get_areas(equipos)
    instructivos = load_instructivos()
    
    print(f"Equipos encontrados: {len(equipos)}")
    print(f"Áreas: {areas}")
    print(f"Instructivos cargados: {sum(len(v) for v in instructivos.values())}")
    
    # Generate index
    index_html = generate_index(equipos, areas)
    with open(os.path.join(OUTPUT_DIR, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_html)
    print("index.html generado")
    
    # Generate individual pages
    for e in equipos:
        html = generate_equipo_page(e, instructivos)
        filepath = os.path.join(EQUIPOS_DIR, f"{e['slug']}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  - {e['slug']}.html")
    
    print(f"\nTotal: {len(equipos)} páginas generadas")

if __name__ == "__main__":
    main()
