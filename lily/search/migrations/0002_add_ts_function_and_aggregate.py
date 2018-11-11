
from __future__ import unicode_literals

from django.db import migrations
from django.db.migrations.operations.base import Operation


class CreateFunctionAndAggregate(Operation):

    reversible = True

    def __init__(self, func_name, func_body, agg_name, agg_body):
        self.func_name = func_name
        self.func_body = func_body
        self.agg_name = agg_name
        self.agg_body = agg_body

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, *args, **kwargs):
        schema_editor.execute(
            "CREATE FUNCTION %s %s" % (self.func_name, self.func_body))
        schema_editor.execute(
            "CREATE AGGREGATE %s %s" % (self.agg_name, self.agg_body))

    def database_backwards(self, app_label, schema_editor, *args, **kwargs):
        schema_editor.execute("DROP AGGREGATE %s" % self.agg_name)
        schema_editor.execute("DROP FUNCTION %s" % self.func_name)

    def describe(self):
        return (
            "Creates function {0} and aggregate {1}".format(
                self.func_name, self.agg_name))


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_add_polish_language_support'),
    ]

    operations = [
        CreateFunctionAndAggregate(
            # function to be used in aggregate data
            "tsvector_add(tsvector, tsvector)",
            """
                RETURNS tsvector
                AS 'SELECT COALESCE($1, '''') || COALESCE($2, '''');'
                LANGUAGE SQL;
            """,
            # aggregate data
            "tsvector_agg(tsvector)",
            """
            (
                sfunc = tsvector_add,
                stype = tsvector
            )
            """),
    ]
