def can_split(slot_size, vehicle_size):
    return slot_size > vehicle_size


def slot_label(slot_id, part_number):
    return f"{slot_id}.{part_number}"


def find_free_start(slot_size, active_parts, vehicle_size):
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
