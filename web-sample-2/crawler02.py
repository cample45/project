import pandas as pd
import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def yahoo(item):
    print('===== yahoo =====')
    url = f'https://tw.buy.yahoo.com/search/product?p={item}'
    r = requests.get(url)
    response = r.text
    soup = BeautifulSoup(r.text)

    items = soup.find('div', class_='main') \
                .find('ul', class_='gridList') \
                .find_all('li', class_='BaseGridItem__grid___2wuJ7')

    links = [ item.find('a')['href'] for item in items ]

    products = []

    for link in links:
        r = requests.get(link)
        response = r.text
        soup = BeautifulSoup(r.text)

        product = {}
        product['網址'] = link
        product['商品名稱'] = soup.find('h1', class_='HeroInfo__title___57Yfg HeroInfo__textTooLong___BXk8j').text
        product['價錢'] = soup.find('div', class_='HeroInfo__mainPrice___1xP9H').text
        product['價錢'] = product['價錢'][1:].replace(',', '')
        product['優惠'] = soup.find('div', class_='InfoCell__cellContentWrap___2yfZW').text
        products.append(product)

    df = pd.DataFrame(products)
    df['來源'] = 'Yahoo'
    df['建立時間'] = datetime.today()
        
    return df

def momo(item):
    print('===== momo =====')
    headers = {
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'  
    }

    url = f'https://m.momoshop.com.tw/search.momo?_advFirst=N&_advCp=N&curPage=1&searchType=&cateLevel=-1&ent=k&searchKeyword={item}&_advThreeHours=N&_isFuzzy=0&_imgSH=fourCardType'
    r = requests.get(url, headers=headers)
    response = r.text
    soup = BeautifulSoup(r.text)

    links = [item.a['href'] for item in soup.find_all('li', class_="goodsItemLi")]
    products = []

    for link in links:
        
        if '/goods.momo' not in link:
            continue

        link = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?{link.split('?')[1]}"
        r = requests.get(link, headers=headers)
        response = r.text
        soup = BeautifulSoup(r.text)

        product = {}
        product['網址'] = link
        product['商品名稱'] = soup.find('div', class_='prdnoteArea').h3.text
        product['價錢'] = soup.find('ul', class_='prdPrice').find('li', class_='special').span.text
        product['價錢'] = product['價錢'].replace(',', '')
        product['優惠'] = ''
        if soup.find('li', id='promoThDesc'):
            product['優惠'] = soup.find('li', id='promoThDesc').text.strip().split('\n')[0]
        products.append(product)

    df = pd.DataFrame(products)
    df['來源'] = 'Momo'
    df['建立時間'] = datetime.today()

    return df

def pchome(item):
    print('===== pchome =====')
    url = f'https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={item}&page=1&sort=sale/dc'
    r = requests.get(url)
    response = json.loads(r.text)

    products = [
        {
            '商品名稱': d['name'],
            '價錢': d['price'],
            '網址': 'https://24h.pchome.com.tw/prod/' + d['Id']
        } for d in response['prods']
    ]

    df = pd.DataFrame(products)
    df['來源'] = 'Pchome'
    df['建立時間'] = datetime.today()

    return df

def shopee(item):
    print('===== shopee =====')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(executable_path='./chromedriver', chrome_options=chrome_options)
    browser.get(f"https://shopee.tw/search?keyword={item}")

    time.sleep(3)

    source = browser.page_source
    soup = BeautifulSoup(source)

    for y in range(0, 3000, 500):
        browser.execute_script(f"window.scrollTo(0, {y})")
        time.sleep(1)

    source = browser.page_source
    soup = BeautifulSoup(source)
    
    # links = [d.a['href'] for d in soup.find_all(class_='shopee-search-item-result__item')]
    links = []
    for d in soup.find_all(class_='shopee-search-item-result__item'):
        if d.a:
            links.append(d.a['href'])

    products = []

    for d in links:
        link = f"https://shopee.tw/{d}"
        browser.get(link)
        
        WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "_3e_UQT")
            )
        )
        
        soup = BeautifulSoup(browser.page_source)
        
        product = {}
        product['網址'] = link
        product['商品名稱'] = soup.find('div', class_='product-briefing') \
            .find('div', class_='attM6y') \
            .find('span').text
        product['價錢'] = soup.find('div', class_='_3e_UQT').text
        product['價錢'] = product['價錢'].split('-')[0].replace('$', '').replace(',', '').replace(' ', '')
        if soup.find('div', class_='_2dyNDF'):
            product['優惠'] = soup.find('div', class_='_2dyNDF').text
        products.append(product)

    browser.quit()    

    df = pd.DataFrame(products)
    df['來源'] = 'Shopee'
    df['建立時間'] = datetime.today()

    return df
