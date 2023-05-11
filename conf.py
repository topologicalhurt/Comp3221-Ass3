from json import load


class Config:
    """Creates namespace dynamically from config file"""
    def __init__(self):
        with open('conf.json', 'r') as f:
            data = load(f)
        for k, v in data.items():
            setattr(self, k, v)
