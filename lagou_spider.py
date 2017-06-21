# -*- coding: utf-8 -*-
import scrapy
import json
import copy
from tutorial.items import LagouItem


class LagouSpider(scrapy.Spider):
    name = "lagou"
    allowed_domains = ["lagou.com"]
    global page, city
    page = 1
    city = 2  # 2 denotes Beijing, which is the first city in this website map.
    start_urls = (
        'https://www.lagou.com/gongsi/%d-0-0.json?first=false&pn=%d&sortField=0&havemark=0' % (city, page),
    )
    custom_settings = {
        # setting cookies
        # 'COOKIES_ENABLED': True,
        # 'DUPEFILTER_DEBUG': True
        # 'DOWNLOAD_DELAY': 0.1,
    }

    def parse(self, response):
        global page, city
        jdic = json.loads(response.body)
        jresults = jdic['result']
        if jresults != []:
            for sel in jresults:
                item = LagouItem()
                item['companyId'] = sel['companyId']
                item['companyFullName'] = sel['companyFullName']
                item['companyShortName'] = sel['companyShortName']
                item['companyFeatures'] = sel['companyFeatures']
                item['industryField'] = sel['industryField']
                item['financeStage'] = sel['financeStage']
                item['city'] = sel['city']
                item['interviewRemarkNum'] = sel['interviewRemarkNum']
                item['positionNum'] = sel['positionNum']
                item['processRate'] = sel['processRate']
                if sel['companyId'] is not None:
                    link = 'https://www.lagou.com/gongsi/' + str(sel['companyId']) + '.html'
                    print 'item: ', sel['companyId'], '  ', item['companyId']
                    yield scrapy.Request(url=link, meta={'item': item}, callback=self.parseIntroduction)
            page += 1
            pagesUrl = "https://www.lagou.com/gongsi/%d-0-0.json?first=false&pn=%d&sortField=0&havemark=0" % (city, page)
            yield scrapy.Request(url=pagesUrl, callback=self.parse)
        else:
            page = 1
            city += 1
            if city <= 50:
                cityUrl = "https://www.lagou.com/gongsi/%d-0-0.json?first=false&pn=%d&sortField=0&havemark=0" % (city,page)
                yield scrapy.Request(url=cityUrl, callback=self.parse)
            else:
                print "congratulations! we finish the task."

    def parseIntroduction(self, response):
        item = copy.deepcopy(response.meta['item'])
        print 'xxxxxxxxxxxxx  ', item['companyId']
        products = list()
        for sel in response.xpath(".//*[@id='company_products']/div[2]/div"):
            products.append(sel.xpath("div/h4/div/a[1]/text()").extract_first().strip())
        item['companyProduct'] = '|'.join(products)

        # scrape the management team
        team = list()
        for sel in response.xpath(".//*[@id='company_managers']/div[2]/div[1]/ul/li"):
            try:
                people = sel.xpath("p[1]/span/text()").extract_first().strip()
                job = sel.xpath("p[2]/text()").extract_first().strip()
                if people == u'' or people == u' ':
                    team.append(u"暂无公司领导详细信息")
                else:
                    team.append((people + ': ' + job))
            except AttributeError:
                print "There is no detail information!"
                team.append(u"暂无公司领导详细信息")
        item['managementTeam'] = '|'.join(team)

        # scrape the company introduction
        histories = list()
        lastDate = ""
        for sel in response.xpath(".//*[@id='history_container']/div[2]/ul/li"):
            date = sel.xpath("div[1]/p[2]/text()").extract_first().strip()
            event = sel.xpath("div[3]/p/span/a/text()").extract_first().strip()
            if date == u' ' or date == u'':
                date = lastDate
                histories.append((date + ': ' + event))
            else:
                histories.append((date + ': ' + event))
                lastDate = date
        item['devHistory'] = '|'.join(histories)

        # crawl company introduction
        try:
            item['companyIntroduction'] = response.xpath(".//*[@id='company_intro']/div[2]/div[1]/span[1]/p/text()").\
                extract_first().strip()
        except AttributeError:
            item['companyIntroduction'] = u"暂无公司介绍"

        # crawl company labels
        labels = list()
        for sel in response.xpath(".//*[@id='tags_container']/div[2]/div/ul/li"):
            labels.append(sel.xpath("text()").extract_first().strip())
        item['companyLabel'] = '|'.join(labels)

        # crawl company scale
        item['companyScale'] = response.xpath(".//*[@id='basic_container']/div[2]/ul/li[3]/span/text()").\
            extract_first().strip()
        yield item

