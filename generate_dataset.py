import random
import csv

# Generates a realistic parking dataset with noise so the model
# actually has to learn patterns, not just memorize a hard rule.

TOTAL_SLOTS = 30
ROWS = 3000
OUTPUT_FILE = 'parking_dataset.csv'

random.seed(42)

def make_row():
    occupied = random.randint(0, TOTAL_SLOTS)
    occupancy_rate = round(occupied / TOTAL_SLOTS, 3)

    vehicle_size = random.choice([1, 2, 3, 4])
    free_exact_slots = random.randint(0, max(0, TOTAL_SLOTS - occupied))
    free_larger_slots = random.randint(0, max(0, TOTAL_SLOTS - occupied - free_exact_slots))
    split_slots_count = random.randint(0, 5)

    # Score that leans towards Best-Fit under high load, First-Fit otherwise.
    # Noise added so this isn't a perfectly learnable hard rule.
    score = (
        occupancy_rate * 3.5
        - free_exact_slots * 0.4
        + split_slots_count * 0.3
        - free_larger_slots * 0.1
    )
    noise = random.gauss(0, 0.45)

    if (score + noise) > 1.5:
        label = 'Best-Fit'
    else:
        label = 'First-Fit'

    return [occupancy_rate, vehicle_size, free_exact_slots, free_larger_slots, split_slots_count, label]


with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['occupancy_rate', 'vehicle_size', 'free_exact_slots',
                     'free_larger_slots', 'split_slots_count', 'target_algorithm'])
    for _ in range(ROWS):
        writer.writerow(make_row())

print(f"Generated {ROWS} rows -> {OUTPUT_FILE}")
