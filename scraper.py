# coding: utf-8

import re
import os
import sys
import time
import json
import redis
import base64
import random
import pprint
import signal
import os.path
import logging
import hashlib
import requests

from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
    
try:
    regional_code = sys.argv[1]
    phone_number = sys.argv[2]
except:
    print("Yang bener lu kalo jalanin, python3 scraper.py regional_code phone_number")

def main(driver):
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
                    reload = driver.find_element_by_css_selector("span > div[role=\"button\"]")
                    reload.click()
                    time.sleep(5)
                except NoSuchElementException:
                    reloadQR(driver)
            except (NoSuchElementException, StaleElementReferenceException):
                isLoggedIn = True
                break

    if isLoggedIn is True:
        retake(driver)
        time.sleep(10)
        retake(driver)
        check = driver.find_elements_by_css_selector("div[data-animate-modal-popup]")
        for x in range(0, 30):
            if len(check) == 0:
                break

        print("collecting contact list")

        retake(driver)

        lastHeight = driver.execute_script("return document.querySelector(\"div#pane-side\").scrollHeight")
        retake(driver)
        while True:
            driver.execute_script("window.scrollTo(0, document.querySelector('div#pane-side').scrollHeight);")
            newHeight = driver.execute_script("return document.querySelector('div#pane-side').scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight
        retake(driver)
        vid_arr = []
        while True:
            contacts = "div#pane-side > div > div > div > div"
            contacts = driver.find_elements_by_css_selector(contacts)
            time.sleep(5)
            for x in contacts:
                try:
                    x.click()
                except:
                    retake(driver)
                    continue
                
                time.sleep(5)

                try:
                    last_height = driver.execute_script("return document.querySelector('div.copyable-area > div').scrollHeight")
                except:
                    retake(driver)

                try:
                    group_name_css = 'div#main span[title][dir="auto"]'
                    group_name_css = driver.find_elements_by_css_selector(group_name_css)
                    group_name = group_name_css[0].text if len(group_name_css) > 0 else ""
                except:
                    retake(driver)

                update_status(group_name, "Running")
                print("[INFO] Scraping Group : " + group_name)
                while True:
                    retake(driver)
                    if last_height < 18000:
                        try:
                            driver.find_element_by_css_selector('div.copyable-area > div').send_keys(Keys.CONTROL + Keys.HOME)
                        except:
                            retake(driver)
                    retake(driver)
                    """
                    select all chat in current scroll / overflow
                    div#main  div.copyable-area > div[tabindex] > div:nth-child(2) > div
                    """
                    chats1 = "div#main div.copyable-area > div[tabindex] > div:last-child > div"
                    chats1 = driver.find_elements_by_css_selector(chats1)
                    chats2 = "div#main div.copyable-area > div[tabindex] > div:nth-child(2) > div"
                    chats2 = driver.find_elements_by_css_selector(chats2)
                    chats = chats1 + chats2
                    retake(driver)
                    
                    # 
                    # div[tabindex] > ul > li[data-animate-dropdown-item]
                    # div[contenteditable="true"]

                    message_in = driver.find_elements_by_css_selector('div.message-in')
                    message_in = message_in[random.randint(0,len(message_in)-1)]

                    hover = ActionChains(driver).move_to_element(message_in)
                    hover.perform()

                    time.sleep(5)

                    print("click opt")
                    chat_opt = driver.find_element_by_css_selector('span[data-icon="down-context"]')
                    chat_opt.click()

                    time.sleep(2)

                    print("click list")
                    opt_list = driver.find_elements_by_css_selector('div[tabindex] > ul > li[data-animate-dropdown-item]')
                    opt_list[0].click()

                    time.sleep(1)

                    print("send chat")
                    driver.find_element_by_css_selector('div[contenteditable="true"]').send_keys('Baru nyate ini lur \n \n')

                    time.sleep(5000000)

                    for c in chats:
                        html = ""
                        
                        retake(driver)

                        try:
                            html = c.get_attribute('innerHTML')
                        except:
                            retake(driver)
                            continue
                        
                        html_val = html
                        soup = BeautifulSoup(html, 'html.parser')
                        file_name = ""
                        retake(driver)
                        if is_audio(html_val) or is_img_desc(html_val) or is_img(html_val):
                            time_ = ""
                            spans = soup.select("span")
                            for span in spans:
                                text = span.text
                                if len(text) == 5 and ":" in text:
                                    time_ = text                            
                            retake(driver)

                            phone = soup.select('span[role="button"]')
                            phone = phone[0].text
                            phone = re.sub("[^0-9]", "", str(phone))

                            buffhash = phone + time_
                            buffhash = re.sub("[^0-9]", "", str(buffhash))
                            retake(driver)
                            if is_img_desc(html_val):
                                src = soup.select('img[src*="blob"]')
                                data_pre_text = soup.select('div[data-pre-plain-text]')
                                uniq_img_desc = info = funiq_img_desc(data_pre_text[0]["data-pre-plain-text"])
                                file_name = uniq_img_desc + '.jpeg'
                                url = src[0]['src']
                                downloadBlob(driver, url, file_name)
                            elif is_img(html_val):  
                                src = soup.select('img[src*="blob"]')
                                url = src[0]['src']
                                file_name = buffhash + '.jpeg'
                                downloadBlob(driver, url, file_name)
                        post_url = 'http://localhost:3500/dirty_html'
                        payload = {"html": html, "file_name": file_name, "for": "dirty_html","group_name": group_name, "regional_code": regional_code, "phone_number": phone_number}
                        requests.post(post_url, data=payload)
                        retake(driver)
                    time.sleep(2)
                    new_height = driver.execute_script("return document.querySelector('div.copyable-area > div').scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                update_status(group_name, "Queued")

def retake(driver):
    check = driver.find_elements_by_css_selector('div[data-animate-modal-popup="true"] div[role="button"]')
    if len(check) == 2:
        check[1].click()

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
    open("./qrcode.png", "wb").write(img64.decode('base64'))

def reloadQR(driver):
    img = driver.find_element_by_css_selector("img[alt=\"Scan me!\"]")
    img64 = bytes(img.get_attribute("src").replace(
        "data:image/png;base64,", ""))
    open("./qrcode.png", "wb").write(img64.decode('base64'))

def downloadBlob(driver, uri, filename):
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
        # filename = str(uri).split("/")[-1]+ext
        path = "/var/app/storage/whatsapp/chat_media/" + filename
        if not os.path.isfile(path):
            open(path, 'wb').write(base64.b64decode(result))

def mongo(col):
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client["osint_1"]
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
    groups = mongo("whatsapp_groups")
    get = groups.find_one({"name": group_name})
    if get:
        get["latest_scrap"] = time.strftime("%Y-%m-%d %H:%M:%S")
        get["latest_scrap_unix"] = int(time.time())
        get["crawling_status"] = status
        groups.update({"_id": ObjectId(str(get["_id"]))}, get)
    else:
        group = {
            "name": group_name,
            "insert_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "insert_date_unix": int(time.time()),
            "latest_scrap": time.strftime("%Y-%m-%d %H:%M:%S"),
            "crawling_status": status,
            "total_member": 0
        }
        groups.insert(group)

def to_uniq(string):
    return base64.b64encode(string)

def funiq_img_desc(string):
    info = string.replace("[", "").replace(" ", "").split("]")
    dt = info[0].split(",")
    time = dt[0]
    date = dt[1]
    phone = info[1].replace(":", "")
    phone = re.sub("[^0-9]", "", str(phone))
    data = time+date+phone
    data = re.sub("[^0-9]", "", str(data))
    return data

def exit_hand(sig, frame):
    driver.quit()

if __name__ == '__main__':
    driverPath = '/usr/bin/chromedriver'
    dataPath = './profile/' + regional_code + '_' +phone_number

    options = webdriver.ChromeOptions()
    options.add_argument("--user-data-dir=" + dataPath)
    # options.add_argument('headless')
    options.add_argument('no-sandbox')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36')
    
    driver = webdriver.Chrome(chrome_options=options, executable_path=driverPath)
    signal.signal(signal.SIGINT, exit_hand)
    main(driver)

