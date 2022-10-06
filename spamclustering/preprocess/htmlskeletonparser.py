from html.parser import HTMLParser
import html

class HTMLSkeletonParser(HTMLParser):
    """ Parser to create HTML skeleton from given HTML.

    This parser strips all content from given HTML-Code. That is, that only 
    HTML-Tags and Style information will remain in the returned HTML.
    
    """
    def __init__(self):
        """ Constructor.
        """
        HTMLParser.__init__(self)
        self.content_list = []
        self.data = ''
        self.last_start_tag = ''

    def handle_starttag(self, tag, attrs):
        """ Store start tag for later decision making. 

            Override handle_starttag of base class. Will be called when feed()
            is invoked and doesn't needs to be invoked manually usally.

        :param tag: HTML tag detected.
        :type tag: string
        :param attr: Attributes of the tag.
        :type attr: List of pairs 
        """
        self.last_start_tag = tag
    
    def handle_data(self, data):
        """ Handles data between HTML tags. Overridden from base class.
        
        This function is invoked, when data between HTML tags is parsed. When 
        invoked, this funcktion decides on the preceeding HTML start tag, if 
        the following data should be removed to create the skeleton. If so, 
        this data wil be buffered for later replacement.

        Will usually be invoked when data is fed to the parser. 

        :param data: Data between two HTML tags 
        :type data: string
        """
        # remove whitespace from replacement lists
        content = data.strip()
        # there are some tags that indivate, that we want to ignore the 
        # following data
        # TODO: do we want to ingore HTML comments or replace them?
        ignore_tags = [
            'style'
        ]
        if ('' != content) and (self.last_start_tag not in ignore_tags):
            # add all versions of a string to the replacement lists. These are
            # a version without any special chars escaped, on with partially 
            # escaped one and one, where all are escaped.
            self.content_list.append(content)
            self.content_list.append(html.escape(content))
            self.content_list.append(html.escape(content, quote=False))
    
    
    def feed(self, data):
        """ Feed data to this parser.

        On parsing behavior view documentation of :class:`html.htmlparser`.

        The buffer of the base class is not reused. Instead, an addtional 
        buffer is used to store given HTML code for later replacement.

        :param data: HTML code to parse.
        :type data: string 
        """
        HTMLParser.feed(self, data)
        self.data += data
    
    def close(self):
        """ Close input of HTML and make the parser parse the input.

        On parsing behavior view documentation of :class:`html.htmlparser`.

        Upon receiving the EOF-like close invocation, all fed data will be 
        parsed and all content data will be removed. In contrast to the base 
        class, this object will return a value, namely the HTML skeleton.

        :return: HTML skelton
        :rtype: string
        """
        HTMLParser.close(self)
        return self.create_skeleton()

    def create_skeleton(self):
        """ Start the striping process of content data from the HTML source.

        Will be invoked by `close` method. Invoking this method manually will 
        process all data fed to the parser so far. No changes on the internal 
        buffers will be done (e.g. overwriting with skeleton).

        :return: HTML skeleton
        :rtype: string
        """
        result = self.data
        # we try to replace on a greedy manner, so we start with the longest 
        # strings first
        self.content_list.sort(key=lambda h: (len(h)), reverse=True)
        for content in self.content_list:
            result = result.replace(content, '')
        return result
