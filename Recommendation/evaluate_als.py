import os
import django

# הגדרת משתנה הסביבה עם המיקום של קובץ ההגדרות שלך
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RecommendationSystem.settings')

# הפעלת Django
django.setup()

# שאר הקוד שלך...

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

# ייבוא הנתונים מ-Django ל-Pandas DataFrame
from Recommendation.models import UserParkingRating  # ייבוא המודל מ-Django

# ייבוא הנתונים מ-Django ל-Pandas DataFrame
ratings = UserParkingRating.objects.all().values('user_id', 'parking_preference_id', 'rating')
ratings_df = pd.DataFrame(ratings)

# הכנה של הנתונים
user_ids = ratings_df['user_id'].values.reshape(-1, 1)
parking_pref_ids = ratings_df['parking_preference_id'].values.reshape(-1, 1)
ratings = ratings_df['rating'].values

# המרת מזהים ל-One-Hot Encoding
encoder = OneHotEncoder()
user_ids_encoded = encoder.fit_transform(user_ids).toarray()
parking_pref_ids_encoded = encoder.fit_transform(parking_pref_ids).toarray()

# שילוב המידע למערך קלט סופי
X = np.hstack((user_ids_encoded, parking_pref_ids_encoded))
y = ratings

# חלוקת הנתונים לסט אימון וסט אימות
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# הגדרת רשת נוירונים פשוטה באמצעות MLPRegressor
model = MLPRegressor(hidden_layer_sizes=(128, 64), activation='relu', solver='adam', max_iter=100, random_state=42)

# אימון המודל
model.fit(X_train, y_train)

# תחזיות והערכת ביצועים
y_train_pred = model.predict(X_train)
y_val_pred = model.predict(X_val)

train_loss = mean_squared_error(y_train, y_train_pred)
val_loss = mean_squared_error(y_val, y_val_pred)

print(f"Training Loss (MSE): {train_loss}")
print(f"Validation Loss (MSE): {val_loss}")

# הצגת Learning Curves (לאורך אפוכים אין תמיכה ב-MLPRegressor)
plt.plot(y_train, label='Actual')
plt.plot(y_train_pred, label='Predicted')
plt.title('Training Data vs Predictions')
plt.xlabel('Samples')
plt.ylabel('Rating')
plt.legend()
plt.show()

# בדיקת Overfitting ו-Underfitting:
if val_loss < train_loss:
    print("No Overfitting detected.")
else:
    print("Possible Overfitting detected.")

if train_loss > val_loss:
    print("Possible Underfitting detected.")
else:
    print("No Underfitting detected.")
