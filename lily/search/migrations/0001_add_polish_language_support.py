
from __future__ import unicode_literals

from django.db import migrations
from django.db.migrations.operations.base import Operation


class AddLanguage(Operation):

    reversible = True

    def __init__(self, name):
        self.name = name

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, *args, **kwargs):
        schema_editor.execute("""
            CREATE TEXT SEARCH CONFIGURATION
                public.%s ( COPY = pg_catalog.english );
        """ % self.name)
        schema_editor.execute("""
            CREATE TEXT SEARCH DICTIONARY %s_ispell (
                TEMPLATE = ispell,
                DictFile = %s,
                AffFile = %s,
                StopWords = %s);
        """ % (self.name, self.name, self.name, self.name))
        schema_editor.execute("""
            ALTER TEXT SEARCH CONFIGURATION %s
                ALTER MAPPING FOR
                    asciiword,
                    asciihword,
                    hword_asciipart,
                    word,
                    hword,
                    hword_part
                WITH %s_ispell, simple;
        """ % (self.name, self.name))

    def database_backwards(self, app_label, schema_editor, *args, **kwargs):
        schema_editor.execute(
            "DROP TEXT SEARCH CONFIGURATION %s" % self.name)
        schema_editor.execute(
            "DROP TEXT SEARCH DICTIONARY %s_ispell" % self.name)

    def describe(self):
        return "Creates Text Search Configuration for {0}".format(self.name)


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        AddLanguage('polish'),
    ]
