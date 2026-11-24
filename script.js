/**
 * Parking Slot Allocator — Frontend Controller

 * Handles vehicle entry, exit, validation and slot updates.
 */

const API_BASE_URL = window.location.protocol.startsWith('http')
    ? ''
    : 'http://127.0.0.1:5001';

const defaultSlotContent = new Map();

// Capture original slot HTML before updating the parking layout
function captureDefaultSlotTemplates() {
    document.querySelectorAll('.slot').forEach(slotElement => {
        const slotId = slotElement.getAttribute('data-slot') ||
            slotElement.querySelector('.slot-name')?.textContent.trim();

        if (slotId) {
            defaultSlotContent.set(slotId, slotElement.innerHTML);
        }
    });
}

// Fetch parking status and update the frontend
async function fetchAndRenderSlots() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status`);
        const result = await response.json();

        if (!result.success) return;

        const occupiedSlotIds = new Set(result.occupied_slots || []);
        const splitSlotsMap = result.splits || {};

        // Update parking statistics
        if (result.stats) {
            const occupiedCounter = document.getElementById('stat_occupied');
            const availableCounter = document.getElementById('stat_available');

            if (occupiedCounter) occupiedCounter.textContent = result.stats.occupied;
            if (availableCounter) availableCounter.textContent = result.stats.available;
        }

        document.querySelectorAll('.slot').forEach(slotElement => {
            const slotId = slotElement.getAttribute('data-slot') ||
                slotElement.querySelector('.slot-name')?.textContent.trim();

            if (!slotId) return;

            if (splitSlotsMap[slotId]) {
                slotElement.classList.add('split');
                slotElement.classList.remove('occupied');

                const parts = splitSlotsMap[slotId];
                let partsHtml = '';

                parts.forEach(part => {
                    const statusClass = part.occupied ? 'occupied' : 'free';

                    partsHtml += `<div class="buddy-part ${statusClass}" data-part="${part.label}">${part.label}</div>`;
                });

                slotElement.innerHTML = partsHtml;

                // Select an occupied split slot for vehicle exit
                slotElement.querySelectorAll('.buddy-part.occupied').forEach(partElement => {
                    partElement.onclick = event => {
                        event.stopPropagation();

                        const exitInput = document.getElementById('exit_slot_id');

                        if (exitInput) {
                            exitInput.value = partElement.getAttribute('data-part');
                            exitInput.focus();
                        }
                    };
                });

            } else {
                // Restore the original slot layout
                if (slotElement.classList.contains('split')) {
                    slotElement.classList.remove('split');

                    if (defaultSlotContent.has(slotId)) {
                        slotElement.innerHTML = defaultSlotContent.get(slotId);
                    }
                }

                const isOccupied = occupiedSlotIds.has(slotId);
                slotElement.classList.toggle('occupied', isOccupied);

                // Select an occupied slot for vehicle exit
                slotElement.onclick = () => {
                    if (slotElement.classList.contains('occupied')) {
                        const exitInput = document.getElementById('exit_slot_id');

                        if (exitInput) {
                            exitInput.value = slotId;
                            exitInput.focus();
                        }
                    }
                };
            }
        });

    } catch (error) {
        console.error('Failed to sync parking status:', error);
    }
}

// Display success and error messages
function displayStatus(element, message, isSuccess) {
    if (!element) return;

    element.textContent = message;
    element.classList.toggle('success', isSuccess);

    clearTimeout(element._timeoutHandle);

    element._timeoutHandle = setTimeout(() => {
        element.textContent = '';
        element.classList.remove('success');
    }, 4500);
}

// Validate vehicle registration number
function validateLicensePlate(plate) {
    if (!plate) {
        return 'Please enter a license plate number.';
    }

    if (plate.length < 4 || plate.length > 15) {
        return 'License plate must contain 4 to 15 characters.';
    }

    if (!/^[A-Z0-9 -]+$/.test(plate)) {
        return 'License plate can only contain letters, numbers, spaces and hyphens.';
    }

    return null;
}

// Handle vehicle parking
async function handleVehicleEntry() {
    const statusElement = document.getElementById('park-status');
    const plateInput = document.getElementById('plate_number');
    const sizeSelect = document.getElementById('vehicle_size');
    const algoSelect = document.getElementById('algo_select');

    if (!plateInput || !sizeSelect || !algoSelect) return;

    const licensePlate = plateInput.value.trim().toUpperCase();
    const sizeString = sizeSelect.value;
    const selectedAlgorithm = algoSelect.value;

    // Validate license plate
    const plateError = validateLicensePlate(licensePlate);

    if (plateError) {
        displayStatus(statusElement, plateError, false);
        plateInput.focus();
        return;
    }

    // Validate vehicle size
    const vehicleSizes = {
        small: 1,
        medium: 2,
        large: 3
    };

    const vehicleSize = vehicleSizes[sizeString];

    if (!vehicleSize) {
        displayStatus(statusElement, 'Please select a valid vehicle size.', false);
        sizeSelect.focus();
        return;
    }

    displayStatus(statusElement, 'Allocating parking slot...', true);

    try {
        const response = await fetch(`${API_BASE_URL}/api/allocate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_size: vehicleSize,
                plate_number: licensePlate,
                algo: selectedAlgorithm
            })
        });

        const result = await response.json();

        if (result.success) {
            displayStatus(statusElement, result.message, true);
            plateInput.value = '';
            fetchAndRenderSlots();
        } else {
            displayStatus(statusElement, result.message, false);
        }

    } catch (error) {
        displayStatus(statusElement, 'Could not connect to the backend server.', false);
    }
}

// Handle vehicle exit
async function handleVehicleExit() {
    const statusElement = document.getElementById('exit-status');
    const exitInput = document.getElementById('exit_slot_id');

    if (!exitInput) return;

    const slotId = exitInput.value.trim().toUpperCase();

    if (!slotId) {
        displayStatus(statusElement, 'Please enter a slot ID (e.g. A1 or B1.1).', false);
        exitInput.focus();
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/exit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slot_id: slotId })
        });

        const result = await response.json();

        if (result.success) {
            displayStatus(statusElement, result.message, true);
            exitInput.value = '';
            fetchAndRenderSlots();
        } else {
            displayStatus(statusElement, result.message, false);
        }

    } catch (error) {
        displayStatus(statusElement, 'Could not connect to the backend server.', false);
    }
}

// Initialize frontend functionality
function initializeApp() {
    captureDefaultSlotTemplates();
    fetchAndRenderSlots();

    // Automatically refresh parking status every 3 seconds
    setInterval(fetchAndRenderSlots, 3000);

    // Park button and Enter key
    const parkButton = document.getElementById('park_btn');
    const plateInput = document.getElementById('plate_number');

    if (parkButton) {
        parkButton.addEventListener('click', handleVehicleEntry);
    }

    if (plateInput) {
        plateInput.addEventListener('keydown', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                handleVehicleEntry();
            }
        });
    }

    // Exit button and Enter key
    const exitButton = document.getElementById('exit_btn');
    const exitInput = document.getElementById('exit_slot_id');

    if (exitButton) {
        exitButton.addEventListener('click', handleVehicleExit);
    }

    if (exitInput) {
        exitInput.addEventListener('keydown', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                handleVehicleExit();
            }
        });
    }
}

// Start application after the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}