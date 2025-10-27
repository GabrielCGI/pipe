import importlib


def main():
    from . import publish_daily_report
    importlib.reload(publish_daily_report)
    publish_daily_report.publish()