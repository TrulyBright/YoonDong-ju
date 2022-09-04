import os
import json


def pytest_configure(config):
    if os.environ["CI"]:
        with open("local.settings.json", encoding="utf-8") as f:
            for key, value in json.load(f)["Values"].items():
                os.environ[key] = value
