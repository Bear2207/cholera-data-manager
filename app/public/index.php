<?php
// public/index.php

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../Controller/HomeController.php';

$controller = new HomeController($pdo);

$action = isset($_GET['action']) ? $_GET['action'] : 'dashboard';

switch ($action) {
    case 'carte':
        $controller->carte();
        break;
    case 'statistiques':
        $controller->statistiques();
        break;
    default:
        $controller->dashboard();
        break;
}