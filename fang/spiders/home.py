# -*- coding: utf-8 -*-
import json
import re
import urllib
from urllib import request
from urllib.parse import urlencode
from PIL import Image  # 导入识别图形的库
import requests
from base64 import b64encode  # 导入b64编码库
import scrapy
from bs4 import BeautifulSoup
# import js2xml

from fang.items import NewHouseItem, ESFHouseItem, HouseIntroItem


class HomeSpider(scrapy.Spider):
    name = 'home'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs = response.xpath('//div[@class="outCont"]//tr')
        province =None
        for tr in trs:
            print("--------------------", type(tr), tr)
            tds = tr.xpath('.//td[not(@class)]')
            province_id = tds[0]
            province_text = province_id.xpath('.//text()').get()
            province_text =re.sub(r'\s','',province_text)
            if province_text:
                province = province_text
            # 不爬取海外城市的消息
            if province == '其它':
                continue
            city_id = tds[1]
            city_links = city_id.xpath('.//a')
            for city_link in city_links:
                city = city_link.xpath('.//text()').get()
                city_url = city_link.xpath('.//@href').get()
                # 构建新房链接
                url_module = city_url.split('//')
                scheme = url_module[0]
                domain = url_module[1]
                # print(domain)
                if 'bj.' in domain:
                    newhouse_url = 'https://newhouse.fang.com/house/s/'
                    esf_url = 'https://esf.fang.com'
                else:
                    # 构建新房链接
                    newhouse_url = scheme + '//' + 'newhouse.' + domain + 'house/s/'
                    # 构建二手房链接
                    esf_url = scheme + '//' + 'esf.' + domain
                yield scrapy.Request(url=newhouse_url, callback=self.parse_newhouse, meta={'info':(province, city)})    # 返回请求
                yield scrapy.Request(url=esf_url, callback=self.parse_esf, meta={'info':(province, city)}, dont_filter=True)
            #     break
            # break
    def parse_newhouse(self, response):
        province, city = response.meta.get('info')  # 元祖解包
        lis = response.xpath('//div[@class="nl_con clearfix"]/ul/li')
        for li in lis:
            name = li.xpath('.//div[@class="nlcd_name"]/a/text()').get()
            if name == None:
                pass
            else:
                name = re.sub(r'\s', '', name)
            # contains是指找到div下class里包含有house_type的div
            house_type_list = li.xpath('.//div[contains(@class,"house_type")]/a/text()').getall()
            # map函数, 用来替换数据里的空字符
            house_type_list = list(map(lambda x:re.sub(r'\s','',x), house_type_list))
            # filter 过滤函数，过滤末尾带有‘居’字的数据, 没有带‘居’的变成空list[]
            rooms = list(filter(lambda x:x.endswith('居'), house_type_list))
            # "".join 是把列表变成字符串 getall()返回的是列表
            area ="".join(li.xpath('.//div[contains(@class,"house_type")]/text()').getall())
            area = re.sub(r'\s|－|/', '', area)
            address = li.xpath('.//div[@class="address"]/a/@title').get()
            district_text ="".join(li.xpath('.//div[@class="address"]/a//text()').getall())
            district_text = re.sub(r'\s', '', district_text)
            district = re.search(r"\[(.+)\]", district_text)
            if district == None:
                pass
            else:
                district = district.group(1)
            sale = li.xpath('.//div[contains(@class,"fangyuan")]/span/text()').get()
            price ="".join(li.xpath('.//div[@class="nhouse_price"]//text()').getall())
            price = re.sub(r'\s|广告', '', price)
            detail_url =li.xpath('.//div[@class="nlcd_name"]/a/@href').get()
            origin_url = response.urljoin(detail_url)
            # origin_url (https://lefuqiangyuerongwan.fang.com)
            # 楼盘简介(https://lefuqiangyuerongwan.fang.com/house/2110175680/housedetail.htm)
            # print("TAG============================", origin_url)
            yield scrapy.Request(url=origin_url, callback=self.get_new_code, meta={'info':(name, origin_url)})
            # newcode = self.get_new_code(origin_url)
            # detail_url = origin_url + "/house/" + newcode + "/housedetail.htm"
            # detail_intro = self.get_house_inttro(detail_url)
            item = NewHouseItem()
            for field in item.fields.keys():  # 取出所有的键
                item[field] = eval(field)
            yield item
        next_url = response.xpath('//div[@class="page"]//a[@class="next"]/@href').get()
        if next_url:
            next_page = response.urljoin(next_url) # 拼接URL urljoin(start_urls, next_page)
            print(next_page)
            yield scrapy.Request(url=next_page, callback=self.parse_newhouse, meta={'info':(province, city)})


    def parse_esf(self, response):
        # captcha_url = response.css('.image img::attr(src)').get()  # 获取验证码
        # yzm_url = response.urljoin(captcha_url)
        # print(yzm_url)
        # if len(yzm_url) > 0:
        #     province, city = response.meta.get('info')  # 元祖解包
        #     formdata = {
        #         'submit': '提交'
        #     }
        #     code = self.text_captcha(yzm_url)
        #     formdata['code'] = code
        #     print(formdata)
        #     url = response.url
        #     yield scrapy.FormRequest(url=url, callback=self.parse_esf,
        #                     meta={'info':(province, city)}, formdata=formdata)
        # else:
        province, city = response.meta.get('info')  # 元祖解包
        dls = response.xpath('//div[contains(@class,"shop_list")]/dl')
        for dl in dls:
            item = ESFHouseItem(province=province, city=city)
            name = dl.xpath('.//p[@class="add_shop"]/a/text()').get()
            if name == None:
                pass
            else:
                item['name'] = re.sub(r'\s', '', name)
            infos = dl.xpath('.//p[@class="tel_shop"]/text()').getall()
            infos = list(map(lambda x: re.sub(r'\s', '', x), infos))
            for info in infos:
                if '厅' in info:
                    item['rooms'] = info
                elif '层' in info:
                    item['floor'] = info
                elif '向' in info:
                    item['toward'] = info
                elif '建' in info:
                    item['year'] = info
                elif '㎡' in info:
                    item['area'] = info

            item['address'] = dl.xpath('.//p[@class="add_shop"]/span/text()').get()
            item['unit'] = dl.xpath('.//dd[@class="price_right"]/span[not(@class)]/text()').get()
            item['price'] = "".join(dl.xpath('.//dd[@class="price_right"]/span[@class="red"]//text()').getall())
            detail_url = dl.xpath('.//h4[@class="clearfix"]/a/@href').get()
            item['origin_url'] = response.urljoin(detail_url)
            yield item
        next_url = response.xpath('//div[@class="page_al"]/p/a/@href').get()
        next_text = response.xpath('//div[@class="page_al"]/p/a/text()').get()
        if next_text == '下一页':
            next_page = response.urljoin(next_url)  # 拼接URL urljoin(start_urls, next_page)
            print(next_page)
            yield scrapy.Request(url=next_page,callback=self.parse_esf, meta={'info':(province, city)})


    def text_captcha(self, yzm_url):
        host = 'http://codevirify.market.alicloudapi.com'
        path = '/icredit_ai_image/verify_code/v1'
        method = 'POST'
        appcode = '851a1b7215354f17808e5125ab2e23d4'
        querys = ''
        bodys = {}
        url = host + path
        bodys['IMAGE'] = yzm_url
        bodys['IMAGE_TYPE'] = '1'
        post_data = urllib.parse.urlencode(bodys).encode(encoding='UTF8')
        request = urllib.request.Request(url, post_data)
        request.add_header('Authorization', 'APPCODE ' + appcode)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        response = urllib.request.urlopen(request)
        content = response.read()
        if (content):
            a = content.decode()
            b = json.loads(a)
            c = b['VERIFY_CODE_ENTITY']['VERIFY_CODE']
            return c


    def get_house_inttro(self, response):
        house_name, new_code = response.meta.get('info')
        # <p class="intro">
        house_intro = response.xpath('.//p[@class="intro"]/text()').get()
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>", house_intro)
        item = HouseIntroItem()
        #house_intro = response.xpath('//div[contains(@class,"shop_list")]/dl')
        item['name'] = house_name
        item['intro'] = house_intro
        yield item

    def get_new_code(self, response):
        try:
            house_name, origin_url = response.meta.get('info')
            soup = BeautifulSoup(response.text, 'lxml')
            src = soup.select('head script')[4]
            new_code = src.string.split(";")[2].split("= '")[1].split("'")[0]
            print("============================", new_code)
            
            # var newcode = '2119198676'
            # src_text = js2xml.parse(src.string, debug=False)
            #new_code = response.xpath('//div[contains(@class,"shop_list")]/dl')
            intro_url = origin_url + "/house/" + new_code + "/housedetail.htm"
            print(intro_url)
            yield scrapy.Request(url=intro_url,callback=self.get_house_inttro, meta={'info':(house_name, new_code)})
        except:
            print("获取 new code 失败...")


