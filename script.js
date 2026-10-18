document.addEventListener('DOMContentLoaded', async () => {

    const parkMsg = document.getElementById('park-status');
    const exitMsg = document.getElementById('exit-status');

    // ---- Page load hone ke baad slots sync karo, aur har 3 second mein dobara ----
    await syncSlots();
    setInterval(syncSlots, 3000);

    // ---- Error message  ----
    function showError(el, msg) {
        el.textContent = msg;
        clearTimeout(el._t);
        el._t = setTimeout(() => { el.textContent = ''; }, 4000);
    }

    function clearGlow() {
        document.querySelectorAll('.slot.last-allocated')
            .forEach(el => el.classList.remove('last-allocated'));
    }

    // ---- Backend se sab slots ka status sync karo ----
    async function syncSlots() {
        try {
            const res = await fetch('http://localhost:5001/api/status');
            const data = await res.json();
            if (data.success) {
                document.querySelectorAll('.slot').forEach(el => {
                    const id = el.querySelector('.slot-id').textContent;
                    el.classList.toggle('occupied', data.occupied_slots.includes(id));
                });
            }
        } catch (e) {
            console.error('Sync nahi hua', e);
        }
    }

    await syncSlots();

    // ---- Park button dabaya ----
    document.getElementById('park_btn').addEventListener('click', async () => {
        parkMsg.textContent = '';

        const sizeStr = document.getElementById('vehicle_size').value;
        const plate = document.getElementById('plate_number').value.trim().toUpperCase();

        if (!plate) {
            showError(parkMsg, 'Plate number daalo.');
            return;
        }

        let sizeNum = 1;
        if (sizeStr === 'medium') sizeNum = 2;
        if (sizeStr === 'large') sizeNum = 3;

        try {
            const res = await fetch('http://localhost:5001/api/allocate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vehicle_size: sizeNum, plate_number: plate })
            });
            const result = await res.json();

            if (result.success) {
                await syncSlots();

                // Best-Fit wale slot pe golden glow lagao
                clearGlow();
                const picked = [...document.querySelectorAll('.slot')]
                    .find(el => el.querySelector('.slot-id').textContent === result.slot.id);
                if (picked) picked.classList.add('last-allocated');

                document.getElementById('plate_number').value = '';

            } else {
                showError(parkMsg, result.message);
            }

        } catch (e) {
            showError(parkMsg, 'Backend se connection nahi hua.');
        }
    });

    // ---- Exit button dabaya ----
    document.getElementById('exit_btn').addEventListener('click', async () => {
        exitMsg.textContent = '';

        const slot = document.getElementById('exit_slot_id').value.trim().toUpperCase();

        if (!slot) {
            showError(exitMsg, 'Slot ID daalo (e.g. A1).');
            return;
        }

        try {
            const res = await fetch('http://localhost:5001/api/exit', {
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
            showError(exitMsg, 'Backend se connection nahi hua.');
        }
    });

});
