let map;
let markers = [];
let flightPath;

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 3,
        center: { lat: 0, lng: 0 },
        mapTypeId: "terrain",
    });
}

function renderMap(record) {
    console.log("Rendering map for record:", record); // Debug log
    if (!record.loading_port_coordinates_geo || !record.open_port_coordinates_geo) {
        console.error("Invalid coordinates for this record:", record);
        alert("Invalid coordinates for this record.");
        return;
    }

    const loadingCoords = {
        lat: record.loading_port_coordinates_geo.coordinates[1],
        lng: record.loading_port_coordinates_geo.coordinates[0],
    };
    const openCoords = {
        lat: record.open_port_coordinates_geo.coordinates[1],
        lng: record.open_port_coordinates_geo.coordinates[0],
    };

    console.log("Loading coordinates:", loadingCoords); // Debug log
    console.log("Open coordinates:", openCoords); // Debug log

    // Clear previous markers and flight path
    markers.forEach(marker => marker.setMap(null));
    if (flightPath) flightPath.setMap(null);

    // Add markers for the two locations
    markers = [
        new google.maps.Marker({ position: loadingCoords, map: map, title: "Loading Port" }),
        new google.maps.Marker({ position: openCoords, map: map, title: "Open Port" }),
    ];

    // Draw a great circle arc between the two points
    flightPath = new google.maps.Polyline({
        path: [loadingCoords, openCoords],
        geodesic: true,
        strokeColor: "#FF0000",
        strokeOpacity: 1.0,
        strokeWeight: 2,
        map: map,
    });

    // Adjust the map view to fit both points
    const bounds = new google.maps.LatLngBounds();
    bounds.extend(loadingCoords);
    bounds.extend(openCoords);
    map.fitBounds(bounds);
}

// Initialize the map
window.initMap = initMap;
window.renderMap = renderMap; // Expose renderMap globally
