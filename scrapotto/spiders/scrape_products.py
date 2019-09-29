import scrapy
import datetime
# import urllib.request
import urllib.request
import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
from googletrans import Translator
import os , sys

class CategorySpider(scrapy.Spider):
    name = "scrape_products"

    def __init__(self):
        print('--->>> Now we started new product detail Scraping <<<<<---')
        self.scrapeurl_prefix = 'https://www.otto.de'
        self.scrape_detail_url_list = []
        self.scrape_product_minpricevalue = 150.0
        self.scrape_product_price_groupname = 'EK'
        self.m_uploaded_imagefilepath = 'http://127.0.0.1/shopware/media/image/upload/'
        self.m_imagefilepath = '../shopware/media/image/upload/'

        self.xml_filepath_articleminimal = './tmp/xml/article_minimal/'
        self.xml_filepath_article_complete = './tmp/xml/article_complete/'
        self.xml_filepath_article_variants_minimal = './tmp/xml/article_variants_minimal/'
        self.xml_filepath_article_images = './tmp/xml/article_images/'
        self.file_path_scrape_detail_url_list = './tmp/log/scrape_detail_url_list.json'
    
    def start_requests(self):
        with open(self.file_path_scrape_detail_url_list) as json_file:  
            self.scrape_detail_url_list = json.load(json_file)
        i = 0
        for url_item in self.scrape_detail_url_list:
            if url_item['is_scraped'] == False:
                url = self.scrapeurl_prefix + url_item['prd_url']
                print('--->>>>>--- Send Request product-id: ' + url_item['prd_id'] + ' ---<<<<<---')
                yield scrapy.Request(url = url , callback = self.parse)

    def parse(self, response):
        current_crawled_prd_id = response.css('#detailviewWrapper::attr(data-productid)').extract_first()
        print('-->>-- Crawled Success product-id: ' + current_crawled_prd_id + ' --<<--')
        print('-->>-- Request URL : ' + response.request.url + ' --<<--')
        category_ids = ['3']
        cur_crawled_prdsrc_url = ''
        cur_scrapedprdlog_index = 0
        i = 0
        for detail_url_item in self.scrape_detail_url_list:
            if detail_url_item['prd_id'] == current_crawled_prd_id:
                category_ids = detail_url_item['cat_id']
                cur_crawled_prdsrc_url = detail_url_item['prd_url']
                cur_scrapedprdlog_index = i
            i += 1
            
        uploaded_imagefilepath = self.m_uploaded_imagefilepath
        imagefilepath = self.m_imagefilepath
        if not os.path.exists(imagefilepath):
            # FOR LINUX
            # os.mkdir(imagefilepath , 0777)
            # FOR WINDOWS
            os.mkdir(imagefilepath , 777)
        productdescription = ""
        prd_description_long_text = ""
        # if (response.css('.prd_section .js_prd_detailIconsTarget').extract_first() != None):
        #     productdescription = response.css('.prd_section .js_prd_detailIconsTarget').extract_first()
        if (response.css('.prd_section .js_prd_sellingPointsTarget').extract_first() != None):
            productdescription += response.css('.prd_section .js_prd_sellingPointsTarget').extract_first()
        if (response.css('.prd_section #js_prd_productInfoTarget .prd_productInfo__description').extract_first() != None):
            productdescription += response.css('.prd_section #js_prd_productInfoTarget .prd_productInfo__description').extract_first()
            prd_description_long_text = response.css('.prd_section #js_prd_productInfoTarget .prd_productInfo__description').extract_first()
        
        productshortdescription = ""
        if (response.css('.prd_section #js_prd_productInfoTarget .prd_productInfo__description').extract_first() != None):
            productshortdescription = response.css('.prd_section #js_prd_productInfoTarget .prd_productInfo__description').extract_first()        
        
        product_data_str = response.css('#productDataJson').extract_first()
        product_data_str = product_data_str.replace('\n' , ' ')
        product_data_str = product_data_str.replace('<script id="productDataJson" type="application/json">' , ' ' , 1)
        product_data_str = product_data_str.replace('</script>' , ' ' , 1)
        prd_scrape_data = json.loads(product_data_str)
        if (prd_scrape_data == None): 
            print('-->>-- Crawled Failed ! No exist product-url: ' + cur_crawled_prdsrc_url + ' --<<--')
            return
        else:
            print('-->>-- Crawled Success ! Exist product-url: ' + cur_crawled_prdsrc_url + ' --<<--')
        if 'imageConfig' not in prd_scrape_data.keys():
            product_imagedata_str = response.css('#js_prd_imageConfig').extract_first()
            product_imagedata_str = product_imagedata_str.replace('\n' , ' ')
            product_imagedata_str = product_imagedata_str.replace('<script id="js_prd_imageConfig" type="application/json">' , ' ' , 1)
            product_imagedata_str = product_imagedata_str.replace('</script>' , ' ' , 1)
            prd_scrape_imagedata = json.loads(product_imagedata_str)
            prd_scrape_data['imageConfig'] = prd_scrape_imagedata

        imageServerPath = prd_scrape_data['imageConfig']['imageServerPath'].replace('#ft5_slash#' , '/')
        prd_optimized_data = {
            'prd_id' : 'SW' + prd_scrape_data['id'] , 
            'prd_brand' : {
                'prd_brand_name' : "Shopware Supplier" , 
                'prd_brand_logo_url' : ''
            } ,        
            'distinctdimensions' : prd_scrape_data['distinctDimensions']
        }
        
        if (prd_scrape_data['brand'] != None and prd_scrape_data['imageConfig']['presets']['brandLogo'] != None):
            prd_optimized_data['prd_brand']['prd_brand_name'] = prd_scrape_data['brand']
            if prd_scrape_data['brandImageId'] != None and prd_scrape_data['imageConfig']['presets']['brandLogo'] != None:
                prd_optimized_data['prd_brand']['prd_brand_logo_url'] = imageServerPath + prd_scrape_data['brandImageId'] + prd_scrape_data['imageConfig']['presets']['brandLogo']
                brandlogofilepath = './tmp/manufactuerlogo/' + prd_optimized_data['prd_brand']['prd_brand_name'] + '.jpg'
                # DOWNLOAD
                self.uploadfile(prd_optimized_data['prd_brand']['prd_brand_logo_url'] , brandlogofilepath)

        i = 0
        for dimension_item in prd_optimized_data['distinctdimensions']:
            if (dimension_item['type'] == 'color'):
                j = 0
                for dimension_option in dimension_item['values']: 
                    # prd_optimized_data['distinctdimensions'][i]['values'][j]['icon-img-url'] = imageServerPath + dimension_option['iconId'] + prd_scrape_data['imageConfig']['presets']['colorDimension']
                    j += 1
            i += 1        
        
        variations = []
        is_product_price_over_limit = False
        for variation in prd_scrape_data['sortedVariationIds']:
            variation_price = str(prd_scrape_data['variations'][variation]['displayPrice']['techPriceAmount'])
            price_str = str(prd_scrape_data['variations'][variation]['displayPrice']['formattedPriceAmount'])
            price_str = price_str.replace('.' , ',')
            if price_str != None:
                buffer_price_strings = price_str.split(',')
                variation_price = ''
                for buf_index in range(0 , len(buffer_price_strings)):
                    if (buf_index < (len(buffer_price_strings) - 1)):
                        variation_price = variation_price + buffer_price_strings[buf_index]
                    else:
                        variation_price = variation_price + '.' + buffer_price_strings[buf_index]
            variation_price = float(variation_price)   
            print('variation_price--->>' + str(variation_price))             
            if (variation_price >= self.scrape_product_minpricevalue):
                is_product_price_over_limit = True
            else:
                print('price--->>' + str(prd_scrape_data['variations'][variation]['displayPrice']['techPriceAmount']))

            variation_item = {
                'variationid' : prd_scrape_data['variations'][variation]['id'] , 
                'prd_name' : prd_scrape_data['variations'][variation]['name'] , 
                'prd_price' : prd_scrape_data['variations'][variation]['displayPrice']['formattedPriceAmount'] , 
                'prd_pseudoprice' : prd_scrape_data['variations'][variation]['displayPrice']['comparativePriceAmount'] ,              
            }
            variation_image_array = []
            i = 1
            for variation_img in prd_scrape_data['variations'][variation]['images']:
                image_item = {
                    'mainImage' : variation_img['mainImage'] ,    
                    'image_url' : imageServerPath + variation_img['id']
                }
                filename = imagefilepath + prd_scrape_data['variations'][variation]['id'] + '_' + str(i) + '.jpg'
                uploaded_imagefilepath = self.m_uploaded_imagefilepath
                uploaded_imagefilepath += prd_scrape_data['variations'][variation]['id'] + '_' + str(i) + '.jpg'
                image_item['image_src_url'] = image_item['image_url']
                image_item['image_write_path'] = filename
                image_item['image_url'] = uploaded_imagefilepath
                i += 1
                
                variation_image_array.append(image_item)
            variation_item['prd_images'] = variation_image_array
            buffer_array = []
            for variation_dimension_item in prd_scrape_data['variations'][variation]['dimensions']['dimension']:
                variation_dimension_item_keys = variation_dimension_item.keys()
                variation_configurator_data = {}
                for dict_key in variation_dimension_item:                    
                    variation_configurator_data['config_group_name'] = variation_dimension_item[dict_key]['displayName']
                    variation_configurator_data['config_option_name'] = variation_dimension_item[dict_key]['value'].replace('#ft5_slash#' , '/')
                buffer_array.append(variation_configurator_data)
            
            variation_item['variation_configurator'] = buffer_array

            # Description
            variation_item['description'] = ""
            # variation_item['description'] = "<div class='prd_detailIcons'>"
            # for detail_quality in prd_scrape_data['variations'][variation]['detailIcons']['quality']:
            #     detail_quality_imageurl = detail_quality['displayName'].replace('#ft5_slash#' , '/')
            #     variation_item['description'] += '<a class="prd_detailIcons__item js_openInPaliLayer js_hasPaliTooltip" href= data-tooltip="' + detail_quality['displayName'] + '" data-tooltip-pos="mouse" data-tooltip-touch="false" data-dialog-sizeid="100" data-tracking-key="' + detail_quality['name'] + '"><img class="prd_detailIcons__image"src="' + detail_quality_imageurl + '"><span class="prd_detailIcons__text">' + detail_quality['displayName'] + '</span></a>'            
            # variation_item['description'] += "</div>"
            variation_item['description'] += "<div class=\"prd_sellingPoints\"><hr class=\"p_line100\"><ul class=\"prd_unorderedList\">"
            for detail_sellingpoints in prd_scrape_data['variations'][variation]['sellingPoints']['sellingPoint']:
                variation_item['description'] += "<li>" + detail_sellingpoints + "</li>"
            variation_item['description'] += "</ul></div>"            

            if (prd_scrape_data['description'] != None):
                variation_item['description'] += prd_scrape_data['description']
            else:
                variation_item['description'] += prd_description_long_text

            # Property Table
            variation_item['description'] += response.css('#js_prd_productInfoAccordion').extract_first()

            variation_item['metatitle'] = prd_scrape_data['variations'][variation]['title']
            variation_item['ean'] = prd_scrape_data['variations'][variation]['ean']
            variations.append(variation_item)
        
        print('---is_product_price_over_limit--- >>> ' + str(is_product_price_over_limit))
        # Add Variations 
        prd_optimized_data['variations'] = variations
        
        if is_product_price_over_limit == True:
            # Generate Minimal XML Data
            xmldata = ET.Element('Root')
            articlesdata = ET.SubElement(xmldata , 'articles')
            articledata = ET.SubElement(articlesdata , 'article')
            # articledata = ET.Element('article')

            el_ordernumber = ET.SubElement(articledata , 'ordernumber')
            el_ordernumber.text = prd_optimized_data['prd_id']
            el_mainnumber = ET.SubElement(articledata , 'mainnumber')
            el_mainnumber.text = prd_optimized_data['prd_id']
            el_name = ET.SubElement(articledata , 'name')
            el_name.text = ''
            if (len(prd_optimized_data['variations']) > 0):
                el_name.text = prd_optimized_data['variations'][0]['prd_name']
            el_supplier = ET.SubElement(articledata , 'supplier')
            el_supplier.text = ' '
            if (prd_optimized_data['prd_brand']['prd_brand_name'] != ''):
                el_supplier.text = prd_optimized_data['prd_brand']['prd_brand_name']
            el_tax = ET.SubElement(articledata , 'tax')
            el_tax.text = '19,00'        
            el_prices = ET.SubElement(articledata , 'prices')
            el_price = ET.SubElement(el_prices , 'price')
            el_price_group = ET.SubElement(el_price , 'group')
            # el_price_group.text = 'EK'
            el_price_group.text = self.scrape_product_price_groupname
            el_price_price = ET.SubElement(el_price , 'price')
            el_price_price.text = '150,00'        
            if (len(prd_optimized_data['variations']) > 0):
                el_price_price.text = prd_optimized_data['variations'][0]['prd_price']
            if (len(prd_optimized_data['variations']) > 0 and prd_optimized_data['variations'][0]['prd_pseudoprice'] != None):
                el_price_pseudoprice = ET.SubElement(el_price , 'pseudoprice')
                el_price_pseudoprice.text = prd_optimized_data['variations'][0]['prd_pseudoprice']
            el_active = ET.SubElement(articledata , 'active')
            el_active.text = "1"
            el_category = ET.SubElement(articledata , 'category')
            # Configurate Category
            el_category = self.get_categoryconfig_elementtree(el_category , category_ids)

            self.generateXml(xmldata , self.xml_filepath_articleminimal + current_crawled_prd_id + "_articles_minimal.xml")  
            
            # Generate Complete XML Data
            xmldata = ET.Element('Root')
            articlesdata = ET.SubElement(xmldata , 'articles')
            articledata = ET.SubElement(articlesdata , 'article')
            el_ordernumber = ET.SubElement(articledata , 'ordernumber')
            el_ordernumber.text = prd_optimized_data['prd_id']
            el_mainnumber = ET.SubElement(articledata , 'mainnumber')
            el_mainnumber.text = prd_optimized_data['prd_id']
            el_name = ET.SubElement(articledata , 'name')
            el_name.text = ''
            if (len(prd_optimized_data['variations']) > 0):
                el_name.text = prd_optimized_data['variations'][0]['prd_name']       
            el_supplier = ET.SubElement(articledata , 'supplier')
            el_supplier.text = ' '
            if (prd_optimized_data['prd_brand']['prd_brand_name'] != ''):
                el_supplier.text = prd_optimized_data['prd_brand']['prd_brand_name']
            el_tax = ET.SubElement(articledata , 'tax')
            el_tax.text = '19,00'        
            el_prices = ET.SubElement(articledata , 'prices')
            el_price = ET.SubElement(el_prices , 'price')
            el_price_group = ET.SubElement(el_price , 'group')
            el_price_group.text = 'EK'
            el_price_price = ET.SubElement(el_price , 'price')
            el_price_price.text = '150,00'        
            if (len(prd_optimized_data['variations']) > 0):
                el_price_price.text = prd_optimized_data['variations'][0]['prd_price']
            if (len(prd_optimized_data['variations']) > 0 and prd_optimized_data['variations'][0]['prd_pseudoprice'] != None):
                el_price_pseudoprice = ET.SubElement(el_price , 'pseudoprice')
                el_price_pseudoprice.text = prd_optimized_data['variations'][0]['prd_pseudoprice']
            el_active = ET.SubElement(articledata , 'active')
            el_active.text = "1"
            el_instock = ET.SubElement(articledata , 'instock')
            el_instock.text = "100"
            el_stockmin = ET.SubElement(articledata , 'stockmin')
            el_stockmin.text = "20"
            el_description_short = ET.SubElement(articledata , 'description')
            if (productshortdescription != ""):
                el_description_short.text = productshortdescription
            else:
                el_description_short.text = " "
            el_description_long = ET.SubElement(articledata , 'description_long')
            el_description_long.text = " "
            if (len(prd_optimized_data['variations']) > 0):
                el_description_long.text += prd_optimized_data['variations'][0]['description']
            el_description_long.text += " "  
            el_shippingfree = ET.SubElement(articledata , 'shippingfree')
            el_shippingfree.text = "0"
            el_minpurchase = ET.SubElement(articledata , 'minpurchase')
            el_minpurchase.text = "1"
            el_unitID = ET.SubElement(articledata , 'unitID')
            el_unitID.text = "9"
            el_pricegroupActive = ET.SubElement(articledata , 'pricegroupActive')
            el_pricegroupActive.text = "0"
            el_laststock = ET.SubElement(articledata , 'laststock')
            el_laststock.text = "0"
            el_weight = ET.SubElement(articledata , 'weight')
            el_weight.text = "0,000"
            if (len(prd_optimized_data['variations']) > 0):
                if prd_optimized_data['variations'][0]['ean'] != None:
                    el_ean = ET.SubElement(articledata , 'ean')
                    el_ean.text = str(prd_optimized_data['variations'][0]['ean'])

            if (len(prd_optimized_data['variations']) > 0):
                el_configurators = ET.SubElement(articledata , 'configurators')
                for buffer_variation in prd_optimized_data['variations'][0]['variation_configurator']:                    
                    el_configurator = ET.SubElement(el_configurators , 'configurator')
                    el_config_type = ET.SubElement(el_configurator , 'configuratortype')                    
                    el_config_type.text = '0'      # if type == color 2
                    el_config_group = ET.SubElement(el_configurator , 'configuratorGroup')  
                    if (buffer_variation['config_group_name'] == 'Unknown'):
                        el_config_group.text = 'Variante'
                    else:
                        el_config_group.text = buffer_variation['config_group_name']
                    el_config_option = ET.SubElement(el_configurator , 'configuratorOptions')  
                    el_config_option.text = buffer_variation['config_option_name']
                    if el_config_group.text == 'Farbe':
                        # Color Case Options Setting
                        el_config_option.text = buffer_variation['config_option_name'].capitalize()
                        el_config_option.text = self.translate(buffer_variation['config_option_name'].capitalize())                    
                        print('articlecomplete congig-options - ' + el_config_option.text)
            el_category = ET.SubElement(articledata , 'category')
            el_category = self.get_categoryconfig_elementtree(el_category , category_ids)
            
            el_purchasePrice = ET.SubElement(articledata , 'purchasePrice')
            el_purchasePrice.text = '0'
            el_metatitle = ET.SubElement(articledata , 'metatitle')
            el_metatitle.text = ' '
            if (len(prd_optimized_data['variations']) > 0):
                el_metatitle.text += prd_optimized_data['variations'][0]['metatitle']  
            self.generateXml(xmldata , self.xml_filepath_article_complete + current_crawled_prd_id + "_articles_complete.xml")  

            # Generate Variants, ImageURL XML Data
            xmldata = ET.Element('Root')
            articlesdata = ET.SubElement(xmldata , 'articles')
            imagexmldata = ET.Element('Root')
            imagesdata = ET.SubElement(imagexmldata , 'images')
            index_subproduct = 0
            color_group_state = []
            for variation_item in prd_optimized_data['variations']:
                articledata = ET.SubElement(articlesdata , 'article')
                el_ordernumber = ET.SubElement(articledata , 'ordernumber')
                
                ordernumber = ''
                if (index_subproduct > 0): 
                    ordernumber = prd_optimized_data['prd_id'] + '.' + str(index_subproduct)
                else: 
                    ordernumber = prd_optimized_data['prd_id']                
                el_ordernumber.text = ordernumber
                                
                el_mainnumber = ET.SubElement(articledata , 'mainnumber')
                el_mainnumber.text = prd_optimized_data['prd_id']

                el_name = ET.SubElement(articledata , 'name')
                el_name.text = variation_item['prd_name']
                el_active = ET.SubElement(articledata , 'active')
                el_active.text = "1"        
                el_prices = ET.SubElement(articledata , 'prices')
                el_price = ET.SubElement(el_prices , 'price')
                el_price_group = ET.SubElement(el_price , 'group')
                el_price_group.text = 'EK'
                el_price_price = ET.SubElement(el_price , 'price')
                el_price_price.text = variation_item['prd_price']
                if (variation_item['prd_pseudoprice'] != None):
                    el_price_pseudoprice = ET.SubElement(el_price , 'pseudoprice')
                    el_price_pseudoprice.text = variation_item['prd_pseudoprice']

                is_exist_color = False
                cur_color = ''
                for config_item in variation_item['variation_configurator']:
                    el_configurator = ET.SubElement(articledata , 'configurator')
                    el_configGroupName = ET.SubElement(el_configurator , 'configGroupName')
                    if (config_item['config_group_name'] == 'Unknown'):
                        el_configGroupName.text = 'Variante'
                    else:
                        el_configGroupName.text = config_item['config_group_name']
                    el_configOptionName = ET.SubElement(el_configurator , 'configOptionName')
                    # Change first letter Uppercase                                
                    el_configOptionName.text = config_item['config_option_name'].capitalize()
                    el_configOptionName.text = self.translate(config_item['config_option_name'].capitalize())    
                    if (config_item['config_group_name'] == 'Farbe'):
                        is_exist_color = True
                        cur_color = config_item['config_option_name']
                        print(el_configOptionName.text)
                image_count = 1
                color_group_state_inserted = False
                if is_exist_color == True:
                    for color_exist_item in color_group_state:
                        if color_exist_item == cur_color:
                            color_group_state_inserted = True

                    # if cur_color in color_group_state : 
                    if color_group_state_inserted == False: 
                        color_group_state.append(cur_color)

                for variation_image in variation_item['prd_images']:
                    if color_group_state_inserted == True:
                        continue                
                    # DOWNLOAD IMAGE START
                    self.uploadfile(variation_image['image_src_url'] , variation_image['image_write_path'])
                    # END
                    el_image = ET.SubElement(imagesdata , 'image')
                    el_ordernumberimage = ET.SubElement(el_image , 'ordernumber')       
                    el_ordernumberimage.text = str(ordernumber)
                    el_imagetag = ET.SubElement(el_image , 'image')
                    el_imagetag.text = variation_image['image_url']
                    el_imagemain = ET.SubElement(el_image , 'main')
                    if variation_image['mainImage'] == True:
                        el_imagemain.text = '1'
                    else:
                        el_imagemain.text = '2'     
                    el_imagedescription = ET.SubElement(el_image , 'description')
                    el_imagedescription.text = " "           
                    el_imageposition = ET.SubElement(el_image , 'position')
                    el_imageposition.text = str(image_count)
                    el_imagewidth = ET.SubElement(el_image , 'width')
                    el_imagewidth.text = "0"
                    el_imageheight = ET.SubElement(el_image , 'height')
                    el_imageheight.text = "0"
                    if (is_exist_color and cur_color != ''):
                        el_imagerelations = ET.SubElement(el_image , 'relations')
                        el_imagerelations.text = "{Farbe:" + cur_color + "}"
                    image_count += 1

                index_subproduct += 1

            
            self.generateXml(xmldata , self.xml_filepath_article_variants_minimal + current_crawled_prd_id + "_article_variants_minimal.xml")  
            self.generateXml(imagexmldata , self.xml_filepath_article_images + current_crawled_prd_id + "_article_images.xml")  
        
        self.scrape_detail_url_list[cur_scrapedprdlog_index]['is_scraped'] = True        
        if is_product_price_over_limit == False:
            print('poped prd_url --> ' + self.scrape_detail_url_list[cur_scrapedprdlog_index]['prd_url'])
            self.scrape_detail_url_list.pop(cur_scrapedprdlog_index)
        with open(self.file_path_scrape_detail_url_list, 'w') as outfile:  
            json.dump(self.scrape_detail_url_list , outfile)

    def get_categoryconfig_elementtree(self , parent_elementtree , category_ids):
        for category_id in category_ids:            
            el_categories = ET.SubElement(parent_elementtree , 'categories')
            el_categories.text = str(category_id)
        return parent_elementtree

    def uploadfile(self, src_url, dest_path):
        print(dest_path)
        imagefile = open(dest_path , 'wb') 
        # imagefile.write(urllib.request.urlopen(src_url).read())
        imagefile.write(urllib.urlopen(src_url).read())
        imagefile.close()
    
    def generateXml(self , xmlElementTree , xmlFilename):
        if xmlElementTree != None:            
            xmlstring = minidom.parseString(ET.tostring(ET.ElementTree(xmlElementTree).getroot(),'utf-8')).toprettyxml(indent="\t")
            buffertree = ET.fromstring(xmlstring)
            ET.ElementTree(buffertree).write(xmlFilename , xml_declaration=True , encoding="UTF-8" ,method="xml")

    def translate(self, translateword):
        retVal = translateword        
        return retVal