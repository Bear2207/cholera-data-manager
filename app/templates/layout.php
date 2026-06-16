<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestion des données choléra - COUSP</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { padding-top: 60px; }
        .container { max-width: 1200px; }
        #map { height: 500px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="?action=dashboard">COUSP Choléra</a>
            <div class="collapse navbar-collapse">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="?action=dashboard">Tableau de bord</a></li>
                    <li class="nav-item"><a class="nav-link" href="?action=carte">Carte</a></li>
                    <li class="nav-item"><a class="nav-link" href="?action=statistiques">Statistiques</a></li>
                </ul>
            </div>
        </div>
    </nav>
    <div class="container">
        <?php echo $content ?? ''; ?>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</body>
</html>