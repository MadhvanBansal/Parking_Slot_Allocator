import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier

DATASET_PATH = 'parking_dataset.csv'
MODEL_PATH = 'model.pkl'

FEATURE_COLUMNS = [
    'occupancy_rate',
    'vehicle_size',
    'free_exact_slots',
    'free_larger_slots',
    'split_slots_count'
]


def train_model():
    dataset = pd.read_csv(DATASET_PATH)
    features = dataset[FEATURE_COLUMNS]
    target = dataset['target_algorithm']

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.20, random_state=42
    )

    model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    train_accuracy = model.score(x_train, y_train)
    test_accuracy = model.score(x_test, y_test)
    print(f"Training accuracy: {train_accuracy * 100:.1f}%")
    print(f"Testing accuracy:  {test_accuracy * 100:.1f}%")

    with open(MODEL_PATH, 'wb') as file:
        pickle.dump(model, file)

    print(f"Saved Gradient Boosting -> {MODEL_PATH}")


if __name__ == '__main__':
    train_model()
