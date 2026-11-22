import random
import pandas as pd

def generate_parking_dataset(sample_count=3000, output_path='parking_dataset.csv'):
    records = []

    for _ in range(sample_count):
        occupancy_rate = round(random.uniform(0.0, 1.0), 3)
        vehicle_size = random.choice([1, 2, 3])

        # Estimate realistic slot availability based on current lot occupancy
        estimated_free = max(1, int(30 * (1.0 - occupancy_rate)))
        free_exact_slots = random.randint(0, min(10, estimated_free))
        free_larger_slots = random.randint(0, min(15, estimated_free)) if vehicle_size < 3 else 0
        split_slots_count = random.randint(0, 5) if occupancy_rate > 0.35 else 0

        # High occupancy or missing exact slots warrants Best-Fit to prevent wasted space.
        # Otherwise, First-Fit achieves faster allocation time with zero waste penalty.
        if occupancy_rate > 0.60 or free_exact_slots == 0:
            target_algorithm = 'Best-Fit'
        else:
            target_algorithm = 'First-Fit'

        records.append({
            'occupancy_rate': occupancy_rate,
            'vehicle_size': vehicle_size,
            'free_exact_slots': free_exact_slots,
            'free_larger_slots': free_larger_slots,
            'split_slots_count': split_slots_count,
            'target_algorithm': target_algorithm
        })

    dataset = pd.DataFrame(records)
    dataset.to_csv(output_path, index=False)
    print(f"Generated {len(records)} samples in {output_path}")

if __name__ == '__main__':
    generate_parking_dataset()
