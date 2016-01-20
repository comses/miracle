import os
import pygments
from pygments.lexers import guess_lexer
from pygments.formatters.html import HtmlFormatter

# http://stackoverflow.com/questions/431684/how-do-i-cd-in-python
class Chdir(object):
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

def highlight(code, lexer=None):
    if lexer is None:
        lexer = guess_lexer(code)
    return pygments.highlight(code,
                              lexer,
                              HtmlFormatter(linenos="inline", cssclass="source"))