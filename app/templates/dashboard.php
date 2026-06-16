<?php ob_start(); ?>
<h1>Tableau de bord choléra</h1>
<table class="table table-striped">
    <thead><tr><th>Province</th><th>Cas totaux</th><th>Décès</th></tr></thead>
    <tbody>
    <?php foreach ($stats as $row): ?>
        <tr><td><?= htmlspecialchars($row['province']) ?></td><td><?= $row['total_cas'] ?></td><td><?= $row['total_deces'] ?></td></tr>
    <?php endforeach; ?>
    </tbody>
</table>
<?php $content = ob_get_clean(); include __DIR__ . '/layout.php'; ?>