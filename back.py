from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
# Allow the frontend to communicate with this backend without CORS errors
CORS(app) 

def get_db_connection():
    conn = sqlite3.connect('parking_system.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/status', methods=['GET'])
def get_status():
    """Fetch all occupied slots to keep frontend perfectly in sync"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT slot_id FROM Slots WHERE status = 'occupied'")
        occupied_slots = [row['slot_id'] for row in cursor.fetchall()]
        return jsonify({"success": True, "occupied_slots": occupied_slots}), 200
    except sqlite3.Error as err:
        return jsonify({"success": False, "message": str(err)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/allocate', methods=['POST'])
def allocate_parking():
    data = request.json
    vehicle_size = data.get('vehicle_size')
    plate_number = data.get('plate_number')

    if not plate_number or not vehicle_size:
        return jsonify({"success": False, "message": "Missing vehicle size or license plate number"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prevent parking the same car twice if it hasn't exited
        cursor.execute('''
            SELECT b.slot_id FROM Bookings b 
            JOIN Vehicles v ON b.vehicle_id = v.vehicle_id 
            WHERE v.plate_number = ? AND b.end_time IS NULL
        ''', (plate_number,))
        existing_booking = cursor.fetchone()
        if existing_booking:
            return jsonify({"success": False, "message": f"Vehicle is already parked in slot {existing_booking['slot_id']}."}), 400

        # BEST-FIT ALGORITHM
        query = "SELECT slot_id, size FROM Slots WHERE status = 'free' AND size >= ? ORDER BY size ASC, position ASC LIMIT 1"
        cursor.execute(query, (vehicle_size,))
        best_slot = cursor.fetchone()

        if not best_slot:
            return jsonify({"success": False, "message": "No suitable parking slot available."}), 404

        slot_id = best_slot['slot_id']
        slot_size = best_slot['size']

        # UPDATE DATABASE RECORDS
        cursor.execute("SELECT vehicle_id FROM Vehicles WHERE plate_number = ?", (plate_number,))
        vehicle_record = cursor.fetchone()
        
        if vehicle_record:
            vehicle_id = vehicle_record['vehicle_id']
        else:
            cursor.execute("INSERT INTO Vehicles (plate_number, size_needed) VALUES (?, ?)", (plate_number, vehicle_size))
            vehicle_id = cursor.lastrowid

        cursor.execute("UPDATE Slots SET status = 'occupied' WHERE slot_id = ?", (slot_id,))
        cursor.execute("INSERT INTO Bookings (vehicle_id, slot_id, strategy_used) VALUES (?, ?, ?)", (vehicle_id, slot_id, 'Best-Fit'))

        conn.commit()

        return jsonify({"success": True, "message": "Vehicle parked successfully.", "slot": {"id": slot_id, "size": slot_size}}), 200

    except sqlite3.Error as err:
        return jsonify({"success": False, "message": "Database error."}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/exit', methods=['POST'])
def exit_parking():
    """Handle vehicle checkout to free up the slot"""
    data = request.json
    slot_id = data.get('slot_id')

    if not slot_id:
        return jsonify({"success": False, "message": "Missing slot ID"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find the active booking for this slot
        cursor.execute('''
            SELECT booking_id 
            FROM Bookings 
            WHERE slot_id = ? AND end_time IS NULL
        ''', (slot_id,))
        active_booking = cursor.fetchone()

        if not active_booking:
            return jsonify({"success": False, "message": f"No active parking found in slot {slot_id}."}), 404

        booking_id = active_booking['booking_id']

        # Free the slot and close the booking
        cursor.execute("UPDATE Slots SET status = 'free' WHERE slot_id = ?", (slot_id,))
        cursor.execute("UPDATE Bookings SET end_time = CURRENT_TIMESTAMP WHERE booking_id = ?", (booking_id,))

        conn.commit()
        return jsonify({"success": True, "message": "Vehicle exited successfully.", "slot_id": slot_id}), 200

    except sqlite3.Error as err:
        return jsonify({"success": False, "message": "Database error."}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
