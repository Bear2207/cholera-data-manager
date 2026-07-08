<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    global $ENDEMIC_PROVINCES;
    
    $query = "SELECT 
                province_notification as province,
                sexe,
                CASE 
                    WHEN age_en_ans < 1 THEN '0-11 mois'
                    WHEN age_en_ans < 5 THEN '12-59 mois'
                    WHEN age_en_ans < 15 THEN '5-15 ans'
                    ELSE '15+ ans'
                END as tranche_age,
                COUNT(*) as count
              FROM cholera.cas_ll
              WHERE annee_epid >= 2025
                AND sexe IS NOT NULL
                AND age_en_ans IS NOT NULL
              GROUP BY province_notification, sexe, tranche_age
              ORDER BY province_notification, tranche_age, sexe";
    $stmt = $pdo->query($query);
    $rows = $stmt->fetchAll();
    
    $endemic_data = [];
    $non_endemic_data = [];
    foreach ($rows as $row) {
        $prov = normalizeProvince(trim($row['province']));
        $sexe = strtoupper(substr(trim($row['sexe']), 0, 1));
        $age = $row['tranche_age'];
        $count = (int)$row['count'];
        $is_endemic = in_array($prov, $ENDEMIC_PROVINCES);
        $target = $is_endemic ? 'endemic_data' : 'non_endemic_data';
        if (!isset($target[$age])) {
            $target[$age] = ['M' => 0, 'F' => 0];
        }
        if ($sexe == 'M' || $sexe == 'F') {
            $target[$age][$sexe] += $count;
        }
    }
    
    $ages = ['0-11 mois', '12-59 mois', '5-15 ans', '15+ ans'];
    $endemic_m = []; $endemic_f = [];
    $non_endemic_m = []; $non_endemic_f = [];
    foreach ($ages as $age) {
        $endemic_m[] = isset($endemic_data[$age]['M']) ? $endemic_data[$age]['M'] : 0;
        $endemic_f[] = isset($endemic_data[$age]['F']) ? $endemic_data[$age]['F'] : 0;
        $non_endemic_m[] = isset($non_endemic_data[$age]['M']) ? $non_endemic_data[$age]['M'] : 0;
        $non_endemic_f[] = isset($non_endemic_data[$age]['F']) ? $non_endemic_data[$age]['F'] : 0;
    }
    
    echo json_encode([
        'success' => true,
        'data' => [
            'ages' => $ages,
            'endemic' => ['M' => $endemic_m, 'F' => $endemic_f],
            'non_endemic' => ['M' => $non_endemic_m, 'F' => $non_endemic_f]
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>