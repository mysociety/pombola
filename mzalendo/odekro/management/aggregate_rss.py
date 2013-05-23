# RSS parser to aggregate desired topics from 
# varios rss feeds
import csv
import os
import feedparser


BASEDIR = os.path.dirname(__file__)
#read list os rss feeds from file
FEEDS =[]
reader= csv.reader(open('rssfeeds.csv','rU'))
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
                feedhtml += '<h2>{0}</h3>'.format(article.title.encode('utf-8','ignore'))
                feedhtml += '<p>Source:{0} Published:{1}</p>'.format(feed['source'],article.published.encode('utf-8','ignore'))
                feedhtml += '<p>{0}</p>'.format(article.description.encode('utf-8','ignore'))
                feedhtml += '</li>'
    return feedhtml


