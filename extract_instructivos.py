#!/usr/bin/env python3
import subprocess
import re
import os
import csv
import json

PDF_PATH = "/home/sam/Downloads/equipos/instructivo de cada equipo corto para cada uno.pdf"
CSV_PATH = "/home/sam/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv"
OUTPUT_DIR = "/home/sam/Projects/04_registros_equipos/inventario_equipos"
INSTRUCTIVOS_DIR = os.path.join(OUTPUT_DIR, "instructivos")

EXCLUDE_KEYWORDS = [
    "silla", "mesa", "escritorio", "extintor", "teclado", "monitor",
    "munition", "cpu", "estabilizador", "camara domo", "camara de tubo",
    "monitor de camaras", "rodadora de video", "pantalla", "impresora"
]

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def extract_text():
    result = subprocess.run(['pdftotext', PDF_PATH, '-'], capture_output=True, text=True)
    return result.stdout

def split_instructivos(text):
    pattern = r'INSTRUCTIVO DE USO[:\s]+(.*?)(?=INSTRUCTIVO DE USO[:\s]|$)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    instructivos = []
    for match in matches:
        content = match.strip()
        if len(content) < 20:
            continue
        
        lines = content.split('\n')
        title_line = lines[0].strip()
        
        marca = ""
        modelo = ""
        serie = ""
        pasos = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('MARCA:'):
                marca = line.replace('MARCA:', '').strip()
            elif line.startswith('MODELO:'):
                modelo = line.replace('MODELO:', '').strip()
            elif line.startswith('SERIE:'):
                serie = line.replace('SERIE:', '').strip()
            elif re.match(r'^\d+\.?\s', line):
                pasos.append(line)
        
        instructivos.append({
            'titulo': title_line,
            'marca': marca,
            'modelo': modelo,
            'serie': serie,
            'pasos': '\n'.join(pasos),
            'contenido_completo': content
        })
    
    return instructivos

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
                'modelo': row.get('Modelo', '').strip(),
                'marca': row.get('Marca 2', '').strip(),
                'serie': row.get('Serie', '').strip(),
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos

def should_exclude(nombre):
    nombre_lower = nombre.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in nombre_lower:
            return True
    return False

def map_instructivos_to_equipos(instructivos, equipos):
    mapping = {}
    
    keyword_map = {
        'agitador vortex': ['agitador-vortex'],
        'microscopio': ['microscopio-011372', 'microscopio-electronico-010361', 'stereoscopio-010360'],
        'balanza de precisión': ['balanza-de-precisión'],
        'balanza analitica': ['balanza-analitica'],
        'plancha de calentamiento': ['agitador-magnetico'],
        'lavador de microplacas': ['lavadora-de-micro-placas-para-elisa'],
        'lector de placas': ['lector-de-placas-elisa'],
        'homogeneizador': ['homogeneizador-de-muestraz'],
        'ultracentrifuga': ['centrifuga-refrigerada-ultra-centrifuga'],
        'centrifuga': ['centrifuga-convencional-011363', 'centrifuga-convencional-011362', 'centrifuga-convencional-011361'],
        'microcentrifuga': ['microcentrifugadora', 'mini-centrifuga-1', 'mini-centrifuga-2', 'centrifuga-de-mircoplacas'],
        'destilador de agua': ['destilador-de-agua'],
        'baño maria': ['baño-maría'],
        'autoclave': ['autoclave'],
        'congeladora': ['refrigerador-1', 'refrigerador-2', 'refrigerador-3'],
        'incubadora': ['incubadora-convencional', 'incubadora-de-co2'],
        'estufa': ['horno-de-esterilización'],
        'refrigeradora': ['refrigerador-1', 'refrigerador-2', 'refrigerador-3'],
        'cabina de pcr': ['pcr-workstation'],
        'cabina de bioseguridad': ['csb-clase-2'],
        'campana de extracción': ['camara-extractora-metálica'],
        'espectofot': ['espectofotrometro', 'espectofotrometro-2'],
        'documentador de geles': ['documentador-de-geles'],
        'ph metro': [],
        'potenciometro': [],
        'cámara de electroforesis vertical': ['camara-de-electroforesis-vertical', 'camara-de-electroforesis-vertical-2'],
        'cámara de electroforesis horizontal': ['camara-de-electroforesis-horizontal'],
        'fluo': [],
        'baño seco': ['baño-seco-digital-de-agitacion-y-calentamiento'],
        'agitador orbital': ['agitador-orbital'],
        'termociclador': ['termociclador', 'termociclador-en-tiempo-real', 'qpcr'],
        'ultrapurificador': ['ultrapurificador-de-agua'],
        'contador de células': [],
        'quantstudio': ['qpcr', 'termociclador-en-tiempo-real'],
    }
    
    for inst in instructivos:
        titulo_lower = inst['titulo'].lower()
        matched_slugs = []
        
        for keyword, slugs in keyword_map.items():
            if keyword in titulo_lower:
                matched_slugs.extend(slugs)
                break
        
        if not matched_slugs:
            for e in equipos:
                if inst['modelo'] and inst['modelo'].lower() in e['modelo'].lower():
                    matched_slugs.append(e['slug'])
                elif inst['marca'] and inst['marca'].lower() in e['marca'].lower():
                    if inst['modelo'] and inst['modelo'].lower() in e['nombre'].lower():
                        matched_slugs.append(e['slug'])
        
        for slug in matched_slugs:
            if slug not in mapping:
                mapping[slug] = []
            mapping[slug].append(inst)
    
    return mapping

def main():
    os.makedirs(INSTRUCTIVOS_DIR, exist_ok=True)
    
    text = extract_text()
    instructivos = split_instructivos(text)
    print(f"Instructivos encontrados: {len(instructivos)}")
    
    equipos = read_csv()
    print(f"Equipos en inventario: {len(equipos)}")
    
    mapping = map_instructivos_to_equipos(instructivos, equipos)
    
    for slug, inst_list in mapping.items():
        for i, inst in enumerate(inst_list):
            filename = f"{slug}.txt" if i == 0 else f"{slug}_{i+1}.txt"
            filepath = os.path.join(INSTRUCTIVOS_DIR, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(inst['contenido_completo'])
    
    print(f"\nMapeo:")
    for slug, inst_list in sorted(mapping.items()):
        names = [inst['titulo'] for inst in inst_list]
        print(f"  {slug}: {', '.join(names)}")
    
    print(f"\nTotal: {sum(len(v) for v in mapping.values())} instructivos mapeados a {len(mapping)} equipos")
    
    json_path = os.path.join(OUTPUT_DIR, "instructivos_map.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({k: [inst['contenido_completo'] for inst in v] for k, v in mapping.items()}, f, ensure_ascii=False, indent=2)
    print(f"Mapping guardado en: {json_path}")

if __name__ == "__main__":
    main()
