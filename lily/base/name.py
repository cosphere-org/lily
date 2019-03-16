
import re

import inflect

from .events import EventFactory


INFLECT_ENGINE = inflect.engine()


IRREGULAR_FORMS = {
    'break': 'broke',
    'broadcast': 'broadcast',
    'buy': 'bought',
    'come': 'came',
    'cost': 'cost',
    'cut': 'cut',
    'eat': 'ate',
    'feel': 'felt',
    'get': 'got',
    'go': 'went',
    'hear': 'heard',
    'hit': 'hit',
    'hurt': 'hurt',
    'is': 'was',
    'let': 'let',
    'lose': 'lost',
    'make': 'made',
    'pay': 'paid',
    'put': 'put',
    'quit': 'quit',
    'read': 'read',
    'reset': 'reset',
    'reset': 'reset',
    'see': 'saw',
    'send': 'sent',
    'sing': 'sang',
    'sit': 'sat',
    'sleep': 'slept',
    'spread': 'spread',
    'teach': 'taught',
    'tell': 'told',
    'understand': 'understood',
}


EXCEPTION_FORMS = {
    'refer': 'referred',
}


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


def to_plural(noun):
    """Forgiving plural form transformer.

    If the `noun` is already in the plural form no transformation will be
    applied.

    """
    if not INFLECT_ENGINE.singular_noun(noun):
        return INFLECT_ENGINE.plural(noun)

    return noun


def to_past(verb):

    verb = verb.lower()
    if verb in IRREGULAR_FORMS:
        return IRREGULAR_FORMS[verb]

    elif verb in EXCEPTION_FORMS:
        return EXCEPTION_FORMS[verb]

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

    finalizers = NotImplemented

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

    def render_event_name(self, request=None, e=None):

        if request and e:
            if not isinstance(e, self.finalizers):
                raise EventFactory.BrokenRequest(
                    event=(
                        'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_'
                        'DETECTED'),
                    context=request)

            return '{noun}_{past_verb}'.format(
                past_verb=self.transform(e.verb or e.__class__.__name__),
                noun=self.noun)

        else:
            return '{noun}_{past_verb}'.format(
                past_verb=self.past_verb,
                noun=self.noun)

    def transform(self, name):
        name = name.upper()
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'\_{2,}', '_', name)

        return name

    @property
    def after(self):
        return Conjunction(effect=self)


class BaseBulkVerb(BaseVerb):

    def __init__(self, noun):

        if not isinstance(noun, str):
            noun = noun._meta.model_name

        super(BaseBulkVerb, self).__init__(to_plural(noun))


class Conjunction:

    def __init__(self, effect):
        self.effect = effect

        # -- Generic Execute
        self.Execute = self.phrase(Execute, effect)

        # -- CRUD
        self.Create = self.phrase(Create, effect)
        self.Read = self.phrase(Read, effect)
        self.Update = self.phrase(Update, effect)
        self.Delete = self.phrase(Delete, effect)

        # -- BULK CRUD
        self.BulkCreate = self.phrase(BulkCreate, effect)
        self.BulkRead = self.phrase(BulkRead, effect)
        self.BulkUpdate = self.phrase(BulkUpdate, effect)
        self.BulkDelete = self.phrase(BulkDelete, effect)

        # -- CONDITIONAL CRUD
        self.CreateOrUpdate = self.phrase(CreateOrUpdate, effect)
        self.CreateOrRead = self.phrase(CreateOrRead, effect)

    def phrase(self, cause_cls, effect):

        class Phrase:

            effect = None

            def __init__(other, *args, **kwargs):  # noqa
                self.cause = cause_cls(*args, **kwargs)

            def render_command_name(other):  # noqa
                return '{effect}_AFTER_{cause}'.format(
                    effect=self.effect.render_command_name(),
                    cause=self.cause.render_command_name())

            def render_event_name(other, request, e):  # noqa
                return '{effect}_AFTER_{cause}'.format(
                    effect=self.effect.render_event_name(request, e),
                    cause=self.cause.render_event_name())

        Phrase.effect = effect
        return Phrase


class ConstantName(BaseVerb):

    def __init__(self, command_name):
        self.command_name = command_name

    def render_command_name(self):
        return self.transform(self.command_name)

    def render_event_name(self, request, e):

        return self.transform(e.event)


class Execute(BaseVerb):

    verb = NotImplemented

    finalizers = (EventFactory.Executed,)

    def __init__(self, verb, noun):
        self.verb = verb

        super(Execute, self).__init__(noun)

    def render_event_name(self, request=None, e=None):

        if request and e:
            if not isinstance(e, self.finalizers):
                raise EventFactory.BrokenRequest(
                    event=(
                        'INVALID_FINALIZER_USED_FOR_SPECIFIC_COMMAND_'
                        'DETECTED'),
                    context=request)

        return '{noun}_{past_verb}'.format(
            past_verb=self.past_verb,
            noun=self.noun)


#
# CRUD
#
class Create(BaseVerb):

    finalizers = (EventFactory.Created,)

    verb = 'create'


class Read(BaseVerb):

    finalizers = (EventFactory.Read,)

    verb = 'read'


class Update(BaseVerb):

    finalizers = (EventFactory.Updated,)

    verb = 'update'


class Delete(BaseVerb):

    finalizers = (EventFactory.Deleted,)

    verb = 'delete'


#
# BULK CRUD
#
class BulkCreate(BaseBulkVerb):

    finalizers = (EventFactory.BulkCreated,)

    verb = 'bulk_create'


class BulkRead(BaseBulkVerb):

    finalizers = (EventFactory.BulkRead,)

    verb = 'bulk_read'


class BulkUpdate(BaseBulkVerb):

    finalizers = (EventFactory.BulkUpdated,)

    verb = 'bulk_update'


class BulkDelete(BaseBulkVerb):

    finalizers = (EventFactory.BulkDeleted,)

    verb = 'bulk_delete'


#
# CONDITIONAL CRUD
#
class CreateOrUpdate(BaseVerb):

    finalizers = (EventFactory.Created, EventFactory.Updated)

    verb = 'create_or_update'


class CreateOrRead(BaseVerb):

    finalizers = (EventFactory.Created, EventFactory.Read)

    verb = 'read_or_create'
