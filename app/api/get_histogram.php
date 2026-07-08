<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    $maladie = 'CHOLERA';
    
    $query = "SELECT 
                annee,
                num_semaine,
                SUM(cas_total) as cas,
                SUM(deces_total) as deces
              FROM cholera.cas_maladie
              WHERE maladie = :maladie AND annee >= 2025
              GROUP BY annee, num_semaine
              ORDER BY annee, num_semaine";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie]);
    $rows = $stmt->fetchAll();
    
    $weeks = [];
    $cases = [];
    $deaths = [];
    $letalite = [];
    
    foreach ($rows as $row) {
        $label = $row['annee'] . '-S' . $row['num_semaine'];
        $weeks[] = $label;
        $cases[] = (int)$row['cas'];
        $deaths[] = (int)$row['deces'];
        $letalite[] = ($row['cas'] > 0) ? round(($row['deces'] / $row['cas']) * 100, 1) : 0;
    }
    
    echo json_encode([
        'success' => true,
        'data' => [
            'weeks' => $weeks,
            'cases' => $cases,
            'deaths' => $deaths,
            'letalite' => $letalite
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>