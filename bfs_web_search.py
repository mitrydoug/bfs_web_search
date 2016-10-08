#! /usr/local/bin/python3

from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime, timedelta

from bs4 import BeautifulSoup as bs
import re
import requests
from urllib.parse import urljoin

BOLD = '\033[1m'
END  = '\033[0m'

def bfs_web_search(args):
    """ Search text of web page and those linked at a max depth of --levels.

    Uses BFS search to find the provided terms/regexes in pages linked from
    [args.srcpage].
    """
    queue = [(0, args.srcpage)]
    start_time = datetime.utcnow()
    while (len(queue) > 0 and
          (datetime.utcnow() - start_time).total_seconds() < args.timeout):
        (level, page), queue = queue[0], queue[1:]
        if level > args.levels:
            break
        try:
            r = requests.get(page)
        except:
            pass
        page = r.url # may have been redirected
        if (r.status_code != 200 or
              'html' not in r.headers['content-type']):
            # This is not a page we want to search
            continue
        html = bs(r.text, 'html.parser')
        html_text = html.get_text().replace('\n', ' ');
        occurrence_dict = defaultdict(list)

        for term in args.terms:
            for m in re.finditer(
                  ((lambda x:x) if args.regex else re.compile)(term),
                  html_text):
                occurrence_dict[term].append((m.start(), len(m.group(0))))

        if len(occurrence_dict) > 0:
            print('Level:%(level)d (%(page)s)' % locals())
            for n, term in sorted(
                  (len(occurrence_dict[t]), t) for t in occurrence_dict): 
                print('  %(n)d occurences for term "%(term)s"' % locals())
                for start, length in occurrence_dict[term]:
                    begin = max(0, start - args.context)
                    end = start + length + args.context
                    print('    ... ' + html_text[begin:start]
                        + BOLD + html_text[start:start+length] + END
                        + html_text[start+length:end] + ' ...')
        for link in html.find_all('a'):
            if link.has_attr('href'):
                newpage = urljoin(page, link.get('href'))
                queue.append((level+1, newpage))
                

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--levels', '-l', type=int, required=False,
      help='A whole number, the maximum number of links to follow')
    parser.add_argument('--timeout', '-t', type=int, required=False,
      default=60, help='A whole number, the maximum number of seconds to '
      'continue search')
    parser.add_argument('--regex', '-r', action='store_true', required=False,
      help='Treat terms as regular expressions')
    parser.add_argument('--context', '-c', type=int, required=False,
      default=10, help='Characters of context before and after match.')
    parser.add_argument('srcpage', type=str,
      help='The source web page to begin the search')
    parser.add_argument('terms', type=str, nargs='+',
      help='Search terms (or regexes, see --regex) to find in pages')
    args = parser.parse_args()
    bfs_web_search(args)
