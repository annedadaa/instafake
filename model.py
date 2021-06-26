import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
import numpy as np
import matplotlib.pyplot as plt
import math
from joblib import dump, load
from sklearn.model_selection import train_test_split
%matplotlib inline
df = pd.read_csv('dataset.csv')
df = df.sample(frac=1).reset_index(drop=True)
train, test = train_test_split(df, test_size=0.2, shuffle=True)

numerical_columns = ["profile pic", "nums/length username", "fullname words",
                     "nums/length fullname", "name==username",
                     "description length", "external URL", "private",
                     "#posts", "#followers", "#follows"]

outputs = ["fake"]
# Train model
logreg = SVC(kernel="linear", probability=True)
logreg.fit(train[numerical_columns], train[outputs])

new_pred_class = logreg.predict(test[numerical_columns])

y_true = test[outputs]
y_pred = new_pred_class

# Plot coeficients
w0 = logreg.intercept_[0]
w = w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11 = logreg.coef_[0]

feature_importance = pd.DataFrame(numerical_columns, columns=["feature"])
feature_importance["importance"] = pow(math.e, w)
feature_importance = feature_importance.sort_values(by=["importance"], ascending=False)

ax = feature_importance.plot.barh(x='feature', y='importance')
plt.show()

