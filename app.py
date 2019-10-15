#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: luozaibo
# date : 2019-09-09 11:07:23

from flask import Flask, render_template, request, send_file, send_from_directory, make_response, redirect, url_for, session, jsonify
from baidu import BaiduImage
import os
from flask_restful import Resource, Api
import requests
from urllib.parse import quote
from pathlib import Path
from flask_socketio import SocketIO,emit
from threading import Lock
import random
import hashlib
from urllib import parse
import time
from uuid import uuid4
from multiprocessing import Pool
from zipfile import ZipFile

async_mode = None
thread = None
thread_lock = Lock()
app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'secret!'
app.config.update(RESTFUL_JSON=dict(ensure_ascii=False))
app.config['JSON_AS_ASCII'] = False
socketio = SocketIO(app, async_handlers=True, ping_timeout=20000)


@app.route('/', methods=['GET', 'POST'])
def baidu1():
    # 设置session
    session['username'] = str(uuid4())
    return render_template('index.html')



# 从百度请求链接
@app.route('/download', methods=['GET', 'POST'])
def download():
    baidu = BaiduImage()
    kw = request.form.get('kw')
    size = request.form.get('size')
    listNum, urls = baidu.get_onepage(kw, size)
    browser = request.headers.get('User-Agent')
    url_filename = hashlib.md5((parse.quote(kw) + browser).encode()).hexdigest()
    # 存储图片链接
    with open(f'./{url_filename}.txt', 'w') as f:
        f.write(kw + '\n')
        f.write(size +'\n')
    # print(f'这是手动提交的: {listNum}')
    # 渲染展示页面
    return render_template('result.html', listNum=listNum, urls=urls, kw=kw, size=size, url_filename=url_filename)

# 跳转到用户下载页面
@app.route('/new/', methods=['GET', 'POST'])
def new():
    number = int(request.form.get('number'))
    url_filename = request.form.get('url_filename')
    return render_template('new.html', url_filename=url_filename, number=number)

# 下载图片
@socketio.on('imessage', namespace='/test')
def download_img(message):
    # socketio 接收客户端传过来的值
    number = int(message['count'])
    url_filename = message['kw']

    with open(f'./{url_filename}.txt', 'r') as f:
        urls = f.readlines()
    urls = [i[:-1] for i in urls]
    size = urls[1]
    keyword = urls[0]
    Path(f'./{keyword}_{url_filename}/{keyword}').mkdir(parents=True, exist_ok=True)


    baidu = BaiduImage()
    # 获取图片的链接地址
    listNum, url_list = baidu.main(keyword, size, number)
    if len(url_list) < number:
        number = len(url_list)
    
    headers = {
            'user-agent': request.headers.get('User-Agent'), 
            'referer': f'https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=index&fr=&hs=0&xthttps=111111&sf=1&fmq=&pv=&ic=0&nc=1&z=&se=1&showtab=0&istype=2&ie=utf-8&word={quote(keyword)}&oq={quote(keyword)}&rsp=-1'
            }
    for url in url_list[:number]:
        count = url_list.index(url)
        if count == number - 1:
            info = '下载完成!'
            # print(f'{info}  {count}')
            keyword1 = f'{keyword}_{url_filename}/{keyword}.zip'
            emit('server_response', {'data': info, 'keyword': keyword1}, namespace='/test')
            socketio.sleep(0.001)
        else:
            m = '{:.0%}'.format(count/number)
            info = f'已下载 {m} ！'
            # print(info)
            # 发给客户端的事件 result.html
            emit('server_response', {'data': info}, namespace='/test')
            socketio.sleep(0.001)

        try:  # requests下载图片
            response = requests.get(url, headers=headers, timeout=3)
            content = response.content
            name = url.split('/')[-1]
            with open(f'./{keyword}_{url_filename}/{keyword}/{name}', 'wb') as f:
                f.write(content)
        except:
            print(f'download error--       {url}')
    # os.system(f'cd {keyword}_{url_filename} && zip -qr {keyword}.zip {keyword}')
    # 打包
    os.chdir(f'{keyword}_{url_filename}')
    with ZipFile(f'{keyword}.zip', 'w') as f:
        for img in os.listdir(keyword):
            f.write(f'{keyword}/{img}')
    os.chdir('..')

@socketio.on('imessage2', namespace='/test')
def pool_download(message2):  # 多进程下载
    number = int(message2['count'])
    url_filename = message2['kw']

    with open(f'./{url_filename}.txt', 'r') as f:
        urls = f.readlines()
    urls = [i[:-1] for i in urls]
    size = urls[1]
    keyword = urls[0]
    Path(f'./{keyword}_{url_filename}/{keyword}').mkdir(parents=True, exist_ok=True)


    baidu = BaiduImage()
    listNum, url_list = baidu.main(keyword, size, number)
    if len(url_list) < number:
        number = len(url_list)
    headers = {
            'user-agent': request.headers.get('User-Agent'), 
            'referer': f'https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=index&fr=&hs=0&xthttps=111111&sf=1&fmq=&pv=&ic=0&nc=1&z=&se=1&showtab=0&istype=2&ie=utf-8&word={quote(keyword)}&oq={quote(keyword)}&rsp=-1'
            }
    info = '请稍后...'
    emit('server_response', {'data': info}, namespace='/test')
    socketio.sleep(0.001)
    p = Pool(20)
    for i in url_list[:number]:
        p.apply_async(pool_downloads, (i, headers, keyword, url_filename))
    p.close()
    p.join()
    info = '下载完成!'
    keyword1 = f'{keyword}_{url_filename}/{keyword}.zip'
    emit('server_response', {'data': info, 'keyword': keyword1}, namespace='/test')
    socketio.sleep(0.001)

    os.chdir(f'{keyword}_{url_filename}')
    with ZipFile(f'{keyword}.zip', 'w') as f:
        for img in os.listdir(keyword):
            f.write(f'{keyword}/{img}')
    os.chdir('..')

# 得到打包文件
@app.route('/file/<path:filename>')
def finished(filename):
    path = os.getcwd()
    f = filename.split('/')[-1]
    r = make_response(send_from_directory(path, filename, as_attachment=True))
    r.headers['Content-Disposition'] = 'attachment;filename={}'.format(f.encode().decode('latin-1'))
    return r

def pool_downloads(url, headers, keyword, url_filename):
    try:
        response = requests.get(url, headers=headers, timeout=3)
        content = response.content
        name = url.split('/')[-1]
        with open(f'./{keyword}_{url_filename}/{keyword}/{name}', 'wb') as f:
            f.write(content)
    except:
        print(f'download error--       {url}')

# 附加功能，提供的一个接口
class ImgApi(Resource):
    def get(self, kw):
        baidu = BaiduImage()
        size = ''
        listNum, urls = baidu.get_onepage(kw, size)
        return jsonify({"nums": len(urls), kw: urls})
api.add_resource(ImgApi, '/imgapi/<string:kw>/')

@app.route('/img/<kw>/')
def getapi(kw):
    baidu = BaiduImage()
    size = ''
    listNum, urls = baidu.get_onepage(kw, size)
    return jsonify({"nums": len(urls), kw: urls})

# 异步获取30张图片
@app.route('/get_ajax/')
def get_ajax():
    kw = request.args.get('kw')
    page = request.args.get('page')
    # print(f'page: {page}')
    size = request.args.get('size')
    baidu = BaiduImage()
    listNum, urls = baidu.get_url_from_page(kw, size, page)
    return jsonify({"nums": len(urls), kw: urls})



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
    # socketio.run(app, host='0.0.0.0', debug=True)
