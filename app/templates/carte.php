<?php ob_start(); ?>
<h1>Carte des zones de santé</h1>
<div id="map"></div>
<script>
    var map = L.map('map').setView([-4.0, 21.0], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    var geojsonData = <?= json_encode($geoJSON) ?>;
    if (geojsonData && geojsonData.features) {
        L.geoJSON(geojsonData, {
            style: { color: '#3388ff', weight: 2, opacity: 0.7 },
            onEachFeature: function (feature, layer) {
                var props = feature.properties;
                var popup = `<b>${props.nom}</b><br>Province: ${props.province}<br>Population: ${props.population || 'N/A'}`;
                layer.bindPopup(popup);
            }
        }).addTo(map);
    }
</script>
<?php $content = ob_get_clean(); include __DIR__ . '/layout.php'; ?>