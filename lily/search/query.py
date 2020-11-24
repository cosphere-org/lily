
# import re

from django.contrib.postgres.search import SearchQuery

from .detector import detector
# from .latex.transformer import transform
from .vector import TextVector
from .constants import HASHTAG_ESCAPE_SEQUENCE, HASHTAG_PATTERN


class Query(SearchQuery):
    """Query object.

    Query object with auto-language detection feature and latex syntax
    parser.

    """

    forbidden_chars = '!"$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    def __init__(self, value, output_field=None, **extra):
        language_conf = detector.detect_db_conf(value)
        self.parsed_value = self.parse_value(value, language_conf)

        super(Query, self).__init__(value, config=language_conf)

    def parse_value(self, text, language_conf):

        # table = str.maketrans(
        #     self.forbidden_chars, len(self.forbidden_chars) * " ")

        # text = transform(text, language_conf)
        # text = text.translate(table).strip()

        # # fetch all hashtags
        hashtags = []

        def remove_hashtag(match):
            hashtags.append(
                HASHTAG_ESCAPE_SEQUENCE + match.group('text'))

            return match.group('prefix') + ' '

        tokens_only_text = HASHTAG_PATTERN.sub(remove_hashtag, text)
        tokens = TextVector().parse_to_list(language_conf, tokens_only_text)

        # if not tokens_only_text.strip():
        #     tokens = []

        # else:
        #     tokens = re.split(r'\s+', tokens_only_text.strip())

        if hashtags and tokens:
            return '{hashtags} & ({tokens})'.format(
                hashtags=' & '.join(hashtags),
                tokens=' | '.join(tokens))

        elif hashtags and not tokens:
            return ' & '.join(hashtags)

        elif not hashtags and tokens:
            return ' | '.join(tokens)

    def as_sql(self, compiler, connection):
        params = [self.parsed_value]

        config_sql, config_params = compiler.compile(self.config)
        template = 'to_tsquery({}::regconfig, %s)'.format(config_sql)
        params = config_params + params

        return template, params
