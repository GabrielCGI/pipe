import datetime
import sys

BS4_MODULE_PATH = (
    "R:/pipeline/networkInstall/python_shares/"
    "python311_nuke_requets_pkgs/Lib/site-packages")
if not BS4_MODULE_PATH in sys.path:
    sys.path.append(BS4_MODULE_PATH)

import bs4


def build_header(soup: bs4.BeautifulSoup):
    header = soup.body.header
    if header is None:
        return False
    timestamp = soup.new_tag('div', attrs={'class':'timestamp'})
    timestamp.string = (
        f'Dernieres 24 heures - Genere le '
        f'{datetime.datetime.now().strftime("%d/%m/%Y a %H:%M:%S")}'
    )
    header.append(timestamp)
    return True
    

def build_worker_stats(soup: bs4.BeautifulSoup, worker_stats: dict):
    grid_stats_div = soup.body.find('div', class_='stats-grid')
    if grid_stats_div is None:
        return False
    for key, value in worker_stats.items():
        div_card = soup.new_tag('div', attrs={'class':'stat-card'})
        div_label = soup.new_tag('div', attrs={'class':'stat-label'})
        div_value = soup.new_tag('div', attrs={'class':'stat-value'})
        div_label.string = key
        div_value.string = value
        grid_stats_div.append(div_card)
        div_card.append(div_label)
        div_card.append(div_value)
    return True


def build_html(template, output_html, worker_stats):
    with open(template, 'r') as template_file:
        soup = bs4.BeautifulSoup(template_file, "html.parser")
    
    if not build_header(soup):
        print('Could not build header')
    
    if not build_worker_stats(soup, worker_stats):
        print('Could not build worker stats div')

    with open(output_html, 'w') as html_file:
        html_file.write(soup.prettify())

    return True
        
        
if __name__ == '__main__':
    template = "R:/pipeline/pipe/deadline/daily_report/empty_body_template.html"
    output_path = "R:/pipeline/pipe/deadline/daily_report/filled_report.html"
    worker_stats = {
        'Rendering': '12',
        'Idle': '3',
        'Stalled': '3',
        'Offline': '5',
        'Disabled': '1'
    }
    build_html(template, output_path, worker_stats)