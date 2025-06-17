import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, mean_squared_error
import numpy as np
from scipy.sparse import csr_matrix
import implicit

from RecommendationSystem.Recommendation.models import UserParkingRating, ParkingLot


# פונקציה להכנת מטריצת אינטראקציות מהנתונים
def prepare_interaction_matrix():
    interactions = UserParkingRating.objects.all().values('user_id', 'parking_preference_id', 'rating')
    df = pd.DataFrame(list(interactions))
    interaction_matrix = df.pivot_table(index='user_id', columns='parking_preference_id', values='rating', fill_value=0)
    return interaction_matrix


# פונקציה לאימון מודל ALS
def train_als_model(interaction_matrix):
    sparse_matrix = csr_matrix(interaction_matrix.values)
    model = implicit.als.AlternatingLeastSquares(factors=50, regularization=0.01, iterations=20)
    model.fit(sparse_matrix)
    return model


# פונקציה לחיזוי דירוגים
def predict_parking_lots(user_id, model, interaction_matrix):
    user_idx = interaction_matrix.index.get_loc(user_id)
    recommendations = model.recommend(user_idx, interaction_matrix, N=10)
    parking_preference_ids = [interaction_matrix.columns[i] for i in recommendations[0]]
    parking_lots = ParkingLot.objects.filter(parkingpreference__id__in=parking_preference_ids).distinct()
    return parking_lots


# פונקציה לשליפת נתוני הבדיקה מ-UserParkingRating
def get_test_data():
    test_data = {}
    ratings = UserParkingRating.objects.all()

    for rating in ratings:
        user_id = rating.user.user_id
        parking_preference_id = rating.parking_preference.id
        rating_value = rating.rating

        if user_id not in test_data:
            test_data[user_id] = {}

        test_data[user_id][parking_preference_id] = rating_value

    return test_data


# פונקציה לבדיקת דיוק המודל
def evaluate_model_performance(als_model, interaction_matrix, test_data):
    y_true = []
    y_pred = []

    for user_id, true_ratings in test_data.items():
        user_idx = interaction_matrix.index.get_loc(user_id)
        user_predictions = als_model.recommend(user_idx, interaction_matrix, N=interaction_matrix.shape[1])

        for item_id, score in user_predictions:
            y_pred.append(score)
            y_true.append(true_ratings.get(item_id, 0))

    precision = precision_score(y_true, np.round(y_pred), average='macro')
    recall = recall_score(y_true, np.round(y_pred), average='macro')
    f1 = f1_score(y_true, np.round(y_pred), average='macro')
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"RMSE: {rmse:.4f}")

    return precision, recall, f1, rmse


# שלבי תהליך הערכת המודל:

# 1. הכנת מטריצת אינטראקציות
interaction_matrix = prepare_interaction_matrix()

# 2. אימון מודל ALS
als_model = train_als_model(interaction_matrix)

# 3. שליפת נתוני הבדיקה
test_data = get_test_data()

# 4. בדיקת ביצועי המודל
precision, recall, f1, rmse = evaluate_model_performance(als_model, interaction_matrix, test_data)
