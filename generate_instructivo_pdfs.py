#!/usr/bin/env python3
"""
Generador de PDFs de instructivos a partir del texto plano.
Lee instructivos_map.json y genera un PDF por cada instructivo.

Uso:
    python3 generate_instructivo_pdfs.py
"""

import json
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ─── Configuración ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTRUCTIVOS_MAP = os.path.join(BASE_DIR, "instructivos_map.json")
PDF_DIR = os.path.join(BASE_DIR, "instructivos_pdf")

# Colores del laboratorio
PRIMARY = HexColor('#2563eb')
DARK = HexColor('#1a1a2e')
GRAY = HexColor('#555555')
LIGHT_GRAY = HexColor('#888888')


# ─── Estilos PDF ────────────────────────────────────────────────

def get_styles():
    """Define los estilos de párrafo para los instructivos."""
    styles = getSampleStyleSheet()
    
    defs = {
        'InstTitle':    {'font': 'Helvetica-Bold', 'size': 16, 'color': PRIMARY, 'align': TA_CENTER, 'after': 4},
        'InstSubtitle': {'font': 'Helvetica',      'size': 9,  'color': LIGHT_GRAY, 'align': TA_CENTER, 'after': 16},
        'InstHeader':   {'font': 'Helvetica-Bold', 'size': 10, 'color': DARK, 'after': 2},
        'InstMeta':     {'font': 'Helvetica',      'size': 10, 'color': GRAY, 'left': 12, 'after': 1},
        'InstStep':     {'font': 'Helvetica',      'size': 10, 'color': DARK, 'left': 24, 'after': 6, 'leading': 14},
        'InstNote':     {'font': 'Helvetica-Oblique', 'size': 9, 'color': LIGHT_GRAY, 'left': 24, 'after': 6},
        'InstFooter':   {'font': 'Helvetica',      'size': 8,  'color': LIGHT_GRAY, 'align': TA_CENTER},
    }
    
    for name, d in defs.items():
        styles.add(ParagraphStyle(
            name=name,
            fontName=d['font'],
            fontSize=d['size'],
            textColor=d['color'],
            alignment=d.get('align', TA_LEFT),
            leftIndent=d.get('left', 0),
            spaceAfter=d.get('after', 0),
            spaceBefore=d.get('before', 0),
            leading=d.get('leading', 0),
        ))
    
    return styles


# ─── Parseo ─────────────────────────────────────────────────────

def parse_instructivo(text):
    """Extrae título, marca, modelo, serie, pasos y notas de un instructivo."""
    result = {'title': '', 'marca': '', 'modelo': '', 'serie': '', 'steps': [], 'notes': []}
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('INSTRUCTIVO DE USO'):
            result['title'] = re.sub(r'^INSTRUCTIVO DE USO[:\s]*', '', line, flags=re.IGNORECASE).strip() or line
        elif line.upper().startswith(('MARCA:', 'MODELO:', 'SERIE:')):
            key, val = line.split(':', 1)
            result[key.strip().lower()] = val.strip()
        elif re.match(r'^\d+\.?\s', line):
            result['steps'].append(re.sub(r'^\d+\.?\s*', '', line))
        elif any(kw in line.upper() for kw in ('OJO:', 'NOTA:', 'IMPORTANTE:')):
            result['notes'].append(line)
        elif result['steps'] and not result['steps'][-1].endswith('.'):
            result['steps'][-1] += ' ' + line
    
    return result


# ─── Generación PDF ─────────────────────────────────────────────

def build_pdf(parsed, pdf_path):
    """Genera un PDF formateado para un instructivo."""
    doc = SimpleDocTemplate(
        pdf_path, pagesize=letter,
        topMargin=0.8*inch, bottomMargin=0.8*inch,
        leftMargin=1*inch, rightMargin=1*inch
    )
    
    styles = get_styles()
    story = []
    
    # Título
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("INSTRUCTIVO DE USO", styles['InstTitle']))
    story.append(Paragraph(parsed['title'] or "INSTRUCTIVO DE USO", styles['InstSubtitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))
    
    # Info del equipo
    if any(parsed[k] for k in ('marca', 'modelo', 'serie')):
        story.append(Paragraph("INFORMACIÓN DEL EQUIPO", styles['InstHeader']))
        for key in ('marca', 'modelo', 'serie'):
            if parsed[key]:
                story.append(Paragraph(f"<b>{key.upper()}:</b> {parsed[key]}", styles['InstMeta']))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd'), spaceAfter=12))
    
    # Pasos
    story.append(Paragraph("PROCEDIMIENTO DE USO", styles['InstHeader']))
    story.append(Spacer(1, 6))
    
    for i, step in enumerate(parsed['steps'], 1):
        story.append(Paragraph(f'<font color="#{PRIMARY.hexval()[2:]}"><b>{i}.</b></font>  {step}', styles['InstStep']))
    
    # Notas
    for note in parsed['notes']:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"⚠ {note}", styles['InstNote']))
    
    # Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd'), spaceAfter=8))
    story.append(Paragraph("Laboratorio de Genética Molecular — UNSAAC", styles['InstFooter']))
    
    doc.build(story)


# ─── Main ──────────────────────────────────────────────────────

def main():
    os.makedirs(PDF_DIR, exist_ok=True)
    
    with open(INSTRUCTIVOS_MAP, 'r', encoding='utf-8') as f:
        instructivos = json.load(f)
    
    count = 0
    for slug, texts in instructivos.items():
        for i, text in enumerate(texts):
            parsed = parse_instructivo(text)
            pdf_name = f"{slug}.pdf" if i == 0 else f"{slug}_{i+1}.pdf"
            build_pdf(parsed, os.path.join(PDF_DIR, pdf_name))
            count += 1
            print(f"  ✓ {pdf_name}")
    
    print(f"\nTotal: {count} PDFs → {PDF_DIR}")


if __name__ == "__main__":
    main()
