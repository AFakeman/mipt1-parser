from collections import defaultdict
from html.parser import HTMLParser
from io import StringIO
import json
from sys import argv, stderr
from urllib.request import Request, urlopen

class MyHTMLParser(HTMLParser):
    paragraph_tags = ['p', 'li', 'h2']

    """
    Implicit assertions:
    1) We cannot have a paragraph in a paragraph
    """

    def __init__(self, imdir='img'):
        super(MyHTMLParser, self).__init__()
        self.in_paragraph = False  # We assert that we cannot have a paragraph in a paragraph
        self.pending_paragraph = ''
        self.sections = []
        self.buffer = StringIO()
        self.tags = defaultdict(list)
        self.images = []
        self.imgdir = imdir
        # There is a vk <h1> right inside the short_content block
        # Can be identified only by name and data should be ignored
        self.in_vk = False

    def in_short_content(self):
        return 'short_content' in self.tags['div']

    def handle_starttag(self, tag, attrs):
        attrs = {key: value for key, value in attrs}
        self.tags[tag].append(attrs.get('class'))
        if not self.in_short_content():
            return

        if tag in self.paragraph_tags:
            assert(not self.in_paragraph)
            self.in_paragraph = True
            if tag == 'li':
                self.pending_paragraph = r'     \item '
        if tag == 'div' and attrs.get('class') == 'short_content':
                print("Entered short_content", file=stderr)
        elif tag == 'img':
            if attrs.get('class') == 'tex':
                if self.in_paragraph:
                    self.pending_paragraph += '${0}$'.format(attrs['alt'])
                else:
                    print('            $${0}$$'.format(attrs['alt']), file=self.buffer)
            elif attrs.get('alt') != 'Система Orphus':
                img_url = 'http://mipt1.ru/{0}'.format(attrs.get('src'))
                filename = '{0}/{1}'.format(self.imgdir, attrs.get('src').replace('/', '+'))
                dot_split = filename.split('.')
                filename = "dot".join(dot_split[:-1]) + '.' + dot_split[-1]
                print(r'            \begin{figure}', file=self.buffer)
                print(r'                \centering', file=self.buffer)
                print(r'                \includegraphics[width=\linewidth]{{{0}}}'
                      .format(filename), file=self.buffer)
                print(r'            \end{figure}', file=self.buffer)
                self.images.append((img_url, filename))
        elif tag == 'h1' and attrs.get('name') == 'vk':
            self.in_vk = True
        elif tag == 'ol' or tag == 'ul':
            print(r'            \begin{itemize}', file=self.buffer)

    def handle_endtag(self, tag):
        if self.tags[tag]:
            self.tags[tag].pop()
        else:
            # There is one closing tag 
            # without a corresponding opening
            # outside of short_content
            assert(not self.in_short_content())

        if self.in_short_content():
            if tag in self.paragraph_tags:
                if self.pending_paragraph:
                    print(r'            {0}\\'.format(self.pending_paragraph[:-1]), file=self.buffer)
                    self.pending_paragraph = ''
                self.in_paragraph = False
            elif tag == 'div' and self.tags[tag][-1] == 'short_content':
                print("Exiting short_content", file=stderr)
            elif tag == 'h1' and self.in_vk:
                self.in_vk = False
            elif tag == 'ol' or tag == 'ul':
                print(r'            \end{itemize}', file=self.buffer)


    def handle_data(self, data):
        if self.in_short_content():
            if self.in_paragraph:
                self.pending_paragraph += data.replace('^', '')
            if self.tags['h1'] and not self.in_vk:
                self.sections.append(data)
                print(r'        \subsubsection{{{0}}}'.format(data), file=self.buffer)

def load_url(text_id):
    req = Request(
        'http://mipt1.ru/file.php?f=5_fiz&id={0}'.format(str(text_id)), 
        data = None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )
    return urlopen(req).read().decode('cp1251')

def save_image(img_url, filename):
    with open(filename, 'wb') as f:
        f.write(urlopen(img_url).read())

image_directory = 'img'

filename = argv[1]
with open(filename) as f:
    data = json.load(f)

for section in data:
    with open(section['filename'], 'w') as f:
        from_id = section['start_id']
        print(r'\section{{{0}}}'.format(section['section']), file=f)
        for count in section['counts']:
            to_id = from_id + count
            parser = MyHTMLParser(image_directory)
            for text_id in range(from_id, to_id):
                parser.feed(load_url(text_id))

            for img_url, filename in parser.images:
                save_image(img_url, filename)

            print(r'    \subsection{{{0}}}'.format(' '.join(parser.sections)), file=f)
            print(parser.buffer.getvalue(), file=f)

            from_id = to_id
