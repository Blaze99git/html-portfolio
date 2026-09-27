(() => {
  "use strict";

  const stations = [
    { id: "ST-01", name: "Body assembly", part: "Workpiece load", count: 226, state: "RUNNING" },
    { id: "ST-02", name: "Weld cell", part: "Weld cycle", count: 218, state: "RUNNING" },
    { id: "ST-03", name: "Surface check", part: "Quality inspection", count: 214, state: "ATTENTION" },
    { id: "ST-04", name: "Powertrain fit", part: "Torque verification", count: 210, state: "RUNNING" },
    { id: "ST-05", name: "Final test", part: "End-of-line check", count: 205, state: "RUNNING" },
    { id: "ST-06", name: "Pack-out", part: "Trace scan", count: 211, state: "IDLE" },
  ];
  const events = [
    { id: "EV-1042", minutesAgo: 1, station: "ST-03", detail: "Inspection retry threshold", state: "REVIEW", alert: true, acknowledged: false },
    { id: "EV-1041", minutesAgo: 2, station: "ST-02", detail: "Weld cycle complete", state: "NORMAL", alert: false, acknowledged: false },
    { id: "EV-1040", minutesAgo: 3, station: "ST-05", detail: "Test result recorded", state: "NORMAL", alert: false, acknowledged: false },
    { id: "EV-1039", minutesAgo: 5, station: "ST-06", detail: "Material buffer low", state: "WATCH", alert: true, acknowledged: false },
    { id: "EV-1038", minutesAgo: 7, station: "ST-01", detail: "Workpiece loaded", state: "NORMAL", alert: false, acknowledged: false },
  ];
  const minuteWindow = { value: 30 };
  let running = true;
  let completed = 1284;
  let phase = 0;

  const $ = (id) => document.getElementById(id);
  const pathFor = (values) => values.map((value, index) => {
    const x = 38 + (672 * index) / (values.length - 1);
    const y = 189 - ((value - 20) / 40) * 164;
    return `${index ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ");
  const localTime = (minutesAgo) => new Date(Date.now() - minutesAgo * 60_000)
    .toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  function renderChart() {
    const count = minuteWindow.value === 30 ? 20 : minuteWindow.value === 120 ? 32 : 42;
    const production = Array.from({ length: count }, (_, index) => {
      const drift = Math.sin((index + phase) * 0.61) * 4.2 + Math.cos((index + phase) * 0.19) * 2.4;
      const dip = (index + phase) % 17 === 0 ? -6 : 0;
      return Math.max(31, Math.min(58, 49 + drift + dip));
    });
    const path = pathFor(production);
    $("production-line").setAttribute("d", path);
    $("chart-fill").setAttribute("d", `${path} L710 189 L38 189 Z`);
    $("target-line").setAttribute("d", pathFor(Array.from({ length: count }, () => 48)));
    $("range-label").textContent = `LAST ${minuteWindow.value === 30 ? "30 MINUTES" : minuteWindow.value === 120 ? "2 HOURS" : "8 HOURS"}`;
    const labels = minuteWindow.value === 30 ? ["-30m", "-20m", "-10m", "-5m"]
      : minuteWindow.value === 120 ? ["-2h", "-90m", "-1h", "-30m"]
      : ["-8h", "-6h", "-4h", "-2h"];
    [...document.querySelectorAll(".chart-labels text")]
      .filter((label) => label.getAttribute("y") === "207")
      .slice(0, 4)
      .forEach((label, index) => { label.textContent = labels[index]; });
  }

  function renderStations() {
    $("station-list").innerHTML = stations.map((station) => {
      const dot = station.state === "ATTENTION" ? "warn" : station.state === "IDLE" ? "off" : "";
      return `<div class="flow-row"><span class="flow-dot ${dot}" aria-label="${station.state.toLowerCase()}"></span><div><div class="flow-name">${station.name}</div><div class="flow-detail">${station.id} · ${station.part}</div></div><div class="flow-count">${station.count}<small>units</small></div></div>`;
    }).join("");
  }

  function renderEvents() {
    const filter = $("event-filter").value;
    const visible = events.filter((event) => filter === "all" || event.station === filter);
    $("events-body").innerHTML = visible.length ? visible.map((event) => {
      const stationName = stations.find((station) => station.id === event.station)?.name || "Unknown station";
      const stateClass = event.alert && !event.acknowledged ? "warn" : "";
      const state = event.acknowledged ? "ACK" : event.state;
      const action = event.alert
        ? `<button class="event-ack" type="button" data-ack="${event.id}" aria-pressed="${event.acknowledged}">${event.acknowledged ? "Acknowledged" : "Acknowledge"}</button>`
        : "";
      return `<tr><td>${localTime(event.minutesAgo)}</td><td title="${stationName}">${event.station}</td><td>${event.detail}</td><td class="event-state ${stateClass}">${state} ${action}</td></tr>`;
    }).join("") : '<tr><td class="event-empty" colspan="4">No events for this station in the selected sample window.</td></tr>';

    $("events-body").querySelectorAll("[data-ack]").forEach((button) => button.addEventListener("click", () => {
      const event = events.find((item) => item.id === button.dataset.ack);
      if (!event) return;
      event.acknowledged = !event.acknowledged;
      renderEvents();
      renderAlertCount();
    }));
  }

  function renderAlertCount() {
    const count = events.filter((event) => event.alert && !event.acknowledged).length;
    $("alerts").textContent = String(count).padStart(2, "0");
    const delta = $("alert-summary");
    delta.textContent = count ? `${count} simulated alerts need review` : "All simulated alerts acknowledged";
    delta.classList.toggle("warn", count > 0);
  }

  function renderQuality() {
    $("quality-bars").innerHTML = Array.from({ length: 24 }, (_, index) => {
      const height = 36 + ((Math.sin((index + phase) * 1.7) + 1) / 2) * 54;
      return `<i style="--h:${height.toFixed(0)}%" aria-hidden="true"></i>`;
    }).join("");
  }

  function updateMetrics() {
    const availability = 87.4;
    const performance = 92.1 + Math.sin(phase / 3) * 0.5;
    const quality = 98.2 + Math.cos(phase / 4) * 0.12;
    const oee = availability * performance * quality / 10_000;
    $("units").textContent = completed.toLocaleString("en-US");
    $("oee").textContent = oee.toFixed(1);
    $("oee-components").textContent = `A ${availability.toFixed(1)} · P ${performance.toFixed(1)} · Q ${quality.toFixed(1)}`;
    $("yield").textContent = quality.toFixed(1);
  }

  function exportCsv() {
    const rows = [
      ["station_id", "station", "state", "units_completed"],
      ...stations.map((station) => [station.id, station.name, station.state, station.count]),
    ];
    const safeCell = (value) => {
      const text = String(value);
      const formulaSafe = /^[\s]*[=+@\-]/.test(text) ? `'${text}` : text;
      return `"${formulaSafe.replaceAll('"', '""')}"`;
    };
    const csv = rows.map((row) => row.map(safeCell).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "synthetic-station-summary.csv";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
  }

  document.querySelectorAll("[data-period]").forEach((button) => button.addEventListener("click", () => {
    const selected = Number(button.dataset.period);
    if (![30, 120, 480].includes(selected)) return;
    minuteWindow.value = selected;
    document.querySelectorAll("[data-period]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    renderChart();
  }));

  stations.forEach((station) => {
    const option = document.createElement("option");
    option.value = station.id;
    option.textContent = `${station.id} · ${station.name}`;
    $("event-filter").append(option);
  });
  $("event-filter").addEventListener("change", renderEvents);
  $("export-csv").addEventListener("click", exportCsv);
  $("pause-sim").addEventListener("click", (event) => {
    running = !running;
    event.currentTarget.setAttribute("aria-pressed", String(!running));
    event.currentTarget.textContent = running ? "Ⅱ Pause" : "▶ Resume";
    $("sim-state").textContent = running ? "SIMULATION RUNNING" : "SIMULATION PAUSED";
  });

  function tick() {
    if (!running) return;
    phase += 1;
    const currentStation = stations[phase % stations.length];
    currentStation.count += 1;
    if (currentStation.id === "ST-06") completed += 1;
    updateMetrics();
    renderChart();
    renderStations();
    renderEvents();
    renderQuality();
  }

  updateMetrics();
  renderChart();
  renderStations();
  renderEvents();
  renderAlertCount();
  renderQuality();
  window.setInterval(tick, 6_000);
})();
