# Buddy system: split a large slot for a small vehicle,
# merge it back when all parts are freed.

# Valid vehicle sizes (units of space needed)
VALID_SIZES = (1, 2, 3)


def can_split(slot_size, vehicle_size):
    """A larger slot can be split to fit a smaller vehicle."""
    return slot_size > vehicle_size


def slot_label(slot_id, part_number):
    """Label for a split part, e.g. B1.1 or B1.2"""
    return f"{slot_id}.{part_number}"


def split_slot(slot_size, vehicle_size):
    """
    Returns the two parts after splitting a slot.
    Part 1 goes to the vehicle, part 2 is the leftover.
    Both parts are returned as (start, size) tuples.
    """
    return (0, vehicle_size), (vehicle_size, slot_size - vehicle_size)


def all_parts_freed(active_parts):
    """True when no parts of a split slot are still occupied."""
    return len(active_parts) == 0
