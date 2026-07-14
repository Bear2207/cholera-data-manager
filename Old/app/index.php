<?php require_once __DIR__ . '/config/app_config.php'; ?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Choléra RDC - Complet</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* --- Global --- */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f4f7fc;
            color: #1a202c;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }

        /* --- Header --- */
        .header {
            background: linear-gradient(135deg, #0a2e4a 0%, #1a4a6e 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .header h1 { font-size: 26px; }
        .header .subtitle { opacity: 0.8; font-size: 14px; }
        .header .badge {
            background: rgba(255,255,255,0.15);
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 500;
        }
        .header .badge i { color: #fbd38d; margin-right: 6px; }
        .header .week-badge {
            background: #fbd38d;
            color: #1a202c;
            padding: 8px 18px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 600;
        }
        .header .week-badge i { margin-right: 6px; }

        /* --- KPI Grid --- */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: white;
            padding: 16px 20px;
            border-radius: 10px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            border-left: 4px solid #3182ce;
        }
        .kpi-card .label { font-size: 12px; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-card .value { font-size: 26px; font-weight: 700; margin: 4px 0; }
        .kpi-card .sub { font-size: 13px; color: #4a5568; }
        .kpi-card .sub .highlight { font-weight: 600; color: #2b6cb0; }

        /* --- Layout sections --- */
        .section {
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title i { color: #3182ce; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        .chart-container { position: relative; height: 250px; }
        .chart-container-sm { height: 200px; }

        /* --- Tableaux --- */
        .table-wrapper { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #f7fafc;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e2e8f0;
            white-space: nowrap;
            font-size: 12px;
        }
        td {
            padding: 8px 12px;
            border-bottom: 1px solid #edf2f7;
            font-size: 13px;
        }
        tr:hover td { background: #f7fafc; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }

        /* --- Badges --- */
        .badge-status {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-green { background: #c6f6d5; color: #276749; }
        .badge-yellow { background: #fefcbf; color: #975a16; }
        .badge-red { background: #fed7d7; color: #9b2c2c; }

        /* --- Responsive --- */
        @media (max-width: 1024px) {
            .grid-2, .grid-3 { grid-template-columns: 1fr; }
        }
        @media (max-width: 600px) {
            .header { flex-direction: column; align-items: flex-start; gap: 12px; }
            .kpi-grid { grid-template-columns: repeat(2, 1fr); }
        }

        /* --- Loading --- */
        .loading { text-align: center; padding: 20px; color: #a0aec0; }

        /* --- Carte placeholder --- */
        .map-placeholder {
            background: #e2e8f0;
            border-radius: 8px;
            height: 280px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-image: radial-gradient(circle, #cbd5e0 1px, transparent 1px);
            background-size: 20px 20px;
            position: relative;
        }
        .map-placeholder .map-label {
            background: white;
            padding: 12px 24px;
            border-radius: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-weight: 500;
        }
        .section .info-note {
            font-size: 12px;
            color: #718096;
            margin-top: 8px;
            font-style: italic;
        }
        .dashboard-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .dashboard-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.16);
            color: white;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 13px;
            text-decoration: none;
            font-weight: 600;
        }
        .dashboard-link:hover {
            background: rgba(255,255,255,0.26);
        }
        .bi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-top: 12px;
        }
        .bi-card {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px;
        }
        .bi-card h3 {
            font-size: 15px;
            margin-bottom: 6px;
        }
        .bi-card p {
            font-size: 13px;
            color: #4a5568;
            margin-bottom: 8px;
        }
        .bi-card a {
            color: #2b6cb0;
            font-weight: 600;
            text-decoration: none;
        }
    </style>
</head>
<body>
<div class="container">

    <!-- HEADER -->
    <header class="header">
        <div>
            <h1><i class="fas fa-biohazard" style="color: #fbd38d;"></i> Dashboard Choléra RDC</h1>
            <div class="subtitle">Système de Gestion d'Incident · Surveillance intégrée</div>
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
            <div class="badge">
                <i class="fas fa-filter"></i> Maladie : <strong>CHOLERA</strong>
            </div>
            <div class="week-badge">
                <i class="fas fa-calendar-alt"></i> Semaine de référence : <strong id="displayWeek">Chargement...</strong>
            </div>
            <div class="badge" style="font-size: 12px;">
                <i class="fas fa-clock"></i> <span id="updateTime"></span>
            </div>
        </div>
    </header>

    <div class="section">
        <div class="section-title"><i class="fas fa-chart-pie"></i> Tableaux de bord BI</div>
        <p>Ouvrez les outils de visualisation et d’exploration directement depuis le tableau de bord.</p>
        <div class="dashboard-links">
            <?php foreach ($BI_DASHBOARDS as $dashboard): ?>
                <a class="dashboard-link" href="<?= htmlspecialchars($dashboard['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer">
                    <i class="fas fa-external-link-alt"></i> <?= htmlspecialchars($dashboard['label'], ENT_QUOTES, 'UTF-8') ?>
                </a>
            <?php endforeach; ?>
        </div>
        <div class="bi-grid">
            <?php foreach ($BI_DASHBOARDS as $dashboard): ?>
                <div class="bi-card">
                    <h3><?= htmlspecialchars($dashboard['label'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($dashboard['description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a href="<?= htmlspecialchars($dashboard['url'], ENT_QUOTES, 'UTF-8') ?>" target="_blank" rel="noopener noreferrer">Ouvrir</a>
                </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- KPI -->
    <div class="kpi-grid" id="kpiContainer">
        <div class="kpi-card"><div class="label">Cas suspects (cumul 2025-2026)</div><div class="value" id="kpiCumulCas">...</div><div class="sub">Semaine actuelle : <span class="highlight" id="kpiWeekCas">...</span></div></div>
        <div class="kpi-card" style="border-color: #e53e3e;"><div class="label">Décès (cumul)</div><div class="value" id="kpiCumulDeces">...</div><div class="sub">Semaine actuelle : <span class="highlight" id="kpiWeekDeces">...</span></div></div>
        <div class="kpi-card" style="border-color: #ed8936;"><div class="label">Létalité cumulée</div><div class="value" id="kpiLetalite">...</div><div class="sub">2025-2026</div></div>
        <div class="kpi-card" style="border-color: #805ad5;"><div class="label">Cas investigués</div><div class="value" id="kpiInvestigues">...</div><div class="sub">Depuis 2025</div></div>
        <div class="kpi-card" style="border-color: #38a169;"><div class="label">TDR Positifs</div><div class="value" id="kpiTdrPos">...</div><div class="sub">Positivité : <span class="highlight" id="kpiPositivite">...</span>%</div></div>
    </div>

    <!-- SECTION 1 : Diagramme déshydratation + Histogramme cas/décès/létalité -->
    <div class="grid-2">
        <div class="section">
            <div class="section-title"><i class="fas fa-tint"></i> Niveau de déshydratation (cumul 2025-2026)</div>
            <div class="chart-container"><canvas id="dehydrationChart"></canvas></div>
        </div>
        <div class="section">
            <div class="section-title"><i class="fas fa-chart-bar"></i> Évolution cas, décès, létalité (2025-2026)</div>
            <div class="chart-container"><canvas id="histogramChart"></canvas></div>
        </div>
    </div>

    <!-- SECTION 2 : Carte situation actuelle ZS -->
    <div class="section">
        <div class="section-title"><i class="fas fa-map-marked-alt"></i> Situation actuelle des zones de santé</div>
        <div class="map-placeholder">
            <div class="map-label"><i class="fas fa-map"></i> Carte interactive (à intégrer via Leaflet ou autre)</div>
        </div>
        <div class="info-note">* La carte affiche les zones de santé actives pour la semaine de référence</div>
    </div>

    <!-- SECTION 3 : Complétude LL vs IDS -->
    <div class="section">
        <div class="section-title"><i class="fas fa-table"></i> Complétude des données : LL vs IDS par province</div>
        <div class="table-wrapper" id="completenessTable">
            <div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>
        </div>
        <div class="info-note">* Comparaison des cas rapportés par IDS (cas_maladie) et LL (cas_ll) - cumul 2025-2026 et semaine de référence</div>
    </div>

    <!-- SECTION 4 : Endémique / Non-endémique -->
    <div class="section">
        <div class="section-title"><i class="fas fa-chart-line"></i> Évolution des cas - provinces endémiques vs non-endémiques (2025-2026)</div>
        <div class="chart-container"><canvas id="endemicChart"></canvas></div>
        <div style="margin-top: 16px;">
            <div class="section-title" style="font-size: 16px;"><i class="fas fa-list"></i> Détail par province (cumul)</div>
            <div id="provinceDetailBars" style="height:200px; position:relative;"><canvas id="provinceDetailChart"></canvas></div>
        </div>
    </div>

    <!-- SECTION 5 : Répartition par province (semaine actuelle) -->
    <div class="section">
        <div class="section-title"><i class="fas fa-flag"></i> Répartition des cas suspects par province - Semaine de référence</div>
        <div class="table-wrapper" id="provinceWeeklyTable">
            <div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>
        </div>
    </div>

    <!-- SECTION 6 : Récapitulatif ZS par province -->
    <div class="section">
        <div class="section-title"><i class="fas fa-hospital"></i> Récapitulatif des ZS affectées par province</div>
        <div class="table-wrapper" id="zsSummaryTable">
            <div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>
        </div>
    </div>

    <!-- SECTION 7 : Répartition par tranche d'âge (4 dernières semaines) -->
    <div class="section">
        <div class="section-title"><i class="fas fa-users"></i> Répartition des cas suspects par tranche d'âge (4 dernières semaines)</div>
        <div id="ageGroupContainer">
            <div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>
        </div>
        <div style="margin-top: 16px;">
            <div class="grid-3">
                <div><h4 style="font-size:14px; margin-bottom:6px;">National</h4><div class="chart-container-sm"><canvas id="ageNationalChart"></canvas></div></div>
                <div><h4 style="font-size:14px; margin-bottom:6px;">Provinces endémiques</h4><div class="chart-container-sm"><canvas id="ageEndemicChart"></canvas></div></div>
                <div><h4 style="font-size:14px; margin-bottom:6px;">Provinces non-endémiques</h4><div class="chart-container-sm"><canvas id="ageNonEndemicChart"></canvas></div></div>
            </div>
        </div>
    </div>

    <!-- SECTION 8 : Distribution âge/sexe (LL) -->
    <div class="section">
        <div class="section-title"><i class="fas fa-venus-mars"></i> Distribution par tranche d'âge et sexe (Source LL)</div>
        <div class="grid-2">
            <div><h4 style="font-size:14px; margin-bottom:8px;">Provinces endémiques</h4><div class="chart-container-sm"><canvas id="ageSexEndemic"></canvas></div></div>
            <div><h4 style="font-size:14px; margin-bottom:8px;">Provinces non-endémiques</h4><div class="chart-container-sm"><canvas id="ageSexNonEndemic"></canvas></div></div>
        </div>
    </div>

    <!-- SECTION 9 : Issues selon déshydratation et province (4 dernières semaines) -->
    <div class="section">
        <div class="section-title"><i class="fas fa-heartbeat"></i> Issues des cas selon le degré de déshydratation et province (4 dernières semaines)</div>
        <div id="outcomesContainer">
            <div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>
        </div>
    </div>

    <!-- SECTION 10 : Sévérité de la maladie - provinces touchées -->
    <div class="section">
        <div class="section-title"><i class="fas fa-exclamation-triangle"></i> Sévérité de la maladie chez les patients admis – provinces les plus touchées (S01/2025-S24/2026)</div>
        <div class="chart-container"><canvas id="severityChart"></canvas></div>
    </div>

    <!-- SECTION 11 : Sources d'eau -->
    <div class="section">
        <div class="section-title"><i class="fas fa-water"></i> Profil des sources d'eau utilisées par les cas de choléra (S01/2025-actuel)</div>
        <div class="chart-container"><canvas id="waterSourceChart"></canvas></div>
    </div>

    <!-- Footer -->
    <footer style="margin-top:30px; text-align:center; color:#a0aec0; border-top:1px solid #e2e8f0; padding-top:16px; font-size:13px;">
        <i class="fas fa-database"></i> Données IDS & LL · COUSP-RDC · Ministère de la Santé
    </footer>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Mise à jour de l'heure
    function updateTime() {
        const now = new Date();
        document.getElementById('updateTime').textContent = now.toLocaleString('fr-FR');
    }
    updateTime();
    setInterval(updateTime, 60000);

    // Charger toutes les données
    loadKPI();
    loadDehydration();
    loadHistogram();
    loadCompleteness();
    loadEndemicNonEndemic();
    loadProvinceWeekly();
    loadZSSummary();
    loadAgeGroups();
    loadAgeSexDistribution();
    loadOutcomesDehydration();
    loadSeverity();
    loadWaterSources();

    // --- Fonctions de chargement ---
    function loadKPI() {
        fetch('api/get_kpi.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const d = data.data;
                    document.getElementById('kpiCumulCas').textContent = d.cumul_cas.toLocaleString();
                    document.getElementById('kpiWeekCas').textContent = d.cas_week.toLocaleString() + ' (SE' + d.current_week + ')';
                    document.getElementById('kpiCumulDeces').textContent = d.cumul_deces.toLocaleString();
                    document.getElementById('kpiWeekDeces').textContent = d.deces_week.toLocaleString() + ' (SE' + d.current_week + ')';
                    document.getElementById('kpiLetalite').textContent = d.letalite_cumul + '%';
                    document.getElementById('kpiInvestigues').textContent = d.cas_investigues.toLocaleString();
                    document.getElementById('kpiTdrPos').textContent = d.tdr_pos.toLocaleString() + ' / ' + d.tdr_total.toLocaleString();
                    document.getElementById('kpiPositivite').textContent = d.positivite;
                    document.getElementById('displayWeek').textContent = 'SE' + d.current_week + ' (' + d.current_year + ')';
                }
            })
            .catch(err => console.error('KPI error:', err));
    }

    function loadDehydration() {
        fetch('api/get_dehydration.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('dehydrationChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.data.labels,
                            datasets: [{
                                label: 'Nombre de cas',
                                data: data.data.values,
                                backgroundColor: ['#e53e3e', '#ed8936', '#48bb78'],
                            }]
                        },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });
                }
            })
            .catch(err => console.error('Dehydration error:', err));
    }

    function loadHistogram() {
        fetch('api/get_histogram.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('histogramChart').getContext('2d');
                    const d = data.data;
                    // Prendre les 20 dernières semaines pour lisibilité
                    const start = Math.max(0, d.weeks.length - 20);
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: d.weeks.slice(start),
                            datasets: [
                                { label: 'Cas', data: d.cases.slice(start), backgroundColor: 'rgba(49,130,206,0.6)' },
                                { label: 'Décès', data: d.deaths.slice(start), backgroundColor: 'rgba(229,62,62,0.6)' },
                                { label: 'Létalité (%)', data: d.letalite.slice(start), type: 'line', borderColor: '#ed8936', fill: false, tension: 0.2, borderWidth: 2 }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'top' } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });
                }
            })
            .catch(err => console.error('Histogram error:', err));
    }

    function loadCompleteness() {
        fetch('api/get_completeness.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let html = `<table>
                        <thead><tr>
                            <th>Province</th>
                            <th>IDS (cumul)</th>
                            <th>LL (cumul)</th>
                            <th>Écart cumul</th>
                            <th>IDS (SE${data.current_week})</th>
                            <th>LL (SE${data.current_week})</th>
                            <th>Écart semaine</th>
                            <th>Observation</th>
                        </tr></thead><tbody>`;
                    data.data.forEach(row => {
                        html += `<tr>
                            <td><strong>${row.province}</strong></td>
                            <td>${row.ids_cumul}</td>
                            <td>${row.ll_cumul}</td>
                            <td>${row.ecart_cumul}</td>
                            <td>${row.ids_week}</td>
                            <td>${row.ll_week}</td>
                            <td>${row.ecart_week}</td>
                            <td>${row.observation || '-'}</td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    document.getElementById('completenessTable').innerHTML = html;
                }
            })
            .catch(err => console.error('Completeness error:', err));
    }

    function loadEndemicNonEndemic() {
        fetch('api/get_endemic_nonendemic.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const d = data.data;
                    // Graphique endémique vs non-endémique
                    const ctx = document.getElementById('endemicChart').getContext('2d');
                    const start = Math.max(0, d.weeks.length - 20);
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: d.weeks.slice(start),
                            datasets: [
                                { label: 'Endémique', data: d.endemic.slice(start), backgroundColor: 'rgba(229,62,62,0.7)' },
                                { label: 'Non-endémique', data: d.non_endemic.slice(start), backgroundColor: 'rgba(49,130,206,0.7)' }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'top' } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });

                    // Graphique détail par province (cumul)
                    const provCtx = document.getElementById('provinceDetailChart').getContext('2d');
                    const provs = d.province_details.map(p => p.province);
                    const vals = d.province_details.map(p => p.total_cas);
                    new Chart(provCtx, {
                        type: 'bar',
                        data: {
                            labels: provs,
                            datasets: [{
                                label: 'Cas cumulés',
                                data: vals,
                                backgroundColor: 'rgba(49,130,206,0.6)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });
                }
            })
            .catch(err => console.error('Endemic error:', err));
    }

    function loadProvinceWeekly() {
        fetch('api/get_province_weekly.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let html = `<table>
                        <thead><tr>
                            <th>Province</th>
                            <th>Nouveaux cas</th>
                            <th>Décès</th>
                            <th>Létalité (%)</th>
                            <th>ZS notifiant</th>
                            <th>Variation (%) vs semaine précédente</th>
                        </tr></thead><tbody>`;
                    data.data.forEach(row => {
                        let varHtml = row.variation !== null ? (row.variation > 0 ? '+' : '') + row.variation + '%' : 'N/A';
                        let varClass = row.variation > 0 ? 'badge-red' : (row.variation < 0 ? 'badge-green' : '');
                        html += `<tr>
                            <td><strong>${row.province}</strong></td>
                            <td>${row.cas}</td>
                            <td>${row.deces}</td>
                            <td>${row.letalite}</td>
                            <td>${row.zs_notifiant}</td>
                            <td><span class="badge-status ${varClass}">${varHtml}</span></td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    document.getElementById('provinceWeeklyTable').innerHTML = html;
                }
            })
            .catch(err => console.error('Province weekly error:', err));
    }

    function loadZSSummary() {
        fetch('api/get_zs_summary.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let html = `<table>
                        <thead><tr>
                            <th>Province</th>
                            <th>Total ZS</th>
                            <th>ZS avec ≥1 cas (début année)</th>
                            <th>ZS avec cas (SE actuelle)</th>
                            <th>ZS avec ≥10 cas (SE)</th>
                            <th>ZS avec ≥1 décès (SE)</th>
                            <th>ZS nouvellement affectées</th>
                            <th>ZS réaffectées (>8 sem.)</th>
                            <th>Prélèvements réalisés</th>
                        </tr></thead><tbody>`;
                    data.data.forEach(row => {
                        html += `<tr>
                            <td><strong>${row.province}</strong></td>
                            <td>${row.total_zs}</td>
                            <td>${row.zs_with_cas_year}</td>
                            <td>${row.zs_with_cas_week}</td>
                            <td>${row.zs_with_10_cas}</td>
                            <td>${row.zs_with_death}</td>
                            <td>${row.zs_new_affected}</td>
                            <td>${row.zs_reaffected}</td>
                            <td>${row.prelevements}</td>
                        </tr>`;
                    });
                    html += '</tbody></table>';
                    document.getElementById('zsSummaryTable').innerHTML = html;
                }
            })
            .catch(err => console.error('ZS summary error:', err));
    }

    function loadAgeGroups() {
        fetch('api/get_age_groups.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const d = data.data;
                    // Tableau récapitulatif
                    let html = `<table>
                        <thead><tr>
                            <th>Groupe</th>
                            <th>Tranche âge</th>
                            <th>Cas</th>
                            <th>Proportion (%)</th>
                            <th>Décès</th>
                            <th>Létalité (%)</th>
                        </tr></thead><tbody>`;
                    ['national', 'endemic', 'non_endemic'].forEach(group => {
                        const label = group === 'national' ? 'National' : (group === 'endemic' ? 'Endémique' : 'Non-endémique');
                        const ages = d[group];
                        for (const [age, vals] of Object.entries(ages)) {
                            html += `<tr>
                                <td>${label}</td>
                                <td>${age}</td>
                                <td>${vals.cas}</td>
                                <td>${vals.proportion}</td>
                                <td>${vals.deces}</td>
                                <td>${vals.letalite}</td>
                            </tr>`;
                        }
                    });
                    html += '</tbody></table>';
                    document.getElementById('ageGroupContainer').innerHTML = html;

                    // Graphiques en barres pour les trois catégories
                    const labels = Object.keys(d.national);
                    const nationalData = labels.map(k => d.national[k].cas);
                    const endemicData = labels.map(k => d.endemic[k].cas);
                    const nonEndemicData = labels.map(k => d.non_endemic[k].cas);

                    new Chart(document.getElementById('ageNationalChart'), {
                        type: 'bar',
                        data: { labels, datasets: [{ label: 'National', data: nationalData, backgroundColor: '#3182ce' }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });
                    new Chart(document.getElementById('ageEndemicChart'), {
                        type: 'bar',
                        data: { labels, datasets: [{ label: 'Endémique', data: endemicData, backgroundColor: '#e53e3e' }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });
                    new Chart(document.getElementById('ageNonEndemicChart'), {
                        type: 'bar',
                        data: { labels, datasets: [{ label: 'Non-endémique', data: nonEndemicData, backgroundColor: '#48bb78' }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
                    });
                }
            })
            .catch(err => console.error('Age groups error:', err));
    }

    function loadAgeSexDistribution() {
        fetch('api/get_age_sex_distribution.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const d = data.data;
                    // Graphique endémique
                    new Chart(document.getElementById('ageSexEndemic'), {
                        type: 'bar',
                        data: {
                            labels: d.ages,
                            datasets: [
                                { label: 'Hommes', data: d.endemic.M, backgroundColor: '#3182ce' },
                                { label: 'Femmes', data: d.endemic.F, backgroundColor: '#e53e3e' }
                            ]
                        },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true } } }
                    });
                    // Graphique non-endémique
                    new Chart(document.getElementById('ageSexNonEndemic'), {
                        type: 'bar',
                        data: {
                            labels: d.ages,
                            datasets: [
                                { label: 'Hommes', data: d.non_endemic.M, backgroundColor: '#3182ce' },
                                { label: 'Femmes', data: d.non_endemic.F, backgroundColor: '#e53e3e' }
                            ]
                        },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true } } }
                    });
                }
            })
            .catch(err => console.error('AgeSex error:', err));
    }

    function loadOutcomesDehydration() {
        fetch('api/get_outcomes_dehydration.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let html = `<table>
                        <thead><tr>
                            <th>Province</th>
                            <th>Déshydratation</th>
                            <th>Guéri</th>
                            <th>Décédé</th>
                            <th>Autre</th>
                        </tr></thead><tbody>`;
                    for (const [prov, dehyds] of Object.entries(data.data)) {
                        for (const [dehyd, issues] of Object.entries(dehyds)) {
                            const gueri = issues['Guéri'] || issues['Guéri(e)'] || 0;
                            const deces = issues['Décédé'] || 0;
                            const autre = Object.entries(issues)
                                .filter(([k]) => !['Guéri', 'Guéri(e)', 'Décédé'].includes(k))
                                .reduce((sum, [_, v]) => sum + v, 0);
                            html += `<tr>
                                <td><strong>${prov}</strong></td>
                                <td>${dehyd}</td>
                                <td>${gueri}</td>
                                <td>${deces}</td>
                                <td>${autre}</td>
                            </tr>`;
                        }
                    }
                    html += '</tbody></table>';
                    document.getElementById('outcomesContainer').innerHTML = html;
                }
            })
            .catch(err => console.error('Outcomes error:', err));
    }

    function loadSeverity() {
        fetch('api/get_severity.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const d = data.data;
                    const ctx = document.getElementById('severityChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: d.provinces,
                            datasets: [
                                { label: 'Sévère', data: d.severe, backgroundColor: '#e53e3e' },
                                { label: 'Modéré', data: d.moderate, backgroundColor: '#ed8936' },
                                { label: 'Léger', data: d.light, backgroundColor: '#48bb78' },
                                { label: 'Décès', data: d.deaths, backgroundColor: '#2d3748' }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { position: 'top' } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });
                }
            })
            .catch(err => console.error('Severity error:', err));
    }

    function loadWaterSources() {
        fetch('api/get_water_sources.php')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const ctx = document.getElementById('waterSourceChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.data.labels,
                            datasets: [{
                                label: 'Cas',
                                data: data.data.values,
                                backgroundColor: 'rgba(56,178,172,0.6)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });
                }
            })
            .catch(err => console.error('Water sources error:', err));
    }
});
</script>
</body>
</html>