
class AsyncTask:

    def __init__(self, callback, args):
        self.callback = callback
        self.args = args
        self.successful = False
        self.result = None
