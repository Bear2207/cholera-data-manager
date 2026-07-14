<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    
    $query = "SELECT MAX(num_semaine_epid) as max_week, MAX(annee_epid) as max_year FROM cholera.cas_ll";
    $stmt = $pdo->query($query);
    $row = $stmt->fetch();
    $current_week = $row['max_week'];
    $current_year = $row['max_year'];
    
    $weeks = [];
    for ($i = 0; $i < 4; $i++) {
        $w = $current_week - $i;
        $y = $current_year;
        if ($w < 1) { $w += 52; $y--; }
        $weeks[] = ['week' => $w, 'year' => $y];
    }
    
    $placeholders = [];
    $params = [];
    foreach ($weeks as $idx => $w) {
        $placeholders[] = "(num_semaine_epid = :week{$idx} AND annee_epid = :year{$idx})";
        $params["week{$idx}"] = $w['week'];
        $params["year{$idx}"] = $w['year'];
    }
    $where = implode(' OR ', $placeholders);
    
    $query = "SELECT 
                province_notification as province,
                degre_deshydratation,
                issue,
                COUNT(*) as count
              FROM cholera.cas_ll
              WHERE ($where)
                AND degre_deshydratation IS NOT NULL
                AND issue IS NOT NULL
              GROUP BY province_notification, degre_deshydratation, issue
              ORDER BY province_notification, degre_deshydratation";
    $stmt = $pdo->prepare($query);
    $stmt->execute($params);
    $rows = $stmt->fetchAll();
    
    // Normaliser les provinces
    $data = [];
    foreach ($rows as $row) {
        $prov = normalizeProvince(trim($row['province']));
        $dehyd = $row['degre_deshydratation'];
        $issue = $row['issue'];
        $count = (int)$row['count'];
        if (!isset($data[$prov])) $data[$prov] = [];
        if (!isset($data[$prov][$dehyd])) $data[$prov][$dehyd] = [];
        if (!isset($data[$prov][$dehyd][$issue])) $data[$prov][$dehyd][$issue] = 0;
        $data[$prov][$dehyd][$issue] += $count;
    }
    
    echo json_encode([
        'success' => true,
        'data' => $data,
        'weeks' => $weeks
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>