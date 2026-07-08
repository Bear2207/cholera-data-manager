<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    $maladie = 'CHOLERA';
    
    global $ENDEMIC_PROVINCES;
    
    $query = "SELECT 
                annee,
                num_semaine,
                province,
                SUM(cas_total) as cas
              FROM cholera.cas_maladie
              WHERE maladie = :maladie AND annee >= 2025
              GROUP BY annee, num_semaine, province
              ORDER BY annee, num_semaine";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie]);
    $rows = $stmt->fetchAll();
    
    // Agrégation par semaine avec normalisation des provinces
    $data = [];
    foreach ($rows as $row) {
        $week_key = $row['annee'] . '-S' . $row['num_semaine'];
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($data[$week_key])) {
            $data[$week_key] = ['endemic' => 0, 'non_endemic' => 0, 'week_label' => $week_key];
        }
        if (in_array($prov, $ENDEMIC_PROVINCES)) {
            $data[$week_key]['endemic'] += (int)$row['cas'];
        } else {
            $data[$week_key]['non_endemic'] += (int)$row['cas'];
        }
    }
    
    ksort($data);
    $weeks = array_keys($data);
    $endemic_vals = array_column($data, 'endemic');
    $non_endemic_vals = array_column($data, 'non_endemic');
    
    // Détail par province (normalisé)
    $query_prov = "SELECT 
                     province,
                     SUM(cas_total) as total_cas
                   FROM cholera.cas_maladie
                   WHERE maladie = :maladie AND annee >= 2025
                   GROUP BY province";
    $stmt = $pdo->prepare($query_prov);
    $stmt->execute(['maladie' => $maladie]);
    $prov_cas = $stmt->fetchAll();
    
    // Normaliser les provinces
    $prov_aggregated = [];
    foreach ($prov_cas as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($prov_aggregated[$prov])) {
            $prov_aggregated[$prov] = 0;
        }
        $prov_aggregated[$prov] += (int)$row['total_cas'];
    }
    $prov_details = [];
    foreach ($prov_aggregated as $prov => $total) {
        $prov_details[] = ['province' => $prov, 'total_cas' => $total];
    }
    usort($prov_details, function($a, $b) { return $b['total_cas'] - $a['total_cas']; });
    
    echo json_encode([
        'success' => true,
        'data' => [
            'weeks' => $weeks,
            'endemic' => $endemic_vals,
            'non_endemic' => $non_endemic_vals,
            'province_details' => $prov_details
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>