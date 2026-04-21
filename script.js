/**
 * Cyber Command 2FA System - Resilient Production Script
 * Built with full safety checks to prevent "Blank Screen" failures.
 */

// Global Error Catcher
window.onerror = function(msg, url, line, col, error) {
    console.error("CRITICAL UI ERROR:", msg, "\nLine:", line, "\nURL:", url);
    // Don't alert the user in production, but we keep it here for debugging if needed
    return false; 
};

// Initialize only when DOM is fully loaded and ready
document.addEventListener('DOMContentLoaded', () => {
    console.log("Cyber Command UI: Initializing...");

    const API_BASE = window.location.origin;

    // 1. Safe DOM Element References
    const getEl = (id) => document.getElementById(id);
    const screens = {
        login: getEl('screen-login'),
        otp: getEl('screen-otp'),
        risk: getEl('screen-risk'),
        dashboard: getEl('dashboard'),
        authFlow: getEl('auth-flow')
    };

    // 2. Safe Icon Initialization
    const refreshIcons = () => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        } else {
            console.warn("Lucide Icons library not loaded yet.");
        }
    };
    refreshIcons();

    // 3. Navigation Logic
    function switchScreen(target) {
        const activeScreen = document.querySelector('.screen.active');
        
        if (activeScreen) {
            activeScreen.classList.add('exit');
            setTimeout(() => {
                activeScreen.classList.remove('active', 'exit');
                activeScreen.style.display = 'none';
                showTarget();
            }, 400);
        } else {
            showTarget();
        }

        function showTarget() {
            if (target === 'dashboard') {
                if (screens.authFlow) screens.authFlow.style.display = 'none';
                if (screens.dashboard) {
                    screens.dashboard.style.display = 'flex';
                    screens.dashboard.style.opacity = '0';
                    setTimeout(() => {
                        screens.dashboard.style.transition = 'opacity 0.8s ease';
                        screens.dashboard.style.opacity = '1';
                        initDashboard();
                    }, 50);
                }
            } else {
                if (screens.authFlow) screens.authFlow.style.display = 'flex';
                const targetScreen = screens[target];
                if (targetScreen) {
                    targetScreen.style.display = 'block';
                    setTimeout(() => {
                        targetScreen.classList.add('active');
                    }, 50);
                }
            }
            refreshIcons();
        }
    }

    // 4. Sidebar & View Management
    const navLinks = document.querySelectorAll('.nav-link');
    const viewSections = document.querySelectorAll('.view-section');

    function switchDashboardView(viewId) {
        viewSections.forEach(section => {
            section.style.display = 'none';
            section.classList.remove('active');
        });
        
        const targetView = getEl(`content-${viewId}`);
        if (targetView) {
            targetView.style.display = 'block';
            setTimeout(() => {
                targetView.classList.add('active');
            }, 10);
        }

        if (viewId === 'history') populateHistory();
        if (viewId === 'identity') populateIdentity();
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const text = link.innerText.trim();
            if (text === 'Sign Out') {
                e.preventDefault();
                location.reload();
                return;
            }

            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            const viewMap = {
                'Overview': 'overview',
                'Auth History': 'history',
                'Identity Pool': 'identity',
                'Security Settings': 'settings'
            };
            
            if (viewMap[text]) switchDashboardView(viewMap[text]);
        });
    });

    // 5. Auth & OTP Logic
    const loginForm = getEl('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = getEl('email')?.value;
            const password = getEl('password')?.value;
            
            try {
                const res = await fetch(`${API_BASE}/api/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                
                if (data.success) {
                    localStorage.setItem('userEmail', email);
                    switchScreen('otp');
                    startOTPTimer();
                    
                    if (data.mock_otp) {
                        const notice = getEl('demo-otp-notice');
                        const codeDisplay = getEl('demo-otp-code');
                        if (notice && codeDisplay) {
                            codeDisplay.textContent = data.mock_otp;
                            notice.style.display = 'block';
                        }
                        console.log("%c SECURITY ALERT: Your OTP for testing is " + data.mock_otp, "color: #3b82f6; font-weight: bold; font-size: 14px;");
                    }
                } else {
                    alert(data.message);
                }
            } catch (err) {
                console.error("API Error:", err);
                alert("Backend Connection Lost. Ensure server.py is running.");
            }
        });
    }

    const otpInputs = document.querySelectorAll('.otp-input');
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                otpInputs[index + 1].focus();
            }
            const otpValue = Array.from(otpInputs).map(i => i.value).join('');
            if (otpValue.length === 6) {
                verifyOTP(otpValue);
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                otpInputs[index - 1].focus();
            }
        });
    });

    async function verifyOTP(otp) {
        const email = localStorage.getItem('userEmail');
        try {
            const res = await fetch(`${API_BASE}/api/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp })
            });
            const data = await res.json();
            
            if (data.success) {
                const msg = getEl('otp-success-msg');
                if (msg) msg.style.display = 'block';
                setTimeout(() => {
                    switchScreen('dashboard');
                }, 1000);
            } else {
                alert(data.message);
                otpInputs.forEach(input => input.value = '');
                if (otpInputs[0]) otpInputs[0].focus();
            }
        } catch (err) {
            alert("Verification system failed.");
        }
    }

    // 6. Data Population
    function updateUserInfo() {
        const email = localStorage.getItem('userEmail');
        const display = getEl('user-display');
        if (display && email) {
            display.textContent = email.split('@')[0].toUpperCase();
        }
    }

    async function populateHistory() {
        const tableBody = getEl('history-table-body');
        if (!tableBody) return;
        
        // Show loading state
        tableBody.innerHTML = '<tr><td colspan="5" class="loading-text" style="text-align: center; padding: 2rem; color: var(--text-secondary);">Initializing secure link...</td></tr>';
        
        try {
            const res = await fetch(`${API_BASE}/api/dashboard-data`);
            const data = await res.json();
            
            console.log("Cyber Command: Auth History Loaded", data);
            if (data.logs && data.logs.length > 0) {
                console.table(data.logs);
                tableBody.innerHTML = data.logs.map(log => `
                    <tr>
                        <td style="font-family: monospace; color: var(--accent-blue);">${log.id}</td>
                        <td>${log.method}</td>
                        <td>${log.time}</td>
                        <td><span class="status-badge status-${log.status}">${log.status}</span></td>
                        <td>${log.loc}</td>
                    </tr>
                `).join('');
            } else {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-secondary);">No authentication logs found.</td></tr>';
            }
        } catch (err) {
            console.error("History fetch error:", err);
            tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem; color: var(--accent-red);">Failed to retrieve encrypted logs.</td></tr>';
        }
    }

    function populateIdentity() {
        const list = getEl('identity-list');
        if (!list) return;
        const identities = [
            { name: 'Admin User', role: 'Super Admin', initials: 'AU' },
            { name: 'Security Op', role: 'Monitor', initials: 'SO' },
            { name: 'Dev Lead', role: 'Access Control', initials: 'DL' },
            { name: 'External Auditor', role: 'Read Only', initials: 'EA' }
        ];
        list.innerHTML = identities.map(user => `
            <div class="user-card">
                <div class="user-avatar">${user.initials}</div>
                <h4>${user.name}</h4>
                <p>${user.role}</p>
            </div>
        `).join('');
    }

    // 7. Background & Charts
    function initDashboard() {
        console.log("Cyber Command: Dashboard Init Phase Start");
        updateUserInfo();
        initChart();
        populateEvents();
        populateHistory();
        populateIdentity();
    }

    function initChart() {
        const chartEl = getEl('activityChart');
        if (!chartEl || typeof Chart === 'undefined') return;
        
        const ctx = chartEl.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

        const labels = ['15:40:00', '15:42:00', '15:44:00', '15:46:00', '15:48:00', '15:50:00', '15:52:00'];
        const data = [850, 920, 880, 1050, 980, 1120, 1080];

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Authentication Attempts (Live)',
                    data: data,
                    borderColor: '#60a5fa',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                }
            }
        });

        setInterval(() => {
            const lastVal = chart.data.datasets[0].data[chart.data.datasets[0].data.length - 1];
            const newVal = lastVal + (Math.random() * 100 - 50);
            chart.data.labels.push(new Date().toLocaleTimeString());
            chart.data.datasets[0].data.push(Math.max(400, Math.min(1500, newVal)));
            if (chart.data.labels.length > 10) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.update('none');
        }, 3000);
    }

    function populateEvents() {
        const list = getEl('events-list');
        if (!list) return;
        const events = [
            { type: 'login', msg: 'Successful login from MacOS', time: '2 mins ago', icon: 'check-circle' },
            { type: 'alert', msg: 'New device detected', time: '1 hour ago', icon: 'alert-circle' }
        ];
        list.innerHTML = events.map(event => `
            <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem; border-radius: 8px;">
                    <i data-lucide="${event.icon}" size="16" style="color: var(--accent-blue);"></i>
                </div>
                <div>
                    <div style="font-size: 0.9rem; font-weight: 500;">${event.msg}</div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary);">${event.time}</div>
                </div>
            </div>
        `).join('');
        refreshIcons();
    }

    // 8. Digital Rain Background
    const canvas = getEl('digitalRain');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
            let width, height, columns;
            const fontSize = 16;
            const chars = "10";
            let drops = [];

            const initRain = () => {
                width = canvas.width = window.innerWidth;
                height = canvas.height = window.innerHeight;
                columns = Math.floor(width / fontSize);
                drops = Array(columns).fill(1);
            };

            const drawRain = () => {
                ctx.fillStyle = 'rgba(12, 17, 32, 0.15)';
                ctx.fillRect(0, 0, width, height);
                ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
                ctx.font = fontSize + 'px monospace';
                for (let i = 0; i < drops.length; i++) {
                    const text = chars[Math.floor(Math.random() * chars.length)];
                    ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                    if (drops[i] * fontSize > height && Math.random() > 0.975) drops[i] = 0;
                    drops[i]++;
                }
            };

            window.addEventListener('resize', initRain);
            initRain();
            setInterval(drawRain, 50);
        }
    }

    // Initial Risk Buttons & Timer hooks
    getEl('risk-approve')?.addEventListener('click', () => switchScreen('dashboard'));
    getEl('risk-block')?.addEventListener('click', () => { alert('Blocked'); location.reload(); });
    
    function startOTPTimer() {
        const display = getEl('timer-display');
        const progress = getEl('timer-progress');
        if (!display) return;
        let timeLeft = 120;
        const interval = setInterval(() => {
            timeLeft--;
            const mins = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;
            display.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            if (progress) progress.style.strokeDashoffset = 238 - (238 * (timeLeft / 120));
            if (timeLeft <= 0) clearInterval(interval);
        }, 1000);
    }
});
