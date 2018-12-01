
import os

from yaml import load


BASE_DIR = os.path.dirname(__file__)


LATEX_CASES = load(open(os.path.join(BASE_DIR, 'latex_cases.yaml'), 'r'))
