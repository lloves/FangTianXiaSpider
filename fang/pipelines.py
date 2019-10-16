# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
# import pymongo
# import pymysql
from scrapy.exporters import JsonItemExporter
from fang.items import NewHouseItem, ESFHouseItem, HouseIntroItem


class FangPipeline(object):
    def __init__(self):
        self.newhouse_fp = open('newhouse.json','wb')
        self.esfhouse_fp = open('esfhouse.json', 'wb')
        self.house_intro = open('house_intro.json', 'wb')
        self.newhouse_exporter = JsonItemExporter(self.newhouse_fp, ensure_ascii=False)
        self.esfhouse_exporter = JsonItemExporter(self.esfhouse_fp, ensure_ascii=False)
        self.house_intro_exporter = JsonItemExporter(self.house_intro, ensure_ascii=False)

    def process_item(self, item, spider):
        if isinstance(item, NewHouseItem):
            self.newhouse_exporter.export_item(item)
        elif isinstance(item,ESFHouseItem):
            self.esfhouse_exporter.export_item(item)
        elif isinstance(item,HouseIntroItem):
            self.house_intro_exporter.export_item(item)
        else:
            return item

    def close_spider(self, spider):
        self.newhouse_fp.close()
        self.esfhouse_fp.close()
        self.house_intro.close()

class MongoPipeline(object):

    def __init__(self, mongo_url, mongo_db):
        self.mongo_url = mongo_url
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_url=crawler.settings.get('MONGO_URL'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        if isinstance(item, NewHouseItem):
            name = item.__class__.__name__
            self.db[name].insert(dict(item))
        elif isinstance(item, ESFHouseItem):
            name = item.__class__.__name__
            self.db[name].insert(dict(item))
        elif isinstance(item,HouseIntroItem):
            self.db[name].insert(dict(item))
        else:
            return item

    def close_spider(self, spider):
        self.client.close()

class MysqlPipeline(object):
    def __init__(self):
        # 连接MySQL数据库
        self.connect = pymysql.connect(host='localhost', user='root', password='123456', port=3306)
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        try:

            self.cursor.execute('create database fang')
            print('创建数据库成功Daatabase created')
        except:
            print('Database fang exists!')
        self.connect.select_db('fang')
        try:
            self.cursor.execute('create table newhouse(id int AUTO_INCREMENT PRIMARY KEY, 省份 VARCHAR(10) NULL,'
                                '城市 VARCHAR(10) NULL, 小区名 VARCHAR(100) NULL, 价格 VARCHAR(100) NULL,'
                                '几居室 VARCHAR(10) NULL, 面积 VARCHAR(10) NULL, 地址 VARCHAR(100) NULL,'
                                '行政区 VARCHAR(10) NULL, 是否在售 VARCHAR(10) NULL, 详情页面URL VARCHAR(100) NULL)')
            print('创建数据表成功Tables created')
        except Exception as e:
            print('The table newhouse exists!',e)
        try:
            self.cursor.execute('create table esfhouse(id int AUTO_INCREMENT PRIMARY KEY, 省份 VARCHAR(10) NULL, '
                                '城市 VARCHAR(10) NULL, 小区名 VARCHAR(10) NULL, 几居室 VARCHAR(100) NULL, 层 VARCHAR(10) NULL,'
                                '朝向 VARCHAR(10) NULL, 年代 VARCHAR(100) NULL, 建筑面积 VARCHAR(10) NULL, 地址 VARCHAR(10) NULL, 总价 VARCHAR(100) NULL,'
                                '单价 VARCHAR(10) NULL, 详情页面URL VARCHAR(100) NULL)')
            print('创建数据表成功Tables created')
        except Exception as e:
            print('The table newhouse exists!', e)
            
        try:
            self.cursor.execute('create table esfhouse(id int AUTO_INCREMENT PRIMARY KEY, 小区名 VARCHAR(20) NULL, '
                                '简介 VARCHAR(2000) NULL)')
            print('创建数据表成功Tables created')
        except Exception as e:
            print('The table newhouse exists!', e)

        if isinstance(item, NewHouseItem):
            try:
                # 往数据库里面写入数据
                self.cursor.execute(
                    'insert into newhouse(省份, 城市, 小区名, 价格, 几居室, 面积, 地址, 行政区, 是否在售, 详情页面URL)VALUES ("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(
                        item['province'], item['city'], item['name'], item['price'], item['rooms'], item['area'], item['address'], item['district'], item['sale'], item['origin_url']))
                self.connect.commit()
                print('插入数据成功')
            except Exception as e:
                # 捕捉到错误就回滚
                self.connect.rollback()
                print(e)

        elif isinstance(item, ESFHouseItem):
            try:
                # 往数据库里面写入数据
                self.cursor.execute(
                    'insert into esfhouse(省份, 城市, 小区名, 几居室, 层, 朝向, 年代, 建筑面积, 地址, 总价, 单价, 详情页面URL)VALUES("{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}","{}")'.format(
                        item['province'], item['city'], item['name'], item['rooms'], item['floor'], item['toward'],
                        item['year'], item['area'], item['address'], item['price'], item['unit'], item['origin_url']))
                self.connect.commit()
                print('插入数据成功')
            except Exception as e:
                # 捕捉到错误就回滚
                self.connect.rollback()
                print(e)
        elif isinstance(item, HouseIntroItem):
            try:
                # 往数据库里面写入数据
                self.cursor.execute(
                    'insert into esfhouse(小区名, 简介)VALUES("{}","{}")'.format(
                        item['name'], item['intro']))
                self.connect.commit()
                print('插入数据成功')
            except Exception as e:
                # 捕捉到错误就回滚
                self.connect.rollback()
                print(e)
        else:
            return item

    # 关闭数据库
    def close_spider(self, spider):
        self.cursor.close()
        self.connect.close()