from sklearn.datasets import load_iris
import pandas as pd

# поки немає даних. використовую iris dataset
def classification_method(patients_dataset):
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    df.columns = [c.replace(' (cm)', '').replace(' ', '_') for c in df.columns]
    df['species'] = [iris.target_names[i] for i in iris.target]
    return df.to_dict(orient='records')