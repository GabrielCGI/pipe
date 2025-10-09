import numpy
import matplotlib.pyplot as plt

import deadline_stats_parser

def convertTime(time: str) -> int:
    """Expected format: 00d 00h 00m 00s


    Args:
        time (str): times written in expected format str.

    Returns:
        int: time in second
    """    
    times = [i for i in  map(lambda x: x[:-1], time.split())]
    
    days = times[0]
    hours = times[1]
    minutes = times[2]
    seconds = times[3]
    
    total_times = (
        days*86400
        + hours*3600
        + minutes*600
        + seconds
    )
    
    return total_times


def drawPlot(times: list[int]):
    pass

def main():
    
    try:
        parser = deadline_stats_parser.DeadlineStatsParser()
    except FileNotFoundError as e:
        print(f"ERREUR: {e}")
        print("\nVerifiez que Deadline est installe au bon emplacement")
        return
    
    # Obtenir les mois (n-1 à n+1)
    start_month = parser.get_previous_month()
    end_month = parser.get_next_month()
    current_month = parser.get_current_month()
    
    print(f"\nPeriode de recherche: {start_month} à {end_month}")
    print(f"   (Mois actuel: {current_month})")
    print(f"\nRecuperation des statistiques...")
    
    # Executer la commande JobStatistics
    output = parser.run_job_statistics(start_month, end_month)
    
    if output:
        print(f"\nDonnees reçues de Deadline ({len(output)} caractères)")
        
        # Parser les jobs
        jobs = parser.parse_job_statistics(output)
        times = []
        for job in jobs:
            wasted_time = job.get("wasted_error_time", '00d 00h 00m 00s')
            times.append(convertTime(wasted_time))
        
        
        np_times = numpy.array(times)            
        fig, ax = plt.plot()
        ax.plot()
            
        print(f"{len(jobs)} job(s) complete(s) trouve(s) dans les dernières 24h")
        
    else:
        print("Impossible de recuperer les statistiques")
        print("\nPour debugger, testez manuellement:")
        print(f'   & "C:\\Program Files\\Thinkbox\\Deadline10\\bin\\deadlinecommand.exe" -JobStatistics {start_month} {end_month} "" "" ""')


if __name__ == "__main__":
    main()