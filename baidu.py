#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: luozaibo
# date : 2019-08-15 20:46:31
import requests
from pprint import pprint
import hashlib
import time
import re
import json
from pathlib import Path
from urllib.parse import quote
import os


class BaiduImage(object):
    # 获取某一页的30条url
    def get_onepage_urls(self, url, keyword):
        headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
                'referer': f'https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=index&fr=&hs=0&xthttps=111111&sf=1&fmq=&pv=&ic=0&nc=1&z=&se=1&showtab=0&istype=2&ie=utf-8&word={quote(keyword)}&oq={quote(keyword)}&rsp=-1'
                }
        response = requests.get(url, headers=headers)
        try:
            item = response.json()
        except:
            print('error')
            return
        listNum = item['listNum']
        urls = item['data'][:30]
        urls = [i['objURL'] for i in urls if 'objURL' in i.keys()]
        urls = [self.decode_url(url) for url in urls]
        return listNum, urls

    # 解码
    def decode_url(self, obj_url):
        intab = '0123456789abcdefghijklmnopqrstuvw'
        outab = '7dgjmoru140852vsnkheb963wtqplifca'
        trans = obj_url.maketrans(intab, outab)
        str_tab = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
        for k, v in str_tab.items():
            obj_url = obj_url.replace(k, v)
        url = obj_url.translate(trans)
        return url

    # 获取某个keyword所有的图片
    def main(self, keyword, size, number):
        if size == '1920×1080':
            width = size[:4]
            height = size[-4:]
        else:
            width = ''
            height = ''
        offset = 0
        url_list = []
        flag = True
        while True:
            url = f'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ie=utf-8&word={quote(keyword)}&pn={offset*30}&width={width}&height={height}'
            try:
                listNum, urls = self.get_onepage_urls(url, keyword)
                print(f'这是下载时执行的: {listNum}')
                if flag:
                    flag = False
                    pic_count = listNum
                for img_url in urls:
                    url_list.append(img_url)
                offset += 1
                if offset * 30 > number:
                    return pic_count, url_list
                if offset * 30 <= number:
                    continue
            except:
                offset += 1
                continue

    # 获取前两页的图片
    def get_onepage(self, keyword, size):
        if size == '1920×1080':
            width = size[:4]
            height = size[-4:]
        else:
            width = ''
            height = ''
        offset = 0
        url_list = []
        flag = True
        while True:
            url = f'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ie=utf-8&word={quote(keyword)}&pn={offset*30}&width={width}&height={height}'
            try:
                listNum, urls = self.get_onepage_urls(url, keyword)
                print(f'这是人为提交的前2页: {listNum}')
                if flag:
                    flag = False
                    pic_count = listNum
                for img_url in urls:
                    url_list.append(img_url)
                offset += 1
                if offset == 2:
                    return pic_count, url_list
            except:
                offset += 1
                continue
    # 异步请求使用的函数，用于异步加载30张图片到页面
    def get_url_from_page(self, keyword, size, page):
        if size == '1920×1080':
            width = size[:4]
            height = size[-4:]
        else:
            width = ''
            height = ''
        offset = int(page)
        while True:
            url = f'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ie=utf-8&word={quote(keyword)}&pn={offset*30}&width={width}&height={height}'
            try:
                listNum, urls = self.get_onepage_urls(url, keyword)
                return listNum, urls
            except:
                offset += 1
