import folium
import pandas as pd
from constants import PIPELINE_COORDS_POLYLINE, PIPELINE_NAMES, COLOR_MAP

def render_map(_conn, pipeline_filter='Все', method_filter='Все', date_from=None, date_to=None, p1_min=0, p1_max=100, search_term=''):
    query = """
        SELECT o.lat, o.lon, o.object_name, o.pipeline_id, latest.method, latest.date, 
               latest.ml_label, latest.param1, latest.defect_description
        FROM Objects o 
        LEFT JOIN (
            SELECT i.object_id, i.method, i.date, d.ml_label, d.param1, d.defect_description
            FROM Inspections i
            LEFT JOIN Defects d ON i.diag_id = d.diag_id
            INNER JOIN (
                SELECT object_id, MAX(date) AS max_date
                FROM Inspections GROUP BY object_id
            ) lm ON i.object_id = lm.object_id AND i.date = lm.max_date
        ) latest ON o.object_id = latest.object_id
        WHERE 1=1
    """
    if pipeline_filter != 'Все': query += f" AND o.pipeline_id = '{pipeline_filter}'"
    if method_filter != 'Все': query += f" AND latest.method = '{method_filter}'"
    if date_from: query += f" AND latest.date >= '{date_from}'"
    if date_to: query += f" AND latest.date <= '{date_to}'"
    if p1_min > 0 or p1_max < 100: query += f" AND COALESCE(latest.param1, 0) BETWEEN {p1_min} AND {p1_max}"
    if search_term: query += f" AND (latest.defect_description LIKE '%{search_term}%' OR o.object_name LIKE '%{search_term}%')"

    df = pd.read_sql(query, _conn)

    m = folium.Map(location=[47.5, 66.0], zoom_start=6, tiles="CartoDB positron")

    for pid, coords in PIPELINE_COORDS_POLYLINE.items():
        folium.PolyLine(
            coords, color="#0066ff", weight=9, opacity=0.75,
            tooltip=f"<b>{pid}</b>: {PIPELINE_NAMES.get(pid, pid)}"
        ).add_to(m)

    for _, row in df.iterrows():
        if pd.isna(row.lat): continue
        color = COLOR_MAP.get(row.ml_label, '#888888')
        status = {'high':'ВЫСОКИЙ', 'medium':'СРЕДНИЙ', 'normal':'НОРМА'}.get(row.ml_label, 'НЕТ ДАННЫХ')
        depth = f"{row.param1:.1f} мм" if pd.notnull(row.param1) and row.param1 > 0 else '—'
        desc = row.defect_description or 'Нет дефектов'
        popup = f"<b style='font-size:15px'>{row.object_name}</b><br>{row.pipeline_id}<br>{row.method or ''} ▪ {row.date or ''}<br><b style='color:{color}'>{status}</b><br>Глубина: {depth}<br>{desc}"
        folium.CircleMarker(
            location=[row.lat, row.lon], radius=15, color=color, weight=3, fill=True, fill_opacity=0.9,
            popup=folium.Popup(popup, max_width=300)
        ).add_to(m)

    return m