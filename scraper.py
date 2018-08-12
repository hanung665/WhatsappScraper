# coding: utf-8

import time
import os
import json
import sys
import pprint
import logging
import hashlib
import requests
import base64
import redis
import re
import config as cfg
username = sys.argv[1]
# Yuk Gabung kumpul di WA Group 2019 GAPRES

# https://chat.whatsapp.com/A5yK4NemFVeECXRJisqjdL
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient
from bson.objectid import ObjectId
from bs4 import BeautifulSoup


def main():
    driverPath = cfg.app['driverPath']
    dataPath = './profile/'+username

    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": "/media/uwu"}
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--user-data-dir=" + dataPath)
    # if cfg.app['headless']:
    #     options.add_argument('headless')

    if cfg.app['no-sandbox']:
        options.add_argument('no-sandbox')

    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36')
    driver = webdriver.Chrome(chrome_options=options,
                              executable_path=driverPath)
    driver.get("https://web.whatsapp.com")
    time.sleep(10)

    isLoggedIn = False

    try:
        img = driver.find_element_by_css_selector("img[alt=\"Scan me!\"]")
    except NoSuchElementException:
        isLoggedIn = True

    if isLoggedIn is False:
        while True:
            try:
                try:
                    reload = driver.find_element_by_css_selector(
                        "span > div[role=\"button\"]")
                    reload.click()
                    time.sleep(5)
                except NoSuchElementException:
                    reloadQR(driver)
            except (NoSuchElementException, StaleElementReferenceException):
                isLoggedIn = True
                break

    if isLoggedIn is True:
        time.sleep(30)
        print("Starting...")
        check = driver.find_elements_by_css_selector(
            "div[data-animate-modal-popup]")
        for x in range(0, 30):
            if len(check) == 0:
                break

        pane_selector = "div#pane-side"

        print("collecting contact list")

        lastHeight = driver.execute_script(
            "return document.querySelector(\"div#pane-side\").scrollHeight")

        while True:
            driver.execute_script(
                "window.scrollTo(0, document.querySelector(\"div#pane-side\").scrollHeight);")
            newHeight = driver.execute_script(
                "return document.querySelector(\"div#pane-side\").scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight

        print("start scrolling")

        vid_arr = []
        while True:
            contacts = "div#pane-side > div > div > div > div"
            contacts = driver.find_elements_by_css_selector(contacts)
            time.sleep(5)
            for x in contacts:
                try:
                    x.click()
                except:
                    continue
                time.sleep(5)

                last_height = driver.execute_script(
                    "return document.querySelector(\"div.copyable-area > div\").scrollHeight")
                scroll_x = 0
                scroll_x_total = 10
                """
                scroll to top, and wait to scrape
                """
                group_name_css = 'div#main span[title][dir="auto"]'
                group_name_css = driver.find_elements_by_css_selector(
                    group_name_css)
                group_name = group_name_css[0].text if len(
                    group_name_css) > 0 else ""
                # update_status(group_name, "Running")
                default_limit = 12
                latest_limit = 0
                print("[INFO] Scraping Group : " + group_name)
                while True:
                    check_limit = 0
                    scroll_x += 1
                    if scroll_x == scroll_x_total:
                        break
                    # Scroll down to bottom
                    driver.find_element_by_css_selector(
                        'div.copyable-area > div').send_keys(Keys.CONTROL + Keys.HOME)
                    # Wait to load page

                    """
                    select all chat in current scroll / overflow
                    div#main  div.copyable-area > div[tabindex] > div:nth-child(2) > div
                    """
                    chats1 = "div#main div.copyable-area > div[tabindex] > div:last-child > div"
                    chats1 = driver.find_elements_by_css_selector(chats1)
                    chats2 = "div#main div.copyable-area > div[tabindex] > div:nth-child(2) > div"
                    chats2 = driver.find_elements_by_css_selector(chats2)
                    chats = chats1 + chats2

                    check_limit = len(chats)
                    # r.append("chats", check_limit)
                    check = 0
                    for c in chats:
                        # try:
                        html = ""
                        try:
                            html = c.get_attribute('innerHTML')
                        except:
                            continue
                        html_val = html
                        soup = BeautifulSoup(html, 'html.parser')
                        url = ""

                        if is_audio(html_val):
                            src = soup.select('audio[src*="blob"]')
                            url = src[0]['src']
                            downloadBlob(driver, url, "audio")
                            print("audio")
                        elif is_pdf(html_val):
                            ""  # c.click()
                        elif is_video_desc(html_val):
                            c.click()
                            a = input_raw("wtf  1")
                            time.sleep(10)
                            src = soup.select('video[src*="blob"]')
                            url = src[0]['src']
                            downloadBlob(driver, url, "video")
                        elif is_video(html_val):
                            c.click()
                            a = input_raw("wtf ")
                            src = soup.select('video[src*="blob"]')
                            url = src[0]['src']
                            downloadBlob(driver, url, "video")
                        elif is_img_desc(html_val):
                            src = soup.select('img[src*="blob"]')
                            url = src[0]['src']
                            downloadBlob(driver, url, "img")
                            print("img with desc")
                        elif is_img(html_val):
                            src = soup.select('img[src*="blob"]')
                            url = src[0]['src']
                            downloadBlob(driver, url, "img")
                            print("img only")

                        post_url = cfg.app["url"]
                        payload = {"html": html, "for": "dirty_html", "type": "",
                                   "group_name": group_name, "url": url, "type": ""}
                        requests.post(post_url, data=payload)
                    if scroll_x_total == scroll_x:
                        break
                    else:
                        print("scrolling")

                    time.sleep(2)
                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script(
                        "return document.querySelector(\"div.copyable-area > div\").scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                # update_status(group_name, "Queued")

def isLoggedInx(driver):
    try:
        img = driver.find_element_by_css_selector("img[alt=\"Scan me!\"]")
        return "yes"
    except NoSuchElementException:
        return "no"

def generateQR(driver):
    img = driver.find_element_by_css_selector("img[alt=\"Scan me!\"]")
    img64 = bytes(img.get_attribute("src").replace(
        "data:image/png;base64,", ""))
    open("/var/temp/qrcode.png", "wb").write(img64.decode('base64'))

def reloadQR(driver):
    img = driver.find_element_by_css_selector("img[alt=\"Scan me!\"]")
    img64 = bytes(img.get_attribute("src").replace(
        "data:image/png;base64,", ""))
    open("/var/temp/qrcode.png", "wb").write(img64.decode('base64'))

def get_image(driver, img_url):
    '''Given an images url, return a binary screenshot of it in png format.'''
    driver.get(img_url)

    # Get the dimensions of the browser and image.
    orig_h = driver.execute_script("return window.outerHeight")
    orig_w = driver.execute_script("return window.outerWidth")
    margin_h = orig_h - driver.execute_script("return window.innerHeight")
    margin_w = orig_w - driver.execute_script("return window.innerWidth")
    new_h = driver.execute_script(
        'return document.getElementsByTagName("img")[0].height')
    new_w = driver.execute_script(
        'return document.getElementsByTagName("img")[0].width')

    # Resize the browser window.
    logging.info("Getting Image: orig %sX%s, marg %sX%s, img %sX%s - %s" % (
        orig_w, orig_h, margin_w, margin_h, new_w, new_h, img_url))
    driver.set_window_size(new_w + margin_w, new_h + margin_h)

    name = to_hash(img_url)
    # Get the image by taking a screenshot of the page.
    driver.get_screenshot_as_file('./download/'+name+".png")
    driver.save_screenshot('./download/'+name+".png")
    # Set the window size back to what it was.
    driver.set_window_size(orig_w, orig_h)
    return True


def downloadBlob(driver, uri, filetype):
    result = driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
    if type(result) == int:
        return "none"
    else:
        ext = ""
        if filetype == "img":
            ext = ".jpg"
        filename = str(uri).split("/")[-1]+ext
        path = "/var/app/storage/" + filename
        open(path, 'wb').write(base64.b64decode(result))

def mongo(col):
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client["tetew"]
    col = db[col]
    return col

# image only
# img[src*="blob"]
def is_img(html):
    soup = BeautifulSoup(html, 'html.parser')
    blob_image = soup.select('img[src*="blob"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    copyable_text = soup.select('span.copyable-text')
    return len(blob_image) > 0 and len(data_pre_text) < 1 and len(copyable_text) < 1

# image with scription
# div[data-pre-plain-text]
# img[src*="blob"]
# span.copyable-text
def is_img_desc(html):
    soup = BeautifulSoup(html, 'html.parser')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    img = soup.select('img[src*="blob"]')
    copyable_text = soup.select('span.copyable-text')
    return len(data_pre_text) > 0 and len(img) > 0 and len(copyable_text) > 0

# pdf
# based on icon
def is_pdf(html):
    soup = BeautifulSoup(html, 'html.parser')
    pdf_icon = soup.select('div.icon-doc-pdf')
    return len(pdf_icon) > 0

# audio
# based on audio[src*="blob"]
def is_audio(html):
    soup = BeautifulSoup(html, 'html.parser')
    audio_tag = soup.select('audio[src*="blob"]')
    return len(audio_tag) > 0

# video only
# div[style*="background-image"]
# span[data-icon="media-play"]
# span each, split :, len 2, last
def is_video(html):
    soup = BeautifulSoup(html, 'html.parser')
    bg_style = soup.select('div[style*="background-image"]')
    media_play = soup.select('span[data-icon="media-play"]')
    span_tag = soup.select('span')
    total_span = 0
    for x in span_tag:
        text = x.text
        if ":" in text and len(text.split(":")) == 2:
            total_span += 1
    return len(bg_style) > 0 and len(media_play) > 0 and total_span == 2

# videos with desc
# div[style*="background-image"]
# span[data-icon="media-play"]
# div[data-pre-plain-text]
# span.copyable-text
def is_video_desc(html):
    soup = BeautifulSoup(html, 'html.parser')
    bg_image = soup.select('div[style*="background-image"]')
    media_play = soup.select('span[data-icon="media-play"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    copyable_text = soup.select('span.copyable-text')
    return len(bg_image) > 0 and len(media_play) > 0 and len(data_pre_text) > 0 and len(copyable_text) > 0

def update_status(group_name, status):
    groups = mongo("groups")
    get = groups.find_one({"name": group_name})
    if get:
        get["latest_scrap"] = time.strftime("%Y-%m-%d %H:%M:%S")
        get["crawling_status"] = status
        groups.update({"_id": ObjectId(str(get["_id"]))}, get)
    else:
        group = {
            "name": group_name,
            "insert_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "latest_scrap": time.strftime("%Y-%m-%d %H:%M:%S"),
            "crawling_status": status,
            "total_member": 0
        }
        groups.insert(group)

def to_uniq(string):
    return base64.b64encode(string)

if __name__ == '__main__':
    main()
