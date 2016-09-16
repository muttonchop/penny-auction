# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from twisted.enterprise import adbapi
from scrapy import log
from scrapy.exceptions import DropItem
import MySQLdb.cursors
import pytz, datetime

class AuctionPipeline(object):
    def __init__(self):
        self.dbPool = adbapi.ConnectionPool('MySQLdb',
                                            db = 'allPayAuctions',
                                            user = 'kuceraa',
                                            passwd = 'ad@m',
                                            cursorclass = MySQLdb.cursors.DictCursor,
                                            charset = 'utf8',
                                            use_unicode = True)
        
    def process_item(self, item, spider):
        # run database query in thread pool
        if item:
            # prepare item for database insertion
            # find the differences in the items, correct for it with if statement, then slap that shit into an insert
            dateInfo = item['end_date'].split('-')
            
            if item['auction_site'] == 'quibids':
                year, month, day = dateInfo[0], dateInfo[1], dateInfo[2]
                hour,minute = item['end_time'].split(' ')[0].split(':')
                sec = '00'
                tmz = 'US/Central'
            else:
                month, day, year = dateInfo[0], dateInfo[1], dateInfo[2]
                hour, minute, sec = item['end_time'].split(' ')[0].split(':')
                tmz = 'US/Eastern'

            item['end_date'], item['end_time'] = self.to_utc([year, month, day], [hour, minute, sec], tmz)
            
            query = self.dbPool.runInteraction(self._condInsertAucData, item)
            query.addErrback(self.handle_error)

            query1 = self.dbPool.runInteraction(self._condInsertBidData, item)
            query1.addErrback(self.handle_error)

            return item        
        else:
            raise DropItem("Empty item")
    
    def _condInsertAucData(self, tx, item):
        # create record if it doesn't exist
        tx.execute("SELECT * FROM auction_data WHERE auction_id = %s", (item['auction_id'], ))
        result = tx.fetchone()
        if result:
            log.msg("Item already in the database", level = log.DEBUG)
        else:
            tx.execute("INSERT INTO auction_data (auction_id, end_price, msrp, end_date, end_time, name) VALUES (%s, %s, %s, %s, %s, %s)",
                       (item['auction_id'],
                        float(item['auction_end_price']),
                        float(item['value_price']),
                        item['end_date'],
                        item['end_time'],
                        item['item_name']))

            log.msg("Item stored in db: %s" % item, level=log.INFO)

    def _condInsertBidData(self, tx, item):
        userNames = item['raw_bid_history'][0::2]
        bidTypes = item['raw_bid_history'][1::2]
        aucID = item['auction_id']
        
        for i in xrange(len(userNames)): # not very pythonic, but quick.
            bt = bidTypes[i]
            if bt == u'Regular' or bt == u'Single Bid':
                bidType = 1 # manual bid
            else:
                bidType = 0 # autobid

            # check for duplicate data
            tx.execute("SELECT * FROM bid_data WHERE (user_id, auction_id, bid_position, bid_type) = (%s, %s, %s, %s)",
                       (userNames[i], aucID, i, bidType))
            result = tx.fetchone()
            if result:
                log.msg("Bid data already in the database", level = log.INFO)
            else:
                tx.execute("INSERT INTO bid_data (user_id, auction_id, bid_position, bid_type) VALUES (%s, %s, %s, %s)",
                           (userNames[i], aucID, i, bidType))
                
                log.msg('Bid Data successfully stored in db: (%s, %s, %s, %s)' % (userNames[i], aucID, i, bidType), level = log.INFO)
                   
    def handle_error(self, e):
        log.err(e)

    def to_utc(self, d, t, tmz):
        # d = [year, month, day]
        # t = [hour, min, sec]
        # returns the utc date and time object
        fmt = "%Y-%m-%d %H:%M:%S"
        local = pytz.timezone(tmz)
        naive = datetime.datetime.strptime ("%s-%s-%s %s:%s:%s" % (d[0], d[1], d[2], t[0], t[1], t[2]), fmt)
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone (pytz.utc)

        return utc_dt.strftime(fmt).split(' ')
