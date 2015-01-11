"""
We need these things in Scrapy and Selectors packages both
"""
from lxml import etree

from .csstranslator import SelectorHTMLTranslator, SelectorGenericTranslator


class SafeXMLParser(etree.XMLParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('resolve_entities', False)
        super(SafeXMLParser, self).__init__(*args, **kwargs)


_ctgroup = {
    'html': {'_parser': etree.HTMLParser,
             '_csstranslator': SelectorHTMLTranslator(),
             '_tostring_method': 'html'},
    'xml': {'_parser': SafeXMLParser,
            '_csstranslator': SelectorGenericTranslator(),
            '_tostring_method': 'xml'},
}
