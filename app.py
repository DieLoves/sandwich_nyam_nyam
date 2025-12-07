import streamlit as st
from streamlit_option_menu import option_menu
import datetime
import pandas as pd
from streamlit_folium import st_folium

from db import init_db
from ml import train_ml_model, classify_criticality, rule_based_criticality
from map import render_map
from cards import render_objects_cards
from dashboard import render_dashboard
from report import generate_pdf_report
from utils import HIDE_STREAMLIT_STYLE

st.set_page_config(page_title="IntegrityOS", layout="wide", initial_sidebar_state="expanded")
st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)

# Инициализация БД и модели (модель переобучится после импорта)
conn = init_db()
model = train_ml_model(conn)

# Стили
st.markdown("""
<style>
    [data-testid="stSidebar"] {background-color: #111111;}
    [data-testid="stSidebar"] * {color: white !important;}
    section[data-testid="stSidebar"] .block-container {padding-top: 2rem;}
    iframe[title="streamlit_option_menu.option_menu"] {background-color: transparent !important;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="text-align:left; padding: 0px 10px 40px 5px;">
        <h2 style="color:#2d8eff; margin:0; font-size: 26px; font-weight:700;">IntegrityOS</h2>
        <p style="color:#808495; margin:5px 0 0 0; font-size:14px;">Мониторинг трубопроводов</p>
    </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["Дашборд", "Импорт данных", "Карта", "Объекты", "Классификатор ИИ", "Отчёты"],
        icons=["grid-fill", "cloud-arrow-up", "map-fill", "building-fill", "cpu-fill", "file-text-fill"],
        default_index=2,
        styles={
            "container": {"padding": "0!important", "background-color": "#111111", "border-radius": "0px"},
            "icon": {"color": "#808495", "font-size": "20px"},
            "nav-link": {"font-size": "18px", "text-align": "left", "margin": "0px", "color": "#ffffff", 
                         "background-color": "#111111", "padding": "18px 20px", "border-radius": "0px"},
            "nav-link-selected": {"background-color": "#111111", "color": "#ffffff", 
                                  "border-left": "6px solid #2d8eff"},
        }
    )

pipeline_options = ['Все', 'MT-01', 'MT-02', 'MT-03', 'MT-04']

if selected == "Дашборд":
    st.title("Аналитический дашборд")
    render_dashboard(conn)

elif selected == "Карта":
    st.title("Карта текущего состояния")
    with st.expander("Фильтры", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: pipeline_f = st.selectbox("Трубопровод", pipeline_options)
        with c2: method_f = st.selectbox("Метод", ['Все', 'VIK','UZK','MFL','PVK','MPK','RGK'])
        with c3:
            date_from = st.date_input("Дата от", datetime.date(2020,1,1))
            date_to = st.date_input("Дата до", datetime.date.today())
        with c4:
            p1_min = st.number_input("Глубина от, мм", 0.0, 100.0, 0.0, 0.1)
            p1_max = st.number_input("Глубина до, мм", 0.0, 100.0, 100.0, 0.1)
            search_t = st.text_input("Поиск по дефекту/объекту")

    m = render_map(conn, pipeline_f, method_f, date_from, date_to, p1_min, p1_max, search_t)
    st_folium(m, height=800, width=None)

elif selected == "Объекты":
    st.title("Объекты контроля")
    with st.expander("Фильтры", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: pipe_f = st.selectbox("Трубопровод", pipeline_options, key="obj_pipe")
        with c2: risk_f = st.selectbox("Риск", ['Все', 'Высокий', 'Средний', 'Норма'])
        with c3: name_s = st.text_input("Поиск по названию")
    render_objects_cards(conn, pipe_f, risk_f, name_s)

elif selected == "Классификатор ИИ":
    st.title("Оценка критичности дефекта ИИ")
    st.markdown("Введите параметры дефекта и получите мгновенную оценку")
    col1, col2, col3 = st.columns(3)
    with col1: p1 = st.slider("Глубина, мм", 0.0, 50.0, 8.0, 0.1)
    with col2: p2 = st.slider("Длина, мм", 0.0, 500.0, 100.0, 1.0)
    with col3: p3 = st.slider("Ширина, мм", 0.0, 30.0, 4.0, 0.1)

    if st.button("Оценить критичность", type="primary"):
        pred, prob = classify_criticality(model, [p1, p2, p3])
        rule = rule_based_criticality([p1, p2, p3])
        prob_text = f" (уверенность {prob*100:.1f}%)" if prob else ""
        col_a, col_b = st.columns(2)
        with col_a:
            st.success(f"**ИИ-модель:** {pred.upper()}{prob_text}")
        with col_b:
            st.warning(f"**Rule-based:** {rule.upper()}")

elif selected == "Отчёты":
    st.title("Генерация PDF-отчёта")
    if st.button("Сгенерировать PDF-отчёт", type="primary"):
        with st.spinner("Генерация отчёта (карта рендерится ~15 сек)..."):
            pdf = generate_pdf_report(conn)
        st.success("Отчёт готов!")
        st.download_button(
            "📥 Скачать IntegrityOS_Отчет.pdf",
            pdf,
            file_name=f"IntegrityOS_Report_{datetime.datetime.now():%Y%m%d_%H%M}.pdf",
            mime="application/pdf"
        )

elif selected == "Импорт данных":
    st.title("🔄 Импорт данных из файлов")
    st.markdown("### Поддерживаются форматы: `.csv` и `.xlsx`")

    # ===== SESSION STATE =====
    if "import_success" not in st.session_state:
        st.session_state.import_success = False
    if "import_error" not in st.session_state:
        st.session_state.import_error = None

    col1, col2 = st.columns(2)

    with col1:
        objects_file = st.file_uploader(
            "**Objects.csv / Objects.xlsx** (обязательно)",
            type=["csv", "xlsx"],
            help="Колонки: object_id, object_name, object_type, pipeline_id, lat, lon, year, material"
        )

    with col2:
        diagnostics_file = st.file_uploader(
            "**Diagnostics.csv / Diagnostics.xlsx** (обязательно)",
            type=["csv", "xlsx"],
            help="Колонки: diag_id, object_id, method, date, temperature, humidity, illumination, defect_found, defect_description, quality_grade, param1, param2, param3, ml_label"
        )

    # ===== КНОПКА =====
    if st.button("🚀 Импортировать данные", type="primary"):
        st.session_state.import_success = False
        st.session_state.import_error = None

        if not objects_file or not diagnostics_file:
            st.session_state.import_error = "Загрузите оба файла!"
        else:
            try:
                with st.spinner("Импорт данных... Это займёт несколько секунд"):
                    # --- Чтение файлов ---
                    obj_df = (
                        pd.read_csv(objects_file)
                        if objects_file.name.endswith(".csv")
                        else pd.read_excel(objects_file)
                    )

                    diag_df = (
                        pd.read_csv(diagnostics_file)
                        if diagnostics_file.name.endswith(".csv")
                        else pd.read_excel(diagnostics_file)
                    )

                    # --- Очистка БД ---
                    with conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM Defects")
                        c.execute("DELETE FROM Inspections")
                        c.execute("DELETE FROM Objects")

                    # --- Загрузка данных ---
                    obj_df.to_sql("Objects", conn, if_exists="append", index=False)

                    if "defect_found" in diag_df.columns:
                        inspections_cols = [
                            "diag_id", "object_id", "method", "date",
                            "temperature", "humidity", "illumination"
                        ]
                        defects_cols = [
                            "diag_id", "defect_found", "defect_description",
                            "quality_grade", "param1", "param2", "param3", "ml_label"
                        ]

                        inspections_df = diag_df[inspections_cols]
                        defects_df = diag_df[defects_cols]

                        inspections_df.to_sql(
                            "Inspections", conn, if_exists="append", index=False
                        )
                        defects_df.to_sql(
                            "Defects", conn, if_exists="append", index=False
                        )
                    else:
                        diag_df.to_sql(
                            "Inspections", conn, if_exists="append", index=False
                        )

                    # --- Переобучение модели ---
                    model = train_ml_model(conn)
                    if model is None:
                        st.warning(
                            "ИИ-модель не обучена — недостаточно данных с метками"
                        )

                    # --- ФИКСИРУЕМ УСПЕХ ---
                    st.session_state.import_success = True

            except Exception as e:
                st.session_state.import_error = f"Ошибка импорта: {e}"

    # ===== СООБЩЕНИЯ (ПОСЛЕ КНОПКИ) =====
    if st.session_state.import_success:
        st.success("✅ Данные успешно импортированы!")

    if st.session_state.import_error:
        st.error(st.session_state.import_error)
        st.info("Проверьте структуру файлов и названия колонок.")
