
document.addEventListener('DOMContentLoaded', async () => {
    const parkButton = document.querySelector('.park_btn');
    const exitButton = document.querySelector('.exit_btn');
    const statusText = document.querySelector('.status_display p');
    const processingText = document.querySelector('.processing_text');

    // Check that the required page elements exist.
    if (!parkButton || !exitButton || !statusText || !processingText) {
        console.error('Required parking page elements were not found.');
        return;
    }

    // Get the latest parking status from the backend.
    async function syncSlots() {
        try {
            const response = await fetch('http://localhost:5001/api/status');

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();

            if (data.success && Array.isArray(data.occupied_slots)) {
                document.querySelectorAll('.slot-id').forEach(slotSpan => {
                    const slotId = slotSpan.textContent.trim();

                    if (data.occupied_slots.includes(slotId)) {
                        slotSpan.parentElement.classList.add('occupied');
                    } else {
                        slotSpan.parentElement.classList.remove('occupied');
                    }
                });

                return true;
            }

            throw new Error('Invalid parking status response.');
        } catch (error) {
            console.error('Could not sync parking slots:', error);
            return false;
        }
    }

    // Synchronize the UI when the page loads.
    await syncSlots();

    // Handle vehicle parking.
    parkButton.addEventListener('click', async event => {
        event.preventDefault();

        const vehicleSizeString =
            document.getElementById('vehicle_size').value;
        const plateInput = document.getElementById('plate_number');
        const plateNumber = plateInput.value.trim();

        if (!plateNumber) {
            alert('Please enter a license plate number!');
            plateInput.focus();
            return;
        }

        let vehicleSizeNumber;

        if (vehicleSizeString === 'small') {
            vehicleSizeNumber = 1;
        } else if (vehicleSizeString === 'medium') {
            vehicleSizeNumber = 2;
        } else if (vehicleSizeString === 'large') {
            vehicleSizeNumber = 3;
        } else {
            alert('Please select a valid vehicle size.');
            return;
        }

        statusText.textContent = 'Status: Finding suitable slot...';
        processingText.textContent = '[ Sending request to backend... ]';
        parkButton.disabled = true;

        try {
            const response = await fetch('http://localhost:5001/api/allocate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    vehicle_size: vehicleSizeNumber,
                    plate_number: plateNumber
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                statusText.textContent =
                    `Failed: ${result.message || 'Unable to park vehicle.'}`;
                processingText.textContent = '[ Parking unsuccessful ]';
                return;
            }

            statusText.textContent = `Success: ${result.message}`;
            processingText.textContent =
                `[ Best Fit found! Slot ID: ${result.slot.id}, Size: ${result.slot.size} ]`;

            await syncSlots();
        } catch (error) {
            console.error('Parking request failed:', error);
            statusText.textContent = 'Error: Could not reach backend.';
            processingText.textContent =
                '[ Check whether the backend server is running ]';
        } finally {
            parkButton.disabled = false;
        }
    });

    // Handle vehicle exit.
    exitButton.addEventListener('click', async event => {
        event.preventDefault();

        const exitSlotInput = document.getElementById('exit_slot_id');
        const exitSlotId = exitSlotInput.value.trim().toUpperCase();

        if (!exitSlotId) {
            alert('Please enter a slot ID, for example A1.');
            exitSlotInput.focus();
            return;
        }

        statusText.textContent = 'Status: Processing vehicle exit...';
        processingText.textContent = '[ Sending request to backend... ]';
        exitButton.disabled = true;

        try {
            const response = await fetch('http://localhost:5001/api/exit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    slot_id: exitSlotId
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                statusText.textContent =
                    `Failed: ${result.message || 'Vehicle exit failed.'}`;
                processingText.textContent = '[ Exit unsuccessful ]';
                return;
            }

            statusText.textContent = `Success: ${result.message}`;
            processingText.textContent =
                `[ Slot ${result.slot_id} is now free! ]`;

            await syncSlots();
        } catch (error) {
            console.error('Vehicle exit request failed:', error);
            statusText.textContent = 'Error: Could not reach backend.';
            processingText.textContent =
                '[ Check whether the backend server is running ]';
        } finally {
            exitButton.disabled = false;
        }
    });
});
