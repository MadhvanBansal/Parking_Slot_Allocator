import sqlite3

def init_db():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS Fragmentation_Log')
    cursor.execute('DROP TABLE IF EXISTS Bookings')
    cursor.execute('DROP TABLE IF EXISTS Slots')
    cursor.execute('DROP TABLE IF EXISTS Vehicles')

    cursor.execute('''
    CREATE TABLE Slots (
        slot_id VARCHAR(10) PRIMARY KEY,
        size INT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'free',
        position INT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE Vehicles (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number VARCHAR(20) NOT NULL UNIQUE,
        size_needed INT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE Bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INT NOT NULL,
        slot_id VARCHAR(10) NOT NULL,
        strategy_used VARCHAR(20) NOT NULL,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME NULL
    )
    ''')

    # Insert 30 initial slots to match the frontend UI perfectly
    # Zone A (Size 1) - Bikes
    for i in range(1, 11):
        cursor.execute("INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)", (f'A{i}', 1, i))
    
    # Zone B (Size 2) - Cars
    for i in range(1, 11):
        cursor.execute("INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)", (f'B{i}', 2, i))
        
    # Zone C (Size 3) - SUVs
    for i in range(1, 11):
        cursor.execute("INSERT INTO Slots (slot_id, size, position) VALUES (?, ?, ?)", (f'C{i}', 3, i))

    conn.commit()
    conn.close()
    print("Database initialized successfully with 30 parking slots mapped to A1 <-> C10")

if __name__ == '__main__':
    init_db()
