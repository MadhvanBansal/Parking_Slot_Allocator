import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from buddy import can_split, slot_label, find_free_start
from ml_model import predict

app = Flask(__name__)
CORS(app)

DATABASE_NAME = 'parking_system.db'


def get_db():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


def get_active_parts(cursor, slot_id):
    """Returns list of (part_start, part_size) for all active bookings in a split slot."""
    cursor.execute(
        "SELECT part_start, part_size FROM Bookings WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL",
        (slot_id,)
    )
    return [(r['part_start'], r['part_size']) for r in cursor.fetchall()]


def label_for_part(slot_id, part_start, part_size):
    """
    Generates a unique label for a split part based on its start byte position.
    Part number = which vehicle_size-unit block this is (1-indexed).
    Example: slot A2 (size 3), car (size 2) at start 0 → A2.1
             bike (size 1) at start 2 → A2.3
    """
    return slot_label(slot_id, part_start + 1)


@app.route('/api/status', methods=['GET'])
def get_parking_status():
    connection = get_db()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT slot_id FROM Slots WHERE status = 'occupied'")
        occupied_slots = [row['slot_id'] for row in cursor.fetchall()]

        split_slots = {}
        cursor.execute("SELECT slot_id, size FROM Slots WHERE status = 'split'")
        for slot in cursor.fetchall():
            slot_id = slot['slot_id']
            slot_size = slot['size']

            active_parts = get_active_parts(cursor, slot_id)
            occupied_positions = set()
            for start, size in active_parts:
                for p in range(start, start + size):
                    occupied_positions.add(p)

            # Build parts list: one entry per unit position, then collapse runs
            parts = []

            # Occupied parts: one entry per active booking
            for start, size in active_parts:
                parts.append({
                    "label": label_for_part(slot_id, start, size),
                    "occupied": True
                })

            # Free ranges: find contiguous free runs in this slot
            free_start = None
            for pos in range(slot_size + 1):
                if pos < slot_size and pos not in occupied_positions:
                    if free_start is None:
                        free_start = pos
                else:
                    if free_start is not None:
                        run_size = pos - free_start
                        parts.append({
                            "label": label_for_part(slot_id, free_start, run_size),
                            "occupied": False
                        })
                        free_start = None

            parts.sort(key=lambda x: x['label'])
            split_slots[slot_id] = parts

        cursor.execute("SELECT COUNT(*) AS total FROM Slots")
        total_slots = cursor.fetchone()['total'] or 30

        return jsonify({
            "success": True,
            "occupied_slots": occupied_slots,
            "splits": split_slots,
            "stats": {
                "total": total_slots,
                "occupied": len(occupied_slots),
                "split": len(split_slots),
                "available": total_slots - len(occupied_slots) - len(split_slots)
            }
        }), 200

    except sqlite3.Error as error:
        return jsonify({"success": False, "message": str(error)}), 500
    finally:
        connection.close()


def allocate_best_fit(cursor, vehicle_size):
    """
    Best-Fit: minimize wasted space.
    1. Exact-size whole slot (zero waste).
    2. Existing split slot with a free range that fits (tightest first).
    3. Smallest larger whole slot — split it (Buddy System).
    """
    # 1. Exact whole slot
    cursor.execute(
        "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size = ? ORDER BY position ASC LIMIT 1",
        (vehicle_size,)
    )
    exact = cursor.fetchone()
    if exact:
        return {"is_split": False, "slot_id": exact['slot_id'], "size": exact['size']}

    # 2. Split slot with enough free space (tightest slot size first)
    cursor.execute(
        "SELECT slot_id, size FROM Slots WHERE status = 'split' AND size > ? ORDER BY size ASC, position ASC",
        (vehicle_size,)
    )
    for slot in cursor.fetchall():
        active_parts = get_active_parts(cursor, slot['slot_id'])
        free_start = find_free_start(slot['size'], active_parts, vehicle_size)
        if free_start is not None:
            return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": free_start}

    # 3. Smallest larger whole slot — split it
    cursor.execute(
        "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size > ? ORDER BY size ASC, position ASC LIMIT 1",
        (vehicle_size,)
    )
    larger = cursor.fetchone()
    if larger:
        return {"is_split": True, "slot_id": larger['slot_id'], "size": larger['size'], "start": 0}

    return None


def allocate_first_fit(cursor, vehicle_size):
    """
    First-Fit: scan all slots in entrance position order, take the first that fits.
    """
    cursor.execute(
        "SELECT slot_id, size, status FROM Slots WHERE status IN ('free', 'split') ORDER BY position ASC"
    )
    for slot in cursor.fetchall():
        if slot['status'] == 'free':
            if slot['size'] == vehicle_size:
                return {"is_split": False, "slot_id": slot['slot_id'], "size": slot['size']}
            if can_split(slot['size'], vehicle_size):
                # Larger free slot — split it, vehicle takes position 0
                return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": 0}

        elif slot['status'] == 'split':
            active_parts = get_active_parts(cursor, slot['slot_id'])
            free_start = find_free_start(slot['size'], active_parts, vehicle_size)
            if free_start is not None:
                return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": free_start}

    # Fallback: any free slot that fits without splitting
    cursor.execute(
        "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size >= ? ORDER BY position ASC LIMIT 1",
        (vehicle_size,)
    )
    fallback = cursor.fetchone()
    if fallback:
        return {"is_split": False, "slot_id": fallback['slot_id'], "size": fallback['size']}

    return None


@app.route('/api/allocate', methods=['POST'])
def allocate_parking_slot():
    payload = request.get_json(silent=True) or {}
    vehicle_size = payload.get('vehicle_size')
    license_plate = (payload.get('plate_number') or '').strip().upper()
    algorithm_selection = payload.get('algo', 'ML Model')

    if not license_plate or not vehicle_size or vehicle_size not in (1, 2, 3):
        return jsonify({"success": False, "message": "Valid license plate and vehicle size (1-3) are required"}), 400

    connection = get_db()
    cursor = connection.cursor()

    try:
        # Prevent double parking for the same license plate
        cursor.execute(
            """
            SELECT b.slot_id FROM Bookings b
            JOIN Vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE v.plate_number = ? AND b.end_time IS NULL
            """,
            (license_plate,)
        )
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "success": False,
                "message": f"Vehicle is already parked in slot {existing['slot_id']}"
            }), 400

        # Resolve algorithm — ML model uses full picture including free space in split slots
        if algorithm_selection == 'ML Model':
            cursor.execute("SELECT COUNT(*) AS count FROM Slots")
            total_slots = cursor.fetchone()['count'] or 30

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'occupied'")
            occupied_count = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'split'")
            split_count = cursor.fetchone()['count'] or 0

            # Count whole free slots that exactly match or are larger than vehicle
            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'free' AND size = ?", (vehicle_size,))
            free_exact = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'free' AND size > ?", (vehicle_size,))
            free_larger = cursor.fetchone()['count'] or 0

            # Also count split slots that have usable free space for this vehicle
            cursor.execute("SELECT slot_id, size FROM Slots WHERE status = 'split'")
            for slot in cursor.fetchall():
                active_parts = get_active_parts(cursor, slot['slot_id'])
                if find_free_start(slot['size'], active_parts, vehicle_size) is not None:
                    free_exact += 1  # treat usable split-slot free space as an exact match

            occupancy_rate = (occupied_count + split_count) / max(total_slots, 1)
            chosen_algorithm = predict(occupancy_rate, vehicle_size, free_exact, free_larger, split_count)
        else:
            chosen_algorithm = algorithm_selection

        # Run allocation
        if chosen_algorithm == 'First-Fit':
            allocation = allocate_first_fit(cursor, vehicle_size)
        else:
            allocation = allocate_best_fit(cursor, vehicle_size)

        if not allocation:
            return jsonify({"success": False, "message": "No suitable parking slot available"}), 404

        # Ensure vehicle record exists
        cursor.execute("SELECT vehicle_id FROM Vehicles WHERE plate_number = ?", (license_plate,))
        vehicle_record = cursor.fetchone()
        if vehicle_record:
            vehicle_id = vehicle_record['vehicle_id']
        else:
            cursor.execute(
                "INSERT INTO Vehicles (plate_number, size_needed) VALUES (?, ?)",
                (license_plate, vehicle_size)
            )
            vehicle_id = cursor.lastrowid

        # Record split part booking
        if allocation['is_split']:
            base_slot_id = allocation['slot_id']
            part_start = allocation['start']

            cursor.execute("UPDATE Slots SET status = 'split' WHERE slot_id = ?", (base_slot_id,))
            cursor.execute(
                "INSERT INTO Bookings (vehicle_id, slot_id, part_start, part_size, algo_used) VALUES (?, ?, ?, ?, ?)",
                (vehicle_id, base_slot_id, part_start, vehicle_size, chosen_algorithm)
            )
            connection.commit()

            assigned_label = label_for_part(base_slot_id, part_start, vehicle_size)
            return jsonify({
                "success": True,
                "message": f"Parked in part {assigned_label} (Algo: {chosen_algorithm})",
                "slot": assigned_label,
                "algo_used": chosen_algorithm
            }), 200

        # Record standard whole-slot booking
        allocated_slot_id = allocation['slot_id']
        cursor.execute("UPDATE Slots SET status = 'occupied' WHERE slot_id = ?", (allocated_slot_id,))
        cursor.execute(
            "INSERT INTO Bookings (vehicle_id, slot_id, algo_used) VALUES (?, ?, ?)",
            (vehicle_id, allocated_slot_id, chosen_algorithm)
        )
        connection.commit()

        return jsonify({
            "success": True,
            "message": f"Parked in slot {allocated_slot_id} (Algo: {chosen_algorithm})",
            "slot": allocated_slot_id,
            "algo_used": chosen_algorithm
        }), 200

    except sqlite3.Error as error:
        connection.rollback()
        return jsonify({"success": False, "message": f"Database error: {error}"}), 500
    finally:
        connection.close()


@app.route('/api/exit', methods=['POST'])
def exit_parking_slot():
    payload = request.get_json(silent=True) or {}
    slot_id = (payload.get('slot_id') or '').strip().upper()

    if not slot_id:
        return jsonify({"success": False, "message": "Slot ID is required"}), 400

    connection = get_db()
    cursor = connection.cursor()

    try:
        # Handle split slot part (e.g. A2.3)
        if '.' in slot_id:
            base_slot_id, part_num_str = slot_id.split('.', 1)

            # part_num = part_start + 1 (see label_for_part)
            try:
                expected_start = int(part_num_str) - 1
            except ValueError:
                return jsonify({"success": False, "message": f"Invalid part label: {slot_id}"}), 400

            cursor.execute(
                "SELECT booking_id FROM Bookings WHERE slot_id = ? AND part_start = ? AND end_time IS NULL",
                (base_slot_id, expected_start)
            )
            booking = cursor.fetchone()
            if not booking:
                return jsonify({"success": False, "message": f"Part {slot_id} is not currently occupied"}), 404

            cursor.execute(
                "UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?",
                (booking['booking_id'],)
            )

            # If no active bookings remain, the slot merges back to free
            cursor.execute(
                "SELECT COUNT(*) AS count FROM Bookings WHERE slot_id = ? AND end_time IS NULL",
                (base_slot_id,)
            )
            remaining = cursor.fetchone()['count']
            if remaining == 0:
                cursor.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (base_slot_id,))

            connection.commit()
            merged = remaining == 0
            msg = f"Exited {slot_id} (Slot {base_slot_id} merged back)" if merged else f"Exited {slot_id}"
            return jsonify({"success": True, "message": msg, "merged": merged}), 200

        # Handle standard whole slot
        cursor.execute(
            "SELECT booking_id FROM Bookings WHERE slot_id = ? AND end_time IS NULL AND part_start IS NULL",
            (slot_id,)
        )
        active_booking = cursor.fetchone()

        if not active_booking:
            cursor.execute(
                "SELECT 1 FROM Bookings WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL",
                (slot_id,)
            )
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": f"Slot {slot_id} is split. Use part label (e.g. {slot_id}.1)"
                }), 400
            return jsonify({"success": False, "message": f"Slot {slot_id} is not currently occupied"}), 404

        cursor.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (slot_id,))
        cursor.execute(
            "UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?",
            (active_booking['booking_id'],)
        )
        connection.commit()

        return jsonify({"success": True, "message": f"Vehicle exited from slot {slot_id}"}), 200

    except sqlite3.Error as error:
        connection.rollback()
        return jsonify({"success": False, "message": f"Database error: {error}"}), 500
    finally:
        connection.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
