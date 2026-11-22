"""
Buddy allocation system for parking slots.

Slots are measured in power-of-two bays:
- Bike (size 1) = 1 bay
- Car  (size 2) = 2 bays
- SUV  (size 3) = 4 bays

When small vehicles lack dedicated slots, larger slots can split in half.
When all buddy parts of a slot are freed, they coalesce back into a whole slot.
"""

# Map vehicle size to required bay count
BAYS = {
    1: 1,
    2: 2,
    3: 4
}


def free_blocks(total_bays, occupied_parts):
    """
    Finds available power-of-two blocks within a slot.
    occupied_parts is a list of (start_bay, bay_count) tuples.
    Returns a sorted list of free (start_bay, bay_count) blocks.
    """
    bay_occupied = [False] * total_bays
    for start_bay, bay_count in occupied_parts:
        for offset in range(bay_count):
            bay_index = start_bay + offset
            if bay_index < total_bays:
                bay_occupied[bay_index] = True

    available_blocks = []
    accounted_for = [False] * total_bays

    # Scan from largest power-of-two down to single bays to coalesce buddies
    block_size = total_bays
    while block_size >= 1:
        for start in range(0, total_bays, block_size):
            span = range(start, start + block_size)
            if all(not bay_occupied[b] and not accounted_for[b] for b in span):
                available_blocks.append((start, block_size))
                for b in span:
                    accounted_for[b] = True
        block_size //= 2

    return sorted(available_blocks)


def pick_block(total_bays, occupied_parts, required_bays):
    """
    Selects the smallest free block that satisfies required_bays.
    Ties are broken by lowest starting bay index.
    """
    candidates = [
        block for block in free_blocks(total_bays, occupied_parts)
        if block[1] >= required_bays
    ]
    if not candidates:
        return None

    # Sort by block size first (best fit), then by starting offset
    return min(candidates, key=lambda block: (block[1], block[0]))


def part_label(slot_id, start_bay, bay_count):
    """
    Formats a user-facing label for a split sub-slot (e.g. B1.1, B1.2).
    """
    part_number = (start_bay // bay_count) + 1
    return f"{slot_id}.{part_number}"
