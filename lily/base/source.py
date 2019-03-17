
import inspect

from lily_assistant.config import Config

from . import serializers


class Source:

    def __init__(self, fn):
        code, firstline = inspect.getsourcelines(fn)
        self.filepath = inspect.getfile(fn).replace(
            Config.get_project_path(), '')
        self.start_line = firstline
        self.end_line = firstline + len(code) - 1

    def __eq__(self, other):
        return (
            self.filepath == other.filepath and
            self.start_line == other.start_line and
            self.end_line == other.end_line)


class SourceSerializer(serializers.Serializer):

    _type = 'source'

    filepath = serializers.CharField()

    start_line = serializers.IntegerField()

    end_line = serializers.IntegerField()
