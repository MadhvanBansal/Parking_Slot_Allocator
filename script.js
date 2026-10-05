document.addEventListener('DOMContentLoaded', async () => {
    const parkButton = document.querySelector('.park_btn');
    const exitButton = document.querySelector('.exit_btn');
    const statusText = document.querySelector('.status_display p');
    const processingText = document.querySelector('.processing_text');

    // HELPER: Sync slots from backend on load
    async function syncSlots() {
        try {
            const res = await fetch('http://localhost:5001/api/status');
            const data = await res.json();
            if (data.success) {
                document.querySelectorAll('.slot-id').forEach(slotSpan => {
                    // Turn on or off the red 'occupied' class depending on database truth
                    if (data.occupied_slots.includes(slotSpan.textContent)) {
                        slotSpan.parentElement.classList.add('occupied');
                    } else {
                        slotSpan.parentElement.classList.remove('occupied');
                    }
                });
            }
        } catch (e) {
            console.error("Could not sync slots", e);
        }
    }

    // Instantly sync the UI with the database right when the page loads!
    await syncSlots();

    parkButton.addEventListener('click', async (event) => {
        event.preventDefault(); // Stop any browser default actions
        
        const vehicleSizeString = document.getElementById('vehicle_size').value;
        const plateNumber = document.getElementById('plate_number').value;
        
        if (!plateNumber.trim()) {
            alert('Please enter a license plate number!');
            return;
        }

        let vehicleSizeNumber = 1;
        if (vehicleSizeString === 'medium') vehicleSizeNumber = 2;
        if (vehicleSizeString === 'large') vehicleSizeNumber = 3;

        statusText.textContent = "Status: Finding suitable slot...";
        processingText.textContent = "[ Sending request to backend... ]";

        try {
            const backendResponse = await fetch('http://localhost:5001/api/allocate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_size: vehicleSizeNumber, plate_number: plateNumber })
            });

            const finalResult = await backendResponse.json();

            if (finalResult.success) {
                statusText.textContent = `Success: ${finalResult.message}`;
                processingText.textContent = `[ Best Fit found! Slot ID: ${finalResult.slot.id}, Size: ${finalResult.slot.size} ]`;
                
                // Refresh all slots from backend to guarantee it updates perfectly
                await syncSlots();
            } else {
                statusText.textContent = `Failed: ${finalResult.message}`;
                processingText.textContent = `[ Error during parking ]`;
            }
        } catch (error) {
            console.error(error);
            statusText.textContent = "Error: Could not reach backend.";
        }
    });

    exitButton.addEventListener('click', async (event) => {
        event.preventDefault();
        
        const exitSlotId = document.getElementById('exit_slot_id').value.toUpperCase();
        if (!exitSlotId.trim()) {
            alert('Please enter the Slot ID you want to empty (e.g., A1)!');
            return;
        }

        statusText.textContent = "Status: Processing vehicle exit...";
        processingText.textContent = "[ Sending request to backend... ]";

        try {
            const backendResponse = await fetch('http://localhost:5001/api/exit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_id: exitSlotId })
            });

            const finalResult = await backendResponse.json();

            if (finalResult.success) {
                statusText.textContent = `Success: ${finalResult.message}`;
                processingText.textContent = `[ Slot ${finalResult.slot_id} is now free! ]`;
                
                // Sync to remove the red color automatically
                await syncSlots();
            } else {
                statusText.textContent = `Failed: ${finalResult.message}`;
                processingText.textContent = `[ Exit failed ]`;
            }
        } catch (error) {
            console.error(error);
            statusText.textContent = "Error: Could not reach backend.";
        }
    });
});
