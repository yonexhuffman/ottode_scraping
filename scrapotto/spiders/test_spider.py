import scrapy
import json
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import sys
from datetime import datetime

class QuotesSpider(scrapy.Spider):
    name = "testspider"
    
    def __init__(self):
        self.status = 2
        self.scrapeurl_prefix = 'https://www.otto.de'
        self.scrape_price_minvalue = 150
        self.init_depth_value = 6
        self.selenium_webdriver_file_path = 'C:/chromedriver.exe'
        # self.selenium_webdriver_file_path = '/usr/bin/chromedriver'
        # self.file_path_optimizedcategory = './tmp/log/__optimizedcategory.json'
        self.file_path_optimizedcategory = './tmp/log/optimizedcategory.json'
        self.file_path_scrape_category_log = './tmp/log/scrape_category_log_underdepth5.json'        
        self.request_sequence = []
        self.category_list = []
        self.scrape_crawl_status = True
        self.category_id_num = 0
        self.scrape_start_time = datetime.today().strftime('%Y-%m-%d_%H_%M_%S')
        self.scrape_end_time = datetime.today().strftime('%Y-%m-%d_%H_%M_%S')
        print('START TIME ----------> ' + self.scrape_start_time)

    def start_requests(self):
        if self.status == 1:                
            urls = [
                'https://www.otto.de' , 
            ]        
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse , errback=self.errback)        
        elif self.status == 2:
            with open(self.file_path_scrape_category_log) as json_file:  
                log_data = json.load(json_file)  
            self.category_id_num = log_data['category_id_num']
            self.arrayindexpath = [int(i) for i in log_data['arrayindexpath'].split('/')]  
            with open(self.file_path_optimizedcategory) as json_file:  
                self.category_list = json.load(json_file)  

            i = 0
            for firstlayer in self.category_list:
                j = 0
                for secondlayer in firstlayer['children']:
                    k = 0
                    for thirdlayer in secondlayer['children']:   
                        l = 0
                        if 'children' not in thirdlayer.keys():
                            k += 1
                            continue
                        for forthlayer in thirdlayer['children']:   
                            m = 0
                            if 'children' not in forthlayer.keys():
                                l += 1
                                continue
                            for fifthlayer in forthlayer['children']:
                                arrayindexpath = str(i) + '/' + str(j) + '/' + str(k) + '/' + str(l) + '/' + str(m)
                                request_item = {
                                    'name' : fifthlayer['name'] ,
                                    'categoryid' : fifthlayer['categoryid'] , 
                                    'parentid' : fifthlayer['parentid'] , 
                                    'requesturl' : self.scrapeurl_prefix + fifthlayer['href'] ,  
                                    'arrayindexpath' : arrayindexpath
                                }
                                self.request_sequence.append(request_item)
                                m += 1
                            l += 1
                        k += 1
                    j += 1
                i += 1

            print(len(self.request_sequence))
            # for count in range(0 , 20):
            #     print(self.request_sequence[count])
            b_start_scrape = False
            for i in range(0 , len(self.request_sequence)):
            # for i in range(0 , 0):
                # print(self.request_sequence[i])
                if log_data['arrayindexpath'].find(self.request_sequence[i]['arrayindexpath']) != -1:
                    b_start_scrape = True
                if b_start_scrape:
                    if self.scrape_crawl_status:
                        self.parseUnderDepthfive(i , self.init_depth_value , self.request_sequence[i]['arrayindexpath']) 
                    else:
                        break
    
    def parseUnderDepthfive(self , request_sequence_index , cur_node_depth , cur_arrayindexpath):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            options.add_argument('window-size=1920x1080')
            options.add_argument("disable-gpu")
            driver = webdriver.Chrome(self.selenium_webdriver_file_path , chrome_options=options)
            # driver = webdriver.Chrome(self.selenium_webdriver_file_path)
            driver.get(self.request_sequence[request_sequence_index]['requesturl'])
            arrayindexpath = cur_arrayindexpath.split('/')
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

            cur_node_status = {
                'm_has_child' : m_bhas_child , 
                'm_bis_leaf' : m_bis_leaf , 
                'm_bhas_product' : m_bhas_product
            }

            action = ActionChains(driver)        
            navigation_lis = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li')
            for navigation_li in navigation_lis:
                ActionChains(driver).move_to_element(navigation_li).perform()

            cur_node_children = []
            if m_bhas_child == True:
                navlocalcategory_links = driver.find_elements_by_css_selector('.localNavigationWrapper .facet ul li a')
                for navlocalcategory_link in navlocalcategory_links:
                    sub_cat_url = navlocalcategory_link.get_attribute('href')
                    sub_cat_name = navlocalcategory_link.text
                    print(sub_cat_name + '---------' + sub_cat_url)
                    if sub_cat_name != None:
                        local_nav_link_item = {
                            'categoryid' : self.category_id_num , 
                            'parentid' : self.request_sequence[request_sequence_index]['categoryid'] ,
                            'name' : sub_cat_name , 
                            'depth' : cur_node_depth
                        }
                        if sub_cat_url != None:
                            local_nav_link_item['href'] = sub_cat_url
                        else:
                            local_nav_link_item['href'] = 'xxxxxxxxx'
                        
                        cur_node_children.append(local_nav_link_item)
                        self.category_id_num += 1
            
            self.setitemvalue(self.category_list , cur_node_status , cur_node_children , cur_arrayindexpath)
            scrape_category_log_data = {
                "arrayindexpath": cur_arrayindexpath , 
                "category_id_num" : self.category_id_num
            }
            log_printstring = json.dumps(scrape_category_log_data , indent=4)
            with open(self.file_path_scrape_category_log, 'w') as outfile:  
                outfile.write(log_printstring)
            for i in range(0 , len(cur_node_children)):
                child_arrayindexpath = cur_arrayindexpath + '/' + str(i)
                request_item = {
                    'name' : cur_node_children[i]['name'] ,
                    'categoryid' : cur_node_children[i]['categoryid'] , 
                    'parentid' : cur_node_children[i]['parentid'] , 
                    'arrayindexpath' : child_arrayindexpath
                }
                if (cur_node_children[i]['href'].find(self.scrapeurl_prefix) != -1):
                    request_item['requesturl'] = cur_node_children[i]['href']
                else:
                    request_item['requesturl'] = self.scrapeurl_prefix + cur_node_children[i]['href']

                self.request_sequence.append(request_item)
                # driver.close()
                self.parseUnderDepthfive(len(self.request_sequence) - 1 , cur_node_depth + 1 , child_arrayindexpath)

            # outstring = json.dumps(self.category_list , indent=4)
            # with open(self.file_path_optimizedcategory, 'w') as outfile:  
            #     outfile.write(outstring)

            with open(self.file_path_optimizedcategory, 'w') as outfile:  
                json.dump(self.category_list , outfile)

            driver.close()
        # except TimeoutException:
        #     driver.close()
        #     print('Session Time Out !')
        #     print("Don't worry about it. Please execute the command.")
        #     self.scrape_crawl_status = False
            
        #     self.scrape_end_time = datetime.today().strftime('%Y-%m-%d_%H_%M_%S')
        #     print('START TIME ----------> ' + self.scrape_start_time)
        #     print('END TIME ----------> ' + self.scrape_end_time)
        except Exception as e:
            # driver.close()
            print(e)
            print("Don't worry about it. Please continue scrapping.")
            self.scrape_crawl_status = False
            self.scrape_end_time = datetime.today().strftime('%Y-%m-%d_%H_%M_%S')
            print('START TIME ----------> ' + self.scrape_start_time)
            print('END TIME ----------> ' + self.scrape_end_time)
    
    def setitemvalue(self , array , cur_node_status , cur_node_children , arraypath):
        path = arraypath.split("/")
        if len(path) > 1:
            index = path[0]
            path.pop(0)
            s = [str(i) for i in path]     
            seperater = "/"
            arraypath_res = seperater.join(s)        
            if 'children' not in array[int(index)].keys():
                array[int(index)]['children'] = []
            self.setitemvalue(array[int(index)]['children'] , cur_node_status , cur_node_children , arraypath_res)
        elif len(path) == 1:
            array[int(path[0])]['m_has_child'] = cur_node_status['m_has_child']
            array[int(path[0])]['m_bis_leaf'] = cur_node_status['m_bis_leaf']
            array[int(path[0])]['m_bhas_product'] = cur_node_status['m_bhas_product']
            array[int(path[0])]['children'] = cur_node_children
        return array

    def parse(self , response):
        print(response.url)

    def errback(self , failure):
        print('ERROR CALLBACK TEST')
        print(failure)
    