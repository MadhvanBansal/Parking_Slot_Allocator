import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from buddy import BAYS, free_blocks, part_label, pick_block
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
            total_bays = BAYS[slot['size']]

            cursor.execute(
                """
                SELECT part_start, part_size FROM Bookings
                WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL
                """,
                (slot_id,)
            )
            active_bookings = cursor.fetchall()
            occupied_parts = [
                (row['part_start'], row['part_size'])
                for row in active_bookings
            ]

            parts = [
                {
                    "label": part_label(slot_id, start, size),
                    "occupied": True
                }
                for start, size in occupied_parts
            ]

            for start, size in free_blocks(total_bays, occupied_parts):
                parts.append({
                    "label": part_label(slot_id, start, size),
                    "occupied": False
                })

            parts.sort(key=lambda item: item['label'])
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
    Best-Fit: Minimizes wasted space (tightest fit first).
    1. Reuses existing split slot if it has an exact or suitable free block.
    2. Uses exact-size whole slot if available (waste = 0).
    3. If no exact slot exists, splits the smallest available larger slot (Buddy System).
    4. Fallback: smallest whole slot >= vehicle_size.
    """
    # 1. Check existing split slots for an exact or smallest fitting block
    cursor.execute(
        """
        SELECT slot_id, size, position FROM Slots
        WHERE status = 'split' AND size >= ?
        ORDER BY position ASC
        """,
        (vehicle_size,)
    )
    best_split = None
    for slot in cursor.fetchall():
        cursor.execute(
            """
            SELECT part_start, part_size FROM Bookings
            WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL
            """,
            (slot['slot_id'],)
        )
        occupied = [(row['part_start'], row['part_size']) for row in cursor.fetchall()]
        block = pick_block(BAYS[slot['size']], occupied, vehicle_size)
        if block:
            cand = (block[1], slot['position'], slot['slot_id'], slot['size'], block[0])
            if best_split is None or cand < best_split:
                best_split = cand

    # 2. Check exact-size whole slot (waste = 0)
    cursor.execute(
        """
        SELECT slot_id, size, position FROM Slots
        WHERE status = 'free' AND size = ?
        ORDER BY position ASC
        LIMIT 1
        """,
        (vehicle_size,)
    )
    exact_whole = cursor.fetchone()

    # If both exact whole slot and exact split block exist, pick earlier position
    if best_split and exact_whole:
        if best_split[0] == BAYS[vehicle_size]:
            if best_split[1] <= exact_whole['position']:
                return {"is_split": True, "slot_id": best_split[2], "size": best_split[3], "start": best_split[4]}
            else:
                return {"is_split": False, "slot_id": exact_whole['slot_id'], "size": exact_whole['size']}

    if exact_whole:
        return {"is_split": False, "slot_id": exact_whole['slot_id'], "size": exact_whole['size']}

    if best_split:
        return {"is_split": True, "slot_id": best_split[2], "size": best_split[3], "start": best_split[4]}

    # 3. No exact slot free: split the smallest available larger slot (Buddy System)
    if vehicle_size in (1, 2):
        cursor.execute(
            """
            SELECT slot_id, size FROM Slots
            WHERE status = 'free' AND size > ?
            ORDER BY size ASC, position ASC
            """,
            (vehicle_size,)
        )
        for slot in cursor.fetchall():
            cursor.execute(
                """
                SELECT part_start, part_size FROM Bookings
                WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL
                """,
                (slot['slot_id'],)
            )
            occupied = [(row['part_start'], row['part_size']) for row in cursor.fetchall()]
            block = pick_block(BAYS[slot['size']], occupied, vehicle_size)
            if block:
                return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": block[0]}

    # 4. Fallback: smallest available whole slot
    cursor.execute(
        """
        SELECT slot_id, size FROM Slots
        WHERE status = 'free' AND size >= ?
        ORDER BY size ASC, position ASC
        LIMIT 1
        """,
        (vehicle_size,)
    )
    fallback = cursor.fetchone()
    if fallback:
        return {"is_split": False, "slot_id": fallback['slot_id'], "size": fallback['size']}

    return None


def allocate_first_fit(cursor, vehicle_size):
    """
    First-Fit: Scans strictly in entrance position order (positions 1-30).
    Allocates the very first available slot or split part that can fit the vehicle.
    """
    cursor.execute("SELECT 1 FROM Slots WHERE status = 'free' AND size = ? LIMIT 1", (vehicle_size,))
    has_exact_whole = cursor.fetchone() is not None

    cursor.execute(
        """
        SELECT slot_id, size, status, position FROM Slots
        WHERE status IN ('free', 'split')
        ORDER BY position ASC
        """
    )
    for slot in cursor.fetchall():
        if slot['status'] == 'split':
            cursor.execute(
                """
                SELECT part_start, part_size FROM Bookings
                WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL
                """,
                (slot['slot_id'],)
            )
            occupied = [(row['part_start'], row['part_size']) for row in cursor.fetchall()]
            block = pick_block(BAYS[slot['size']], occupied, vehicle_size)
            if block:
                return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": block[0]}

        elif slot['status'] == 'free':
            if slot['size'] >= vehicle_size:
                # If slot is larger and no exact slots exist, split it under Buddy System
                if slot['size'] > vehicle_size and not has_exact_whole and vehicle_size in (1, 2):
                    return {"is_split": True, "slot_id": slot['slot_id'], "size": slot['size'], "start": 0}
                # Otherwise, take the whole slot immediately (First Open!)
                return {"is_split": False, "slot_id": slot['slot_id'], "size": slot['size']}

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
        existing_booking = cursor.fetchone()
        if existing_booking:
            return jsonify({
                "success": False,
                "message": f"Vehicle is already parked in slot {existing_booking['slot_id']}"
            }), 400

        # Resolve algorithm
        if algorithm_selection == 'ML Model':
            cursor.execute("SELECT COUNT(*) AS count FROM Slots")
            total_slots = cursor.fetchone()['count'] or 30

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'occupied'")
            occupied_count = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'split'")
            split_count = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'free' AND size = ?", (vehicle_size,))
            free_exact = cursor.fetchone()['count'] or 0

            cursor.execute("SELECT COUNT(*) AS count FROM Slots WHERE status = 'free' AND size > ?", (vehicle_size,))
            free_larger = cursor.fetchone()['count'] or 0

            occupancy_rate = (occupied_count + split_count) / max(total_slots, 1)
            chosen_algorithm = predict(occupancy_rate, vehicle_size, free_exact, free_larger, split_count)
        else:
            chosen_algorithm = algorithm_selection

        # Allocate slot based on algorithm
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
            cursor.execute("UPDATE Slots SET status = 'split' WHERE slot_id = ?", (base_slot_id,))
            cursor.execute(
                """
                INSERT INTO Bookings (vehicle_id, slot_id, part_start, part_size, algo_used)
                VALUES (?, ?, ?, ?, ?)
                """,
                (vehicle_id, base_slot_id, allocation['start'], vehicle_size, chosen_algorithm)
            )
            connection.commit()

            assigned_label = part_label(base_slot_id, allocation['start'], vehicle_size)
            return jsonify({
                "success": True,
                "message": f"Parked in part {assigned_label} (Algo: {chosen_algorithm})",
                "slot": assigned_label,
                "algo_used": chosen_algorithm
            }), 200

        # Record standard slot booking
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
        # Handle split slot part (e.g. B1.2)
        if '.' in slot_id:
            base_slot_id, part_number_str = slot_id.split('.', 1)

            cursor.execute(
                """
                SELECT booking_id, part_start, part_size FROM Bookings
                WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL
                """,
                (base_slot_id,)
            )
            matching_booking = None
            for row in cursor.fetchall():
                calculated_number = str((row['part_start'] // row['part_size']) + 1)
                if calculated_number == part_number_str:
                    matching_booking = row
                    break

            if not matching_booking:
                return jsonify({"success": False, "message": f"Part {slot_id} is not currently occupied"}), 404

            cursor.execute(
                "UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?",
                (matching_booking['booking_id'],)
            )

            # Check if all sibling parts are now empty so the slot can merge back
            cursor.execute(
                "SELECT COUNT(*) AS active_count FROM Bookings WHERE slot_id = ? AND end_time IS NULL",
                (base_slot_id,)
            )
            has_remaining_parts = cursor.fetchone()['active_count'] > 0
            if not has_remaining_parts:
                cursor.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (base_slot_id,))

            connection.commit()
            exit_message = f"Exited {slot_id} (Slot {base_slot_id} merged back)" if not has_remaining_parts else f"Exited {slot_id}"
            return jsonify({"success": True, "message": exit_message, "merged": not has_remaining_parts}), 200

        # Handle standard whole slot
        cursor.execute(
            """
            SELECT booking_id FROM Bookings
            WHERE slot_id = ? AND end_time IS NULL AND part_start IS NULL
            """,
            (slot_id,)
        )
        active_booking = cursor.fetchone()

        if not active_booking:
            # Check if user passed a split parent slot without part suffix
            cursor.execute(
                "SELECT 1 FROM Bookings WHERE slot_id = ? AND end_time IS NULL AND part_start IS NOT NULL",
                (slot_id,)
            )
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": f"Slot {slot_id} is split into parts. Please specify part (e.g. {slot_id}.1)"
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
