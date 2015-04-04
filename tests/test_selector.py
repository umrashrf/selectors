import re
import warnings
import weakref

from twisted.trial import unittest

from selectors import Selector


class SelectorTestCase(unittest.TestCase):

    sscls = Selector

    def test_simple_selection(self):
        """Simple selector tests"""
        body = "<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        sel = self.sscls(url="http://example.com", text=body)

        xl = sel.xpath('//input')
        self.assertEqual(2, len(xl))
        for x in xl:
            assert isinstance(x, self.sscls)

        self.assertEqual(sel.xpath('//input').extract(),
                         [x.extract() for x in sel.xpath('//input')])

        self.assertEqual([x.extract() for x in sel.xpath("//input[@name='a']/@name")],
                         [u'a'])
        self.assertEqual([x.extract() for x in sel.xpath("number(concat(//input[@name='a']/@value, //input[@name='b']/@value))")],
                         [u'12.0'])

        self.assertEqual(sel.xpath("concat('xpath', 'rules')").extract(),
                         [u'xpathrules'])
        self.assertEqual([x.extract() for x in sel.xpath("concat(//input[@name='a']/@value, //input[@name='b']/@value)")],
                         [u'12'])

    def test_representation_slice(self):
        body = u"<p><input name='{}' value='\xa9'/></p>".format(50 * 'b')
        sel = self.sscls(url="http://example.com", text=body)

        self.assertEqual(
            map(repr, sel.xpath('//input/@name')),
            ["<Selector xpath='//input/@name' data=u'{}'>".format(40 * 'b')]
        )

    def test_representation_unicode_query(self):
        body = u"<p><input name='{}' value='\xa9'/></p>".format(50 * 'b')
        sel = self.sscls(url="http://example.com", text=body)
        self.assertEqual(
            map(repr, sel.xpath(u'//input[@value="\xa9"]/@value')),
            ["<Selector xpath=u'//input[@value=\"\\xa9\"]/@value' data=u'\\xa9'>"]
        )

    def test_extract_first(self):
        """Test if extract_first() returns first element"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(url="http://example.com", text=body)

        self.assertEqual(sel.xpath('//ul/li/text()').extract_first(),
                         sel.xpath('//ul/li/text()').extract()[0])

        self.assertEqual(sel.xpath('//ul/li[@id="1"]/text()').extract_first(),
                         sel.xpath('//ul/li[@id="1"]/text()').extract()[0])

        self.assertEqual(sel.xpath('//ul/li[2]/text()').extract_first(),
                         sel.xpath('//ul/li/text()').extract()[1])

        self.assertEqual(sel.xpath('/ul/li[@id="doesnt-exist"]/text()').extract_first(), None)

    def test_re_first(self):
        """Test if re_first() returns first matched element"""
        body = '<ul><li id="1">1</li><li id="2">2</li></ul>'
        sel = self.sscls(url="http://example.com", text=body)

        self.assertEqual(sel.xpath('//ul/li/text()').re_first('\d'),
                         sel.xpath('//ul/li/text()').re('\d')[0])

        self.assertEqual(sel.xpath('//ul/li[@id="1"]/text()').re_first('\d'),
                         sel.xpath('//ul/li[@id="1"]/text()').re('\d')[0])

        self.assertEqual(sel.xpath('//ul/li[2]/text()').re_first('\d'),
                         sel.xpath('//ul/li/text()').re('\d')[1])

        self.assertEqual(sel.xpath('/ul/li/text()').re_first('\w+'), None)
        self.assertEqual(sel.xpath('/ul/li[@id="doesnt-exist"]/text()').re_first('\d'), None)

    def test_select_unicode_query(self):
        body = u"<p><input name='\xa9' value='1'/></p>"
        sel = self.sscls(url="http://example.com", text=body)
        self.assertEqual(sel.xpath(u'//input[@name="\xa9"]/@value').extract(), [u'1'])

    def test_list_elements_type(self):
        """Test Selector returning the same type in selection methods"""
        text = '<p>test<p>'
        assert isinstance(self.sscls(text=text).xpath("//p")[0], self.sscls)
        assert isinstance(self.sscls(text=text).css("p")[0], self.sscls)

    def test_boolean_result(self):
        body = "<p><input name='a'value='1'/><input name='b'value='2'/></p>"
        xs = self.sscls(url="http://example.com", text=body)
        self.assertEquals(xs.xpath("//input[@name='a']/@name='a'").extract(), [u'1'])
        self.assertEquals(xs.xpath("//input[@name='a']/@name='n'").extract(), [u'0'])

    def test_differences_parsing_xml_vs_html(self):
        """Test that XML and HTML Selector's behave differently"""
        # some text which is parsed differently by XML and HTML flavors
        text = '<div><img src="a.jpg"><p>Hello</div>'
        hs = self.sscls(text=text, type='html')
        self.assertEqual(hs.xpath("//div").extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></div>'])

        xs = self.sscls(text=text, type='xml')
        self.assertEqual(xs.xpath("//div").extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></img></div>'])

    def test_nested_selectors(self):
        """Nested selector tests"""
        body = """<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>"""

        x = self.sscls(url="http://example.com", text=body)
        divtwo = x.xpath('//div[@class="two"]')
        self.assertEqual(divtwo.xpath("//li").extract(),
                         ["<li>one</li>", "<li>two</li>", "<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath("./ul/li").extract(),
                         ["<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath(".//li").extract(),
                         ["<li>four</li>", "<li>five</li>", "<li>six</li>"])
        self.assertEqual(divtwo.xpath("./li").extract(), [])

    def test_mixed_nested_selectors(self):
        body = '''<body>
                    <div id=1>not<span>me</span></div>
                    <div class="dos"><p>text</p><a href='#'>foo</a></div>
               </body>'''
        sel = self.sscls(text=body)
        self.assertEqual(sel.xpath('//div[@id="1"]').css('span::text').extract(), [u'me'])
        self.assertEqual(sel.css('#1').xpath('./span/text()').extract(), [u'me'])

    def test_dont_strip(self):
        sel = self.sscls(text='<div>fff: <a href="#">zzz</a></div>')
        self.assertEqual(sel.xpath("//text()").extract(), [u'fff: ', u'zzz'])

    def test_namespaces_simple(self):
        body = """
        <test xmlns:somens="http://scrapy.org">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        """

        x = self.sscls(url="http://example.com", text=body, type="xml")

        x.register_namespace("somens", "http://scrapy.org")
        self.assertEqual(x.xpath("//somens:a/text()").extract(),
                         [u'take this'])

    def test_namespaces_multiple(self):
        body = """<?xml version="1.0" encoding="UTF-8"?>
<BrowseNode xmlns="http://webservices.amazon.com/AWSECommerceService/2005-10-05"
            xmlns:b="http://somens.com"
            xmlns:p="http://www.scrapy.org/product" >
    <b:Operation>hello</b:Operation>
    <TestTag b:att="value"><Other>value</Other></TestTag>
    <p:SecondTestTag><material>iron</material><price>90</price><p:name>Dried Rose</p:name></p:SecondTestTag>
</BrowseNode>
        """
        x = self.sscls(url="http://example.com", text=body, type="xml")
        x.register_namespace("xmlns", "http://webservices.amazon.com/AWSECommerceService/2005-10-05")
        x.register_namespace("p", "http://www.scrapy.org/product")
        x.register_namespace("b", "http://somens.com")
        self.assertEqual(len(x.xpath("//xmlns:TestTag")), 1)
        self.assertEqual(x.xpath("//b:Operation/text()").extract()[0], 'hello')
        self.assertEqual(x.xpath("//xmlns:TestTag/@b:att").extract()[0], 'value')
        self.assertEqual(x.xpath("//p:SecondTestTag/xmlns:price/text()").extract()[0], '90')
        self.assertEqual(x.xpath("//p:SecondTestTag").xpath("./xmlns:price/text()")[0].extract(), '90')
        self.assertEqual(x.xpath("//p:SecondTestTag/xmlns:material/text()").extract()[0], 'iron')

    def test_re(self):
        body = """<div>Name: Mary
                    <ul>
                      <li>Name: John</li>
                      <li>Age: 10</li>
                      <li>Name: Paul</li>
                      <li>Age: 20</li>
                    </ul>
                    Age: 20
                  </div>"""
        x = self.sscls(url="http://example.com", text=body)

        name_re = re.compile("Name: (\w+)")
        self.assertEqual(x.xpath("//ul/li").re(name_re),
                         ["John", "Paul"])
        self.assertEqual(x.xpath("//ul/li").re("Age: (\d+)"),
                         ["10", "20"])

    def test_selector_over_text(self):
        hs = self.sscls(text='<root>lala</root>')
        self.assertEqual(hs.extract(), u'<html><body><root>lala</root></body></html>')
        xs = self.sscls(text='<root>lala</root>', type='xml')
        self.assertEqual(xs.extract(), u'<root>lala</root>')
        self.assertEqual(xs.xpath('.').extract(), [u'<root>lala</root>'])

    def test_invalid_xpath(self):
        x = self.sscls(url="http://example.com", text="<html></html>")
        xpath = "//test[@foo='bar]"
        try:
            x.xpath(xpath)
        except ValueError as e:
            assert xpath in str(e), "Exception message does not contain invalid xpath"
        except Exception:
            raise AssertionError("A invalid XPath does not raise ValueError")
        else:
            raise AssertionError("A invalid XPath does not raise an exception")

    def test_empty_bodies(self):
        # shouldn't raise errors
        self.sscls(url='http://www.example.com', text='').xpath('//text()').extract()

    def test_null_bytes(self):
        # shouldn't raise errors
        self.sscls(url='http://www.example.com',
                    text='<root>pre\x00post</root>',
                    type='xml') \
            .xpath('//text()').extract()

    def test_select_on_unevaluable_nodes(self):
        r = self.sscls(text=u'<span class="big">some text</span>')
        # Text node
        x1 = r.xpath('//text()')
        self.assertEquals(x1.extract(), [u'some text'])
        self.assertEquals(x1.xpath('.//b').extract(), [])
        # Tag attribute
        x1 = r.xpath('//span/@class')
        self.assertEquals(x1.extract(), [u'big'])
        self.assertEquals(x1.xpath('.//text()').extract(), [])

    def test_select_on_text_nodes(self):
        r = self.sscls(text=u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.xpath("//div/descendant::text()[preceding-sibling::b[contains(text(), 'Options')]]")
        self.assertEquals(x1.extract(), [u'opt1'])

        x1 = r.xpath("//div/descendant::text()/preceding-sibling::b[contains(text(), 'Options')]")
        self.assertEquals(x1.extract(), [u'<b>Options:</b>'])

    def test_nested_select_on_text_nodes(self):
        # FIXME: does not work with lxml backend [upstream]
        r = self.sscls(text=u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.xpath("//div/descendant::text()")
        x2 = x1.xpath("./preceding-sibling::b[contains(text(), 'Options')]")
        self.assertEquals(x2.extract(), [u'<b>Options:</b>'])
    test_nested_select_on_text_nodes.skip = "Text nodes lost parent node reference in lxml"

    def test_remove_namespaces(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link type="text/html">
  <link type="application/atom+xml">
</feed>
"""
        sel = self.sscls(url="http://example.com/feed.atom", text=xml, type="xml")
        self.assertEqual(len(sel.xpath("//link")), 0)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link")), 2)

    def test_remove_attributes_namespaces(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:atom="http://www.w3.org/2005/Atom" xml:lang="en-US" xmlns:media="http://search.yahoo.com/mrss/">
  <link atom:type="text/html">
  <link atom:type="application/atom+xml">
</feed>
"""
        sel = self.sscls(url="http://example.com/feed.atom", text=xml, type="xml")
        self.assertEqual(len(sel.xpath("//link/@type")), 0)
        sel.remove_namespaces()
        self.assertEqual(len(sel.xpath("//link/@type")), 2)

    def test_smart_strings(self):
        """Lxml smart strings return values"""

        class SmartStringsSelector(Selector):
            _lxml_smart_strings = True

        body = """<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>"""

        # .getparent() is available for text nodes and attributes
        # only when smart_strings are on
        x = self.sscls(url="http://example.com", text=body)
        li_text = x.xpath('//li/text()')
        self.assertFalse(any(map(lambda e: hasattr(e._root, 'getparent'), li_text)))
        div_class = x.xpath('//div/@class')
        self.assertFalse(any(map(lambda e: hasattr(e._root, 'getparent'), div_class)))

        x = SmartStringsSelector(url="http://example.com", text=body)
        li_text = x.xpath('//li/text()')
        self.assertTrue(all(map(lambda e: hasattr(e._root, 'getparent'), li_text)))
        div_class = x.xpath('//div/@class')
        self.assertTrue(all(map(lambda e: hasattr(e._root, 'getparent'), div_class)))

    def test_xml_entity_expansion(self):
        malicious_xml = '<?xml version="1.0" encoding="ISO-8859-1"?>'\
            '<!DOCTYPE foo [ <!ELEMENT foo ANY > <!ENTITY xxe SYSTEM '\
            '"file:///etc/passwd" >]><foo>&xxe;</foo>'

        sel = self.sscls(url='http://example.com', text=malicious_xml, type="xml")

        self.assertEqual(sel.extract(), '<foo>&xxe;</foo>')


class ExsltTestCase(unittest.TestCase):

    sscls = Selector

    def test_regexp(self):
        """EXSLT regular expression tests"""
        body = """
        <p><input name='a' value='1'/><input name='b' value='2'/></p>
        <div class="links">
        <a href="/first.html">first link</a>
        <a href="/second.html">second link</a>
        <a href="http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml">EXSLT match example</a>
        </div>
        """
        sel = self.sscls(url="http://example.com", text=body)

        # re:test()
        self.assertEqual(
            sel.xpath(
                '//input[re:test(@name, "[A-Z]+", "i")]').extract(),
            [x.extract() for x in sel.xpath('//input[re:test(@name, "[A-Z]+", "i")]')])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "\.html$")]/text()')],
            [u'first link', u'second link'])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "first")]/text()')],
            [u'first link'])
        self.assertEqual(
            [x.extract()
             for x in sel.xpath(
                 '//a[re:test(@href, "second")]/text()')],
            [u'second link'])


        # re:match() is rather special: it returns a node-set of <match> nodes
        #[u'<match>http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml</match>',
        #u'<match>http</match>',
        #u'<match>www.bayes.co.uk</match>',
        #u'<match></match>',
        #u'<match>/xml/index.xml?/xml/utils/rechecker.xml</match>']
        self.assertEqual(
            sel.xpath('re:match(//a[re:test(@href, "\.xml$")]/@href,'
                      '"(\w+):\/\/([^/:]+)(:\d*)?([^# ]*)")/text()').extract(),
            [u'http://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.xml',
             u'http',
             u'www.bayes.co.uk',
             u'',
             u'/xml/index.xml?/xml/utils/rechecker.xml'])



        # re:replace()
        self.assertEqual(
            sel.xpath('re:replace(//a[re:test(@href, "\.xml$")]/@href,'
                      '"(\w+)://(.+)(\.xml)", "","https://\\2.html")').extract(),
            [u'https://www.bayes.co.uk/xml/index.xml?/xml/utils/rechecker.html'])

    def test_set(self):
        """EXSLT set manipulation tests"""
        # microdata example from http://schema.org/Event
        body="""
        <div itemscope itemtype="http://schema.org/Event">
          <a itemprop="url" href="nba-miami-philidelphia-game3.html">
          NBA Eastern Conference First Round Playoff Tickets:
          <span itemprop="name"> Miami Heat at Philadelphia 76ers - Game 3 (Home Game 1) </span>
          </a>

          <meta itemprop="startDate" content="2016-04-21T20:00">
            Thu, 04/21/16
            8:00 p.m.

          <div itemprop="location" itemscope itemtype="http://schema.org/Place">
            <a itemprop="url" href="wells-fargo-center.html">
            Wells Fargo Center
            </a>
            <div itemprop="address" itemscope itemtype="http://schema.org/PostalAddress">
              <span itemprop="addressLocality">Philadelphia</span>,
              <span itemprop="addressRegion">PA</span>
            </div>
          </div>

          <div itemprop="offers" itemscope itemtype="http://schema.org/AggregateOffer">
            Priced from: <span itemprop="lowPrice">$35</span>
            <span itemprop="offerCount">1938</span> tickets left
          </div>
        </div>
        """
        sel = self.sscls(url="http://example.com", text=body)

        self.assertEqual(
            sel.xpath('''//div[@itemtype="http://schema.org/Event"]
                            //@itemprop''').extract(),
            [u'url',
             u'name',
             u'startDate',
             u'location',
             u'url',
             u'address',
             u'addressLocality',
             u'addressRegion',
             u'offers',
             u'lowPrice',
             u'offerCount']
        )

        self.assertEqual(sel.xpath('''
                set:difference(//div[@itemtype="http://schema.org/Event"]
                                    //@itemprop,
                               //div[@itemtype="http://schema.org/Event"]
                                    //*[@itemscope]/*/@itemprop)''').extract(),
                         [u'url', u'name', u'startDate', u'location', u'offers'])
