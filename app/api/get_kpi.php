<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    $maladie = 'CHOLERA';
    
    // Dernière semaine disponible
    $last = getLastWeek($pdo, $maladie);
    $current_week = $last['week'];
    $current_year = $last['year'];
    
    // 1. Cas suspects cumulés depuis 2025
    $query = "SELECT SUM(cas_total) as total FROM cholera.cas_maladie WHERE maladie = :maladie AND annee >= 2025";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie]);
    $cumul_cas = (int)$stmt->fetch()['total'];
    
    // Cas suspects semaine actuelle
    $query = "SELECT SUM(cas_total) as total FROM cholera.cas_maladie WHERE maladie = :maladie AND num_semaine = :week AND annee = :year";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie, 'week' => $current_week, 'year' => $current_year]);
    $cas_week = (int)$stmt->fetch()['total'];
    
    // 2. Décès cumulés depuis 2025
    $query = "SELECT SUM(deces_total) as total FROM cholera.cas_maladie WHERE maladie = :maladie AND annee >= 2025";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie]);
    $cumul_deces = (int)$stmt->fetch()['total'];
    
    // Décès semaine actuelle
    $query = "SELECT SUM(deces_total) as total FROM cholera.cas_maladie WHERE maladie = :maladie AND num_semaine = :week AND annee = :year";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie, 'week' => $current_week, 'year' => $current_year]);
    $deces_week = (int)$stmt->fetch()['total'];
    
    // Létalité cumulée
    $letalite_cumul = ($cumul_cas > 0) ? round(($cumul_deces / $cumul_cas) * 100, 1) : 0;
    
    // 3. Cas investigués
    $query = "SELECT COUNT(*) as total FROM cholera.cas_ll WHERE date_investigation IS NOT NULL AND annee_epid >= 2025";
    $stmt = $pdo->query($query);
    $cas_investigues = (int)$stmt->fetch()['total'];
    
    // 4. TDR Positifs
    $query = "SELECT 
                COUNT(*) as total_tdr,
                SUM(CASE WHEN tdr_resultat ILIKE '%positif%' THEN 1 ELSE 0 END) as tdr_pos
              FROM cholera.cas_ll 
              WHERE tdr_realise = 'Oui' AND annee_epid >= 2025";
    $stmt = $pdo->query($query);
    $row = $stmt->fetch();
    $total_tdr = (int)$row['total_tdr'];
    $tdr_pos = (int)$row['tdr_pos'];
    $positivite = ($total_tdr > 0) ? round(($tdr_pos / $total_tdr) * 100, 1) : 0;
    
    echo json_encode([
        'success' => true,
        'data' => [
            'cumul_cas' => $cumul_cas,
            'cas_week' => $cas_week,
            'cumul_deces' => $cumul_deces,
            'deces_week' => $deces_week,
            'letalite_cumul' => $letalite_cumul,
            'cas_investigues' => $cas_investigues,
            'tdr_pos' => $tdr_pos,
            'tdr_total' => $total_tdr,
            'positivite' => $positivite,
            'current_week' => $current_week,
            'current_year' => $current_year
        ]
    ]);
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>