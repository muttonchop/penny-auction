# Scrapy settings for quibids project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'allpayAuctions'

SPIDER_MODULES = ['allpayAuctions.spiders']
NEWSPIDER_MODULE = 'allpayAuctions.spiders'

DOWNLOAD_DELAY = 2.5 # delay download requests by 750 ms (radomized by default)

ITEM_PIPELINES = {'allpayAuctions.pipelines.AuctionPipeline': 100,}

DOWNLOADER_MIDDLEWARES = {'scrapyjs.middleware.WebkitDownloader':1,} 

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'quibids (+http://www.yourdomain.com)'
