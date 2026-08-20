#!/usr/bin/env python3
"""
Extracto de instructivos del PDF del profesor.
Lee el PDF con pdftotext, separa cada instructivo y lo mapea a los equipos del CSV.

Uso:
    python3 extract_instructivos.py
"""

import subprocess
import re
import os
import csv
import json

# ─── Configuración ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.expanduser("~/Downloads/equipos/instructivo de cada equipo corto para cada uno.pdf")
CSV_PATH = os.path.expanduser("~/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv")
INSTRUCTIVOS_DIR = os.path.join(BASE_DIR, "instructivos")
INSTRUCTIVOS_MAP = os.path.join(BASE_DIR, "instructivos_map.json")

EXCLUDE_KEYWORDS = [
    "silla", "mesa", "escritorio", "extintor", "teclado", "monitor",
    "munition", "cpu", "estabilizador", "camara domo", "camara de tubo",
    "monitor de camaras", "rodadora de video", "pantalla", "impresora"
]

# Mapeo de palabras clave del instructivo → slugs de equipos
KEYWORD_MAP = {
    'agitador vortex':            ['agitador-vortex'],
    'microscopio':                ['microscopio-011372', 'microscopio-electronico-010361', 'stereoscopio-010360'],
    'balanza de precisión':       ['balanza-de-precisión'],
    'balanza analitica':          ['balanza-analitica'],
    'plancha de calentamiento':   ['agitador-magnetico'],
    'lavador de microplacas':     ['lavadora-de-micro-placas-para-elisa'],
    'lector de placas':           ['lector-de-placas-elisa'],
    'homogeneizador':             ['homogeneizador-de-muestraz'],
    'ultracentrifuga':            ['centrifuga-refrigerada-ultra-centrifuga'],
    'centrifuga':                 ['centrifuga-convencional-011363', 'centrifuga-convencional-011362', 'centrifuga-convencional-011361'],
    'microcentrifuga':            ['microcentrifugadora', 'mini-centrifuga-1', 'mini-centrifuga-2', 'centrifuga-de-mircoplacas'],
    'destilador de agua':         ['destilador-de-agua'],
    'baño maria':                 ['baño-maría'],
    'autoclave':                  ['autoclave'],
    'congeladora':                ['refrigerador-1', 'refrigerador-2', 'refrigerador-3'],
    'incubadora':                 ['incubadora-convencional', 'incubadora-de-co2'],
    'estufa':                     ['horno-de-esterilización'],
    'refrigeradora':              ['refrigerador-1', 'refrigerador-2', 'refrigerador-3'],
    'cabina de pcr':              ['pcr-workstation'],
    'cabina de bioseguridad':     ['csb-clase-2'],
    'campana de extracción':      ['camara-extractora-metálica'],
    'espectofot':                 ['espectofotrometro', 'espectofotrometro-2'],
    'documentador de geles':      ['documentador-de-geles'],
    'cámara de electroforesis vertical':  ['camara-de-electroforesis-vertical', 'camara-de-electroforesis-vertical-2'],
    'cámara de electroforesis horizontal': ['camara-de-electroforesis-horizontal'],
    'baño seco':                  ['baño-seco-digital-de-agitacion-y-calentamiento'],
    'agitador orbital':           ['agitador-orbital'],
    'termociclador':              ['termociclador', 'termociclador-en-tiempo-real', 'qpcr'],
    'ultrapurificador':           ['ultrapurificador-de-agua'],
    'quantstudio':                ['qpcr', 'termociclador-en-tiempo-real'],
}


# ─── Utilidades ─────────────────────────────────────────────────

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def should_exclude(nombre):
    nombre_lower = nombre.lower()
    return any(kw in nombre_lower for kw in EXCLUDE_KEYWORDS)


# ─── Extracción del PDF ────────────────────────────────────────

def extract_text():
    """Extrae texto del PDF del profesor usando pdftotext."""
    result = subprocess.run(['pdftotext', PDF_PATH, '-'], capture_output=True, text=True)
    return result.stdout


def split_instructivos(text):
    """Divide el texto extraído en instructivos individuales."""
    pattern = r'INSTRUCTIVO DE USO[:\s]+(.*?)(?=INSTRUCTIVO DE USO[:\s]|$)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    instructivos = []
    for match in matches:
        content = match.strip()
        if len(content) < 20:
            continue
        
        lines = content.split('\n')
        parsed = {'titulo': lines[0].strip(), 'marca': '', 'modelo': '', 'serie': '', 'contenido_completo': content}
        
        for line in lines:
            line = line.strip()
            if line.startswith('MARCA:'):
                parsed['marca'] = line.replace('MARCA:', '').strip()
            elif line.startswith('MODELO:'):
                parsed['modelo'] = line.replace('MODELO:', '').strip()
            elif line.startswith('SERIE:'):
                parsed['serie'] = line.replace('SERIE:', '').strip()
        
        instructivos.append(parsed)
    
    return instructivos


# ─── CSV ────────────────────────────────────────────────────────

def read_csv():
    """Lee el CSV de inventario (solo campos necesarios para el mapeo)."""
    equipos = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            nombre = row.get('Nombre', '').strip()
            if not nombre or should_exclude(nombre):
                continue
            codigo = row.get('Codigo Actual', '').strip()
            if not codigo:
                continue
            equipos.append({
                'nombre': nombre,
                'codigo': codigo,
                'modelo': row.get('Modelo', '').strip(),
                'marca': row.get('Marca 2', '').strip(),
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos


# ─── Mapeo ──────────────────────────────────────────────────────

def map_instructivos(instructivos, equipos):
    """Mapea cada instructivo a los equipos correspondientes."""
    mapping = {}
    
    for inst in instructivos:
        titulo_lower = inst['titulo'].lower()
        matched_slugs = []
        
        # Buscar por palabra clave
        for keyword, slugs in KEYWORD_MAP.items():
            if keyword in titulo_lower:
                matched_slugs.extend(slugs)
                break
        
        # Fallback: buscar por modelo/marca
        if not matched_slugs:
            for e in equipos:
                if inst['modelo'] and inst['modelo'].lower() in e['modelo'].lower():
                    matched_slugs.append(e['slug'])
                elif inst['marca'] and inst['marca'].lower() in e['marca'].lower():
                    if inst['modelo'] and inst['modelo'].lower() in e['nombre'].lower():
                        matched_slugs.append(e['slug'])
        
        for slug in matched_slugs:
            mapping.setdefault(slug, []).append(inst)
    
    return mapping


# ─── Main ──────────────────────────────────────────────────────

def main():
    os.makedirs(INSTRUCTIVOS_DIR, exist_ok=True)
    
    text = extract_text()
    instructivos = split_instructivos(text)
    print(f"Instructivos en PDF: {len(instructivos)}")
    
    equipos = read_csv()
    print(f"Equipos en CSV: {len(equipos)}")
    
    mapping = map_instructivos(instructivos, equipos)
    
    # Guardar textos individuales
    for slug, inst_list in mapping.items():
        for i, inst in enumerate(inst_list):
            filename = f"{slug}.txt" if i == 0 else f"{slug}_{i+1}.txt"
            with open(os.path.join(INSTRUCTIVOS_DIR, filename), 'w', encoding='utf-8') as f:
                f.write(inst['contenido_completo'])
    
    # Guardar mapeo JSON
    json_data = {k: [inst['contenido_completo'] for inst in v] for k, v in mapping.items()}
    with open(INSTRUCTIVOS_MAP, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Resumen
    print(f"\nMapeo ({len(mapping)} equipos, {sum(len(v) for v in mapping.values())} instructivos):")
    for slug in sorted(mapping):
        names = [inst['titulo'] for inst in mapping[slug]]
        print(f"  {slug}: {', '.join(names)}")
    
    print(f"\nGuardado en: {INSTRUCTIVOS_MAP}")


if __name__ == "__main__":
    main()
