<?php ob_start(); ?>
<h1>Évolution hebdomadaire</h1>
<canvas id="chart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    const ctx = document.getElementById('chart').getContext('2d');
    const data = <?= json_encode($data) ?>;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.num_semaine),
            datasets: [{
                label: 'Cas hebdomadaires',
                data: data.map(d => d.cas),
                borderColor: 'blue',
                fill: false
            }]
        }
    });
</script>
<?php $content = ob_get_clean(); include __DIR__ . '/layout.php'; ?>