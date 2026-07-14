<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    $maladie = 'CHOLERA';
    global $ENDEMIC_PROVINCES;
    
    $last = getLastWeek($pdo, $maladie);
    $current_week = $last['week'];
    $current_year = $last['year'];
    
    // 4 dernières semaines
    $weeks = [];
    for ($i = 0; $i < 4; $i++) {
        $w = $current_week - $i;
        $y = $current_year;
        if ($w < 1) { $w += 52; $y--; }
        $weeks[] = ['week' => $w, 'year' => $y];
    }
    
    $placeholders = [];
    $params = ['maladie' => $maladie];
    foreach ($weeks as $idx => $w) {
        $placeholders[] = "(num_semaine = :week{$idx} AND annee = :year{$idx})";
        $params["week{$idx}"] = $w['week'];
        $params["year{$idx}"] = $w['year'];
    }
    $where = implode(' OR ', $placeholders);
    
    $query = "SELECT 
                province,
                SUM(cas_0_11_mois) as age_0_11,
                SUM(cas_12_59_mois) as age_12_59,
                SUM(cas_5_15_ans) as age_5_15,
                SUM(cas_15_plus) as age_15plus,
                SUM(cas_total) as total_cas,
                SUM(deces_0_11_mois) as deces_0_11,
                SUM(deces_12_59_mois) as deces_12_59,
                SUM(deces_5_15_ans) as deces_5_15,
                SUM(deces_15_plus) as deces_15plus,
                SUM(deces_total) as total_deces
              FROM cholera.cas_maladie
              WHERE maladie = :maladie AND ($where)
              GROUP BY province";
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();
    
    // Initialiser les totaux
    $national = ['0-11' => 0, '12-59' => 0, '5-15' => 0, '15+' => 0, 'total_cas' => 0, 
                 'deces_0-11' => 0, 'deces_12-59' => 0, 'deces_5-15' => 0, 'deces_15+' => 0, 'total_deces' => 0];
    $endemic_data = $national;
    $non_endemic_data = $national;
    
    foreach ($rows as $row) {
        $prov = normalizeProvince(trim($row['province']));
        $is_endemic = in_array($prov, $ENDEMIC_PROVINCES);
        $target = $is_endemic ? 'endemic_data' : 'non_endemic_data';
        
        ${$target}['0-11'] += (int)$row['age_0_11'];
        ${$target}['12-59'] += (int)$row['age_12_59'];
        ${$target}['5-15'] += (int)$row['age_5_15'];
        ${$target}['15+'] += (int)$row['age_15plus'];
        ${$target}['total_cas'] += (int)$row['total_cas'];
        ${$target}['deces_0-11'] += (int)$row['deces_0_11'];
        ${$target}['deces_12-59'] += (int)$row['deces_12_59'];
        ${$target}['deces_5-15'] += (int)$row['deces_5_15'];
        ${$target}['deces_15+'] += (int)$row['deces_15plus'];
        ${$target}['total_deces'] += (int)$row['total_deces'];
        
        // National
        $national['0-11'] += (int)$row['age_0_11'];
        $national['12-59'] += (int)$row['age_12_59'];
        $national['5-15'] += (int)$row['age_5_15'];
        $national['15+'] += (int)$row['age_15plus'];
        $national['total_cas'] += (int)$row['total_cas'];
        $national['deces_0-11'] += (int)$row['deces_0_11'];
        $national['deces_12-59'] += (int)$row['deces_12_59'];
        $national['deces_5-15'] += (int)$row['deces_5_15'];
        $national['deces_15+'] += (int)$row['deces_15plus'];
        $national['total_deces'] += (int)$row['total_deces'];
    }
    
    function compute_metrics($data) {
        $total = $data['total_cas'];
        $result = [];
        $age_map = ['0-11' => 'deces_0-11', '12-59' => 'deces_12-59', '5-15' => 'deces_5-15', '15+' => 'deces_15+'];
        foreach (['0-11', '12-59', '5-15', '15+'] as $age) {
            $cas = $data[$age];
            $d = $data[$age_map[$age]];
            $prop = ($total > 0) ? round(($cas / $total) * 100, 1) : 0;
            $letalite = ($cas > 0) ? round(($d / $cas) * 100, 1) : 0;
            $result[$age] = ['cas' => $cas, 'proportion' => $prop, 'deces' => $d, 'letalite' => $letalite];
        }
        return $result;
    }
    
    echo json_encode([
        'success' => true,
        'data' => [
            'national' => compute_metrics($national),
            'endemic' => compute_metrics($endemic_data),
            'non_endemic' => compute_metrics($non_endemic_data)
        ],
        'weeks' => $weeks
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>