import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

@st.cache_resource
def train_ml_model(_conn):
    df = pd.read_sql("SELECT param1, param2, param3, ml_label FROM Defects WHERE ml_label IS NOT NULL AND ml_label != ''", _conn)
    if len(df) < 10:
        return None
    df = df.dropna()
    X = df[['param1', 'param2', 'param3']]
    y = df['ml_label']
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    return model

def rule_based_criticality(params):
    depth, length, width = params
    if depth > 12 or length > 150 or width > 6:
        return 'high'
    elif depth > 5 or length > 80 or width > 3:
        return 'medium'
    return 'normal'

def classify_criticality(model, params):
    if model is None:
        return rule_based_criticality(params), None
    try:
        pred = model.predict([params])[0]
        prob = model.predict_proba([params])[0].max()
        return pred, round(prob, 3)
    except:
        return rule_based_criticality(params), None