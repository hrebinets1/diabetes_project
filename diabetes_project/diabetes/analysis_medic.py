"""diabetes_dataset формат файлу:
Glucose_Level - рівень глюкози
HbA1c - гемоглобін
Measurement_Context - контекст заміру (0 - звичайний стан; 1 - після їжі; 2 - після ліків; 3 - після активності)
Diabetes_Type - тип діабету (1 чи 2)
Outcome - кінцевий 'діагноз'
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import os
from django.conf import settings
import joblib

def classification_method():
    df = pd.read_csv(os.path.join(settings.BASE_DIR, 'data', 'diabetes_dataset.csv'))
    X = df.drop(columns=['Outcome'])
    y = df['Outcome']
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    filename="diabetes/clf_model.joblib"
    joblib.dump(model, open(filename, "wb"))
    print("Success")
