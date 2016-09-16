# spider to crawl pages for end auction data from beezid.com

import json
from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from scrapy.http import Request
from allpayAuctions.items import AuctionItem
from scrapy import log

class BeezidSpider(BaseSpider):
    name = 'beezidStatic'
    allowed_domains = ['beezid.com']

    def start_requests(self):
        """ generate start urls to be scrapped
        """
        baseUrl = "http://www.beezid.com/auctions/closed?page="
        for i in range(1,330): # 334 total pages
            yield Request(baseUrl+str(i), callback = self.parse_recentlyCompleted)

    def parse_recentlyCompleted(self, response):
        """ yields individual completed auctions generated from start_requests
        """
        sel = Selector(response)
        links = sel.xpath("//div[@class='auction_box_easy_view']//a/@href").extract()

        for link in links:
            auctionURL = "http://www.beezid.com%s" % link
            yield Request("http://localhost:8050/render.html?url=%s" % auctionURL,
                          dont_filter=True,
                          callback=self.parse_items)

    def parse_items(self, response):
        """build item from individual auctions
        """
        sel = Selector(response)
        try:
            item = self.makeItem(sel)
        except:
            item = None
            self.log('Item creation error: %s' % response.url, level=log.WARNING)
        yield item
    
    def makeItem(self, sel):
        """ takes a Selector and create beezid item
        """
        rawBidHistory = sel.xpath("//*[@id='historyTop']/div[@class='bidding_history_column_holder']/p/text()").extract()
        
        auctionID = sel.xpath("//*[@id='auction_id_div']/text()").extract()[0].split(' ')[-1]
        itemName = sel.xpath("//div[@id='content_big_details']/div[@class='adetails_header']/div[@class='adetails_title']/h1/text()").extract()[0]
        endPrice = rawBidHistory[0].strip('$')
        date,time  = sel.xpath("//*[@id='timer_%s']/text()" % auctionID).extract()
        msrp = sel.xpath("//div[@id='price_auc_div']/text()").extract()[0].split('$')
        
        ## create item ##
        item = AuctionItem()
        item['auctionSite'] = 'beezid'
        item['auctionID'] = auctionID
        item['itemName'] = itemName
        item['auctionEndPrice'] = endPrice
        item['date'] = date
        item['time'] = time
        item['valuePrice'] = msrp[-1]

        del rawBidHistory[0::3] # don't care about anything other than winning price
        item['rawBidHistory'] = rawBidHistory

        return item
