#!/usr/bin/env python3
import csv
import os
import re
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

CSV_PATH = "/home/sam/Downloads/Laboratorio Genetica Molecular - Inventario Equipos (Inventario) 2026-08-18_15-59.csv"
OUTPUT_DIR = "/home/sam/Projects/04_registros_equipos/inventario_equipos"
BASE_URL = "https://genetica-molecular.github.io/manual-de-equipos-de-laboratorio/equipos/"

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

def should_exclude(nombre):
    nombre_lower = nombre.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in nombre_lower:
            return True
    return False

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
                'slug': slugify(f"{nombre}-{codigo}")
            })
    return equipos

def generate_qr_pdf(equipos):
    pdf_path = os.path.join(OUTPUT_DIR, "qr-equipos.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    qr_size = 3.5 * inch
    cols = 2
    rows = 2
    margin_x = (width - cols * (qr_size + 0.5 * inch)) / 2 + 0.3 * inch
    margin_top = 1 * inch
    
    page_num = 0
    items_per_page = cols * rows
    
    for idx, e in enumerate(equipos):
        pos_on_page = idx % items_per_page
        
        if pos_on_page == 0:
            if idx > 0:
                c.showPage()
            page_num += 1
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawCentredString(width / 2, height - 0.5 * inch,
                f"Laboratorio de Genética Molecular - Página {page_num}")
        
        col = pos_on_page % cols
        row = pos_on_page // cols
        
        x = margin_x + col * (qr_size + 0.5 * inch)
        y = height - margin_top - (row + 1) * (qr_size + 0.7 * inch)
        
        url = f"{BASE_URL}{e['slug']}.html"
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_path = f"/tmp/qr_{e['slug']}.png"
        img.save(img_path)
        
        c.drawImage(img_path, x, y + 0.4 * inch, qr_size, qr_size)
        
        label = f"{e['nombre']}"
        code_label = f"Cód: {e['codigo']}"
        
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + qr_size / 2, y + 0.2 * inch, label)
        
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawCentredString(x + qr_size / 2, y + 0.05 * inch, code_label)
        
        os.remove(img_path)
    
    c.save()
    print(f"PDF generado: {pdf_path}")
    print(f"Total: {len(equipos)} QR codes en {page_num} páginas")

def main():
    equipos = read_csv()
    print(f"Equipos encontrados: {len(equipos)}")
    generate_qr_pdf(equipos)

if __name__ == "__main__":
    main()
