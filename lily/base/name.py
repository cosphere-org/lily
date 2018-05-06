# -*- coding: utf-8 -*-

import re


IRREGULAR_FORMS = {
    'break': 'broke',
    'buy': 'bought',
    'come': 'came',
    'eat': 'ate',
    'feel': 'felt',
    'get': 'got',
    'go': 'went',
    'hear': 'heard',
    'is': 'was',
    'lose': 'lost',
    'make': 'made',
    'pay': 'paid',
    'see': 'saw',
    'sing': 'sang',
    'sit': 'sat',
    'sleep': 'slept',
    'teach': 'taught',
    'tell': 'told',
    'understand': 'understood',
}


EXCEPTION_FORMS = {
    'refer': 'referred',
}


SINGLE_FORMS = set([
    'broadcast',
    'cost',
    'cut',
    'hit',
    'hurt',
    'let',
    'put',
    'quit',
    'read',
    'spread',
])


VOWELS = set(['a', 'e', 'i', 'o', 'u', 'y'])


END_HUSHERS = set([
    'ch',
    'ck',
    'h',
    'k',
    'lk',
    'lp',
    'nt',
    'sh',
    'st',
    'wn',
    'x',
])


def to_past(verb):

    verb = verb.lower()
    if verb in IRREGULAR_FORMS:
        return IRREGULAR_FORMS[verb]

    elif verb in EXCEPTION_FORMS:
        return EXCEPTION_FORMS[verb]

    elif verb in SINGLE_FORMS:
        return verb

    # -- last letter is `e`
    elif verb[-1] == 'e':
        return verb + 'd'

    # -- last letter is `y`
    elif verb[-1] == 'y':
        if verb[-2] in VOWELS:
            return verb + 'ed'

        else:
            return verb[:-1] + 'ied'

    elif needs_double_consonant(verb):
        return verb + verb[-1] + 'ed'

    else:
        return verb + 'ed'


def needs_double_consonant(verb):

    vowels_count = len([letter for letter in verb if letter in VOWELS])

    return not (
        vowels_count > 1 or         # -- is monosyllabic word
        verb[-1] in END_HUSHERS or   # -- last letter is husher
        verb[-2:] in END_HUSHERS or  # -- last two letters are hushers
        verb[-1] == verb[-2]         # -- last two letters already repeated
    )


class BaseVerb:

    verb = NotImplemented

    def __init__(self, noun):

        # -- verb
        self.verb = self.transform(self.verb)

        # -- past_verb
        self.past_verb = self.transform(to_past(self.verb))

        # -- noun
        if isinstance(noun, str):
            self.noun = self.transform(noun)

        else:
            self.noun = self.transform(noun._meta.model_name)

    def render_command_name(self):

        return '{verb}_{noun}'.format(
            verb=self.verb, noun=self.noun)

    def render_event_name(self):

        return '{noun}_{past_verb}'.format(
            past_verb=self.past_verb, noun=self.noun)

    def transform(self, name):
        name = name.upper()
        name = re.sub('\s+', '_', name)
        name = re.sub('\_{2,}', '_', name)

        return name

    @property
    def after(self):
        return Conjunction(effect=self)


class Conjunction:

    def __init__(self, effect):
        self.effect = effect
        self.Create = self.wrap(Create)
        self.Read = self.wrap(Read)
        self.List = self.wrap(List)
        self.Upsert = self.wrap(Upsert)
        self.Update = self.wrap(Update)
        self.Delete = self.wrap(Delete)
        self.Execute = self.wrap(Execute)

    def wrap(self, cls):

        class Wrapper:
            def __init__(other, *args, **kwargs):
                self.cause = cls(*args, **kwargs)

            def render_command_name(other):
                return '{effect}_AFTER_{cause}'.format(
                    effect=self.effect.render_command_name(),
                    cause=self.cause.render_command_name())

            def render_event_name(other):
                return '{effect}_AFTER_{cause}'.format(
                    effect=self.effect.render_event_name(),
                    cause=self.cause.render_event_name())

        return Wrapper


class Execute(BaseVerb):

    verb = NotImplemented

    def __init__(self, verb, noun):
        self.verb = verb

        super(Execute, self).__init__(noun)


class Create(BaseVerb):

    verb = 'create'


class Upsert(BaseVerb):

    verb = 'upsert'


class Read(BaseVerb):

    verb = 'read'


class List(BaseVerb):

    verb = 'list'


class Update(BaseVerb):

    verb = 'update'


class Delete(BaseVerb):

    verb = 'delete'
