# Smart Parking Slot Allocator

## Overview
The **Smart Parking Slot Allocator** is an interactive application that solves the everyday problem of parking management by applying core concepts from Operating Systems (OS) and Database Management Systems (DBMS). 

Instead of randomly assigning parking spots, this system treats the parking lot like a computer's memory and the arriving vehicles like programs needing memory. It uses classic memory allocation algorithms to decide the most efficient slot for a new car. At the same time, it uses database transactions to handle scenarios where multiple people try to book a spot at the exact same moment, ensuring that double-booking never happens.

## Key Features
* **Smart Allocation Strategies:** 
  * **First-Fit:** Assigns the first available slot that is large enough for the vehicle.
  * **Best-Fit:** Assigns the tightest-fitting available slot to minimize wasted space.
  * **Worst-Fit:** Assigns the largest available slot to leave a bigger remaining gap for future cars.
* **Fragmentation Tracking:** Visually tracks and calculates the empty spaces (gaps) left between parked cars, serving as a live demonstration of "external fragmentation".
* **Concurrency Control:** Safely resolves simultaneous booking requests using database transactions and locking mechanisms. This is a practical solution to the OS "critical section problem".
* **Live Analytics:** A dashboard that logs booking history and tracks space utilization over time.

## Technology Stack
* **Frontend (UI):** HTML, CSS, JavaScript (for a live visual grid of the parking lot)
* **Backend (Logic):** Python with Flask
* **Database:** SQLite (Lightweight database that perfectly handles our required transactions)

## How It Works
1. **Arrival:** A user requests a parking slot by entering their vehicle's size.
2. **Allocation:** The backend engine scans the database and picks the best slot based on the active strategy (First-Fit, Best-Fit, or Worst-Fit).
3. **Safe Booking:** The system attempts to reserve the slot using a secure database transaction. If another user grabs it first, the system safely retries.
4. **Departure:** When a car leaves, the slot is marked as free, and the system instantly recalculates the empty gaps.

## Team (Smashers, T104)
* **Bhavya Jain**
* **Madhvan Bansal**
* **Neha Sharma**
* **Himanshi Negi**

---
*(Note: Setup and installation instructions, along with the repository link, will be updated here as development progresses.)*
