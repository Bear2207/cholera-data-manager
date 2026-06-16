<?php
// Controller/HomeController.php

require_once __DIR__ . '/../Model/CholeraModel.php';

class HomeController {
    private $model;

    public function __construct($pdo) {
        $this->model = new CholeraModel($pdo);
    }

    public function dashboard() {
        $stats = $this->model->getCasParProvince();
        include __DIR__ . '/../templates/dashboard.php';
    }

    public function carte() {
        $geoJSON = $this->model->getZonesGeoJSON();
        include __DIR__ . '/../templates/carte.php';
    }

    public function statistiques() {
        $data = $this->model->getCasParSemaine();
        include __DIR__ . '/../templates/statistiques.php';
    }
}