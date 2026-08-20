#!/bin/bash
# update.sh — Script maestro de actualización del sitio de inventario
# Uso: ./update.sh

set -e

echo "=== Inventario de Equipos — Actualización ==="
echo ""

cd "$(dirname "$0")"

echo "1/4 Extrayendo instructivos del PDF del profesor..."
python3 extract_instructivos.py
echo ""

echo "2/4 Generando PDFs de instructivos..."
python3 generate_instructivo_pdfs.py
echo ""

echo "3/4 Generando páginas HTML..."
python3 generate.py
echo ""

echo "4/4 Generando QR codes..."
python3 generate_qr.py
echo ""

echo "=== Listo ==="
echo ""
echo "Resumen:"
echo "  - $(ls equipos/*.html | wc -l) páginas de equipos"
echo "  - $(ls instructivos_pdf/*.pdf | wc -l) instructivos PDF"
echo "  - $(ls pdfs/*.pdf | wc -l) manuales PDF"
echo "  - qr-equipos.pdf actualizado"
echo ""
echo "Para previsualizar: python3 -m http.server 8000"
echo "Para desplegar: git add . && git commit -m 'update' && git push"
