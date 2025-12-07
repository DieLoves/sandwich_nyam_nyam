import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def render_dashboard(_conn):
    df = pd.read_sql("""SELECT i.method, d.ml_label FROM Inspections i LEFT JOIN Defects d ON i.diag_id = d.diag_id""", _conn)

    total = len(df)
    high = len(df[df.ml_label == 'high'])
    medium = len(df[df.ml_label == 'medium'])
    normal = len(df[df.ml_label == 'normal'])

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Всего инспекций", total)
    with c2: st.metric("Высокий риск", high)
    with c3: st.metric("Средний риск", medium)
    with c4: st.metric("Норма", normal)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(10,6))
        df['method'].value_counts().plot.bar(ax=ax, color='#FF6B6B')
        ax.set_title('Инспекции по методам', color='white')
        ax.tick_params(colors='white')
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(8,8))
        sizes = [high, medium, normal, total-high-medium-normal]
        labels = ['Высокий', 'Средний', 'Норма', 'Нет данных']
        colors = ['#FF4444', '#FFA500', '#44AA44', '#666666']
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, textprops={'color':'white'})
        ax.set_title('Распределение критичности', color='white')
        fig.patch.set_facecolor('#0e1117')
        st.pyplot(fig)

    st.markdown("#### ТОП-5 высокого риска")
    top5 = pd.read_sql("""
        SELECT o.object_name, o.pipeline_id, latest.date, latest.defect_description, latest.param1 AS depth
        FROM Objects o
        JOIN (
            SELECT i.object_id, i.date, d.defect_description, d.param1
            FROM Inspections i JOIN Defects d ON i.diag_id = d.diag_id
            INNER JOIN (SELECT object_id, MAX(date) AS max_date FROM Inspections GROUP BY object_id) lm
            ON i.object_id = lm.object_id AND i.date = lm.max_date
            WHERE d.ml_label = 'high'
        ) latest ON o.object_id = latest.object_id
        ORDER BY latest.param1 DESC LIMIT 5
    """, _conn)

    if not top5.empty:
        top5['depth'] = top5['depth'].round(1).astype(str) + ' мм'
        st.dataframe(top5[['object_name','pipeline_id','date','defect_description','depth']], 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Высокорисковых объектов нет")