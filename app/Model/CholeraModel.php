<?php
// Model/CholeraModel.php

class CholeraModel {
    private $pdo;

    public function __construct($pdo) {
        $this->pdo = $pdo;
    }

    public function getCasParProvince() {
        $sql = "SELECT province, SUM(cas_total) as total_cas, SUM(deces_total) as total_deces 
                FROM cas_maladie 
                GROUP BY province ORDER BY total_cas DESC";
        $stmt = $this->pdo->query($sql);
        return $stmt->fetchAll();
    }

    public function getCasParSemaine($maladie = 'cholera') {
        $sql = "SELECT num_semaine, SUM(cas_total) as cas 
                FROM cas_maladie 
                WHERE maladie = :maladie 
                GROUP BY num_semaine ORDER BY num_semaine";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute(['maladie' => $maladie]);
        return $stmt->fetchAll();
    }

    public function getZonesGeoJSON() {
        // Récupère les zones avec leurs géométries au format GeoJSON
        $sql = "SELECT json_build_object(
                    'type', 'FeatureCollection',
                    'features', json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(geom)::json,
                            'properties', json_build_object(
                                'nom', nom,
                                'province', province,
                                'population', population
                            )
                        )
                    )
                ) as geojson
                FROM zones";
        $stmt = $this->pdo->query($sql);
        $row = $stmt->fetch();
        return $row ? json_decode($row['geojson'], true) : null;
    }
}