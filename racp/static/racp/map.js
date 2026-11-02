(() => {
  const pointsElement = document.getElementById("road-map-points");
  const mapElement = document.getElementById("road-map");
  if (!pointsElement || !mapElement || !window.L) return;
  // let ptsStr = pointsElement.textContent.replace(/\bNaN\b/g, "null");

  let points = JSON.parse(pointsElement.textContent);//JSON.parse(ptsStr);
  console.log(`points = ${typeof points}`)
  console.log(points);
  if (!points.length) return;
  const center = [
    -27.454178165442357, 153.03858515277315
  ];
  const map = L.map(mapElement).setView(center, 7);
  L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);
  console.log(typeof points)
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
