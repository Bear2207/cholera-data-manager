<?php
// config/app_config.php
// Centralisation des paramètres et mappings

// Mapping des noms de provinces pour harmoniser les tables
// Clé = nom dans la base (province ou province_notification), Valeur = nom normalisé
$PROVINCE_MAPPING = [
    // Provinces existantes - adaptez selon vos données réelles
    'Sud-Kivu' => 'Sud-Kivu',
    'Sud Kivu' => 'Sud-Kivu',
    'SUD-KIVU' => 'Sud-Kivu',
    'Nord-Kivu' => 'Nord-Kivu',
    'Nord Kivu' => 'Nord-Kivu',
    'NORD-KIVU' => 'Nord-Kivu',
    'Kinshasa' => 'Kinshasa',
    'KINSHASA' => 'Kinshasa',
    'Haut-Katanga' => 'Haut-Katanga',
    'Haut Katanga' => 'Haut-Katanga',
    'HAUT-KATANGA' => 'Haut-Katanga',
    'Tanganyika' => 'Tanganyika',
    'TANGANYIKA' => 'Tanganyika',
    'Kongo Central' => 'Kongo Central',
    'Kongo Central' => 'Kongo Central',
    'KONGO CENTRAL' => 'Kongo Central',
    'Équateur' => 'Équateur',
    'Equateur' => 'Équateur',
    'EQUATEUR' => 'Équateur',
    'Mai-Ndombe' => 'Mai-Ndombe',
    'Mai Ndombe' => 'Mai-Ndombe',
    'MAI-NDOMBE' => 'Mai-Ndombe',
    'Lualaba' => 'Lualaba',
    'LUALABA' => 'Lualaba',
    'Sud-Ubangi' => 'Sud-Ubangi',
    'Sud Ubangi' => 'Sud-Ubangi',
    'SUD-UBANGI' => 'Sud-Ubangi',
    'Tshopo' => 'Tshopo',
    'TSHOPO' => 'Tshopo',
    'Mongala' => 'Mongala',
    'MONGALA' => 'Mongala',
    'Sankuru' => 'Sankuru',
    'SANKURU' => 'Sankuru',
    'Kasaï' => 'Kasaï',
    'Kasai' => 'Kasaï',
    'KASAI' => 'Kasaï',
    'Kasaï-Central' => 'Kasaï-Central',
    'Kasai-Central' => 'Kasaï-Central',
    'KASAI-CENTRAL' => 'Kasaï-Central',
    'Kasaï-Oriental' => 'Kasaï-Oriental',
    'Kasai-Oriental' => 'Kasaï-Oriental',
    'KASAI-ORIENTAL' => 'Kasaï-Oriental',
    'Lomami' => 'Lomami',
    'LOMAMI' => 'Lomami',
    'Haut-Lomami' => 'Haut-Lomami',
    'Haut Lomami' => 'Haut-Lomami',
    'HAUT-LOMAMI' => 'Haut-Lomami',
    'Tshuapa' => 'Tshuapa',
    'Tshuapa' => 'Tshuapa',
    'Bas-Uele' => 'Bas-Uele',
    'Bas Uele' => 'Bas-Uele',
    'BAS-UELE' => 'Bas-Uele',
    'Haut-Uele' => 'Haut-Uele',
    'Haut Uele' => 'Haut-Uele',
    'HAUT-UELE' => 'Haut-Uele',
    'Ituri' => 'Ituri',
    'ITURI' => 'Ituri',
    'Maniema' => 'Maniema',
    'MANIEMA' => 'Maniema',
    'Nord-Ubangi' => 'Nord-Ubangi',
    'Nord Ubangi' => 'Nord-Ubangi',
    'NORD-UBANGI' => 'Nord-Ubangi',
];

// Provinces endémiques (à ajuster selon votre contexte)
$ENDEMIC_PROVINCES = ['Sud-Kivu', 'Nord-Kivu', 'Kinshasa', 'Haut-Katanga', 'Tanganyika'];

// Fonction pour récupérer la dernière semaine disponible dans cas_maladie (pour CHOLERA)
function getLastWeek($pdo, $maladie = 'CHOLERA') {
    $query = "SELECT MAX(num_semaine) as max_week, MAX(annee) as max_year 
              FROM cholera.cas_maladie 
              WHERE maladie = :maladie";
    $stmt = $pdo->prepare($query);
    $stmt->execute(['maladie' => $maladie]);
    $row = $stmt->fetch();
    return ['week' => (int)$row['max_week'], 'year' => (int)$row['max_year']];
}

// Fonction pour normaliser les noms de provinces
function normalizeProvince($name) {
    global $PROVINCE_MAPPING;
    $name = trim($name);
    return isset($PROVINCE_MAPPING[$name]) ? $PROVINCE_MAPPING[$name] : $name;
}

// Fonction pour normaliser un tableau de données avec mapping des provinces
function normalizeProvinceData($data, $provinceKey) {
    global $PROVINCE_MAPPING;
    $result = [];
    foreach ($data as $row) {
        $prov = trim($row[$provinceKey]);
        $normalized = isset($PROVINCE_MAPPING[$prov]) ? $PROVINCE_MAPPING[$prov] : $prov;
        if (!isset($result[$normalized])) {
            $result[$normalized] = $row;
            $result[$normalized][$provinceKey] = $normalized;
        } else {
            // Agréger si déjà existant
            foreach ($row as $key => $value) {
                if (is_numeric($value) && $key != $provinceKey) {
                    $result[$normalized][$key] += (int)$value;
                }
            }
        }
    }
    return array_values($result);
}
?>