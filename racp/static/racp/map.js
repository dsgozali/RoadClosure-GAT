function parseRoadData(text) {
  let value = text.trim();

  for (let i = 0; i < 3 && typeof value === "string"; i++) {
    value = value.replace(/\bNaN\b/g, "null");
    try {
      value = JSON.parse(value);
    } catch (e) {
      value = value
          .replace(/^"|"$/g, "")
          .replace(/\\+"/g, '"');
      value = JSON.parse(value);
    }
  }

  if (!Array.isArray(value)) {
    value = [];
  }

  return value;
}


(() => {
  const pointsElement = document.getElementById("road-map-points");
  const mapElement = document.getElementById("road-map");
  if (!pointsElement || !mapElement || !window.L) return;
  const points = parseRoadData(pointsElement.textContent);
  if (!points.length) return;
  const center = [
    -27.454178165442357, 153.03858515277315
  ];
  const map = L.map(mapElement).setView(center, 7);
  L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
    referrerPolicy: "strict-origin-when-cross-origin",
  }).addTo(map);
  points.forEach((point) => {
    const popup = document.createElement("div");
    const road = document.createElement("strong");
    road.textContent = point.road;
    popup.append(road);
    for (const [label, value] of [
      ["Weekday", point.weekdays],
      ["Saturday", point.saturday],
      ["Sunday", point.sunday],
    ]) {
      const line = document.createElement("div");
      line.textContent = `${label} ${value.toFixed(2)}`;
      popup.append(line);
    }
    L.circleMarker([point.latitude, point.longitude], {
      radius: 7,
      color: "#ffffff",
      weight: 1,
      fillColor: "#e65100",
      fillOpacity: 0.8,
    })
      .bindPopup(popup)
      .addTo(map);
  });
})();
