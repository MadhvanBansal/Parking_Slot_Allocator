
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)


def connect():
    db = sqlite3.connect('parking_system.db')
    db.row_factory = sqlite3.Row
    return db


@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        db = connect()
        cur = db.cursor()
        cur.execute("SELECT slot_id FROM Slots WHERE status = 'occupied'")
        taken = [row['slot_id'] for row in cur.fetchall()]
        return jsonify({"success": True, "occupied_slots": taken}), 200
    except sqlite3.Error:
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


@app.route('/api/allocate', methods=['POST'])
def park_vehicle():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or missing JSON request"
        }), 400

    vsize = data.get('vehicle_size')
    plate = data.get('plate_number')

    # Validate vehicle size
    try:
        if isinstance(vsize, bool):
            raise ValueError
        vsize = int(vsize)
        if vsize not in (1, 2, 3):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Vehicle size must be 1 (Bike), 2 (Car), or 3 (SUV)"
        }), 400

    # Validate and clean number plate
    if not isinstance(plate, str) or not plate.strip():
        return jsonify({
            "success": False,
            "message": "A valid plate number is required"
        }), 400

    plate = plate.strip().upper()

    try:
        db = connect()
        cur = db.cursor()

        cur.execute('''
            SELECT b.slot_id FROM Bookings b
            JOIN Vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE v.plate_number = ? AND b.end_time IS NULL
        ''', (plate,))
        already_parked = cur.fetchone()

        if already_parked:
            return jsonify({
                "success": False,
                "message": f"Gaadi pehle se slot {already_parked['slot_id']} mein hai"
            }), 400

        cur.execute(
            "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size >= ? ORDER BY (size - ?) ASC, position ASC LIMIT 1",
            (vsize, vsize)
        )
        chosen = cur.fetchone()

        if not chosen:
            return jsonify({
                "success": False,
                "message": "Koi bhi slot available nahi hai"
            }), 404

        slot = chosen['slot_id']
        slot_size = chosen['size']

        cur.execute("SELECT vehicle_id FROM Vehicles WHERE plate_number = ?", (plate,))
        old = cur.fetchone()

        if old:
            vid = old['vehicle_id']
        else:
            cur.execute(
                "INSERT INTO Vehicles (plate_number, size_needed) VALUES (?, ?)",
                (plate, vsize)
            )
            vid = cur.lastrowid

        cur.execute("UPDATE Slots SET status = 'occupied' WHERE slot_id = ?", (slot,))
        cur.execute(
            "INSERT INTO Bookings (vehicle_id, slot_id, strategy_used) VALUES (?, ?, ?)",
            (vid, slot, 'Best-Fit')
        )

        db.commit()
        return jsonify({
            "success": True,
            "message": "Gaadi park ho gayi",
            "slot": {"id": slot, "size": slot_size}
        }), 200

    except sqlite3.Error:
        if 'db' in locals():
            db.rollback()
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


@app.route('/api/exit', methods=['POST'])
def remove_vehicle():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or missing JSON request"
        }), 400

    slot = data.get('slot_id')

    if not isinstance(slot, str) or not slot.strip():
        return jsonify({
            "success": False,
            "message": "A valid slot ID is required"
        }), 400

    slot = slot.strip().upper()

    try:
        db = connect()
        cur = db.cursor()

        cur.execute('''
            SELECT booking_id FROM Bookings
            WHERE slot_id = ? AND end_time IS NULL
        ''', (slot,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({
                "success": False,
                "message": f"Slot {slot} mein koi gaadi nahi hai"
            }), 404

        cur.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (slot,))
        cur.execute(
            "UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?",
            (booking['booking_id'],)
        )

        db.commit()
        return jsonify({
            "success": True,
            "message": "Gaadi nikal gayi",
            "slot_id": slot
        }), 200

    except sqlite3.Error:
        if 'db' in locals():
            db.rollback()
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
