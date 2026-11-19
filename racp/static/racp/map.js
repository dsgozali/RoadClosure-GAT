$(document).ready(function() {
  $('select').selectize({
    sortField: 'text'
  });
});

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
  const roadsElement = document.getElementById("roads-map-line");
  const mapElement = document.getElementById("road-map");
  
  const tooltip = document.getElementById("road-map-tooltip");
  const previewElement = document.getElementById("road-preview-map");

  if (!pointsElement || !mapElement || !window.L || !roadsElement || !tooltip || !previewElement) return;
  
  // const title = tooltip.querySelector(".road-map-tooltip-title");
  let previewMap = null;
  let previewMarker = null;
  let currentUrl = null;
  let hideTimer = null;
  const points = parseRoadData(pointsElement.textContent);
  let roads = JSON.parse(roadsElement.textContent);
  roads = JSON.parse(roads);
  if (!points.length) return;
  const selectedRoad = mapElement.dataset.selectedRoad;
  const center = [
    -27.454178165442357, 153.03858515277315
    // points[0]["latitude"], points[0]["longitude"]
  ];
  const selectedMarkers = [];

  const map = L.map(mapElement).setView(center, 7);
  let tile = L.tileLayer(
    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
    referrerPolicy: "strict-origin-when-cross-origin",
  }).addTo(map);;

  function initializeMap() {
    if (previewMap) {
        return;
    }

    previewMap = L.map(
        previewElement,
        {
            zoomControl: false,
            attributionControl: false,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
        }
    );
    tile.addTo(previewMap);
    previewMap.on("click", () => {
        if (currentUrl) {
            window.location.href = currentUrl;
        }
    });
  }
  
  function showTooltip(trigger) {
    clearTimeout(hideTimer);
    const latitude =
        Number(trigger.dataset.lat);
    const longitude =
        Number(trigger.dataset.lng);
    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
    ) {
        return;
    }
    currentUrl =
        trigger.dataset.mapUrl;
    title.textContent =
        trigger.dataset.road;
    tooltip.hidden = false;
    /* Position tooltip below road name */

    const rect =
        trigger.getBoundingClientRect();
    tooltip.style.left =
        `${rect.left + window.scrollX}px`;
    tooltip.style.top =
        `${rect.bottom + window.scrollY + 8}px`;
    initializeMap();
    const location = [
        latitude,
        longitude,
    ];
    previewMap.setView(
        location,
        13
    );
    if (previewMarker) {
        previewMarker.setLatLng(
            location
        );
    } else {
        previewMarker = L.circleMarker(
            location,
            {
                radius: 7,
                color: "#ffffff",
                weight: 1,
                fillColor: "#e65100",
                fillOpacity: 0.9,
            }
        ).addTo(previewMap);

    }
    /*
      * Leaflet was initially created inside a
      * hidden element. Tell it the container
      * is now visible.
      */
    setTimeout(() => {
        previewMap.invalidateSize();
    }, 0);
  }

  function scheduleHide() {
 
        hideTimer = setTimeout(() => {
            tooltip.hidden = true;
        }, 200);
 
    }
  document
    .querySelectorAll(".road-map-trigger")
    .forEach((trigger) => {

        trigger.addEventListener(
            "mouseenter",
            () => showTooltip(trigger)
        );

        trigger.addEventListener(
            "mouseleave",
            scheduleHide
        );

        trigger.addEventListener(
            "focus",
            () => showTooltip(trigger)
        );

        trigger.addEventListener(
            "blur",
            scheduleHide
        );

    });

 
    /*
     * Keep tooltip open while user moves
     * from road name onto map.
     */
 
    tooltip.addEventListener(
        "mouseenter",
        () => clearTimeout(hideTimer)
    );
 
    tooltip.addEventListener(
        "mouseleave",
        scheduleHide
    );

  tile.addTo(map);
  feat_attr = {
    color: '#00ff00',
    weight: 5,
    opacity: 0.8,
    lineCap: 'round',
    lineJoin: 'round'
  }
  roads.features.forEach(feat => {
    let props = feat['properties'];
    let raw_coords = feat['geometry']['coordinates'];
    let cleaned_coords = raw_coords.filter(x => !(Number.isNaN(x[0]) && Number.isNaN(x[1]))).map(x => [...x].reverse());
    L.polyline(cleaned_coords, feat_attr).addTo(map);
  });
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
      // console.log(`VAL = ${value}`);
      line.textContent = `${label} ${value ? value.toFixed(2) : 0}`;
      // line.textContent = `${label} ${value.toFixed(2)}`;
      popup.append(line);
    }
    const aref = document.createElement("a");
    aref.href = point.url;
    aref.textContent = "View Road";
    aref.className = "map-road-link";
    popup.append(aref);

    let marker = L.circleMarker([point.latitude, point.longitude], {
      radius: 7,
      color: "#ffffff",
      weight: 1,
      fillColor: "#e65100",
      fillOpacity: 0.8,
    })
      .bindPopup(popup)
      .addTo(map);

    if (point.road === selectedRoad) {
      selectedMarkers.push(marker);
      marker.setStyle({
        radius:10,
        fillColor: "d9534f",
        fillOpacity: 1,
        weight:3
      });
    }

    if (selectedMarkers.length) {
      const group = L.featureGroup(selectedMarkers);
      map.fitBounds(
        group.getBounds(),
        {
          padding: [40, 40],
          maxZoom: 15,
        }
      )
    }
  });
})();


// // TEST START //
//   const table =
//         document.getElementById("traffic-table");
//     if (!table) {
//         return;
//     }
//     const dayFilter =
//         document.getElementById("day-filter");
//     const hourFilter =
//         document.getElementById("hour-filter");
//     const descriptionFilter =
//         document.getElementById("description-filter");
//     const directionFilter =
//         document.getElementById("direction-filter");
//     const resetButton =
//         document.getElementById("reset-traffic-filters");
//     const resultCount =
//         document.getElementById("traffic-result-count");
//     const rows =
//         Array.from(
//             table.querySelectorAll("tbody tr[data-hour]")
//         );
//     function updateTable() {
//         const selectedDay =
//             dayFilter.value;
//         const selectedHour =
//             hourFilter.value;
//         const selectedDescription =
//             descriptionFilter.value;
//         const selectedDirection =
//             directionFilter.value;
//         let visibleCount = 0;
//         rows.forEach((row) => {
//             const matchesHour =
//                 selectedHour === "ALL" ||
//                 row.dataset.hour === selectedHour;
//             const matchesDescription =
//                 selectedDescription === "ALL" ||
//                 row.dataset.description === selectedDescription;
//             const matchesDirection =
//                 selectedDirection === "ALL" ||
//                 row.dataset.direction === selectedDirection;
//             const visible =
//                 matchesHour &&
//                 matchesDescription &&
//                 matchesDirection;
//             row.hidden = !visible;
//             if (!visible) {
//                 return;
//             }
//             visibleCount++;
//             const dayCell =
//                 row.querySelector(".selected-day");
//             const volumeCell =
//                 row.querySelector(".selected-volume");
//             if (selectedDay === "ALL") {
//                 dayCell.textContent = "All";
//                 volumeCell.textContent =
//                     "Select a day";
//                 return;
//             }
//             const volume =
//                 row.dataset[
//                     selectedDay.toLowerCase()
//                 ];
//             dayCell.textContent =
//                 selectedDay;
//             if (
//                 volume === "" ||
//                 volume === "None" ||
//                 volume === "nan"
//             ) {
//                 volumeCell.textContent = "N/A";
//             } else {
//                 const numericVolume =
//                     Number(volume);
//                 volumeCell.textContent =
//                     Number.isFinite(numericVolume)
//                         ? numericVolume.toLocaleString()
//                         : "N/A";
//             }
//         });
//         resultCount.textContent =
//             `${visibleCount} record${visibleCount === 1 ? "" : "s"} shown`;
//     }
//     [
//         dayFilter,
//         hourFilter,
//         descriptionFilter,
//         directionFilter,
//     ].forEach((filter) => {
//         filter.addEventListener(
//             "change",
//             updateTable
//         );
//     });
//     resetButton.addEventListener(
//         "click",
//         () => {
//             dayFilter.value = "ALL";
//             hourFilter.value = "ALL";
//             descriptionFilter.value = "ALL";
//             directionFilter.value = "ALL";
//             updateTable();
//         }
//     );
//     updateTable();


//   // TEST END //

// (() => {
 
//     const tooltip =
//         document.getElementById("road-map-tooltip");
 
//     const previewElement =
//         document.getElementById("road-preview-map");
 
//     if (!tooltip || !previewElement || !window.L) {
//         return;
//     }
 
//     const title =
//         tooltip.querySelector(".road-map-tooltip-title");
 
//     let previewMap = null;
//     let previewMarker = null;
//     let currentUrl = null;
//     let hideTimer = null;
 
 
//     function initializeMap() {
 
//         if (previewMap) {
//             return;
//         }
 
//         previewMap = L.map(
//             previewElement,
//             {
//                 zoomControl: false,
//                 attributionControl: false,
//                 dragging: false,
//                 scrollWheelZoom: false,
//                 doubleClickZoom: false,
//             }
//         );
 
//         L.tileLayer(
//             "YOUR_TILE_URL/{z}/{x}/{y}.png",
//             {
//                 maxZoom: 19,
//             }
//         ).addTo(previewMap);
 
 
//         previewMap.on("click", () => {
 
//             if (currentUrl) {
//                 window.location.href = currentUrl;
//             }
 
//         });
//     }
 
 
//     function showTooltip(trigger) {
 
//         clearTimeout(hideTimer);
 
//         const latitude =
//             Number(trigger.dataset.lat);
 
//         const longitude =
//             Number(trigger.dataset.lng);
 
//         if (
//             !Number.isFinite(latitude) ||
//             !Number.isFinite(longitude)
//         ) {
//             return;
//         }
 
//         currentUrl =
//             trigger.dataset.mapUrl;
 
//         title.textContent =
//             trigger.dataset.road;
 
//         tooltip.hidden = false;
 
 
//         /* Position tooltip below road name */
 
//         const rect =
//             trigger.getBoundingClientRect();
 
//         tooltip.style.left =
//             `${rect.left + window.scrollX}px`;
 
//         tooltip.style.top =
//             `${rect.bottom + window.scrollY + 8}px`;
 
 
//         initializeMap();
 
 
//         const location = [
//             latitude,
//             longitude,
//         ];
 
//         previewMap.setView(
//             location,
//             13
//         );
 
 
//         if (previewMarker) {
 
//             previewMarker.setLatLng(
//                 location
//             );
 
//         } else {
 
//             previewMarker = L.circleMarker(
//                 location,
//                 {
//                     radius: 7,
//                     color: "#ffffff",
//                     weight: 1,
//                     fillColor: "#e65100",
//                     fillOpacity: 0.9,
//                 }
//             ).addTo(previewMap);
 
//         }
 
 
//         /*
//          * Leaflet was initially created inside a
//          * hidden element. Tell it the container
//          * is now visible.
//          */
 
//         setTimeout(() => {
//             previewMap.invalidateSize();
//         }, 0);
//     }
 
 
//     function scheduleHide() {
 
//         hideTimer = setTimeout(() => {
//             tooltip.hidden = true;
//         }, 200);
 
//     }
 
 
//     document
//         .querySelectorAll(".road-map-trigger")
//         .forEach((trigger) => {
 
//             trigger.addEventListener(
//                 "mouseenter",
//                 () => showTooltip(trigger)
//             );
 
//             trigger.addEventListener(
//                 "mouseleave",
//                 scheduleHide
//             );
 
//             trigger.addEventListener(
//                 "focus",
//                 () => showTooltip(trigger)
//             );
 
//             trigger.addEventListener(
//                 "blur",
//                 scheduleHide
//             );
 
//         });
 
 
//     /*
//      * Keep tooltip open while user moves
//      * from road name onto map.
//      */
 
//     tooltip.addEventListener(
//         "mouseenter",
//         () => clearTimeout(hideTimer)
//     );
 
//     tooltip.addEventListener(
//         "mouseleave",
//         scheduleHide
//     );
 
// })();
 