"use strict";

async function update() {
    const status = document.getElementById("status");
    const formatter = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "medium",
    });


    try {
        const res = await fetch("/api", {
            cache: "no-store",
        });

        const data = await res.json();

        temperature.textContent = `${data.temperature.toFixed(1)} °C`;
        humidity.textContent = `${data.humidity.toFixed(1)} %`;

        const remote = new Date(data.timestamp * 1000);
        remoteTime.textContent = formatter.format(remote);

        status.textContent = "● 已连接";
        status.className = "ok";
    } catch (err) {
        console.error(err);

        status.textContent = "● 离线";
        status.className = "bad";
    }

    localTime.textContent = formatter.format(new Date());
}

update();
setInterval(update, 1000);