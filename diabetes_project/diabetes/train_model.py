import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

from pathlib import Path

"""diabetes_dataset формат файлу:
Glucose_Level - рівень глюкози
HbA1c - глікований гемоглобін
Measurement_Context - контекст заміру (0 - звичайний стан; 1 - після їжі; 2 - після ліків; 3 - після активності)
Diabetes_Type - тип діабету (1 чи 2)
Outcome - кінцевий 'діагноз'
"""

BASE_DIR = Path(__file__).resolve().parent

df = pd.read_csv(BASE_DIR / 'diabetes_dataset.csv')
X = df.drop(columns=['Outcome'])
y = df['Outcome']
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)
filename = "clf_model.pkl"
joblib.dump(model, open(filename, "wb"))
print("Success")