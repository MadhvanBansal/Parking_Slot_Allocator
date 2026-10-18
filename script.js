const API_BASE = (window.location.hostname === 'localhost')
    ? 'http://localhost:5001'
    : 'http://127.0.0.1:5001';


async function syncSlots() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();

        if (data.success) {
            const occupied = data.occupied_slots || [];
            const slots = document.querySelectorAll('.slot');

            // Update the visual state of every parking slot
            slots.forEach(el => {
                const id = el.querySelector('.slot-id').textContent;
                el.classList.toggle('occupied', occupied.includes(id));
            });

            // Calculate live parking statistics
            const total = slots.length;
            const occupiedCount = slots.filter(
                el => el.classList.contains('occupied')
            ).length;
            const availableCount = total - occupiedCount;

            // Update the dashboard counters
            document.getElementById('total-slots').textContent = total;
            document.getElementById('occupied-slots').textContent =
                occupiedCount;
            document.getElementById('available-slots').textContent =
                availableCount;
        }
    } catch (e) {
        console.error('Failed to sync slots:', e);
    }
}


function clearGlow() {
    document.querySelectorAll('.slot.last-allocated')
        .forEach(el => el.classList.remove('last-allocated'));
}

function showError(el, msg) {
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.textContent = ''; }, 4000);
}

function init() {
    const parkMsg = document.getElementById('park-status');
    const exitMsg = document.getElementById('exit-status');

    // Initial load and periodic refresh
    syncSlots();
    setInterval(syncSlots, 3000);

    // Park vehicle
    document.getElementById('park_btn').addEventListener('click', async () => {
        parkMsg.textContent = '';

        const sizeStr = document.getElementById('vehicle_size').value;
        const plate = document.getElementById('plate_number').value.trim().toUpperCase();

        if (!plate) {
            showError(parkMsg, 'Please enter license plate number.');
            return;
        }

        let sizeNum = 1;
        if (sizeStr === 'medium') sizeNum = 2;
        if (sizeStr === 'large') sizeNum = 3;

        try {
            const res = await fetch(`${API_BASE}/api/allocate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_size: sizeNum, plate_number: plate })
            });
            const result = await res.json();

            if (result.success) {
                await syncSlots();
                clearGlow();
                const picked = [...document.querySelectorAll('.slot')]
                    .find(el => el.querySelector('.slot-id').textContent === result.slot.id);
                if (picked) picked.classList.add('last-allocated');

                document.getElementById('plate_number').value = '';
            } else {
                showError(parkMsg, result.message);
            }
        } catch (e) {
            showError(parkMsg, 'Could not connect to server.');
        }
    });

    // Exit vehicle
    document.getElementById('exit_btn').addEventListener('click', async () => {
        exitMsg.textContent = '';

        const slot = document.getElementById('exit_slot_id').value.trim().toUpperCase();

        if (!slot) {
            showError(exitMsg, 'Please enter slot ID (e.g. A1).');
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/api/exit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_id: slot })
            });
            const result = await res.json();

            if (result.success) {
                clearGlow();
                await syncSlots();
                document.getElementById('exit_slot_id').value = '';
            } else {
                showError(exitMsg, result.message);
            }
        } catch (e) {
            showError(exitMsg, 'Could not connect to server.');
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
