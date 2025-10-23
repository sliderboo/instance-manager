document.getElementById('logout_button').addEventListener("click", async function () {
    let r = await fetch("/api/auth/logout").then(res => res.json());
    if (r.code === 200) {
        // Clear stored token on logout
        localStorage.removeItem('authToken');
        window.location.href = "/";
    }
});

// Helper function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    if (token) {
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    return {
        'Content-Type': 'application/json'
    };
}

let buttonTypes = ['start', 'leave', 'join'];

for (let buttonType of buttonTypes) {
    let buttons = document.getElementsByClassName(`${buttonType}_button`);
    if (buttons) {
        for (let button of buttons) {
            button.addEventListener("click", async function (e) {
                button.disabled = true;
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    Loading...
                `;
                let buttonId = e.target.id;
                chall_id = buttonId.split('_')[2];
                let r = await fetch(`/api/challenge/${buttonType}`, {
                    "method": "POST",
                    "headers": getAuthHeaders(),
                    "body": JSON.stringify({
                        "challenge_id": chall_id
                    })
                }).then(res => res.json());
                let success = true;
                await new Promise(r => setTimeout(r, 2000));
                if (r?.code === 200) {
                    if (buttonType === 'start') {
                        if (buttonType === "start") {
                            success = r?.data;
                        }
                        if (!success) {
                            success = await waitForServer(chall_id, 'running');
                        }
                    }
                }
                if (!success) {
                    displayAlert();
                    button.disabled = false;
                    button.textContent = button.classList.contains('join_button') ? 'Join' : button.classList.contains('start_button') ? 'Start' : button.classList.contains('leave_button') ? 'Leave' : 'Reset';
                } else {
                    window.location.reload();
                }
            });
        }
    }
}

connectButtons = document.getElementsByClassName('connect_button');
for (let button of connectButtons) {
    button.addEventListener("click", async function (e) {
        window.location.href = "/challenge/" + e.target.id.split('_')[2];
    });
}

function displayAlert() {
    document.getElementById('alert-banner').classList.remove('d-none');
    document.getElementById('alert-banner').classList.add('show');
}
function hideAlert() {
    const alertBanner = document.getElementById('alert-banner');
    alertBanner.classList.add('d-none');
    alertBanner.classList.remove('show');
}

async function waitForServer(chall_id, stop_status) {
    await new Promise(r => setTimeout(r, 2000));
    let r = await fetch(`/api/challenge/${chall_id}/status`, {
        headers: getAuthHeaders()
    }).then(res => res.json());
    if (r?.code === 200) {
        if (r?.data === stop_status) {
            return true;
        }
        if (r?.data === 'stopped' || r?.data === 'pulling') {
            return false;
        }
    }
    return await waitForServer(chall_id, stop_status);
}