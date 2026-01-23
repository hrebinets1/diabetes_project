import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

df = pd.read_csv(BASE_DIR / 'diabetes_dataset.csv')
X = df.drop(columns=['Outcome'])
y = df['Outcome']
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)
filename = "clf_model.joblib"
joblib.dump(model, open(filename, "wb"))
print("Success")