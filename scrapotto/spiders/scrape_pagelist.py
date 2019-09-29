import scrapy
import json

class CategorySpider(scrapy.Spider):
    name = "scrape_pagelist"

    def __init__(self):
        self.scrapeurl_prefix = 'https://www.otto.de'
        # 6: scraping_page_list generate
        self.status = 6           

        self.category_list = []
        self.scraping_pagelist = []

        self.file_path_optimizedcategory = './tmp/log/optimizedcategory.json'
        self.file_path_scraping_pagelist = './tmp/log/scraping_pagelist.json'
        self.total_category_count = 0
            
    def start_requests(self):
        if self.status == 1:                
            urls = [
                'https://www.otto.de' , 
            ]        
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse)   
        # scraping_page_list generate
        elif self.status == 6:
            with open(self.file_path_optimizedcategory) as json_file:  
                self.category_list = json.load(json_file)
            self.generate_scraping_pagelist(self.category_list)

            self.scraping_pagelist = sorted(self.scraping_pagelist , key = lambda i: (i['categoryid']))
            with open(self.file_path_scraping_pagelist, 'w') as outfile:  
                json.dump(self.scraping_pagelist , outfile)
            print(len(self.scraping_pagelist))
    
    # COMPLETE FUNCTION USAGE ----->>>>> is_leaf=true and has_product=true product page list generate
    def generate_scraping_pagelist(self , categorylist):
        for category in categorylist:
            if (('is_leaf' in category.keys()) and ('has_product' in category.keys())):
                if ((category['is_leaf'] == True) and (category['has_product'] == True)):
                    # if 'depth' in category.keys():
                    #     continue
                    insert_pageitem = {
                        'href' : self.scrapeurl_prefix + category['href'] , 
                        'categoryid' : category['categoryid'] , 
                        'is_scraped' : False
                    }
                    print(category['name'] + '-->' + str(category['categoryid']))
                    self.scraping_pagelist.append(insert_pageitem)
            
            if ('children' in category.keys()):
                if (len(category['children']) > 0):
                    self.generate_scraping_pagelist(category['children'])

      