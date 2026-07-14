<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    $maladie = 'CHOLERA';
    
    $last = getLastWeek($pdo, $maladie);
    $current_week = $last['week'];
    $current_year = $last['year'];
    
    // Semaine précédente
    $prev_week = $current_week - 1;
    $prev_year = $current_year;
    if ($prev_week < 1) { $prev_week = 52; $prev_year--; }
    
    // Données semaine actuelle par province (normalisées)
    $query = "SELECT 
                province,
                SUM(cas_total) as cas,
                SUM(deces_total) as deces,
                COUNT(DISTINCT zone_sante) as zs_count
              FROM cholera.cas_maladie
              WHERE maladie = :maladie AND num_semaine = :week AND annee = :year
              GROUP BY province";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie, 'week' => $current_week, 'year' => $current_year]);
    $current_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Normaliser les provinces
    $current_mapped = [];
    foreach ($current_data as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($current_mapped[$prov])) {
            $current_mapped[$prov] = ['cas' => 0, 'deces' => 0, 'zs_count' => 0];
        }
        $current_mapped[$prov]['cas'] += (int)$row['cas'];
        $current_mapped[$prov]['deces'] += (int)$row['deces'];
        $current_mapped[$prov]['zs_count'] += (int)$row['zs_count'];
    }
    
    // Données semaine précédente
    $query_prev = "SELECT 
                     province,
                     SUM(cas_total) as cas_prev
                   FROM cholera.cas_maladie
                   WHERE maladie = :maladie AND num_semaine = :week AND annee = :year
                   GROUP BY province";
    $stmt = $pdo->prepare($query_prev);
    $stmt->execute(['maladie' => $maladie, 'week' => $prev_week, 'year' => $prev_year]);
    $prev_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $prev_mapped = [];
    foreach ($prev_data as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($prev_mapped[$prov])) {
            $prev_mapped[$prov] = 0;
        }
        $prev_mapped[$prov] += (int)$row['cas_prev'];
    }
    
    // Construire résultat
    $result = [];
    foreach ($current_mapped as $prov => $data) {
        $cas = $data['cas'];
        $deces = $data['deces'];
        $letalite = ($cas > 0) ? round(($deces / $cas) * 100, 1) : 0;
        $prev_cas = isset($prev_mapped[$prov]) ? $prev_mapped[$prov] : 0;
        $variation = ($prev_cas > 0) ? round((($cas - $prev_cas) / $prev_cas) * 100, 1) : null;
        
        $result[] = [
            'province' => $prov,
            'cas' => $cas,
            'deces' => $deces,
            'letalite' => $letalite,
            'zs_notifiant' => $data['zs_count'],
            'variation' => $variation
        ];
    }
    
    // Trier par cas décroissant
    usort($result, function($a, $b) { return $b['cas'] - $a['cas']; });
    
    echo json_encode([
        'success' => true,
        'data' => $result,
        'week' => $current_week,
        'year' => $current_year
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>