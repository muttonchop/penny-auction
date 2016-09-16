# 1/28/2014
# spider to crawl pages for static end-auction data
import json, time
from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from scrapy.http import FormRequest, Request
from scrapy import log
from allpayAuctions.items import AuctionItem


class QuibidsSpider(BaseSpider): # change to Spider for 0.22+ versions
    name = "quibids_static"
    allowed_domains = ["quibids.com"]
    download_delay = 2
    
    def start_requests(self):
        ajax_url = "http://www.quibids.com/ajax/spots.php"
        payload = {'a':'h',
                   'ea':'20',
                   'groupBy':'a',
                   'p':'0',
                   'sort':'endingsoon',
                   'tab':'c',
                   'type':'ending',
                   'v':'g'}
        for i in range(106): # expect 2000 auction entries
            payload['p'] = str(i)
            yield FormRequest(
                ajax_url, formdata=payload, callback = self.parse_recentlyCompleted)

    def parse_recentlyCompleted(self, response):
        """ takes each of the recently completed pages and extracts 
        the individual auction links.
        """
        data = json.loads(response.body)
        
        for auction in data['Auctions']:
            html = auction['html']
            sel = Selector(text=html)

            url_from_html_xpath = "//h5[@class='auction-item-title']//a/@href"
            indv_auc_url_from_html = sel.xpath(url_from_html_xpath).extract()[0]

            indv_auc_fullUrl = 'http://www.quibids.com/en' + indv_auc_url_from_html

            req_url = "http://localhost:8050/render.html?url={}".format(indv_auc_fullUrl)
            yield Request(req_url, dont_filter = True, callback=self.parse_items)

    def parse_items(self,response):
        """ Takes individual auctions and parses items out. Each response 
        should be downloaded with the splash download middleware.
        """
        sel = Selector(response)
        auction_id = response.url.split('-')[1]

        try:
            item = self.make_item(sel)
            item['auction_id'] = auction_id
        except Exception as e:
            # TODO: This is shitty error logging. Fix this.
            item = None
            self.log(str(e), level=log.DEBUG)
            self.log('Item creation error: %s' % response.url, level = log.WARNING)
        yield item
    
    def make_item(self, sel):
        """ takes a Selector object and creates quibids item.
        """
        bid_hist_xpath = "//table[@id='bid-history']/tbody/tr/td/text()"
        bid_history = sel.xpath(bid_hist_xpath).extract() # table rows

        item_name_xpath = "//*[@id='product_title']/text()"
        item_name = sel.xpath(item_name_xpath).extract()

        auction_end_price = bid_history[1].strip('$')
        
        datetime_xpath = "//div[@id='end-time-disclaim']/p[2]/text()"
        date_and_time = sel.xpath(datetime_xpath).extract()[0]
        date_and_time = date_and_time.split(' ')
        date_and_time.remove('') # remove empty space

        end_date = date_and_time[0]
        end_time = date_and_time[1] + ' ' + date_and_time[2] 

        value_price = sel.xpath("//ul[@class='price-breakdown']/li//span/text()").extract()[0]
        value_price = value_price.join(value_price.split())[1:] # strip all the nasty characters from value_price (stupid html)

        ## put information into item ##
        item = AuctionItem()
        item['auction_site'] = 'quibids'
        item['item_name'] = item_name
        item['auction_end_price'] = auction_end_price
        item['end_date'] = end_date
        item['end_time'] = end_time
        item['value_price'] = value_price
        del bid_history[1::3]
        item['raw_bid_history'] = bid_history

        return item
