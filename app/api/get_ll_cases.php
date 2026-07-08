<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once '../config/database.php';

try {
    $pdo = getDBConnection();
    
    $query = "
        SELECT 
            n_epid,
            province_notification,
            zone_de_sante_notification,
            age_en_ans,
            classification_finale,
            date_debut_maladie,
            issue
        FROM cholera.cas_ll
        WHERE annee_epid = 2026
        ORDER BY id DESC
        LIMIT 20
    ";
    
    $stmt = $pdo->query($query);
    $cases = $stmt->fetchAll();
    
    // Ajouter le statut
    foreach ($cases as &$case) {
        if ($case['issue'] === 'Décédé') {
            $case['status'] = 'death';
            $case['status_label'] = 'Décédé';
        } elseif ($case['classification_finale'] === 'Confirmé') {
            $case['status'] = 'confirmed';
            $case['status_label'] = 'Confirmé';
        } else {
            $case['status'] = 'suspect';
            $case['status_label'] = 'Suspect';
        }
    }
    
    echo json_encode(['success' => true, 'data' => $cases]);
    
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>