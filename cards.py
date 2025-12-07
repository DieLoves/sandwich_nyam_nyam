import streamlit as st
import pandas as pd
from constants import COLOR_MAP, RISK_TEXT

def render_objects_cards(_conn, pipeline_filter='Все', risk_filter='Все', search_name=''):
    query = """
        SELECT o.object_id, o.object_name, o.pipeline_id, o.object_type, o.year, o.material,
               latest.date, latest.method, latest.ml_label, latest.defect_description, latest.param1
        FROM Objects o
        LEFT JOIN (
            SELECT i.object_id, i.date, i.method, d.ml_label, d.defect_description, d.param1
            FROM Inspections i
            LEFT JOIN Defects d ON i.diag_id = d.diag_id
            INNER JOIN (
                SELECT object_id, MAX(date) AS max_date FROM Inspections GROUP BY object_id
            ) lm ON i.object_id = lm.object_id AND i.date = lm.max_date
        ) latest ON o.object_id = latest.object_id
        WHERE 1=1
    """
    if pipeline_filter != 'Все': query += f" AND o.pipeline_id = '{pipeline_filter}'"
    if search_name: query += f" AND o.object_name LIKE '%{search_name}%'"

    df = pd.read_sql(query, _conn)

    if risk_filter != 'Все':
        risk_map = {'Высокий':'high', 'Средний':'medium', 'Норма':'normal'}
        df = df[df['ml_label'] == risk_map.get(risk_filter)]

    risk_order = {'high':0, 'medium':1, 'normal':2, None:3}
    df['sort'] = df['ml_label'].map(risk_order)
    df = df.sort_values('sort').drop('sort', axis=1)

    cols = st.columns(3)
    for idx, row in enumerate(df.itertuples()):
        with cols[idx % 3]:
            color = COLOR_MAP.get(row.ml_label, '#666666')
            st.markdown(f"""
            <div style="border-left:7px solid {color}; background:#1a1d24; border-radius:14px; padding:20px; box-shadow:0 6px 16px rgba(0,0,0,0.4); margin-bottom:24px; position:relative;">
                <div style="position:absolute; top:16px; right:16px;">
                    <span style="background:{color}; color:white; padding:8px 18px; border-radius:30px; font-weight:bold;">
                        {RISK_TEXT.get(row.ml_label, 'НЕТ ДАННЫХ')}
                    </span>
                </div>
                <h4 style="margin:0 0 16px 0; color:#fff;">{row.object_name}</h4>
                <p style="margin:6px 0; color:#bbb; line-height:1.5;">
                    <b>Трубопровод:</b> {row.pipeline_id}<br>
                    <b>Тип:</b> {row.object_type} ▪ <b>Год:</b> {row.year} ▪ <b>Материал:</b> {row.material}
                </p>
            """, unsafe_allow_html=True)

            if pd.notnull(row.date):
                depth = f"{row.param1:.1f} мм" if row.param1 else "—"
                st.markdown(f"<p style='color:#ccc; margin:12px 0 8px 0;'><b>Последняя инспекция:</b> {row.method} ▪ {row.date} ▪ Глубина: {depth}</p>", unsafe_allow_html=True)

            if row.defect_description:
                with st.expander(f"Комментарий: {row.defect_description[:70]}{'...' if len(row.defect_description)>70 else ''}"):
                    st.write(row.defect_description)

            with st.expander("История инспекций"):
                hist = pd.read_sql(f"""
                    SELECT i.date, i.method, d.ml_label, d.defect_description, d.quality_grade,
                           d.param1 AS depth, d.param2 AS length, d.param3 AS width
                    FROM Inspections i
                    LEFT JOIN Defects d ON i.diag_id = d.diag_id
                    WHERE i.object_id = {row.object_id}
                    ORDER BY i.date DESC
                """, _conn)
                st.dataframe(hist, hide_index=True, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)