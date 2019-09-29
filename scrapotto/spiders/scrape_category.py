import scrapy
import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
from scrapy_splash import SplashRequest
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import sys

class CategorySpider(scrapy.Spider):
    name = "scrape_category"

    def __init__(self):
        self.scrapeurl_prefix = 'https://www.otto.de'
        self.scrape_price_minvalue = 150
        self.selenium_webdriver_file_path = 'C:/chromedriver.exe'
        # self.selenium_webdriver_file_path = '/usr/bin/chromedriver'
        # 5: use selenium driver scrape category depth 4
        # self.status = 5
        # 8: use selenium driver scrape category depth 5  
        self.status = 8         
        self.second_layer_scrape_startnum = 6729
        self.third_layer_endnum = 34097
    
        self.request_sequence = []
        self.category_list = []
        self.scraping_pagelist = []

        self.file_path_optimizedcategory = './tmp/log/optimizedcategory.json'
        self.file_path_scraping_pagelist = './tmp/log/scraping_pagelist.json'
        self.file_path_scrape_detail_url_list = './tmp/log/scrape_detail_url_list.json'  
        self.file_path_scrape_category_log = './tmp/log/scrape_category_log.json'        
        
        self.fifth_layer_scrape_startnum = 12948
        self.fifth_layer_startnum = 45553

        self.scrape_crawl_status = True

    def start_requests(self):
        if self.status == 1:                
            urls = [
                'https://www.otto.de' , 
            ]        
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse)    
        elif self.status == 4:
            with open('./tmp/optimizedcategory.json') as json_file:  
                self.category_list = json.load(json_file)  
            i = 0
            j = 0
            k = 0
            for firstlayer in self.category_list:
                j = 0
                for secondlayer in firstlayer['children']:
                    k = 0
                    for thirdlayer in secondlayer['children']:                        
                        categorypath = str(firstlayer['categoryid']) + '/' + str(secondlayer['categoryid']) + '/' + str(thirdlayer['categoryid'])
                        arrayindexpath = str(i) + '/' + str(j) + '/' + str(k)
                        request_item = {
                            'name' : thirdlayer['name'] ,
                            'categoryid' : thirdlayer['categoryid'] , 
                            'parentid' : thirdlayer['parentid'] , 
                            'requesturl' : self.scrapeurl_prefix + thirdlayer['href'] , 
                            'categorypath' : categorypath , 
                            'arrayindexpath' : arrayindexpath
                        }
                        self.request_sequence.append(request_item)
                        k += 1
                    j += 1
                i += 1
            
            for i in range(0 , len(self.request_sequence)):
                yield scrapy.Request(url = self.request_sequence[i]['requesturl'] , callback = self.parsethirdlayer)    
        elif self.status == 5:
            with open(self.file_path_optimizedcategory) as json_file:  
                self.category_list = json.load(json_file)  
            i = 0
            j = 0
            k = 0
            for firstlayer in self.category_list:
                j = 0
                for secondlayer in firstlayer['children']:
                    k = 0
                    for thirdlayer in secondlayer['children']:   
                        if (thirdlayer['categoryid'] < self.second_layer_scrape_startnum):
                            continue
                        categorypath = str(firstlayer['categoryid']) + '/' + str(secondlayer['categoryid']) + '/' + str(thirdlayer['categoryid'])
                        arrayindexpath = str(i) + '/' + str(j) + '/' + str(k)
                        request_item = {
                            'name' : thirdlayer['name'] ,
                            'categoryid' : thirdlayer['categoryid'] , 
                            'parentid' : thirdlayer['parentid'] , 
                            'requesturl' : self.scrapeurl_prefix + thirdlayer['href'] , 
                            'categorypath' : categorypath , 
                            'arrayindexpath' : arrayindexpath
                        }
                        self.request_sequence.append(request_item)
                        k += 1
                    j += 1
                i += 1
            for i in range(0 , len(self.request_sequence)):
                self.parseCategoryWithChromeDriver(self.request_sequence[i]['requesturl'] , i) 
        elif self.status == 8:
            with open(self.file_path_scrape_category_log) as json_file:  
                log_data = json.load(json_file)  
            self.fifth_layer_scrape_startnum = int(log_data['fifth_layer_scrape_startnum']) + 1
            self.fifth_layer_startnum = int(log_data['fifth_layer_startnum']) + 1
            print(self.fifth_layer_scrape_startnum , self.fifth_layer_startnum)
            
            with open(self.file_path_optimizedcategory) as json_file:  
                self.category_list = json.load(json_file)  
            i = 0
            j = 0
            k = 0
            for firstlayer in self.category_list:
                j = 0
                for secondlayer in firstlayer['children']:
                    k = 0
                    for thirdlayer in secondlayer['children']:   
                        l = 0
                        for forthlayer in thirdlayer['children']:   
                            if (forthlayer['categoryid'] < self.fifth_layer_scrape_startnum):
                                continue
                            categorypath = str(firstlayer['categoryid']) + '/' + str(secondlayer['categoryid']) + '/' + str(thirdlayer['categoryid']) + '/' + str(forthlayer['categoryid'])
                            arrayindexpath = str(i) + '/' + str(j) + '/' + str(k) + '/' + str(l)
                            request_item = {
                                'name' : forthlayer['name'] ,
                                'categoryid' : forthlayer['categoryid'] , 
                                'parentid' : forthlayer['parentid'] , 
                                'requesturl' : self.scrapeurl_prefix + forthlayer['href'] , 
                                'categorypath' : categorypath , 
                                'arrayindexpath' : arrayindexpath
                            }
                            self.request_sequence.append(request_item)
                            l += 1
                        k += 1
                    j += 1
                i += 1
            print(len(self.request_sequence))

            for i in range(0 , len(self.request_sequence)):
                if self.scrape_crawl_status:
                    self.parseCategoryWithChromeDriverDepthfive(self.request_sequence[i]['requesturl'] , i) 
                else:
                    break
         
    # COMPLETE FUNCTION USAGE ----->>>>> scrape depth-5 categories with selenium driver
    def parseCategoryWithChromeDriverDepthfive(self , request_url , request_sequence_index):     
        print('REQUESTURL ------> ' + request_url)   
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        driver = webdriver.Chrome(self.selenium_webdriver_file_path , chrome_options=options)
        try:
            driver.get(request_url)
            arrayindexpath = self.request_sequence[request_sequence_index]['arrayindexpath'].split('/')
            product_list_wrapper = driver.find_elements_by_css_selector('#san_searchResult')

            is_productlistpage = False
            if (len(product_list_wrapper) > 0):
                is_productlistpage = True
            
            is_cur_category_page = False
            cur_category_selected_item = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li span.selected')
            if (len(cur_category_selected_item) > 0):
                is_cur_category_page = True

            category_product_max_price_searchinput = driver.find_elements_by_css_selector('.retailprice .san_facetValues .san_customRange__input')
            max_price_value = -1
            if (len(category_product_max_price_searchinput) > 1):
                max_price_value = int(category_product_max_price_searchinput[1].get_attribute('placeholder'))        
            
            if is_cur_category_page == True:
                m_bhas_child = False
                m_bis_leaf = True
            else:
                m_bhas_child = True
                m_bis_leaf = False
            
            if max_price_value >= 0:
                if max_price_value < self.scrape_price_minvalue:
                    m_bhas_child = False
                    m_bis_leaf = True
                    m_bhas_product = False
                else:
                    m_bhas_product = True
            else:
                m_bhas_product = True
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])]['has_child'] = m_bhas_child
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])]['is_leaf'] = m_bis_leaf
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])]['has_product'] = m_bhas_product

            print('m_bhas_child' , m_bhas_child , 'm_bis_leaf' , m_bis_leaf , 'm_bhas_product' , m_bhas_product)
            print('self.fifth_layer_startnum ----->>>>> ' + str(self.fifth_layer_startnum))

            action = ActionChains(driver)        
            navigation_lis = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li')
            for navigation_li in navigation_lis:
                ActionChains(driver).move_to_element(navigation_li).perform()

            if m_bhas_child == True:
                navlocalcategory_links = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li a')
                for navlocalcategory_link in navlocalcategory_links:
                    sub_cat_url = navlocalcategory_link.get_attribute('href')
                    sub_cat_name = navlocalcategory_link.text
                    print(sub_cat_name + '---------' + sub_cat_url)
                    if sub_cat_name != None:
                        local_nav_link_item = {
                            'categoryid' : self.fifth_layer_startnum , 
                            'parentid' : self.request_sequence[request_sequence_index]['categoryid'] ,
                            'name' : sub_cat_name , 
                            'depth' : 5
                        }
                        if sub_cat_url != None:
                            local_nav_link_item['href'] = sub_cat_url
                        else:
                            local_nav_link_item['href'] = 'xxxxxxxxx'
                        
                        if 'children' not in self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])].keys():
                            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])]['children'] = []
                        self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'][int(arrayindexpath[3])]['children'].append(local_nav_link_item)

                        scrape_category_log_data = {
                            "fifth_layer_scrape_startnum": self.request_sequence[request_sequence_index]['categoryid'] , 
                            "fifth_layer_startnum": self.fifth_layer_startnum
                        }
                        log_printstring = json.dumps(scrape_category_log_data , indent=4)
                        with open(self.file_path_scrape_category_log, 'w') as outfile:  
                            outfile.write(log_printstring)
                        self.fifth_layer_startnum += 1

            # outstring = json.dumps(self.category_list , indent=4)
            # with open(self.file_path_optimizedcategory, 'w') as outfile:  
            #     outfile.write(outstring)

            with open(self.file_path_optimizedcategory, 'w') as outfile:  
                json.dump(self.category_list , outfile)

            driver.close()
        except TimeoutException:
            driver.close()
            print('Session Time Out !')
            print("Don't worry about it. Please execute the command.")
            self.scrape_crawl_status = False

    # COMPLETE FUNCTION USAGE ----->>>>> scrape depth-4 categories with selenium driver
    def parseCategoryWithChromeDriver(self , request_url , request_sequence_index):     
        print('REQUESTURL ------> ' + request_url)    
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        driver = webdriver.Chrome(self.selenium_webdriver_file_path , chrome_options=options)
        driver.get(request_url)
        arrayindexpath = self.request_sequence[request_sequence_index]['arrayindexpath'].split('/')
        product_list_wrapper = driver.find_elements_by_css_selector('#san_searchResult')

        is_productlistpage = False
        if (len(product_list_wrapper) > 0):
            is_productlistpage = True
        
        is_cur_category_page = False
        cur_category_selected_item = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li span.selected')
        if (len(cur_category_selected_item) > 0):
            is_cur_category_page = True

        category_product_max_price_searchinput = driver.find_elements_by_css_selector('.retailprice .san_facetValues .san_customRange__input')
        max_price_value = -1
        if (len(category_product_max_price_searchinput) > 1):
            max_price_value = int(category_product_max_price_searchinput[1].get_attribute('placeholder'))        
        
        if is_cur_category_page == True:
            m_bhas_child = False
            m_bis_leaf = True
        else:
            m_bhas_child = True
            m_bis_leaf = False
        
        if max_price_value >= 0:
            if max_price_value < 150:
                m_bhas_child = False
                m_bis_leaf = True
                m_bhas_product = False
            else:
                m_bhas_product = True
        else:
            m_bhas_product = True
        self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['has_child'] = m_bhas_child
        self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['is_leaf'] = m_bis_leaf
        self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['has_product'] = m_bhas_product

        print('m_bhas_child' , m_bhas_child , 'm_bis_leaf' , m_bis_leaf , 'm_bhas_product' , m_bhas_product)
        print('self.third_layer_endnum ----->>>>> ' + str(self.third_layer_endnum))

        action = ActionChains(driver)        
        navigation_lis = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li')
        for navigation_li in navigation_lis:
            ActionChains(driver).move_to_element(navigation_li).perform()

        if m_bhas_child == True:
            navlocalcategory_links = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li a')
            for navlocalcategory_link in navlocalcategory_links:
                sub_cat_url = navlocalcategory_link.get_attribute('href')
                sub_cat_name = navlocalcategory_link.text
                print(sub_cat_name + '---------' + sub_cat_url)
                if sub_cat_name != None:
                    local_nav_link_item = {
                        'categoryid' : self.third_layer_endnum , 
                        'parentid' : self.request_sequence[request_sequence_index]['categoryid'] ,
                        'name' : sub_cat_name , 
                        'depth' : 4
                    }
                    if sub_cat_url != None:
                        local_nav_link_item['href'] = sub_cat_url
                    else:
                        local_nav_link_item['href'] = 'xxxxxxxxx'
                    self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'].append(local_nav_link_item)
                    self.third_layer_endnum += 1

        outstring = json.dumps(self.category_list , indent=4)
        with open(self.file_path_optimizedcategory, 'w') as outfile:  
            outfile.write(outstring)
        driver.close()
            
    def parsethirdlayer(self , response):
        response_url = response.request.url
        print(response_url)
        request_sequence_index = -1
        for i in range(0 , len(self.request_sequence)):
            if self.request_sequence[i]['requesturl'] == response_url:
                request_sequence_index = i
        print(request_sequence_index)
        if request_sequence_index >= 0:
            # self.request_sequence.pop(request_sequence_index)
            # print(self.request_sequence[request_sequence_index])            
            arrayindexpath = self.request_sequence[request_sequence_index]['arrayindexpath'].split('/')
                        
            is_productlistpage = False
            if (response.css('#san_searchResult').extract_first() != None):
                is_productlistpage = True
            
            is_cur_category_page = False
            if (response.css('.facet ul li span.selected').extract_first() != None):
                is_cur_category_page = True

            max_price = response.css('.retailprice .san_facetValues .san_customRange__input::attr(placeholder)').extract()
            max_price_value = -1
            if max_price != None:
                if len(max_price) == 2:
                    max_price_value = int(max_price[1])
            
            if is_cur_category_page == True:
                m_bhas_child = False
                m_bis_leaf = True
            else:
                m_bhas_child = True
                m_bis_leaf = False
            
            if max_price_value >= 0:
                if max_price_value < 150:
                    m_bhas_child = False
                    m_bis_leaf = True
                    m_bhas_product = False
                else:
                    m_bhas_product = True
            else:
                m_bhas_product = True
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['has_child'] = m_bhas_child
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['is_leaf'] = m_bis_leaf
            self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['has_product'] = m_bhas_product
            
            print(is_productlistpage , is_cur_category_page , max_price_value)
            print(m_bhas_child , m_bis_leaf , m_bhas_product)
            print('self.third_layer_endnum' , self.third_layer_endnum)
            if m_bhas_child == True:
                navlocalcategory_lis = response.css('.localNavigationWrapper .facet ul li')
                for navlocalcategory_li in navlocalcategory_lis:
                    sub_cat_url = navlocalcategory_li.css('a::attr(href)').extract_first()
                    sub_cat_name = navlocalcategory_li.css('a::text').extract_first()
                    if sub_cat_name == None: 
                        sub_cat_name = navlocalcategory_li.css('span::text').extract_first()
                    if sub_cat_name != None:
                        local_nav_link_item = {
                            'categoryid' : self.third_layer_endnum , 
                            'parentid' : self.request_sequence[request_sequence_index]['categoryid'] ,
                            'name' : sub_cat_name , 
                            'depth' : 4
                        }
                        if sub_cat_url != None:
                            local_nav_link_item['href'] = sub_cat_url
                        else:
                            local_nav_link_item['href'] = 'xxxxxxxxx'
                        self.category_list[int(arrayindexpath[0])]['children'][int(arrayindexpath[1])]['children'][int(arrayindexpath[2])]['children'].append(local_nav_link_item)
                        self.third_layer_endnum += 1
            print('self.third_layer_endnum' , self.third_layer_endnum)

            # if len(self.request_sequence) == 0:
            outstring = json.dumps(self.category_list , indent=4)
            with open('./tmp/optimizedcategory.json', 'w') as outfile:  
                outfile.write(outstring)
        return
            
    def optimizeCategoryList(self , category_list):
        print(len(category_list))
        first_layer_startnum = 11
        first_layer_parentid = 3
        second_layer_startnum = len(category_list) + first_layer_startnum        
        for i in range(0 , len(category_list)):
            category_list[i]['categoryid'] = first_layer_startnum
            category_list[i]['parentid'] = first_layer_parentid
            for j in range(0 , len(category_list[i]['children'])):
                category_list[i]['children'][j]['categoryid'] = second_layer_startnum
                category_list[i]['children'][j]['parentid'] = first_layer_startnum
                second_layer_startnum += 1
            first_layer_startnum += 1
        
        third_layer_startnum = second_layer_startnum
        for i in range(0 , len(category_list)):
            for j in range(0 , len(category_list[i]['children'])):
                for k in range(0 , len(category_list[i]['children'][j]['children'])):
                    category_list[i]['children'][j]['children'][k]['categoryid'] = third_layer_startnum
                    category_list[i]['children'][j]['children'][k]['parentid'] = category_list[i]['children'][j]['categoryid']
                    third_layer_startnum += 1
        
        outstring = json.dumps(category_list , indent=4)
        with open('./tmp/optimizedcategory.json', 'w') as outfile:  
            outfile.write(outstring)
        return

    def parseCategoryName(self , response):
        print('RESPONSE URL -------------------> ' + response.url)
        response_url = response.url
        self.category_start_num = 5251
        navlocalcategory_lis = response.css('.nav_local-category ul li')
        # navlocalcategory_lis = response.css('.localNavigationWrapper ul li')
        for navlocalcategory_li in navlocalcategory_lis:
            sub_cat_url = navlocalcategory_li.css('a::attr(href)').extract_first()
            sub_cat_name = navlocalcategory_li.css('a::text').extract_first()
            if sub_cat_name != None and sub_cat_url != None:
                local_nav_link_item = {
                    'categoryid' : self.category_start_num , 
                    'parentid' : 10000 ,
                    'name' : sub_cat_name , 
                    'href' : sub_cat_url , 
                    'children' : [

                    ]
                }
                # print(sub_cat_name + ' ------ ' + sub_cat_url)
                self.category_list.append(local_nav_link_item)
                self.category_start_num += 1
            else: 
                sub_cat_name = navlocalcategory_li.css('span::text').extract_first()
                if (sub_cat_name != None):
                    local_nav_link_item = {
                        'categoryid' : self.category_start_num , 
                        'parentid' : 10000 ,
                        'name' : sub_cat_name , 
                        'href' : 'xxxxxxxxx' ,
                        'children' : [
                            
                        ]
                    }
                    print(sub_cat_name + ' ------ #')
                    self.category_list.append(local_nav_link_item)
                    self.category_start_num += 1
                else:
                    print('sub_cat_name is None')
                
        outstring = json.dumps(self.category_list , indent=4)
        with open('./tmp/temp.json', 'w') as outfile:  
        # with open('./tmp/othertemp.json', 'w') as outfile:  
            outfile.write(outstring)
