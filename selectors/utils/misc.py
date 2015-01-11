"""Helper functions which doesn't fit anywhere else"""
import re

from w3lib.html import replace_entities

from .python import flatten


def extract_regex(regex, text, encoding='utf-8'):
    """Extract a list of unicode strings from the given text/encoding using the following policies:

    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """

    if isinstance(regex, basestring):
        regex = re.compile(regex, re.UNICODE)

    try:
        strings = [regex.search(text).group('extract')]   # named group
    except:
        strings = regex.findall(text)    # full regex or numbered groups
    strings = flatten(strings)

    if isinstance(text, unicode):
        return [replace_entities(s, keep=['lt', 'amp']) for s in strings]
    else:
        return [replace_entities(unicode(s, encoding), keep=['lt', 'amp']) for s in strings]
