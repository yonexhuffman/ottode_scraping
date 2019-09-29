import scrapy
import json

class CategorySpider(scrapy.Spider):
    name = "scrape_detailurllist"

    def __init__(self):
        self.scrapeurl_prefix = 'https://www.otto.de'
        # 7: update scrape_detail_url_list.json  
        self.status = 7             

        self.scraping_pagelist = []
        self.scrape_detail_url_list = []

        self.file_path_scraping_pagelist = './tmp/log/scraping_pagelist.json'
        self.file_path_scrape_detail_url_list = './tmp/log/scrape_detail_url_list.json'        
            
    def start_requests(self):
        if self.status == 1:                
            urls = [
                'https://www.otto.de' , 
            ]        
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse)   
        # get product list
        elif self.status == 7:
            with open(self.file_path_scraping_pagelist) as json_file:  
                self.scraping_pagelist = json.load(json_file)
            with open(self.file_path_scrape_detail_url_list) as json_file:  
                self.scrape_detail_url_list = json.load(json_file)            
            for scraping_page in self.scraping_pagelist:
                if scraping_page['is_scraped'] == True:
                    continue
                yield scrapy.Request(url = scraping_page['href'] , callback = self.parseproductpage)
    
    def parseproductpage(self , response):
        requesturl = response.request.url
        responseurl = response.url
        if requesturl != responseurl:
            print('REQUESTURL != RESPONSEURL')
            print(requesturl , responseurl)
        else:
            print('Request URL ---> ' + requesturl)
        list_index = -1
        for i in range(0 , len(self.scraping_pagelist)):
            if requesturl.find(self.scraping_pagelist[i]['href']) != -1:
                list_index = i
                if responseurl != requesturl:
                    self.scraping_pagelist[list_index]['href'] = responseurl
        
        # print('list_index' + '--->>>' + str(list_index))

        if list_index >= 0:
            product_categoryid = self.scraping_pagelist[list_index]['categoryid']
            product_ids = response.css('#san_resultSection article::attr(data-productid)').extract()
            product_links = response.css('#san_resultSection article a.productLink::attr(href)').extract()
            product_count = len(product_ids)
            # print('product_ids_count--->>>' + str(product_count))
            # print('product_links_count--->>>' + str(len(product_links)))

            if len(product_ids) == len(product_links):
                for i in range(0 , product_count):
                    product_id = product_ids[i]
                    detail_url_list_index = self.is_exist_scrape_detail_url_list(product_id)
                    if (detail_url_list_index < 0):
                        insert_item = {
                            'cat_id' : [product_categoryid] , 
                            'prd_id' : product_id , 
                            'prd_url' : product_links[i] , 
                            'is_scraped' : False
                        }
                        self.scrape_detail_url_list.append(insert_item)
                        self.scrape_detail_url_list = sorted(self.scrape_detail_url_list , key = lambda i: (i['prd_id']))
                    else:                        
                        # print(self.scrape_detail_url_list[detail_url_list_index]['cat_id'])
                        # print('new_cate_id' + str(product_categoryid))
                        if int(product_categoryid) not in self.scrape_detail_url_list[detail_url_list_index]['cat_id']:
                            self.scrape_detail_url_list[detail_url_list_index]['cat_id'].append(int(product_categoryid))
                            self.scrape_detail_url_list[detail_url_list_index]['is_scraped'] = False

                with open(self.file_path_scrape_detail_url_list, 'w') as outfile:  
                    json.dump(self.scrape_detail_url_list , outfile)
                    
                # if next button exist
                next_page_link = response.css('#san_pagingBottomNext').extract()
                # print('next_btn--->>>' + str(len(next_page_link)))
                if len(next_page_link) > 0:
                    next_page_url = None
                    next_page_link_href = response.css('#san_pagingBottomNext a.ts-link::attr(href)').extract_first()
                    if next_page_link_href != None:
                        next_page_url = self.scrapeurl_prefix + next_page_link_href
                    else:
                        next_page_link_info = response.css('#san_pagingBottomNext span::attr(data-ts-link)').extract_first()
                        print('next_page_link_info-->' + next_page_link_info)
                        data_ts_link_info = json.loads(next_page_link_info)
                        if 'san_NaviPaging' in data_ts_link_info.keys():
                            page_num = data_ts_link_info['san_NaviPaging']
                            pagination_url_afterfix = 'p=' + str(page_num) + '&ps=' + str(product_count)
                            if self.scraping_pagelist[list_index]['href'].find('?') != -1:
                                next_page_url = self.scraping_pagelist[list_index]['href'] + '&' + pagination_url_afterfix
                            else:
                                next_page_url = self.scraping_pagelist[list_index]['href'] + '?' + pagination_url_afterfix
                    
                    print('next_page_url --->> ' + next_page_url)

                    if next_page_url != None:
                        next_page = response.urljoin(next_page_url)
                        print("Found url: {}".format(next_page))
                        yield scrapy.Request(next_page , callback = self.parseproductpage)
                else:
                    self.scraping_pagelist[list_index]['is_scraped'] = True
                    print(self.scraping_pagelist[list_index])
                    with open(self.file_path_scraping_pagelist, 'w') as outfile:  
                        json.dump(self.scraping_pagelist , outfile)
            else:
                print('ERRORPAGE--->' + self.scraping_pagelist[list_index]['href'])

    def is_exist_scrape_detail_url_list(self , product_id):
        # half search algorithm must use
        list_index = -1
        for i in range(0 , len(self.scrape_detail_url_list)):
            if self.scrape_detail_url_list[i]['prd_id'] == product_id:
                list_index = i

        return list_index
    