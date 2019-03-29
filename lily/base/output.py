

class Output:

    def __init__(self, serializer):
        self.serializer = serializer

    def __eq__(self, other):
        return self.serializer == other.serializer
