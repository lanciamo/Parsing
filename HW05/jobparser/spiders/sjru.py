# -*- coding: utf-8 -*-
import scrapy


class SjruSpider(scrapy.Spider):
    name = 'sjru'
    allowed_domains = ['superjob.ru']
    start_urls = ['http://superjob.ru/']

    def parse(self, response):
        pass
