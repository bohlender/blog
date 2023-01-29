openring \
  -s https://www.msoos.org/feed \
  -s https://www.rifters.com/crawl/?feed=rss2 \
  -s http://fabiensanglard.net/rss.xml \
  -s https://secret.club/feed.xml \
  -s https://dragan.rocks/feed.xml \
  < openring-template.toml \
  > data/webring.toml
