import os
import time
import datetime
from io import BytesIO
import pandas as pd
import folium
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from utils import get_font_path
from constants import PIPELINE_COORDS_POLYLINE, COLOR_MAP

def get_map_image_bytes(_conn):
    df = pd.read_sql("""
        SELECT o.lat, o.lon, latest.ml_label
        FROM Objects o 
        LEFT JOIN (
            SELECT i.object_id, d.ml_label
            FROM Inspections i LEFT JOIN Defects d ON i.diag_id = d.diag_id
            INNER JOIN (SELECT object_id, MAX(date) AS max_date FROM Inspections GROUP BY object_id) lm
            ON i.object_id = lm.object_id AND i.date = lm.max_date
        ) latest ON o.object_id = latest.object_id
    """, _conn)

    m = folium.Map(location=[47.5, 66.0], zoom_start=6, tiles="CartoDB positron")
    for pid, coords in PIPELINE_COORDS_POLYLINE.items():
        folium.PolyLine(coords, color="#0066ff", weight=10, opacity=0.8).add_to(m)

    for _, row in df.iterrows():
        if pd.isna(row.lat): continue
        color = COLOR_MAP.get(row.ml_label, '#888888')
        folium.CircleMarker([row.lat, row.lon], radius=15, color=color, weight=3, fill=True, fill_opacity=0.9).add_to(m)

    m.fit_bounds(m.get_bounds())
    tmp = "temp_map_pdf.html"
    m.save(tmp)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,1600")

    driver = webdriver.Chrome(options=options)
    driver.get(f"file://{os.path.abspath(tmp)}")
    time.sleep(5)
    png = driver.get_screenshot_as_png()
    driver.quit()
    os.remove(tmp)
    return png

def generate_pdf_report(_conn):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # шрифты
    normal = "Helvetica"
    bold = "Helvetica-Bold"
    np = get_font_path("DejaVuSans.ttf")
    bp = get_font_path("DejaVuSans-Bold.ttf")
    if np and bp:
        pdfmetrics.registerFont(TTFont("DejaVu", np))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", bp))
        normal, bold = "DejaVu", "DejaVu-Bold"

    c.setFont(bold, 28)
    c.setFillColorRGB(0, 0.4, 1)
    c.drawCentredString(w/2, h-100, "Отчёт IntegrityOS")
    c.setFont(normal, 12)
    c.setFillColorRGB(0,0,0)
    c.drawString(70, h-140, f"Дата: {datetime.datetime.now():%d.%m.%Y %H:%M}")

    top5 = pd.read_sql("""
        SELECT o.object_name, o.pipeline_id, latest.date, latest.defect_description, latest.param1
        FROM Objects o
        JOIN (
            SELECT i.object_id, i.date, d.defect_description, d.param1
            FROM Inspections i
            JOIN Defects d ON i.diag_id = d.diag_id
            INNER JOIN (
                SELECT object_id, MAX(date) AS max_date
                FROM Inspections GROUP BY object_id
            ) lm ON i.object_id = lm.object_id AND i.date = lm.max_date
            WHERE d.ml_label = 'high'
        ) latest ON o.object_id = latest.object_id
        ORDER BY latest.param1 DESC
        LIMIT 5
    """, _conn)
    c.setFont(bold, 18)
    c.drawString(70, h-180, "ТОП-5 высокого риска:")
    y = h - 210
    c.setFont(normal, 11)
    for _, r in top5.iterrows():
        text = f"• {r['object_name']} | {r['pipeline_id']} | {r['date']} | {r['defect_description'] or '—'} | {r['param1']:.1f} мм"
        c.drawString(90, y, text[:130])
        y -= 26

    c.showPage()
    c.setFont(bold, 20)
    c.drawString(70, h-80, "Карта состояния")
    img_data = get_map_image_bytes(_conn)
    if img_data:
        c.drawImage(ImageReader(BytesIO(img_data)), 50, h-780, width=500, height=620, preserveAspectRatio=True)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()