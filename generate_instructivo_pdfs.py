#!/usr/bin/env python3
import json
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUTPUT_DIR = "/home/sam/Projects/04_registros_equipos/inventario_equipos"
INSTRUCTIVOS_MAP = os.path.join(OUTPUT_DIR, "instructivos_map.json")
PDF_DIR = os.path.join(OUTPUT_DIR, "instructivos_pdf")

PRIMARY = HexColor('#2563eb')
PRIMARY_LIGHT = HexColor('#3b82f6')
DARK = HexColor('#1a1a2e')
GRAY = HexColor('#555555')
LIGHT_GRAY = HexColor('#888888')
BG_LIGHT = HexColor('#f0f4f8')

def get_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='InstTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=4,
        spaceBefore=0,
    ))
    
    styles.add(ParagraphStyle(
        name='InstSubtitle',
        fontName='Helvetica',
        fontSize=9,
        textColor=LIGHT_GRAY,
        alignment=TA_CENTER,
        spaceAfter=16,
    ))
    
    styles.add(ParagraphStyle(
        name='InstHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=DARK,
        spaceAfter=2,
        spaceBefore=0,
    ))
    
    styles.add(ParagraphStyle(
        name='InstMeta',
        fontName='Helvetica',
        fontSize=10,
        textColor=GRAY,
        leftIndent=12,
        spaceAfter=1,
    ))
    
    styles.add(ParagraphStyle(
        name='InstStep',
        fontName='Helvetica',
        fontSize=10,
        textColor=DARK,
        leftIndent=24,
        spaceAfter=6,
        leading=14,
    ))
    
    styles.add(ParagraphStyle(
        name='InstNote',
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=LIGHT_GRAY,
        leftIndent=24,
        spaceAfter=6,
    ))
    
    styles.add(ParagraphStyle(
        name='InstFooter',
        fontName='Helvetica',
        fontSize=8,
        textColor=LIGHT_GRAY,
        alignment=TA_CENTER,
    ))
    
    return styles

def parse_instructivo(text):
    lines = text.strip().split('\n')
    title = ""
    marca = ""
    modelo = ""
    serie = ""
    steps = []
    notes = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('INSTRUCTIVO DE USO'):
            title = re.sub(r'^INSTRUCTIVO DE USO[:\s]*', '', line, flags=re.IGNORECASE).strip()
            if not title:
                title = line
        elif line.upper().startswith('MARCA:'):
            marca = line.split(':', 1)[1].strip()
        elif line.upper().startswith('MODELO:'):
            modelo = line.split(':', 1)[1].strip()
        elif line.upper().startswith('SERIE:'):
            serie = line.split(':', 1)[1].strip()
        elif re.match(r'^\d+\.?\s', line):
            step_text = re.sub(r'^\d+\.?\s*', '', line)
            steps.append(step_text)
        elif 'OJO:' in line.upper() or 'NOTA:' in line.upper() or 'IMPORTANTE:' in line.upper():
            notes.append(line)
        elif steps:
            if steps[-1] and not steps[-1].endswith('.'):
                steps[-1] += ' ' + line
            else:
                steps.append(line)
    
    return {
        'title': title,
        'marca': marca,
        'modelo': modelo,
        'serie': serie,
        'steps': steps,
        'notes': notes
    }

def build_pdf(parsed, pdf_path):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        topMargin=0.8*inch,
        bottomMargin=0.8*inch,
        leftMargin=1*inch,
        rightMargin=1*inch
    )
    
    styles = get_styles()
    story = []
    
    story.append(Spacer(1, 0.2*inch))
    
    header_text = parsed['title'] if parsed['title'] else "INSTRUCTIVO DE USO"
    story.append(Paragraph(f"INSTRUCTIVO DE USO", styles['InstTitle']))
    story.append(Paragraph(header_text, styles['InstSubtitle']))
    
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))
    
    if parsed['marca'] or parsed['modelo'] or parsed['serie']:
        story.append(Paragraph("INFORMACIÓN DEL EQUIPO", styles['InstHeader']))
        story.append(Spacer(1, 4))
        
        meta_data = []
        if parsed['marca']:
            meta_data.append(['<b>MARCA:</b>', parsed['marca']])
        if parsed['modelo']:
            meta_data.append(['<b>MODELO:</b>', parsed['modelo']])
        if parsed['serie']:
            meta_data.append(['<b>SERIE:</b>', parsed['serie']])
        
        for label, value in meta_data:
            story.append(Paragraph(f"{label} {value}", styles['InstMeta']))
        
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd'), spaceAfter=12))
    
    story.append(Paragraph("PROCEDIMIENTO DE USO", styles['InstHeader']))
    story.append(Spacer(1, 6))
    
    for i, step in enumerate(parsed['steps'], 1):
        step_html = f'<font color="#{PRIMARY.hexval()[2:]}"><b>{i}.</b></font>  {step}'
        story.append(Paragraph(step_html, styles['InstStep']))
    
    for note in parsed['notes']:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"⚠ {note}", styles['InstNote']))
    
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#dddddd'), spaceAfter=8))
    story.append(Paragraph("Laboratorio de Genética Molecular — UNSAAC", styles['InstFooter']))
    
    doc.build(story)

def main():
    os.makedirs(PDF_DIR, exist_ok=True)
    
    with open(INSTRUCTIVOS_MAP, 'r', encoding='utf-8') as f:
        instructivos = json.load(f)
    
    count = 0
    for slug, texts in instructivos.items():
        for i, text in enumerate(texts):
            parsed = parse_instructivo(text)
            
            if i == 0:
                pdf_name = f"{slug}.pdf"
            else:
                pdf_name = f"{slug}_{i+1}.pdf"
            
            pdf_path = os.path.join(PDF_DIR, pdf_name)
            build_pdf(parsed, pdf_path)
            count += 1
            print(f"  ✓ {pdf_name}")
    
    print(f"\nTotal: {count} PDFs generados en {PDF_DIR}")

if __name__ == "__main__":
    main()
