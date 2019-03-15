
import os

import yaml


BASE_DIR = os.path.dirname(__file__)


LATEX_CASES = yaml.load(
    open(os.path.join(BASE_DIR, 'latex_cases.yaml'), 'r'),
    Loader=yaml.FullLoader)
