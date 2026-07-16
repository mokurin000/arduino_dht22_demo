"use strict";

const STORAGE_KEY = "dht22_devices";
const API_PORT = 8888;

let devices = [];
let nextId = 1;

// ── localStorage ────────────────────────────────────────

function loadDevices() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function saveDevices() {
    const data = devices.map(d => ({ ip: d.ip, name: d.name }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

// ── Card DOM ────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function createDeviceCard(device) {
    const card = document.createElement("div");
    card.className = "device-card";
    card.id = `device-${device.id}`;

    card.innerHTML = `
        <div class="card-header">
            <span class="device-name">${escapeHtml(device.name)}</span>
            <button class="delete-btn" data-id="${device.id}" title="删除设备">✕</button>
        </div>
        <article class="kv">
            <span class="label">🌡 温度</span>
            <span class="value large temp-value">--.- °C</span>
        </article>
        <article class="kv">
            <span class="label">💧 相对湿度</span>
            <span class="value large humi-value">--.- %</span>
        </article>
        <article class="kv">
            <span class="label">⏰ 对端时间</span>
            <span class="value remote-value">--</span>
        </article>
        <footer class="status">
            <span class="device-status">● 等待数据…</span>
        </footer>
    `;

    card.querySelector(".delete-btn").addEventListener("click", () => removeDevice(device.id));

    return card;
}

function renderAllCards() {
    const grid = document.getElementById("deviceGrid");
    grid.innerHTML = "";
    devices.forEach(d => grid.appendChild(createDeviceCard(d)));
    toggleEmptyState();
}

function toggleEmptyState() {
    const empty = document.getElementById("emptyState");
    if (empty) empty.style.display = devices.length === 0 ? "block" : "none";
}

// ── Device fetch ───────────────────────────────────────

function updateDeviceCard(device, data) {
    const card = document.getElementById(`device-${device.id}`);
    if (!card) return;

    device.temperature = data.temperature;
    device.humidity = data.humidity;
    device.timestamp = data.timestamp;
    device.online = true;

    const formatter = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "medium",
    });

    card.querySelector(".temp-value").textContent = `${data.temperature.toFixed(1)} °C`;
    card.querySelector(".humi-value").textContent = `${data.humidity.toFixed(1)} %`;

    const remote = new Date(data.timestamp * 1000);
    card.querySelector(".remote-value").textContent = formatter.format(remote);

    const status = card.querySelector(".device-status");
    status.textContent = "● 已连接";
    status.className = "device-status ok";
}

function markDeviceOffline(device) {
    const card = document.getElementById(`device-${device.id}`);
    if (!card) return;

    device.online = false;

    const status = card.querySelector(".device-status");
    status.textContent = "● 离线";
    status.className = "device-status bad";
}

async function fetchDevice(device) {
    try {
        const res = await fetch(`http://${device.ip}:${API_PORT}/api`, {
            cache: "no-store",
        });
        const data = await res.json();
        updateDeviceCard(device, data);
    } catch (err) {
        console.error(`[${device.name}]`, err);
        markDeviceOffline(device);
    }
}

function startDevicePolling(device) {
    fetchDevice(device);
    device.timerId = setInterval(() => fetchDevice(device), 1000);
}

function stopDevicePolling(device) {
    if (device.timerId) {
        clearInterval(device.timerId);
        device.timerId = null;
    }
}

// ── Add / Remove ───────────────────────────────────────

function addDevice(ip, name) {
    ip = ip.trim();
    name = name.trim() || ip;

    if (!ip) return false;
    if (devices.some(d => d.ip === ip)) return false;

    const device = { id: nextId++, ip, name, online: false };
    devices.push(device);
    saveDevices();

    document.getElementById("deviceGrid").appendChild(createDeviceCard(device));
    toggleEmptyState();
    startDevicePolling(device);
    return true;
}

function removeDevice(id) {
    const idx = devices.findIndex(d => d.id === id);
    if (idx === -1) return;

    stopDevicePolling(devices[idx]);
    devices.splice(idx, 1);
    saveDevices();

    const card = document.getElementById(`device-${id}`);
    if (card) card.remove();
    toggleEmptyState();
}

// ── Local time (independent) ───────────────────────────

function startLocalTime() {
    const el = document.getElementById("localTime");
    const formatter = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "medium",
    });

    function tick() {
        el.textContent = formatter.format(new Date());
    }
    tick();
    setInterval(tick, 1000);
}

// ── Init ───────────────────────────────────────────────

function init() {
    const saved = loadDevices();
    saved.forEach(s => {
        const device = { id: nextId++, ip: s.ip, name: s.name || s.ip, online: false };
        devices.push(device);
        document.getElementById("deviceGrid").appendChild(createDeviceCard(device));
        startDevicePolling(device);
    });

    toggleEmptyState();
    startLocalTime();

    document.getElementById("addBtn").addEventListener("click", () => {
        const ipInput = document.getElementById("ipInput");
        const nameInput = document.getElementById("nameInput");
        const ip = ipInput.value.trim();
        const name = nameInput.value.trim();

        if (!ip) { ipInput.focus(); return; }

        if (addDevice(ip, name)) {
            ipInput.value = "";
            nameInput.value = "";
            ipInput.focus();
        }
    });

    document.getElementById("ipInput").addEventListener("keydown", e => {
        if (e.key === "Enter") document.getElementById("addBtn").click();
    });
    document.getElementById("nameInput").addEventListener("keydown", e => {
        if (e.key === "Enter") document.getElementById("addBtn").click();
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}