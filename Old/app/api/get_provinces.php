<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    
    $query = "
        SELECT 
            province,
            SUM(cas_total) as cas,
            SUM(deces_total) as deces,
            ROUND((SUM(deces_total)::NUMERIC / NULLIF(SUM(cas_total), 0)) * 100, 2) as letalite
        FROM cholera.cas_maladie
        WHERE annee = 2026 
          AND num_semaine <= 26 
          AND maladie = 'CHOLERA'
        GROUP BY province
        ORDER BY cas DESC
        LIMIT 10
    ";
    
    $stmt = $pdo->query($query);
    $provinces = $stmt->fetchAll();
    
    // Calculer le max pour les barres
    $maxCas = !empty($provinces) ? max(array_column($provinces, 'cas')) : 1;
    foreach ($provinces as &$p) {
        $p['bar_width'] = round(($p['cas'] / $maxCas) * 100);
    }
    
    echo json_encode(['success' => true, 'data' => $provinces]);
    
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>