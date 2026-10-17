
import sqlite3


def init_db():
    conn = sqlite3.connect('parking_system.db')

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS Fragmentation_Log')
        cursor.execute('DROP TABLE IF EXISTS Bookings')
        cursor.execute('DROP TABLE IF EXISTS Slots')
        cursor.execute('DROP TABLE IF EXISTS Vehicles')

        cursor.execute('''
        CREATE TABLE Slots (
            slot_id VARCHAR(10) PRIMARY KEY,
            size INT NOT NULL CHECK (size IN (1, 2, 3)),
            status VARCHAR(20) NOT NULL DEFAULT 'free'
                CHECK (status IN ('free', 'occupied')),
            position INT NOT NULL
        )
        ''')

        cursor.execute('''
        CREATE TABLE Vehicles (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number VARCHAR(20) NOT NULL UNIQUE,
            size_needed INT NOT NULL CHECK (size_needed IN (1, 2, 3))
        )
        ''')

        cursor.execute('''
        CREATE TABLE Bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INT NOT NULL,
            slot_id VARCHAR(10) NOT NULL,
            strategy_used VARCHAR(20) NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME NULL,
            FOREIGN KEY (vehicle_id) REFERENCES Vehicles(vehicle_id),
            FOREIGN KEY (slot_id) REFERENCES Slots(slot_id)
        )
        ''')

        # Zone A: Bikes (size 1)
        for i in range(1, 11):
            cursor.execute(
                "INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)",
                (f'A{i}', 1, i)
            )

        # Zone B: Cars (size 2)
        for i in range(1, 11):
            cursor.execute(
                "INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)",
                (f'B{i}', 2, i)
            )

        # Zone C: SUVs / large vehicles (size 3)
        for i in range(1, 11):
            cursor.execute(
                "INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)",
                (f'C{i}', 3, i)
            )

        conn.commit()
        print("Database initialized successfully with 30 parking slots.")

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
