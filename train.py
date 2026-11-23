import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

DATASET = 'parking_dataset.csv'
MODEL_FILE = 'model.pkl'

FEATURE_COLS = [
    'occupancy_rate',
    'vehicle_size',
    'free_exact_slots',
    'free_larger_slots',
    'split_slots_count'
]

def train_model():
    df = pd.read_csv(DATASET)
    X = df[FEATURE_COLS]
    y = df['target_algorithm']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    candidates = {
        'Decision Tree':        DecisionTreeClassifier(max_depth=5, random_state=42),
        'Logistic Regression':  LogisticRegression(max_iter=200, random_state=42),
        'Random Forest':        RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting':    GradientBoostingClassifier(n_estimators=100, random_state=42),
    }

    print(f"\n{'Algorithm':<22} {'Train Acc':>10} {'Test Acc':>10}")
    print('-' * 44)

    best_name = None
    best_acc = 0.0
    best_model = None

    for name, clf in candidates.items():
        clf.fit(X_train, y_train)
        train_acc = clf.score(X_train, y_train)
        test_acc = clf.score(X_test, y_test)
        print(f"{name:<22} {train_acc * 100:>9.1f}% {test_acc * 100:>9.1f}%")

        if test_acc > best_acc:
            best_acc = test_acc
            best_name = name
            best_model = clf

    print(f"\nBest: {best_name}  ({best_acc * 100:.1f}% test accuracy)")

    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(best_model, f)

    print(f"Saved {best_name} -> {MODEL_FILE}\n")

if __name__ == '__main__':
    train_model()
