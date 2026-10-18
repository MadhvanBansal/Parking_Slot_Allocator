
document.addEventListener('DOMContentLoaded', async () => {

    const parkMsg = document.getElementById('park-status');
    const exitMsg = document.getElementById('exit-status');

    const parkButton = document.getElementById('park_btn');
    const exitButton = document.getElementById('exit_btn');

    // Sync slots when page loads
    await syncSlots();
    setInterval(syncSlots, 3000);

    // Show error messages
    function showError(el, msg) {
        if (!el) return;

        el.textContent = msg;
        clearTimeout(el._t);

        el._t = setTimeout(() => {
            el.textContent = '';
        }, 4000);
    }

    function clearGlow() {
        document.querySelectorAll('.slot.last-allocated')
            .forEach(el => el.classList.remove('last-allocated'));
    }

    // Sync slot status with backend
    async function syncSlots() {
        try {
            const res = await fetch('http://localhost:5001/api/status');

            if (!res.ok) {
                throw new Error('Unable to fetch slot status');
            }

            const data = await res.json();

            if (data.success && Array.isArray(data.occupied_slots)) {
                document.querySelectorAll('.slot').forEach(el => {
                    const slotId = el.querySelector('.slot-id')?.textContent.trim();

                    el.classList.toggle(
                        'occupied',
                        data.occupied_slots.includes(slotId)
                    );
                });
            }
        } catch (e) {
            console.error('Slot sync failed:', e);
        }
    }

    // Park vehicle
    parkButton.addEventListener('click', async () => {
        if (parkButton.disabled) return;

        parkMsg.textContent = '';

        const sizeStr = document.getElementById('vehicle_size').value;
        const plate = document.getElementById('plate_number')
            .value.trim().toUpperCase();

        if (!plate) {
            showError(parkMsg, 'Plate number daalo.');
            return;
        }

        let sizeNum = 1;

        if (sizeStr === 'medium') sizeNum = 2;
        if (sizeStr === 'large') sizeNum = 3;

        parkButton.disabled = true;

        try {
            const res = await fetch('http://localhost:5001/api/allocate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vehicle_size: sizeNum,
                    plate_number: plate
                })
            });

            const result = await res.json();

            if (!res.ok || !result.success) {
                showError(parkMsg, result.message || 'Parking failed.');
                return;
            }

            await syncSlots();

            // Highlight the allocated slot
            clearGlow();

            const picked = [...document.querySelectorAll('.slot')]
                .find(el =>
                    el.querySelector('.slot-id')?.textContent.trim()
                    === String(result.slot.id)
                );

            if (picked) {
                picked.classList.add('last-allocated');
            }

            document.getElementById('plate_number').value = '';

        } catch (e) {
            showError(parkMsg, 'Backend se connection nahi hua.');
        } finally {
            parkButton.disabled = false;
        }
    });

    // Exit vehicle
    exitButton.addEventListener('click', async () => {
        if (exitButton.disabled) return;

        exitMsg.textContent = '';

        const slot = document.getElementById('exit_slot_id')
            .value.trim().toUpperCase();

        if (!slot) {
            showError(exitMsg, 'Slot ID daalo (e.g. A1).');
            return;
        }

        exitButton.disabled = true;

        try {
            const res = await fetch('http://localhost:5001/api/exit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_id: slot })
            });

            const result = await res.json();

            if (!res.ok || !result.success) {
                showError(exitMsg, result.message || 'Exit failed.');
                return;
            }

            clearGlow();
            await syncSlots();

            document.getElementById('exit_slot_id').value = '';

        } catch (e) {
            showError(exitMsg, 'Backend se connection nahi hua.');
        } finally {
            exitButton.disabled = false;
        }
    });

});
