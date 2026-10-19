from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Connect to the database
def connect():
    db = sqlite3.connect('parking_system.db')
    db.row_factory = sqlite3.Row
    return db


# Get occupied slots
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        db = connect()
        cur = db.cursor()
        cur.execute("SELECT slot_id FROM Slots WHERE status = 'occupied'")
        taken = [row['slot_id'] for row in cur.fetchall()]
        return jsonify({"success": True, "occupied_slots": taken}), 200
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if 'db' in locals():
            db.close()


# Park vehicle using Best-Fit
@app.route('/api/allocate', methods=['POST'])
def park_vehicle():
    data = request.json
    vsize = data.get('vehicle_size')
    plate = data.get('plate_number')

    if not plate or not vsize:
        return jsonify({"success": False, "message": "License plate or vehicle size is missing"}), 400

    try:
        db = connect()
        cur = db.cursor()

        # Check if vehicle is already parked
        cur.execute('''
            SELECT b.slot_id FROM Bookings b
            JOIN Vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE v.plate_number = ? AND b.end_time IS NULL
        ''', (plate,))
        already_parked = cur.fetchone()
        if already_parked:
            return jsonify({"success": False, "message": f"Vehicle is already parked in slot {already_parked['slot_id']}"}), 400

        # Best-Fit: find free slot with minimum wasted space
        cur.execute(
            "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size >= ? ORDER BY size ASC, position ASC LIMIT 1",
            (vsize,)
        )
        chosen = cur.fetchone()

        if not chosen:
            return jsonify({"success": False, "message": "No suitable slot available"}), 404

        slot = chosen['slot_id']
        slot_size = chosen['size']

        # Check or register vehicle
        cur.execute("SELECT vehicle_id FROM Vehicles WHERE plate_number = ?", (plate,))
        old = cur.fetchone()

        if old:
            vid = old['vehicle_id']
        else:
            cur.execute("INSERT INTO Vehicles (plate_number, size_needed) VALUES (?, ?)", (plate, vsize))
            vid = cur.lastrowid

        # Update slot and add booking
        cur.execute("UPDATE Slots SET status = 'occupied' WHERE slot_id = ?", (slot,))
        cur.execute("INSERT INTO Bookings (vehicle_id, slot_id) VALUES (?, ?)", (vid, slot))

        db.commit()
        return jsonify({"success": True, "message": "Vehicle parked successfully", "slot": {"id": slot, "size": slot_size}}), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


# Exit vehicle and free slot
@app.route('/api/exit', methods=['POST'])
def remove_vehicle():
    data = request.json
    slot = data.get('slot_id')

    if not slot:
        return jsonify({"success": False, "message": "Slot ID is missing"}), 400

    try:
        db = connect()
        cur = db.cursor()

        cur.execute("SELECT booking_id FROM Bookings WHERE slot_id = ? AND end_time IS NULL", (slot,))
        booking = cur.fetchone()

        if not booking:
            return jsonify({"success": False, "message": f"Slot {slot} is not currently occupied"}), 404

        cur.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (slot,))
        cur.execute("UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?", (booking['booking_id'],))

        db.commit()
        return jsonify({"success": True, "message": "Vehicle exited successfully", "slot_id": slot}), 200

    except sqlite3.Error as e:
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if 'db' in locals():
            db.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)