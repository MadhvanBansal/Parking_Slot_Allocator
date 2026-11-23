# Buddy system: split a large slot for a small vehicle,
# merge it back when all parts are freed.

# Size meaning: 1 = Bike, 2 = Car, 3 = SUV (abstract capacity units)
VALID_SIZES = (1, 2, 3)


def can_split(slot_size, vehicle_size):
    """True when a slot is large enough to share with a smaller vehicle."""
    return slot_size > vehicle_size


def slot_label(slot_id, part_number):
    """Human label for a split part, e.g. A2.1 or B3.2"""
    return f"{slot_id}.{part_number}"


def find_free_start(slot_size, active_parts, vehicle_size):
    """
    Finds the first start position inside a split slot where a vehicle of
    vehicle_size can fit without overlapping any active booking.

    active_parts: list of (part_start, part_size) for currently parked vehicles.
    Returns a valid start integer, or None if no room.
    """
    # Build a set of all occupied positions within the slot
    occupied = set()
    for start, size in active_parts:
        for pos in range(start, start + size):
            occupied.add(pos)

    # Scan for the first contiguous run of vehicle_size free positions
    run_start = None
    run_len = 0
    for pos in range(slot_size):
        if pos not in occupied:
            if run_start is None:
                run_start = pos
            run_len += 1
            if run_len == vehicle_size:
                return run_start
        else:
            run_start = None
            run_len = 0

    return None  # no room
