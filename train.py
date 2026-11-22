import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

def train_model(dataset_path='parking_dataset.csv', model_path='model.pkl'):
    data = pd.read_csv(dataset_path)

    feature_names = [
        'occupancy_rate',
        'vehicle_size',
        'free_exact_slots',
        'free_larger_slots',
        'split_slots_count'
    ]

    features = data[feature_names]
    target = data['target_algorithm']

    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.20, random_state=42
    )

    classifier = DecisionTreeClassifier(max_depth=5, random_state=42)
    classifier.fit(x_train, y_train)

    train_accuracy = classifier.score(x_train, y_train)
    test_accuracy = classifier.score(x_test, y_test)
    print(f"Training accuracy: {train_accuracy * 100:.1f}%")
    print(f"Testing accuracy:  {test_accuracy * 100:.1f}%")

    with open(model_path, 'wb') as file:
        pickle.dump(classifier, file)

    print(f"Saved trained model to {model_path}")

if __name__ == '__main__':
    train_model()
