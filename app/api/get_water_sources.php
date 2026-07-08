<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    
    $query = "SELECT 
                source_approvisionnement_en_eau as source,
                COUNT(*) as count
              FROM cholera.cas_ll
              WHERE source_approvisionnement_en_eau IS NOT NULL
                AND annee_epid >= 2025
              GROUP BY source_approvisionnement_en_eau
              ORDER BY count DESC";
    $stmt = $pdo->query($query);
    $rows = $stmt->fetchAll();
    
    $labels = array_column($rows, 'source');
    $values = array_column($rows, 'count');
    
    echo json_encode([
        'success' => true,
        'data' => [
            'labels' => $labels,
            'values' => $values
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>