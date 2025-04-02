let map;
let markers = [];
let flightPath;

function initMap() {
    console.log("Google Maps initialized");
    // 初始化地图逻辑
}

function renderMap(record) {
    console.log("Rendering map for record:", record);

    const loadingCoords = {
        lat: record.loading_port_coordinates_geo.coordinates[1],
        lng: record.loading_port_coordinates_geo.coordinates[0],
    };
    const openCoords = {
        lat: record.open_port_coordinates_geo.coordinates[1],
        lng: record.open_port_coordinates_geo.coordinates[0],
    };

    console.log("Loading coordinates:", loadingCoords);
    console.log("Open coordinates:", openCoords);

    if (typeof google === "undefined" || typeof google.maps === "undefined") {
        console.error("Google Maps API is not loaded");
        alert("Google Maps API failed to load. Please check your network or API key.");
        return;
    }

    const map = new google.maps.Map(document.getElementById("map"), {
        center: loadingCoords,
        zoom: 8,
    });

    new google.maps.Marker({ position: loadingCoords, map, title: "Loading Port" });
    new google.maps.Marker({ position: openCoords, map, title: "Open Port" });
}

// Initialize the map
window.initMap = initMap;
window.renderMap = renderMap; // Expose renderMap globally
