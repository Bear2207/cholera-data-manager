<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    // On utilise la table cas_ll qui contient degre_deshydratation
    $query = "SELECT 
                degre_deshydratation,
                COUNT(*) as count
              FROM cholera.cas_ll
              WHERE degre_deshydratation IS NOT NULL
                AND degre_deshydratation IN ('Sévère', 'Modéré', 'Léger')
                AND annee_epid >= 2025
              GROUP BY degre_deshydratation
              ORDER BY 
                CASE degre_deshydratation
                  WHEN 'Sévère' THEN 1
                  WHEN 'Modéré' THEN 2
                  WHEN 'Léger' THEN 3
                END";
    $stmt = $pdo->query($query);
    $data = $stmt->fetchAll();
    
    // Assurer que les trois catégories existent
    $labels = ['Sévère', 'Modéré', 'Léger'];
    $values = array_fill_keys($labels, 0);
    foreach ($data as $row) {
        $values[$row['degre_deshydratation']] = (int)$row['count'];
    }
    
    echo json_encode([
        'success' => true,
        'data' => [
            'labels' => $labels,
            'values' => array_values($values)
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>