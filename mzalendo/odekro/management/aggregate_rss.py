# RSS parser to aggregate desired topics from 
# varios rss feeds
mport csv
import os
import feedparser
import dateutil

BASEDIR = os.path.dirname(__file__)
#read list os rss feeds from file
FEEDS =[]
reader= csv.reader(open(os.path.join(BASEDIR,'rssfeeds.csv'),'rU'))
for row in reader:
    if reader.line_num ==1:
        headers = row
    else:
        if any(row):
            FEEDS.append(dict(zip(headers,[col.strip() for col in row])))


def aggregate_articles():
    feedhtml = ""
    for feed in FEEDS:
        f = feedparser.parse(feed['feed'])
        focused = feed['category'] is 'parliament'
        for article in f['entries']:
            if focused or 'parliament' in article.title.lower() or 'parliament' in article.description.lower():
                feedhtml += '<li>'
                feedhtml += '<h3><a href="{0}">{1}</a></h3>'.format(article.link.encode('utf-8','ignore'), article.title.encode('utf-8','igno
re'))
                pubdate = dateutil.parser.parse(article.published.encode('utf-8','ignore')).date().strftime('%a %B %d, %Y')
                feedhtml += '<span><a href="http://{0}">{0}</a> &nbsp;&nbsp;<b>Published:</b>&nbsp;{1}</span>'.format(feed['source'],pubdate)
                feedhtml += '<div>{0}</div>'.format(article.description.encode('utf-8','ignore'))
                feedhtml += '</li>'
    return feedhtml


