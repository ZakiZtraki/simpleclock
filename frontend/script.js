const apiBase = 'http://localhost:8000';

const elements = {
    autoTimezone: document.getElementById('autoTimezone'),
    detectedTz: document.getElementById('detectedTz'),
    localInput: document.getElementById('localTimezone'),
    targetInput: document.getElementById('targetTimezone'),
    timezonesDatalist: document.getElementById('timezones'),
    timeSlider: document.getElementById('timeSlider'),
    offsetLabel: document.getElementById('offsetLabel'),
    localClock: document.getElementById('localClock'),
    targetClock: document.getElementById('targetClock'),
    localTzLabel: document.getElementById('localTzLabel'),
    targetTzLabel: document.getElementById('targetTzLabel'),
    resetBtn: document.getElementById('resetBtn'),
};

let detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
let selectedLocalTz = detectedTimezone;
let selectedTargetTz = '';

async function fetchTimezones() {
    try {
        const response = await fetch(`${apiBase}/api/timezones`);
        const data = await response.json();
        elements.timezonesDatalist.innerHTML = '';
        data.forEach((tz) => {
            const option = document.createElement('option');
            option.value = tz;
            elements.timezonesDatalist.appendChild(option);
        });
    } catch (err) {
        console.error('Failed to load timezones', err);
    }
}

function setDetectedTimezone() {
    elements.detectedTz.textContent = detectedTimezone;
    elements.localInput.value = '';
    elements.localInput.disabled = elements.autoTimezone.checked;
    selectedLocalTz = detectedTimezone;
}

function updateOffsetLabel(value) {
    const num = parseFloat(value);
    elements.offsetLabel.textContent = `${num > 0 ? '+' : ''}${num}h`;
}

async function updateLocalClock(offsetHours) {
    try {
        const response = await fetch(`${apiBase}/api/time/local`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timezone: selectedLocalTz, offset_hours: offsetHours }),
        });
        if (!response.ok) {
            throw new Error('Invalid local timezone');
        }
        const data = await response.json();
        elements.localClock.textContent = new Date(data.datetime_iso).toLocaleTimeString();
        elements.localTzLabel.textContent = data.timezone;
    } catch (err) {
        elements.localClock.textContent = 'Error fetching time';
        console.error(err);
    }
}

async function updateTargetClock(offsetHours) {
    if (!selectedTargetTz) {
        elements.targetClock.textContent = 'Choose a timezone';
        elements.targetTzLabel.textContent = '--';
        return;
    }
    try {
        const response = await fetch(`${apiBase}/api/time/convert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_timezone: selectedLocalTz,
                to_timezone: selectedTargetTz,
                offset_hours: offsetHours,
            }),
        });
        if (!response.ok) {
            throw new Error('Invalid target timezone');
        }
        const data = await response.json();
        elements.targetClock.textContent = new Date(data.datetime_iso).toLocaleTimeString();
        elements.targetTzLabel.textContent = data.timezone;
    } catch (err) {
        elements.targetClock.textContent = 'Error fetching time';
        console.error(err);
    }
}

async function updateClocks() {
    const offsetHours = parseFloat(elements.timeSlider.value);
    updateOffsetLabel(offsetHours);
    await Promise.all([updateLocalClock(offsetHours), updateTargetClock(offsetHours)]);
}

function handleAutoToggle() {
    elements.localInput.disabled = elements.autoTimezone.checked;
    if (elements.autoTimezone.checked) {
        selectedLocalTz = detectedTimezone;
    } else if (elements.localInput.value.trim()) {
        selectedLocalTz = elements.localInput.value.trim();
    }
    updateClocks();
}

function handleLocalInput() {
    if (elements.autoTimezone.checked) return;
    const value = elements.localInput.value.trim();
    if (value) {
        selectedLocalTz = value;
        elements.localTzLabel.textContent = value;
        updateClocks();
    }
}

function handleTargetInput() {
    const value = elements.targetInput.value.trim();
    if (value) {
        selectedTargetTz = value;
    } else {
        selectedTargetTz = '';
    }
    updateClocks();
}

function resetAll() {
    elements.autoTimezone.checked = true;
    setDetectedTimezone();
    elements.localInput.value = '';
    elements.targetInput.value = '';
    selectedTargetTz = '';
    elements.timeSlider.value = 0;
    updateClocks();
}

function setupEventListeners() {
    elements.autoTimezone.addEventListener('change', handleAutoToggle);
    elements.localInput.addEventListener('change', handleLocalInput);
    elements.targetInput.addEventListener('change', handleTargetInput);
    elements.timeSlider.addEventListener('input', updateClocks);
    elements.resetBtn.addEventListener('click', resetAll);
}

async function init() {
    await fetchTimezones();
    setDetectedTimezone();
    setupEventListeners();
    await updateClocks();
    setInterval(updateClocks, 1000);
}

window.addEventListener('DOMContentLoaded', init);
