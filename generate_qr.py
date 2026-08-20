#!/usr/bin/env python3
"""
Generador de QR codes para cada equipo.
Crea un PDF con 56 QR codes, 4 por página, listos para imprimir y pegar.

Uso:
    python3 generate_qr.py
"""

import csv
import os
import re
import tempfile
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ─── Configuración ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.expanduser("~/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv")
BASE_URL = "https://genetica-molecular.github.io/manual-de-equipos-de-laboratorio/equipos/"
OUTPUT_PDF = os.path.join(BASE_DIR, "qr-equipos.pdf")

EXCLUDE_KEYWORDS = [
    "silla", "mesa", "escritorio", "extintor", "teclado", "monitor",
    "munition", "cpu", "estabilizador", "camara domo", "camara de tubo",
    "monitor de camaras", "rodadora de video", "pantalla", "impresora"
]

# Layout de la página
QR_SIZE = 3.5 * inch
COLS = 2
ROWS = 2
ITEMS_PER_PAGE = COLS * ROWS


# ─── Utilidades ─────────────────────────────────────────────────

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def should_exclude(nombre):
    nombre_lower = nombre.lower()
    return any(kw in nombre_lower for kw in EXCLUDE_KEYWORDS)


def read_csv():
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
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos


# ─── Generación QR ──────────────────────────────────────────────

def generate_qr_pdf(equipos):
    """Genera un PDF con QR codes, 4 por página."""
    c = canvas.Canvas(OUTPUT_PDF, pagesize=letter)
    width, height = letter
    
    margin_x = (width - COLS * (QR_SIZE + 0.5*inch)) / 2 + 0.3*inch
    margin_top = 1*inch
    
    for idx, e in enumerate(equipos):
        pos = idx % ITEMS_PER_PAGE
        
        if pos == 0:
            if idx > 0:
                c.showPage()
            page_num = idx // ITEMS_PER_PAGE + 1
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawCentredString(width/2, height - 0.5*inch,
                f"Laboratorio de Genética Molecular — Página {page_num}")
        
        col = pos % COLS
        row = pos // COLS
        x = margin_x + col * (QR_SIZE + 0.5*inch)
        y = height - margin_top - (row + 1) * (QR_SIZE + 0.7*inch)
        
        # Generar QR
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
        qr.add_data(f"{BASE_URL}{e['slug']}.html")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        c.drawImage(tmp_path, x, y + 0.4*inch, QR_SIZE, QR_SIZE)
        os.remove(tmp_path)
        
        # Etiquetas
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + QR_SIZE/2, y + 0.2*inch, e['nombre'])
        
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawCentredString(x + QR_SIZE/2, y + 0.05*inch, f"Cód: {e['codigo']}")
    
    c.save()
    pages = (len(equipos) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    print(f"PDF: {OUTPUT_PDF} ({len(equipos)} QR codes, {pages} páginas)")


# ─── Main ──────────────────────────────────────────────────────

def main():
    equipos = read_csv()
    print(f"Equipos: {len(equipos)}")
    generate_qr_pdf(equipos)


if __name__ == "__main__":
    main()
