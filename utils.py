import os

def get_font_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path1 = os.path.join(script_dir, filename)
    if os.path.exists(path1):
        return path1
    path2 = os.path.join(os.getcwd(), filename)
    if os.path.exists(path2):
        return path2
    return None

HIDE_STREAMLIT_STYLE = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp > header {background: none;}
    section[data-testid="stSidebar"] {background-color: #0f1117;}
    [data-testid="stMetricValue"] {font-size: 28px;}
</style>
"""