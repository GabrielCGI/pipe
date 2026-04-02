import os

import requests  # noqa: E402
import bs4  # noqa: E402
from dotenv import load_dotenv

load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
)

ILLOGIC_RLM_URL = os.environ.get("ILLOGIC_RLM_URL")
PORT_NUKE = os.environ.get("PORT_NUKE")
PORT_NUKE_13 = os.environ.get("PORT_NUKE_13")
PARAMS = {"wb": "rlmstat", "isv": "foundry", "instance": "0"}
USAGE_URL = f"http://{ILLOGIC_RLM_URL}/goform/rlmstat_lic_process"
SESSION = requests.Session()
TIMEOUT = 3.05
MAX_WORKERS = 4


def parse_params(row: bs4.element.Tag):
    forms = row.find_all("form")
    if not forms:
        return {}

    usage_form = forms[0]
    usage_params = {}
    for input in usage_form.find_all("input"):
        name = input.attrs.get("name")
        value = input.attrs.get("value")
        if name is None or value is None:
            continue
        usage_params[name] = value
    return usage_params


def parse_users(usage_requests: requests.models.Response):
    if usage_requests.status_code != 200:
        return None

    soup = bs4.BeautifulSoup(usage_requests.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return None

    usage_table = tables[0]
    users = set()
    for row in usage_table.find_all("tr")[1:]:
        cells = [td.text.strip() for td in row.find_all("td")]
        try:
            users.add(cells[3])
        except IndexError:
            continue

    return sorted(list(users))


def parse_handles(usage_requests: requests.models.Response, user: str):
    if usage_requests.status_code != 200:
        return None

    soup = bs4.BeautifulSoup(usage_requests.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return None

    handles = []
    usage_table = tables[0]
    rows = usage_table.find_all("tr")
    # skip header row if present
    for row in rows[1:]:
        cells = row.find_all("td")
        if not cells:
            continue
        user_cell = cells[3]
        if user_cell.text.strip() == user:
            last_td = cells[-1]
            handle_input = last_td.find("input", attrs={"name": "handle"})
            handle = handle_input["value"]
            handles.append(handle)
    return handles


def query_entry(item: tuple):
    _, license_data = item
    usage_params = license_data.get("query_params")
    if usage_params is None:
        return
    usage_request = SESSION.get(USAGE_URL, params=usage_params, timeout=TIMEOUT)
    license_data["usage_request"] = usage_request


def query_usage(licenses_data: dict):
    for item in licenses_data.items():
        query_entry(item)


def parse_license(request: requests.models.Response):

    soup = bs4.BeautifulSoup(request.text, "html.parser")
    tables = soup.find_all("table")

    if len(tables) < 3:
        return {}

    license_table = tables[2]
    licenses_data = {}

    for row in license_table.find_all("tr")[1:]:
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) < 12:
            continue
        license_type = cells[0]
        if license_type not in ["nuke_i", "nukex_i", "nukestudio_i"]:
            continue
        id = cells[2]
        state = cells[3]
        count = int(cells[4])
        inuse = cells[6]

        license_data = {}
        if count > 1:
            if f"{id}.0" in licenses_data:
                continue
            for license_index in range(count):
                license_data = licenses_data.setdefault(f"{id}.{license_index}", {})
        else:
            license_data = licenses_data.setdefault(id, {})

        license_data["used"] = bool(int(inuse))

        if state == "permanent":
            license_data["limited"] = True
        else:
            license_data["limited"] = False
        try:
            inuse = int(inuse)
        except ValueError:
            continue
        if inuse <= 0:
            continue
        usage_params = parse_params(row)
        if len(usage_params):
            license_data["query_params"] = usage_params
            query_entry((id, license_data))
            usage_request = license_data.get("usage_request")
            users = parse_users(usage_request)
            if users is None:
                continue
            for i, user in enumerate(users):
                license_data_copy = license_data.copy()
                if count > 1:
                    licenses_data[f"{id}.{i}"] = license_data_copy
                else:
                    licenses_data[id] = license_data_copy
                handles = parse_handles(usage_request, user)
                license_data_copy["handles"] = handles

                user = user.replace(".", " ").title().replace(" ", ".")
                license_data_copy["user"] = user

    for id in licenses_data:
        license_data = licenses_data[id]
        try:
            del license_data["query_params"]
        except KeyError:
            pass
        try:
            del license_data["usage_request"]
        except KeyError:
            pass

    return licenses_data


def getData(domain):
    global USAGE_URL
    USAGE_URL = f"http://{domain}/goform/rlmstat_lic_process"
    url_license = f"http://{domain}/goform/rlmstat_isv"
    license_request = SESSION.get(url_license, params=PARAMS, timeout=TIMEOUT)
    if license_request.status_code != 200:
        print(
            "Could not access license rlm site."
            f"/nStatus Code: {license_request.status_code}"
        )

    licenses_data = parse_license(license_request)
    return licenses_data


def main():
    nuke_13_datas = getData(f"{ILLOGIC_RLM_URL}:{PORT_NUKE_13}")
    nuke_datas = getData(f"{ILLOGIC_RLM_URL}:{PORT_NUKE}")

    for key, value in nuke_13_datas.items():
        nuke_datas[key] = value

    return nuke_datas


if __name__ == "__main__":
    data = main()
