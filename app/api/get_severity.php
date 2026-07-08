<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    
    $query = "SELECT 
                province_notification as province,
                COUNT(*) as total_cas,
                SUM(CASE WHEN degre_deshydratation = 'Sévère' THEN 1 ELSE 0 END) as severe,
                SUM(CASE WHEN degre_deshydratation = 'Modéré' THEN 1 ELSE 0 END) as moderate,
                SUM(CASE WHEN degre_deshydratation = 'Léger' THEN 1 ELSE 0 END) as light,
                SUM(CASE WHEN issue = 'Décédé' THEN 1 ELSE 0 END) as deaths
              FROM cholera.cas_ll
              WHERE annee_epid BETWEEN 2025 AND 2026
                AND num_semaine_epid <= 24
                AND degre_deshydratation IS NOT NULL
              GROUP BY province_notification
              ORDER BY total_cas DESC
              LIMIT 10";
    $stmt = $pdo->query($query);
    $provinces = $stmt->fetchAll();
    
    // Normaliser les provinces et agréger
    $aggregated = [];
    foreach ($provinces as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($aggregated[$prov])) {
            $aggregated[$prov] = ['severe' => 0, 'moderate' => 0, 'light' => 0, 'deaths' => 0];
        }
        $aggregated[$prov]['severe'] += (int)$row['severe'];
        $aggregated[$prov]['moderate'] += (int)$row['moderate'];
        $aggregated[$prov]['light'] += (int)$row['light'];
        $aggregated[$prov]['deaths'] += (int)$row['deaths'];
    }
    
    // Trier par sévérité
    uasort($aggregated, function($a, $b) { 
        return ($b['severe'] + $b['moderate']) - ($a['severe'] + $a['moderate']);
    });
    
    $labels = array_keys($aggregated);
    $severe = array_column($aggregated, 'severe');
    $moderate = array_column($aggregated, 'moderate');
    $light = array_column($aggregated, 'light');
    $deaths = array_column($aggregated, 'deaths');
    
    echo json_encode([
        'success' => true,
        'data' => [
            'provinces' => $labels,
            'severe' => $severe,
            'moderate' => $moderate,
            'light' => $light,
            'deaths' => $deaths
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>