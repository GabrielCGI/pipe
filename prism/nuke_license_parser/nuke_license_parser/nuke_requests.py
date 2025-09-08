import sys

REQUEST_DEPS_PATH = "R:/pipeline/networkInstall/python_shares/python311_nuke_requets_pkgs/Lib/site-packages"
if not REQUEST_DEPS_PATH in sys.path:
    sys.path.append(REQUEST_DEPS_PATH)

import requests
import bs4

sys.path.remove(REQUEST_DEPS_PATH)

URL = '10.16.34.37:4102'
PARAMS = {
    'wb': 'rlmstat',
    'isv': 'foundry',
    'instance': '0'
}
USAGE_URL = f"http://{URL}/goform/rlmstat_lic_process"
SESSION = requests.Session()
TIMEOUT = 3.05
MAX_WORKERS = 4


def parse_params(row: bs4.element.Tag):
    forms = row.find_all('form')
    if not forms:
        return {}
    
    usage_form = forms[0]
    usage_params = {}
    for input in usage_form.find_all('input'):
        name = input.attrs.get('name')
        value = input.attrs.get('value')
        if name is None or value is None:
            continue
        usage_params[name] = value
    return usage_params


def parse_user(usage_requests: requests.models.Response):
    if usage_requests.status_code != 200:
        return None
    
    soup = bs4.BeautifulSoup(usage_requests.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return None
    
    usage_table = tables[0]
    row = usage_table.find_all("tr")[1]
    cells = [td.text.strip() for td in row.find_all("td")]
    user = cells[3]
    return user


def query_entry(item: tuple):
    _, license_data = item
    usage_params = license_data.get('query_params')
    if usage_params is None:
        return
    usage_request = SESSION.get(
        USAGE_URL,
        params=usage_params,
        timeout=TIMEOUT
    )
    license_data['usage_request'] = usage_request


def query_usage(licenses_data: dict):
    for item in licenses_data.items():
        query_entry(item)
 

def parse_license(request: requests.models.Response):
    
    soup = bs4.BeautifulSoup(request.text, 'html.parser')
    tables = soup.find_all('table')
    
    if len(tables) < 3:
        return {}
    
    license_table = tables[2]
    licenses_data = {}
    
    for row in license_table.find_all("tr")[1:]:
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) < 12:
            continue
        license_type = cells[0]
        if license_type != 'nuke_i':
            continue
        pool = cells[1]
        state = cells[3] # TODO Check if the license is permanent (so limited to nuke 13.x)
        inuse = cells[6]
        licenses_data[pool] = {
            'used': bool(int(inuse))
        }
        if state == 'permanent':
            licenses_data[pool]['limited'] = True
        else:
            licenses_data[pool]['limited'] = False 
        if inuse != '1':
            continue
        usage_params = parse_params(row)
        if len(usage_params):
            licenses_data[pool]['query_params'] = usage_params
                 
    query_usage(licenses_data)
    
    for pool in licenses_data:
        license_data = licenses_data[pool]
        usage_request = license_data.get('usage_request')
        if usage_request is None:
            continue
        user = parse_user(usage_request)
        if user is None:
            continue
        user = user.replace('.', ' ').title().replace(' ', '.')
        license_data['user'] = user
        
    for pool in licenses_data:
        license_data = licenses_data[pool]
        try:
            del license_data['query_params']
        except:
            pass
        try:
            del license_data['usage_request']
        except:
            pass
        
    return licenses_data


def main():
    url_license = f'http://{URL}/goform/rlmstat_isv'
    license_request = SESSION.get(
            url_license,
            params=PARAMS,
            timeout=TIMEOUT
        )
    if license_request.status_code != 200:
        print(
            'Could not access license rlm site.'
            f'/nStatus Code: {license_request.status_code}'
        )
        
    licenses_data = parse_license(license_request)
    return licenses_data


if __name__ == '__main__':
    data = main()