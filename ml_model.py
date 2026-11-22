import pickle
import pandas as pd

_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        try:
            with open('model.pkl', 'rb') as file:
                _model_cache = pickle.load(file)
        except FileNotFoundError:
            import train
            train.train_model()
            with open('model.pkl', 'rb') as file:
                _model_cache = pickle.load(file)
    return _model_cache

def predict(occupancy_rate, vehicle_size, free_exact_slots, free_larger_slots, split_slots_count):
    model = get_model()
    sample = pd.DataFrame([{
        'occupancy_rate': occupancy_rate,
        'vehicle_size': vehicle_size,
        'free_exact_slots': free_exact_slots,
        'free_larger_slots': free_larger_slots,
        'split_slots_count': split_slots_count
    }])
    return model.predict(sample)[0]
