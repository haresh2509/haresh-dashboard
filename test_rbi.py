#!/usr/bin/env python3
import requests, xml.etree.ElementTree as ET

def test_rss():
    url = "https://rbi.org.in/rss.xml"
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        print("RBI RSS status:", r.status_code)
        print("Content-type:", r.headers.get('Content-Type'))
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall('.//item')
            print("Found items:", len(items))
            for i, item in enumerate(items[:3]):
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                print(f"{i+1}. {title}\n   {link}")
    except Exception as e:
        print("Error:", e)

test_rss()
