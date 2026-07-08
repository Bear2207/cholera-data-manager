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
    
    // Données IDS
    $query_ids = "SELECT 
                    province,
                    SUM(cas_total) as ids_cas_cumul,
                    SUM(CASE WHEN num_semaine = :week AND annee = :year THEN cas_total ELSE 0 END) as ids_cas_week
                  FROM cholera.cas_maladie
                  WHERE maladie = :maladie AND annee >= 2025
                  GROUP BY province";
    $stmt = $pdo->prepare($query_ids);
    $stmt->execute(['maladie' => $maladie, 'week' => $current_week, 'year' => $current_year]);
    $ids_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Normaliser les provinces IDS
    $ids_mapped = [];
    foreach ($ids_data as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($ids_mapped[$prov])) {
            $ids_mapped[$prov] = ['ids_cas_cumul' => 0, 'ids_cas_week' => 0];
        }
        $ids_mapped[$prov]['ids_cas_cumul'] += (int)$row['ids_cas_cumul'];
        $ids_mapped[$prov]['ids_cas_week'] += (int)$row['ids_cas_week'];
    }
    
    // Données LL
    $query_ll = "SELECT 
                    province_notification as province,
                    COUNT(*) as ll_cas_cumul,
                    SUM(CASE WHEN num_semaine_epid = :week AND annee_epid = :year THEN 1 ELSE 0 END) as ll_cas_week
                  FROM cholera.cas_ll
                  WHERE annee_epid >= 2025
                  GROUP BY province_notification";
    $stmt = $pdo->prepare($query_ll);
    $stmt->execute(['week' => $current_week, 'year' => $current_year]);
    $ll_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    $ll_mapped = [];
    foreach ($ll_data as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($ll_mapped[$prov])) {
            $ll_mapped[$prov] = ['ll_cas_cumul' => 0, 'll_cas_week' => 0];
        }
        $ll_mapped[$prov]['ll_cas_cumul'] += (int)$row['ll_cas_cumul'];
        $ll_mapped[$prov]['ll_cas_week'] += (int)$row['ll_cas_week'];
    }
    
    // Fusion
    $all_provinces = array_unique(array_merge(array_keys($ids_mapped), array_keys($ll_mapped)));
    $result = [];
    foreach ($all_provinces as $prov) {
        $ids_cumul = isset($ids_mapped[$prov]['ids_cas_cumul']) ? $ids_mapped[$prov]['ids_cas_cumul'] : 0;
        $ids_week = isset($ids_mapped[$prov]['ids_cas_week']) ? $ids_mapped[$prov]['ids_cas_week'] : 0;
        $ll_cumul = isset($ll_mapped[$prov]['ll_cas_cumul']) ? $ll_mapped[$prov]['ll_cas_cumul'] : 0;
        $ll_week = isset($ll_mapped[$prov]['ll_cas_week']) ? $ll_mapped[$prov]['ll_cas_week'] : 0;
        
        $result[] = [
            'province' => $prov,
            'ids_cumul' => $ids_cumul,
            'll_cumul' => $ll_cumul,
            'ecart_cumul' => $ids_cumul - $ll_cumul,
            'ids_week' => $ids_week,
            'll_week' => $ll_week,
            'ecart_week' => $ids_week - $ll_week,
            'observation' => ($ids_cumul != $ll_cumul) ? (($ids_cumul > $ll_cumul) ? 'IDS supérieur' : 'LL supérieur') : ''
        ];
    }
    
    usort($result, function($a, $b) { return strcmp($a['province'], $b['province']); });
    
    echo json_encode([
        'success' => true,
        'data' => $result,
        'current_week' => $current_week,
        'current_year' => $current_year
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>