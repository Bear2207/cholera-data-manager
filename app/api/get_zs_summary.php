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
    
    // Nombre total de ZS par province (normalisé)
    $query_zs = "SELECT 
                   province,
                   COUNT(DISTINCT zone_sante) as total_zs
                 FROM cholera.cas_maladie
                 WHERE maladie = :maladie AND annee >= 2025
                 GROUP BY province";
    $stmt = $pdo->prepare($query_zs);
    $stmt->execute(['maladie' => $maladie]);
    $zs_total = $stmt->fetchAll(PDO::FETCH_ASSOC);
    $province_zs = [];
    foreach ($zs_total as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($province_zs[$prov])) {
            $province_zs[$prov] = 0;
        }
        $province_zs[$prov] += (int)$row['total_zs'];
    }
    
    // Indicateurs par province
    $query = "SELECT 
                province,
                COUNT(DISTINCT zone_sante) as zs_with_cas_year,
                COUNT(DISTINCT CASE WHEN num_semaine = :week AND annee = :year THEN zone_sante END) as zs_with_cas_week,
                COUNT(DISTINCT CASE WHEN num_semaine = :week AND annee = :year AND cas_total >= 10 THEN zone_sante END) as zs_with_10_cas,
                COUNT(DISTINCT CASE WHEN num_semaine = :week AND annee = :year AND deces_total >= 1 THEN zone_sante END) as zs_with_death,
                COUNT(DISTINCT CASE WHEN num_semaine = :week AND annee = :year AND rec_status = 1 THEN zone_sante END) as zs_new_affected,
                COUNT(DISTINCT CASE 
                    WHEN num_semaine = :week AND annee = :year 
                    AND NOT EXISTS (
                        SELECT 1 FROM cholera.cas_maladie cm2 
                        WHERE cm2.zone_sante = cas_maladie.zone_sante 
                        AND cm2.maladie = :maladie 
                        AND (cm2.num_semaine > :week - 8 OR cm2.annee < :year) 
                        AND NOT (cm2.num_semaine = :week AND cm2.annee = :year)
                    ) THEN zone_sante 
                END) as zs_reaffected
              FROM cholera.cas_maladie
              WHERE maladie = :maladie AND annee >= 2025
              GROUP BY province";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie, 'week' => $current_week, 'year' => $current_year]);
    $indicators = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    // Prélèvements par province (normalisés)
    $query_prelev = "SELECT 
                       province_notification as province,
                       COUNT(*) as prelevements
                     FROM cholera.cas_ll
                     WHERE prelevement = 'Oui' AND annee_epid >= 2025
                     GROUP BY province_notification";
    $stmt = $pdo->query($query_prelev);
    $prelev_data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    $prelev_mapped = [];
    foreach ($prelev_data as $row) {
        $prov = normalizeProvince(trim($row['province']));
        if (!isset($prelev_mapped[$prov])) {
            $prelev_mapped[$prov] = 0;
        }
        $prelev_mapped[$prov] += (int)$row['prelevements'];
    }
    
    // Construire résultat avec normalisation des provinces
    $result = [];
    foreach ($indicators as $row) {
        $prov = normalizeProvince(trim($row['province']));
        $result[] = [
            'province' => $prov,
            'total_zs' => isset($province_zs[$prov]) ? $province_zs[$prov] : 0,
            'zs_with_cas_year' => (int)$row['zs_with_cas_year'],
            'zs_with_cas_week' => (int)$row['zs_with_cas_week'],
            'zs_with_10_cas' => (int)$row['zs_with_10_cas'],
            'zs_with_death' => (int)$row['zs_with_death'],
            'zs_new_affected' => (int)$row['zs_new_affected'],
            'zs_reaffected' => (int)$row['zs_reaffected'],
            'prelevements' => isset($prelev_mapped[$prov]) ? $prelev_mapped[$prov] : 0
        ];
    }
    
    usort($result, function($a, $b) { return strcmp($a['province'], $b['province']); });
    
    echo json_encode([
        'success' => true,
        'data' => $result
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>