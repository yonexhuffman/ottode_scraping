import scrapy
import json
from xml.dom import minidom
import xml.etree.ElementTree as ET
import glob
import os , sys
from datetime import datetime

class QuotesSpider(scrapy.Spider):
    name = "generate_xmldata"
    
    def __init__(self):
        self.status = 2
        self.file_path_minimalfiles = './tmp/xml/article_minimal/'
        self.file_path_completefiles = './tmp/xml/article_complete/'
        self.file_path_variantsfiles = './tmp/xml/article_variants_minimal/'
        self.file_path_imagesfiles = './tmp/xml/article_images/'  

    def start_requests(self):
        if self.status == 1:                
            urls = [
                'https://www.otto.de' , 
            ]        
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse)        
        elif self.status == 2:       
            # FOR WINDOWS
            # path = self.file_path_minimalfiles
            # minimal_files = [f for f in glob.glob(path + "**/*.xml", recursive=True)]
            # path = self.file_path_completefiles
            # complete_files = [f for f in glob.glob(path + "**/*.xml", recursive=True)]
            # path = self.file_path_variantsfiles
            # variants_files = [f for f in glob.glob(path + "**/*.xml", recursive=True)]
            # path = self.file_path_imagesfiles
            # images_files = [f for f in glob.glob(path + "**/*.xml", recursive=True)]

            # FOR WINDOWS , LINUX
            path = self.file_path_minimalfiles
            minimal_files = []
            for r, d, f in os.walk(path):
                for file in f:
                    if '.xml' in file:
                        minimal_files.append(os.path.join(r, file))
                        
            path = self.file_path_completefiles
            complete_files = []
            for r, d, f in os.walk(path):
                for file in f:
                    if '.xml' in file:
                        complete_files.append(os.path.join(r, file))
                        
            path = self.file_path_variantsfiles
            variants_files = []
            for r, d, f in os.walk(path):
                for file in f:
                    if '.xml' in file:
                        variants_files.append(os.path.join(r, file))
                        
            path = self.file_path_imagesfiles
            images_files = []
            for r, d, f in os.walk(path):
                for file in f:
                    if '.xml' in file:
                        images_files.append(os.path.join(r, file))

            self.generateXmlData(minimal_files , complete_files , variants_files , images_files)
    
    def parse(self , response):
        print(response.url)
    
    def generateXml(self , xmlElementTree , xmlFilename):
        if xmlElementTree != None:
            xmlstring = minidom.parseString(ET.tostring(ET.ElementTree(xmlElementTree).getroot(),'utf-8')).toprettyxml(indent="\t")
            buffertree = ET.fromstring(xmlstring)
            ET.ElementTree(buffertree).write(xmlFilename , xml_declaration=True , encoding="UTF-8" ,method="xml")

    def generateXmlData(self , minimal_files , complete_files , variants_files , images_files):
        xml_element_tree_articleminimal = None
        for xml_file in minimal_files:
            # get root
            data = ET.parse(xml_file).getroot()
            for result in data.iter('articles'):
                if xml_element_tree_articleminimal is None:
                    xml_element_tree_articleminimal = data 
                    insertion_point = xml_element_tree_articleminimal.findall("./articles")[0]
                else:
                    insertion_point.extend(result) 
        xml_element_tree_articlecomplete = None
        for xml_file in complete_files:
            # get root
            data = ET.parse(xml_file).getroot()
            for result in data.iter('articles'):
                if xml_element_tree_articlecomplete is None:
                    xml_element_tree_articlecomplete = data 
                    insertion_point = xml_element_tree_articlecomplete.findall("./articles")[0]
                else:
                    insertion_point.extend(result) 
        xml_element_tree_articlevariants = None
        for xml_file in variants_files:
            # get root
            data = ET.parse(xml_file).getroot()
            for result in data.iter('articles'):
                if xml_element_tree_articlevariants is None:
                    xml_element_tree_articlevariants = data 
                    insertion_point = xml_element_tree_articlevariants.findall("./articles")[0]
                else:
                    insertion_point.extend(result) 
        xml_element_tree_articleimages = None
        for xml_file in images_files:
            # get root
            data = ET.parse(xml_file).getroot()
            for result in data.iter('images'):
                if xml_element_tree_articleimages is None:
                    xml_element_tree_articleimages = data 
                    insertion_point = xml_element_tree_articleimages.findall("./images")[0]
                else:
                    insertion_point.extend(result) 
        
        directory = "./tmp/xml/" + datetime.today().strftime('%Y-%m-%d_%H_%M_%S') + "/"
        if not os.path.exists(directory):
            # FOR LINUX
            # os.mkdir(directory , 0777)
            # FOR WINDOWS
            os.mkdir(directory , 777)       

        self.generateXml(xml_element_tree_articleminimal , directory + "1_articles_minimal.xml")  
        self.generateXml(xml_element_tree_articlecomplete , directory + "2_articles_complete.xml")  
        self.generateXml(xml_element_tree_articlevariants , directory + "3_article_variants_minimal.xml")  
        self.generateXml(xml_element_tree_articleimages , directory + "4_article_images.xml")  
                
        for deltefile in minimal_files:            
            if os.path.isfile(deltefile):
                os.remove(deltefile)
        for deltefile in complete_files:            
            if os.path.isfile(deltefile):
                os.remove(deltefile)
        for deltefile in variants_files:            
            if os.path.isfile(deltefile):
                os.remove(deltefile)
        for deltefile in images_files:            
            if os.path.isfile(deltefile):
                os.remove(deltefile)
        return