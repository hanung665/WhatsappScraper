# coding: utf-8

from flask import Flask, request, render_template, redirect, session, flash, jsonify, Session
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
import time
import datetime
import bcrypt
import os
import sys
import json
import hashlib
import re
from pymongo import MongoClient

app = Flask(__name__, template_folder='templates')

SESSION_TYPE = 'redis'
UPLOAD_FOLDER = './static/upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "R298G3KSOKLH2UIGGLS36EJG"
app.config.from_object(__name__) 


def mongo(col):
    client = MongoClient("mongodb://localhost:27017")
    db = client["osint_1"]
    col = db[col]
    return col

"""
List of html tag typing, this code maybe will be most eating commit history
if is_audio(html_val):
elif is_pdf(html_val):
elif is_group_invite(html_val):
elif is_video_desc(html_
elif is_video(html_
elif is_img_desc(html_val):
elif is_img(html_val):
elif is_link_desc(html_
elif is_link(html_
elif is_text(html_val):

N O T E !!!
This code must be sorted !!!!
"""

# text only
# span.copyable-text
# div.data-pre-plain-text
# span[dir*="auto"][0]
def is_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    copyable_text = soup.select("span.copyable-text")
    data_pre_text = soup.select("div[data-pre-plain-text]")
    name = soup.select('span[dir*="auto"]')
    draggable = soup.select('img[draggable="false"]')
    return len(copyable_text) > 0 and len(data_pre_text) > 0

# link only with thumbnail
# img[src*="data"]
# div[data-pre-plain-text]
# a[href]
def is_link(html):
    soup = BeautifulSoup(html, 'html.parser')
    b64_image = soup.select('img[src*="data"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    href = soup.select('a[href]')
    return len(b64_image) > 0 and len(data_pre_text) > 0 and len(href) > 0

# Link with description requirement :
# img 1, img[src*="data"]
# div[data-pre-plain-text]
# span.copyable-text
# a[href]
def is_link_desc(html):
    soup = BeautifulSoup(html, 'html.parser')
    b64_image = soup.select('img[src*="data"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    copyable_text = soup.select('span.copyable-text')
    where_link = soup.select('a[href*="http"]')
    return len(b64_image) > 0 and len(data_pre_text) > 0 and len(copyable_text) > 0 and len(where_link) > 0

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

# div[data-pre-plain-text]
# img[src*="data"]
# div[title*="WhatsApp Group Invite"]
def is_group_invite(html):
    soup = BeautifulSoup(html, 'html.parser')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    img = soup.select('img[src*="data"]')
    invite_title = soup.select('div[title*="WhatsApp"]')

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


"""
  GETTER function, same alghoritm with selector, but getter real get the data
  and getter doesnt need sorting ;)
  {
	"_id" : ObjectId("5aa3a2644f78623f73b59eff"),
	"image_hash" : "",
	"insert_date" : "16:16 10/03/2018",
	"sentiment" : "informational",
	"media" : "",
	"time" : "10:56",
	"group_name" : "10Jaringan Anti Kejahatan",
	"text_hash" : "b940099106c9a044b04520d821152c0c",
	"address_num" : "6281294719130",
	"chat" : "https://telusur.co.id/2018/03/09/ppp-poros-baru-di-pilpres-nggak-bakal-ada/",
	"address" : "+62812-9471-9130",
	"date" : "3/9/2018",
	"type" : "text",
	"sentiment_info" : {
		"positive" : 0,
		"informational" : 1,
		"negative" : 0,
		"provocative" : 0
	}
  }
"""

def to_fuck_name(string):
    if len(string) > 0:
        kean_nesbit = string.split("/")
        return kean_nesbit[-1]
    else:
        return ""

def to_md5(time, date, phone, text_string, group_name):
    ass = str(time) + str(date) + str(phone) + \
        str(text_string.encode('utf-8')) + str(group_name)
    m = hashlib.md5()
    m.update(ass.encode('utf-8'))
    return str(m.hexdigest())

def to_info(string):
    info = string.replace("[", "").replace(" ", "").split("]")
    dt = info[0]
    dt = dt.split(",")
    time = dt[0]
    date = dt[1]
    phone = info[1].replace(":", "")
    data = [time, date, phone]
    return data

def get_text(html, group_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    copyable_text = soup.select("span.copyable-text")  # val
    data_pre_text = soup.select("div[data-pre-plain-text]")  # attr
    name = soup.select('span[dir*="auto"]')  # name
    draggable = soup.select('img[draggable="false"]')
    chat = copyable_text[0].text
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    # build_data(_type, time,date,phone,text_string, group_name, media)
    build_data("text", info[0], info[1], info[2], chat, group_name, "", regional_code, logged_number)

def get_link(html, group_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    b64_image = soup.select('img[src*="data"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    href = soup.select('a[href]')
    chat = href[0]["href"]
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    media = b64_image[0]["src"]
    # build_data(_type, time,date,phone,text_string, group_name, media)
    build_data("text", info[0], info[1], info[2], chat, group_name, media, regional_code, logged_number)

def get_link_desc(html, group_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    b64_image = soup.select('img[src*="data"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    copyable_text = soup.select('span.copyable-text')
    where_link = soup.select('a[href*="http"]')
    chat = copyable_text[0].text
    media = b64_image[0]["src"]
    link = ""
    for x in where_link:
        text = x["href"]
        link += text + ","
    chat = chat + "<~!~>" + link
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    # build_data(_type, time,date,phone,text_string, group_name, media)
    build_data("text", info[0], info[1], info[2], chat, group_name, media, regional_code, logged_number)
    print("link desc")

def get_img(html, group_name, url, file_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    blob_image = soup.select('img[src*="blob"]')
    copyable_text = soup.select('span.copyable-text')
    phone = soup.select('span[role="button"]')
    name = soup.select('span[dir="auto"]')
    phone = phone[0].text
    if len(name) > 0:
        name = name[0].text
    time = ""
    spans = soup.select("span")
    for span in spans:
        text = span.text
        if len(text) == 5 and ":" in text:
            time = text
    build_data("image", time, "", phone, "", group_name, file_name, regional_code, logged_number)


def get_img_desc(html, group_name, url, file_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    img = soup.select('img[src*="blob"]')
    copyable_text = soup.select('span.copyable-text')
    chat = copyable_text[0].text
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    build_data("image", info[0], info[1], info[2], chat, group_name, file_name, regional_code, logged_number)


def get_video(html, group_name, url, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    bg_style = soup.select('div[style*="background-image"]')
    media_play = soup.select('span[data-icon="media-play"]')
    phone = soup.select('span[role="button"]')
    name = soup.select('span[dir="auto"]')
    phone = phone[0].text
    if len(name) > 0:
        name = name[0].text
    time = ""
    spans = soup.select("span")
    for span in spans:
        text = span.text
        if len(text) == 5 and ":" in text:
            time = text
    filename = to_fuck_name(url)
    # build_data(_type, time,date,phone,text_string, group_name, media)
    build_data("video", time, "", phone, "", group_name, filename, regional_code, logged_number)


def get_video_desc(html, group_name, url, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    bg_image = soup.select('div[style*="background-image"]')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    copyable_text = soup.select('span.copyable-text')
    chat = copyable_text[0].text
    filename = to_fuck_name(url)
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    # build_data(_type, time,date,phone,text_string, group_name, media)
    build_data("video", info[0], info[1], info[2], chat, group_name, filename, regional_code, logged_number)


def get_group_invite(html, group_name, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    data_pre_text = soup.select('div[data-pre-plain-text]')
    img = soup.select('img[src*="data"]')
    copyable_text = soup.select("div.copyable_text")
    info = to_info(data_pre_text[0]["data-pre-plain-text"])
    href = soup.select("a[href]")
    href = href[0]["href"]
    dts = soup.select('div[title] > span[dir="auto"]')
    buff = ""
    for x in dts:
        buff += x.text + " "
    chat = copyable_text[0].text
    chat = chat + " " + buff
    build_data("invite_url", info[0], info[1], info[2], chat, group_name, href, regional_code, logged_number)


def get_pdf(html, group_name, url, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    phone = soup.select('span[role="button"]')
    name = soup.select('span[dir="auto"]')
    title = soup.select("a[title]")

    chat = title[0]["title"]
    phone = phone[0].text

    if len(name) > 0:
        name = name[0].text
    time = ""
    spans = soup.select("span")
    for span in spans:
        text = span.text
        if len(text) == 5 and ":" in text:
            time = text
    filename = to_fuck_name(url)
    build_data("document", time, "", phone, chat, group_name, filename, regional_code, logged_number)


def get_audio(html, group_name, url, regional_code, logged_number):
    soup = BeautifulSoup(html, 'html.parser')
    audio_tag = soup.select('audio[src*="blob"]')
    phone = soup.select('span[role="button"]')
    name = soup.select('span[dir="auto"]')
    phone = phone[0].text
    if len(name) > 0:
        name = name[0].text
    time = ""
    spans = soup.select("span")
    for span in spans:
        text = span.text
        if len(text) == 5 and ":" in text:
            time = text
    filename = to_fuck_name(url)
    build_data("audio", time, "", phone, "", group_name, filename, regional_code, logged_number)


def latest_date(group_name):
    data = mongo("data")
    latest = data.find_one({"group_name": group_name})
    return latest["date"]

def build_data(_type, _time, date, phone, text_string, group_name, media, regional_code, logged_number):
    chats = mongo("whatsapp_chats")

    if phone == "":
        phone = group_name

    uniq_hash = to_md5(time, date, phone, text_string, group_name)
    ptoi = re.sub("[^0-9]", "", str(phone))

    check = chats.find_one({"uhash": uniq_hash})
    if check:
        "diem aja"
    else:
        is_adv = False
        ads_word = ['PPOB', 'referral', 'payfazz', 'Agen Pulsa', 'Info Lowongan Kerja', '#loker', 'Lowongan Kerja', 'Diskon', 'Promo', 'Potongan Harga']
        if any(x in text_string for x in ads_word):
            is_adv = True
        date = time.strftime("%-m/%-d/%Y") if date == "" else date
        data = {
            "insert_date": str(time.strftime("%Y-%m-%d %H:%M:%S")),
            "insert_date_unix": int(time.time()),
            "sentiment": "",
            "media": media,
            "time": _time,
            "group_name": group_name,
            "uhash": uniq_hash,
            "address_num": str(ptoi),
            "chat": text_string,
            "address": phone,
            "date": date,
            "type": _type,
            "is_adv": is_adv,
            "regional_code": regional_code,
            "logged_number": logged_number
        }
        chats.insert(data)

@app.route("/dirty_html", methods=['POST'])
def _dirty_html():
    post = {}
    for k, v in request.form.items():
        post[k] = v
    if post["for"] == "dirty_html":
        group_name = post["group_name"]
        this, html_val = str(post["html"].encode('utf-8')), str(post["html"].encode('utf-8'))
        file_name = post["file_name"]
        url = ""
        regional_code = post["regional_code"]
        logged_number = post["phone_number"]

        if is_audio(this):
            get_audio(this, group_name, url, regional_code, logged_number)

        elif is_pdf(this):
            get_pdf(this, group_name, url, regional_code, logged_number)

        elif is_group_invite(this):
            get_group_invite(this, group_name, regional_code, logged_number)

        elif is_video_desc(this):
            get_video_desc(this, group_name, url, regional_code, logged_number)

        elif is_video(this):
            get_video(this, group_name, url)

        elif is_img_desc(this):
            get_img_desc(this, group_name, url, file_name, regional_code, logged_number)

        elif is_img(this):
            get_img(this, group_name, url, file_name, regional_code, logged_number)

        elif is_link_desc(this):
            get_link_desc(this, group_name, regional_code, logged_number)

        elif is_link(this):
            get_link(this, group_name, regional_code, logged_number)

        elif is_text(this):
            get_text(this, group_name, regional_code, logged_number)
        else:
            "do nothing"
        return "what"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3500, debug=True)
