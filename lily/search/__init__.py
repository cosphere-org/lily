# -*- coding: utf-8 -*-

from .query import Query
from .rank import Rank, RankCD
from .vector import (
    StoredVector,
    OnTheFlyVector,
    to_tsvector,
    concatenate_tsvectors,
)
from .detector import get_search_conf_language
from .latex.transformer import transform as transform_latex
