# items for static auction scraping

from scrapy.item import Item, Field

class AuctionItem(Item):
   auction_site = Field()
   auction_id = Field()
   item_name = Field()
   auction_end_price = Field()
   end_date = Field() # Auction end day
   end_time = Field() # Auction end time
   value_price = Field() # value of item as assigned by website
   raw_bid_history = Field() # raw bidding history, set up in

   ## bidStuff = [('id0', bool), ('id1', bool), ... , ('id9', bool)]
   ## in-order for (username, bool for autobid) true for auto, false for manual
   
   ## for position, data in enumerate(bidStuff):
   ##    print position, data
