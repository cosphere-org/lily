
import re


LATEX_PATTERN = re.compile(r'(\$\$(.+?)\$\$)')


MAX_ITERATIONS_COUNT = 20
"""
Maximum number of allowed iterations of transformations loop. Preventing
from looping too much over highly nested formulas.

"""

__PATTERN = r"""
    \s*(?P<%s>
    [0-9A-Za-z]|                           # single number or character
    \\[0-9A-Za-z]+((\s*\{.*\}\s*){1,2})?|  # any latex keyword or expression
                                           # with one or two arguments
                                           # enclosed within {}
    \{\s*.*?\s*\}                          # any expression enclosed within
                                           # { } braces
                                           # or already replaced string
    )%s\s*
"""

ARG_PATTERN = lambda n, o = False: __PATTERN % (n, (o and '?') or '')  # noqa
"""
Pattern of allowed values which can be found as argument of subscripts
operator ``_`` or superscript operator ``^``.

"""


EN_TRIGONOMETRY_FN_NAMES = {
    'sin': 'sine',
    'cos': 'cosine',
    'tan': 'tangent',
    'cot': 'cotangent',
}
PL_TRIGONOMETRY_FN_NAMES = {
    'sin': 'sinus',
    'cos': 'kosinus',
    'tan': 'tangens',
    'cot': 'kotangens',
}

PL = 'polish'
EN = 'english'
SUPPORTED_LANGUAGES = (EN, PL)


DEFAULT_LANGUAGE = 'english'


def decorate_transformations_repl(transformations):

    for transformation in transformations:
        replacements = transformation['replacements']

        for language, replacement in replacements.items():
            is_latex_function = transformation.get('is_latex_function', False)
            shortcut = transformation.get('shortcut', '')
            if isinstance(replacement, str):

                replacement = decorate_str_repl(
                    replacement, is_latex_function, shortcut)

            else:
                replacement = decorate_function_repl(
                    replacement, is_latex_function, shortcut)

            transformation['replacements'][language] = replacement

    return transformations


def decorate_function_repl(fn, is_latex_function, shortcut):

    def inner(m):
        return _decorate_repl(fn(m), is_latex_function, shortcut)

    return inner


def decorate_str_repl(s, is_latex_function, shortcut):
    return _decorate_repl(s, is_latex_function, shortcut)


def _decorate_repl(s, is_latex_function=False, shortcut=None):
    if is_latex_function:
        return r' \\REPL{%s %s} ' % (shortcut, s)
    else:
        return r' %s %s ' % (shortcut, s)


TRANSFORMATIONS = decorate_transformations_repl([

    #
    # Special symbols and modifiers
    #
    {
        'pattern': r'\\infty',
        'shortcut': 'infty',
        'replacements': {
            EN: r'infinity',
            PL: r'nieskończoność',
        },
    },
    {
        'pattern': r'\\dim',
        'shortcut': 'dim',
        'replacements': {
            EN: r'dimension of',
            PL: r'wymiar',
        },
    },
    {
        'pattern': r'\\degree',
        'shortcut': 'degree',
        'replacements': {
            EN: r'degrees',
            PL: r'stopni',
        },
    },
    {
        'pattern': r'\\to',
        'replacements': {
            EN: r'to ',
            PL: r'dążące do',
        },
    },
    {
        'pattern': r'\\limits',
        'replacements': {
            EN: r'in limits',
            PL: r'w granicach',
        },
    },

    #
    # Accent Functions
    #
    {
        'pattern': r'\\vec',
        'replacements': {
            EN: r'vector',
            PL: r'wektor',
        },
    },
    {
        'pattern': r'\\dot',
        'replacements': {
            EN: r'time derivative of',
            PL: r'pochodna po czasie z',
        },
    },
    {
        'pattern': r'\\bar',
        'replacements': {
            EN: r'average',
            PL: r'średnia',
        },
    },
    {
        'pattern': r'\\hat',
        'replacements': {
            EN: r'operator',
            PL: r'operator',
        },
    },


    #
    # Arithmetic
    #
    {
        'pattern': r'\+',
        'replacements': {
            EN: r'plus',
            PL: r'plus',
        },
    },
    {
        'pattern': r'\-',
        'replacements': {
            EN: r'minus',
            PL: r'minus',
        },
    },
    {
        'pattern': r'\*',
        'replacements': {
            EN: r'times',
            PL: r'razy mnożone przez',
        },
    },
    {
        'pattern': r'\\times',
        'replacements': {
            EN: r'times',
            PL: r'razy mnożone przez',
        },
    },
    {
        'pattern': r'\/',
        'replacements': {
            EN: r'divided by',
            PL: r'dzielone przez',
        }
    },
    {
        'pattern': r'\=',
        'replacements': {
            EN: r'equals to ',
            PL: r'równa się',
        },
    },
    {
        'pattern': r'\\neq',
        'replacements': {
            EN: r'not equals to ',
            PL: r'jest różne od',
        },
    },

    #
    # Number Relations
    #
    {
        'pattern': r'\\approx',
        'replacements': {
            EN: r'is approximately',
            PL: r'równa się w przybliżeniu',
        },
    },
    {
        'pattern': r'\\leq',
        'replacements': {
            EN: r'is less than equal to',
            PL: r'jest mniejsze lub równe',
        },
    },
    {
        'pattern': r'\\ll',
        'replacements': {
            EN: r'is much smaller than',
            PL: r'jest dużo mniejsze niż',
        },
    },
    {
        'pattern': r'\\geq',
        'replacements': {
            EN: r'is greater than equal to',
            PL: r'jest większe lub równe',
        },
    },
    {
        'pattern': r'\\gg',
        'replacements': {
            EN: r'is much greater than',
            PL: r'jest dużo większe niż',
        },
    },

    #
    # Fractions
    #
    {
        'pattern': r'\\[td]?frac{(.*)}{(.*)}',
        'is_latex_function': True,
        'replacements': {
            EN: r'fraction \1 divided by \2',
            PL: r'ułamek \1 dzielone przez \2',
        },
    },
    {
        'pattern': (
            r'\{' +
            ARG_PATTERN('num') +
            r'\\over' +
            ARG_PATTERN('den') +
            r'\}'),
        'is_latex_function': True,
        'replacements': {
            EN: r'fraction \g<num> divided by \g<den>',
            PL: r'ułamek \g<num> dzielone przez \g<den>',
        },
    },

    #
    # Complex Numbers
    #
    {
        'pattern': r'\\Im',
        'is_latex_function': True,
        'replacements': {
            EN: r'imaginary part of',
            PL: r'część urojona zespolona z',
        },
    },
    {
        'pattern': r'\\Re',
        'is_latex_function': True,
        'replacements': {
            EN: r'real part of',
            PL: r'część rzeczywista z',
        },
    },

    #
    # Exponentiation and Polynomials
    #

    # square
    {
        'pattern': r'\^\s*(2|\{\s*2\s*\})',
        'replacements': {
            EN: r'squared',
            PL: r'do kwadratu',
        },
    },

    # general numerical exponent
    {
        'pattern': (
            r'\^\s*('
            r'[0-13-9]+|'
            r'\{\s*[0-13-9]+\s*\}|'
            r'\{\s*(minus|plus|\+|\-)\s*[0-9]+\s*\}'
            r')'
        ),
        'replacements': {
            EN: r'to the power of \1',
            PL: r'podniesione do potęgi \1',
        },
    },

    # square root
    {
        'pattern': r'\\sqrt',
        'shortcut': 'sqrt',
        'is_latex_function': True,
        'replacements': {
            EN: r'square root function of',
            PL: r'funkcja pierwiastek kwadratowy z',
        },
    },

    #
    # Calculus
    #

    # limits
    {
        'pattern': r'\\lim(?!s|i)+',
        'shortcut': 'lim',
        'replacements': {
            EN: r'limit',
            PL: r'granica',
        },
    },
    {
        'pattern': r'\\liminf',
        'shortcut': 'liminf',
        'replacements': {
            EN: r'infimum limit',
            PL: r'granica infimum',
        },
    },
    {
        'pattern': r'\\limsup',
        'shortcut': 'limsup',
        'replacements': {
            EN: r'supremum limit',
            PL: r'granica supremum',
        },
    },
    {
        'pattern': r'\\inf',
        'shortcut': 'inf',
        'replacements': {
            EN: r'infimum of',
            PL: r'infimum z',
        },
    },
    {
        'pattern': r'\\sup',
        'shortcut': 'sup',
        'replacements': {
            EN: r'supremum of',
            PL: r'supremum z',
        },
    },
    {
        'pattern': r'\\max',
        'shortcut': 'max',
        'replacements': {
            EN: r'maximum of',
            PL: r'maksimum z',
        },
    },
    {
        'pattern': r'\\min',
        'shortcut': 'min',
        'replacements': {
            EN: r'minimum of',
            PL: r'minimum z',
        },
    },



    # sums
    {
        'pattern': r'\\sum',
        'shortcut': 'sum',
        'replacements': {
            EN: r'sum of',
            PL: r'suma',
        },
    },

    # products
    {
        'pattern': r'\\prod',
        'shortcut': 'prod',
        'replacements': {
            EN: r'product of',
            PL: r'iloczyn',
        },
    },

    # derivatives
    {
        'pattern': r'\\partial',
        'shortcut': 'partial',
        'replacements': {
            EN: r'partial derivative',
            PL: r'pochodna cząstkowa',
        },
    },

    # indefinite integral
    {
        'pattern': (
            r'\\((?P<o>o)?i{0,3}int(?!o)|smallint|intop)\s*'
            r'(?P<rest>[^_^]+)'),
        'shortcut': 'int',
        'replacements': {
            EN: (
                lambda m: '{o} indefinite integral of {rest}'.format(
                    o=(m.group('o') and 'countour') or '',
                    rest=m.group('rest'))),
            PL: (
                lambda m: 'całka nieoznaczona {o} z {rest}'.format(
                    o=(m.group('o') and 'po konturze') or '',
                    rest=m.group('rest'))),
        },
    },

    # definite integral
    # \int_A?^B pattern
    {
        'pattern': (
            r'\\((?P<o>o)?i{0,3}int(?!o)|smallint|intop)\s*' +
            r'\_' + ARG_PATTERN('sub') +
            r'\^?' + ARG_PATTERN('sup', True)),
        'shortcut': 'int',
        'is_latex_function': True,
        'replacements': {
            EN: (
                lambda m: (
                    r'{o} definite integral from {sub} to {sup} of'.format(
                        o=(m.group('o') and 'countour') or '',
                        sub=m.group('sub'),
                        sup=m.group('sup')))),
            PL: (
                lambda m: (
                    r'całka oznaczona {o} od {sub} do {sup} z'.format(
                        o=(m.group('o') and 'po konturze') or '',
                        sub=m.group('sub'),
                        sup=m.group('sup')))),
        },
    },

    # \int^B_A pattern
    {
        'pattern': (
            r'\\((?P<o>o)?i{0,3}int(?!o)|smallint|intop)\s*' +
            r'\^' + ARG_PATTERN('sup') +
            r'\_?' + ARG_PATTERN('sub', True)),
        'shortcut': 'int',
        'is_latex_function': True,
        'replacements': {
            EN: (
                lambda m: (
                    r'{o} definite integral from {sub} to {sup} of'.format(
                        o=(m.group('o') and 'countour') or '',
                        sub=m.group('sub'),
                        sup=m.group('sup')))),
            PL: (
                lambda m: (
                    r'całka oznaczona {o} od {sub} do {sup} z'.format(
                        o=(m.group('o') and 'po konturze') or '',
                        sub=m.group('sub'),
                        sup=m.group('sup')))),
        },
    },

    #
    # Greek letters
    #
    {
        'pattern': r'\\alpha',
        'is_latex_function': True,
        'replacements': {
            EN: r'alpha',
            PL: r'alfa',
        },
    },
    {
        'pattern': r'\\pi',
        'is_latex_function': True,
        'replacements': {
            EN: r'number pi',
            PL: r'liczba pi',
        },
    },
    {
        'pattern': r'\\Delta',
        'is_latex_function': True,
        'replacements': {
            EN: r'change delta of',
            PL: r'zmiana delta',
        },
    },
    {
        'pattern': r'\\Nabla',
        'replacements': {
            EN: r'divergence nabla of',
            PL: r'dywergencja nabla',
        },
    },

    #
    # Logarithms and Exponent functions
    #
    {
        'pattern': r'\\exp',
        'shortcut': 'exp',
        'replacements': {
            EN: 'exponent function of',
            PL: 'funkcja wykładnicza z',
        },
    },
    {
        'pattern': r'\\ln',
        'shortcut': 'ln',
        'replacements': {
            EN: 'natural logarithm function of',
            PL: 'funkcja logarytm naturalny z',
        },
    },
    {
        'pattern': r'\\log',
        'shortcut': 'log',
        'replacements': {
            EN: 'logarithm function of',
            PL: 'funkcja logarytm z',
        },
    },

    #
    # Trigonometry
    #
    # Since trigonometrical functions are using rather complex
    # pattern one inject their shortcut directly inside the repl
    {
        'pattern': r'\\(?P<arc>arc)?(?P<fn>sin|cos|cot|tan)(?P<h>h)?',
        'replacements': {
            EN: lambda m: r'{s} {arc}{h} {fn} function of'.format(
                arc=(m.group('arc') and 'inverse arc') or '',
                h=(m.group('h') and 'hyperbolic') or '',
                s=(
                    (m.group('arc') or '') +
                    m.group('fn') +
                    (m.group('h') or '')),
                fn=EN_TRIGONOMETRY_FN_NAMES.get(m.group('fn'), '')),
            PL: lambda m: r'{s} funkcja {arc} {fn} {h} z'.format(
                arc=(m.group('arc') and 'arkus') or '',
                h=(m.group('h') and 'hiperboliczny') or '',
                s=(
                    (m.group('arc') or '') +
                    m.group('fn') +
                    (m.group('h') or '')),
                fn=PL_TRIGONOMETRY_FN_NAMES.get(m.group('fn'), '')),
        },
    },

    #
    # Binomials
    #
    {
        'pattern': r'!',
        'replacements': {
            EN: r'factorial',
            PL: r'silnia',
        },
    },
    {
        'pattern': (
            r'\\[td]?binom' +
            ARG_PATTERN('up') +
            ARG_PATTERN('down')),
        'shortcut': 'binom',
        'is_latex_function': True,
        'replacements': {
            EN: r'binomial \g<up> choose \g<down>',
            PL: r'kombinacja \g<up> nad \g<down>'
        },
    },
    {
        'pattern': (
            r'\{' +
            ARG_PATTERN('up') +
            r'\\choose' +
            ARG_PATTERN('down') +
            r'\}'),
        'shortcut': 'choose',
        'is_latex_function': True,
        'replacements': {
            EN: r'binomial \g<up> choose \g<down>',
            PL: r'kombinacja \g<up> nad \g<down>',
        },
    },

    #
    # FUTURE: matrix notation
    #
    # Spec: should be able to parse simple matrix
    # Spec: should be able to parse matrix multiplication and other operations

    #
    # FUTURE: tensor notation
    #
    # Spec: Should be able to parse Einstein's general relativity equations
    # Spec: Should be able to parse Maxwell's equations written in tensor form
    # Spec: Should be able to parse Standard Model Lagrangian

    #
    # FUTURE: logic
    #
    # TODO: \forall \exists \nexists \therefore \because \equiv, \bigvee,
    # \bigwedge

])


def transform(text, language):
    """Transform provided text.

    Transform provided text by injecting after each occurrence of LaTeX
    syntax its human readable representation in a language of the text.

    """

    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE

    formulas = LATEX_PATTERN.findall(text)
    for raw_formula, formula_inner in set(formulas):
        text = text.replace(
            raw_formula,
            _transform_formula(formula_inner, language))

    return re.sub(r'\s+', ' ', text.strip())


def _transform_formula(formula, language):
    """Transform single LaTeX formula.

    Transform single LaTeX formula by iteratively replacing all occurrences
    of handled patterns and replacing them with human readable phrases.

    It has builtin maximum iteration mechanism which prevents parser
    from doing too many loops of replacement (loop which are meant to
    catch all nested formulas).

    """
    # initial cleaning
    formula = formula.replace('(', ' ').replace(')', ' ')

    iteration_no = 0
    current_transformations = TRANSFORMATIONS
    while current_transformations:
        next_transformations = []
        iteration_no += 1

        for transformation in current_transformations:

            formula, replacement_count = re.subn(
                transformation['pattern'],
                transformation['replacements'][language],
                formula.strip(),
                flags=re.VERBOSE)

            if replacement_count:
                next_transformations.append(transformation)

        current_transformations = next_transformations
        if iteration_no >= MAX_ITERATIONS_COUNT:
            break

    # final cleaning
    return re.sub(r'(REPL|\{|\}|\\|\,|\_|\^)', ' ', formula)
