#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour extraire les statistiques Deadline et générer un rapport HTML
"""

import subprocess
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict

class DeadlineStatsParser:
    def __init__(self):
        self.jobs = []
        # Chemin en dur vers deadlinecommand.exe
        self.deadline_cmd = r"C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe"
        
        if not os.path.exists(self.deadline_cmd):
            raise FileNotFoundError(
                f"deadlinecommand.exe introuvable à l'emplacement: {self.deadline_cmd}"
            )
        print(f"✅ Deadline trouvé: {self.deadline_cmd}")
        
    def get_current_month(self):
        """Retourne le mois en cours au format yyyy-MM"""
        return datetime.now().strftime("%Y-%m")
    
    def get_previous_month(self):
        """Retourne le mois précédent au format yyyy-MM"""
        today = datetime.now()
        # Calculer le mois précédent
        if today.month == 1:
            prev_month = datetime(today.year - 1, 12, 1)
        else:
            prev_month = datetime(today.year, today.month - 1, 1)
        return prev_month.strftime("%Y-%m")
    
    def get_next_month(self):
        """Retourne le mois suivant au format yyyy-MM"""
        today = datetime.now()
        # Calculer le mois suivant
        if today.month == 12:
            next_month = datetime(today.year + 1, 1, 1)
        else:
            next_month = datetime(today.year, today.month + 1, 1)
        return next_month.strftime("%Y-%m")
    
    def run_job_statistics(self, start_month: str, end_month: str, 
                          pool_filter: str = "", group_filter: str = "", 
                          plugin_filter: str = ""):
        """
        Execute la commande deadlinecommand -JobStatistics
        
        Args:
            start_month: Format yyyy-MM (ex: 2025-10)
            end_month: Format yyyy-MM (ex: 2025-10)
            pool_filter: Filtres de pools séparés par virgules (chaîne vide par défaut)
            group_filter: Filtres de groupes séparés par virgules (chaîne vide par défaut)
            plugin_filter: Filtres de plugins séparés par virgules (chaîne vide par défaut)
        """
        # Construction de la commande avec guillemets et arguments vides explicites
        cmd = [
            self.deadline_cmd,
            "-JobStatistics",
            start_month,
            end_month,
            pool_filter,      # Peut être "" (chaîne vide)
            group_filter,     # Peut être "" (chaîne vide)
            plugin_filter     # Peut être "" (chaîne vide)
        ]
        
        # Affichage pour debug
        cmd_display = f'"{self.deadline_cmd}" -JobStatistics {start_month} {end_month} "" "" ""'
        print(f"🔧 Commande: {cmd_display}")
        
        try:
            # subprocess.run gère automatiquement les guillemets pour les chemins avec espaces
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'exécution de la commande: {e}")
            print(f"Code de retour: {e.returncode}")
            print(f"Sortie d'erreur: {e.stderr}")
            return None
        except FileNotFoundError as e:
            print(f"❌ Fichier introuvable: {e}")
            print(f"Chemin utilisé: {self.deadline_cmd}")
            return None
    
    def parse_job_statistics(self, output: str) -> List[Dict]:
        """
        Parse la sortie de JobStatistics et extrait les informations pertinentes
        """
        jobs = []
        current_job = {}
        
        # Split par job (chaque job commence par un ID entre crochets)
        job_blocks = re.split(r'\n(?=\[)', output)
        
        for block in job_blocks:
            if not block.strip():
                continue
                
            lines = block.strip().split('\n')
            job_data = {}
            
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    job_data[key] = value
            
            # Filtrer les jobs des dernières 24h
            if 'FinishDateTime' in job_data:
                try:
                    finish_date = datetime.strptime(job_data['FinishDateTime'], '%Y/%m/%d %H:%M:%S')
                    now = datetime.now()
                    if (now - finish_date) <= timedelta(hours=24):
                        jobs.append({
                            'job_name': job_data.get('JobName', 'N/A'),
                            'user': job_data.get('User', 'N/A'),
                            'avg_frame_render_time': job_data.get('AverageFrameRenderTime', 'N/A'),
                            'wasted_error_time': job_data.get('WastedErrorTime', 'N/A'),
                            'finish_date': job_data.get('FinishDateTime', 'N/A'),
                            'pool': job_data.get('Pool', 'N/A'),
                            'plugin': job_data.get('Plugin', 'N/A'),
                            'frame_count': job_data.get('FrameCount', 'N/A'),
                            'error_count': job_data.get('ErrorCount', 'N/A')
                        })
                except ValueError:
                    continue
        
        return jobs
    
    def get_worker_statistics(self):
        """
        Obtient les statistiques des workers via GetSlaveStatistics
        """
        cmd = [self.deadline_cmd, "-GetSlaveStatistics"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            stats = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    stats[key.strip()] = value.strip()
            return stats
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'obtention des stats workers: {e}")
            return {}
        except FileNotFoundError:
            print(f"❌ deadlinecommand introuvable")
            return {}
    
    def generate_html_report(self, jobs: List[Dict], worker_stats: Dict, output_dir: str = r"R:\devMathieu\deadlineStats", output_filename: str = None):
        """
        Génère un rapport HTML avec les statistiques
        
        Args:
            jobs: Liste des jobs complétés
            worker_stats: Statistiques des workers
            output_dir: Dossier de destination (par défaut R:\devMathieu\deadlineStats)
            output_filename: Nom du fichier (par défaut deadline_report_YYYY-MM-DD.html)
        """
        # Créer le dossier s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        # Générer le nom du fichier avec la date
        if output_filename is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_filename = f"deadline_report_{date_str}.html"
        
        # Chemin complet
        output_path = os.path.join(output_dir, output_filename)
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deadline Statistics Report - Dernières 24h</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .timestamp {{
            opacity: 0.8;
            font-size: 0.9em;
        }}
        
        .section {{
            padding: 30px;
        }}
        
        h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-size: 1.8em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        thead {{
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            user-select: none;
            position: relative;
        }}
        
        th:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        th::after {{
            content: ' ⇅';
            opacity: 0.3;
            font-size: 0.8em;
        }}
        
        th.sort-asc::after {{
            content: ' ▲';
            opacity: 1;
        }}
        
        th.sort-desc::after {{
            content: ' ▼';
            opacity: 1;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        tbody tr:hover {{
            background-color: #f7fafc;
            transition: background-color 0.2s;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #718096;
            font-style: italic;
        }}
        
        .error-highlight {{
            color: #e53e3e;
            font-weight: bold;
        }}
        
        .success-highlight {{
            color: #38a169;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Deadline Statistics Report</h1>
            <div class="timestamp">Dernières 24 heures - Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</div>
        </header>
        
        <div class="section">
            <h2>💼 Workers Status</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Rendering</div>
                    <div class="stat-value">{worker_stats.get('Rendering Machines', '0')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Idle</div>
                    <div class="stat-value">{worker_stats.get('Idle Machines', '0')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Stalled</div>
                    <div class="stat-value">{worker_stats.get('Stalled Machines', '0')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Offline</div>
                    <div class="stat-value">{worker_stats.get('OfflineMachines', '0')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Disabled</div>
                    <div class="stat-value">{worker_stats.get('Disabled Machines', '0')}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>✅ Jobs Complétés (24h)</h2>
            {self._generate_jobs_table(jobs)}
        </div>
    </div>
    
    <script>
        // Fonction de tri des tableaux
        function sortTable(table, column, asc = true) {{
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Fonction pour extraire la valeur de tri
            const getValue = (row, col) => {{
                const cell = row.cells[col];
                const text = cell.textContent.trim();
                
                // Essayer de convertir en nombre si possible
                const num = parseFloat(text.replace(/[^\d.-]/g, ''));
                if (!isNaN(num)) return num;
                
                // Sinon retourner le texte
                return text.toLowerCase();
            }};
            
            // Trier les lignes
            rows.sort((a, b) => {{
                const aVal = getValue(a, column);
                const bVal = getValue(b, column);
                
                if (aVal < bVal) return asc ? -1 : 1;
                if (aVal > bVal) return asc ? 1 : -1;
                return 0;
            }});
            
            // Réinsérer les lignes triées
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        // Ajouter les écouteurs d'événements sur les en-têtes
        document.addEventListener('DOMContentLoaded', () => {{
            const table = document.querySelector('table');
            if (!table) return;
            
            const headers = table.querySelectorAll('th');
            let currentSort = {{ column: -1, asc: true }};
            
            headers.forEach((header, index) => {{
                header.addEventListener('click', () => {{
                    // Déterminer la direction du tri
                    const asc = currentSort.column === index ? !currentSort.asc : true;
                    
                    // Retirer les classes de tri précédentes
                    headers.forEach(h => {{
                        h.classList.remove('sort-asc', 'sort-desc');
                    }});
                    
                    // Ajouter la classe appropriée
                    header.classList.add(asc ? 'sort-asc' : 'sort-desc');
                    
                    // Trier
                    sortTable(table, index, asc);
                    
                    // Mémoriser le tri actuel
                    currentSort = {{ column: index, asc }};
                }});
            }});
        }});
    </script>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Rapport HTML généré:")
        print(f"   📁 Dossier: {output_dir}")
        print(f"   📄 Fichier: {output_filename}")
        print(f"   🔗 Chemin complet: {output_path}")
        return output_path
    
    def _generate_jobs_table(self, jobs: List[Dict]) -> str:
        """Génère le tableau HTML des jobs"""
        if not jobs:
            return '<div class="no-data">Aucun job complété dans les dernières 24h</div>'
        
        rows = ""
        for job in jobs:
            error_class = 'error-highlight' if int(job['error_count']) > 0 else ''
            rows += f"""
            <tr>
                <td>{job['job_name']}</td>
                <td>{job['user']}</td>
                <td>{job['avg_frame_render_time']}</td>
                <td class="{error_class}">{job['wasted_error_time']}</td>
                <td>{job['pool']}</td>
                <td>{job['plugin']}</td>
                <td>{job['frame_count']}</td>
                <td class="{error_class}">{job['error_count']}</td>
                <td>{job['finish_date']}</td>
            </tr>"""
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Job Name</th>
                    <th>User</th>
                    <th>Avg Frame Time</th>
                    <th>Wasted Error Time</th>
                    <th>Pool</th>
                    <th>Plugin</th>
                    <th>Frames</th>
                    <th>Errors</th>
                    <th>Finish Date</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <div style="margin-top: 20px; color: #718096;">
            Total: {len(jobs)} job(s) complété(s)
        </div>
        """


def main():
    """Fonction principale"""
    print("=" * 60)
    print("   📊 DEADLINE STATISTICS REPORTER")
    print("=" * 60)
    
    try:
        parser = DeadlineStatsParser()
    except FileNotFoundError as e:
        print(f"\n❌ ERREUR: {e}")
        print("\n💡 Vérifiez que Deadline est installé au bon emplacement")
        return
    
    # Obtenir les mois (n-1 à n+1)
    start_month = parser.get_previous_month()
    end_month = parser.get_next_month()
    current_month = parser.get_current_month()
    
    print(f"\n📅 Période de recherche: {start_month} à {end_month}")
    print(f"   (Mois actuel: {current_month})")
    print(f"\n🔍 Récupération des statistiques...")
    
    # Exécuter la commande JobStatistics
    output = parser.run_job_statistics(start_month, end_month)
    
    if output:
        print(f"\n✅ Données reçues de Deadline ({len(output)} caractères)")
        
        # Parser les jobs
        jobs = parser.parse_job_statistics(output)
        print(f"✅ {len(jobs)} job(s) complété(s) trouvé(s) dans les dernières 24h")
        
        # Obtenir les stats des workers
        print(f"\n🔍 Récupération des stats workers...")
        worker_stats = parser.get_worker_statistics()
        
        # Générer le rapport HTML
        parser.generate_html_report(jobs, worker_stats)
    else:
        print("❌ Impossible de récupérer les statistiques")
        print("\n💡 Pour débugger, testez manuellement:")
        print(f'   & "C:\\Program Files\\Thinkbox\\Deadline10\\bin\\deadlinecommand.exe" -JobStatistics {start_month} {end_month} "" "" ""')


if __name__ == "__main__":
    main()