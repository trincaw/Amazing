
import time
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from db import db
from telegram_bot import telegram


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(
            By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def start(is_headless=True):
    options = Options()
    options.headless = is_headless
    return TorBrowserDriver(
        "/home/nicolo/Documents/dev/Amazing/tor-browser-linux64-12.0.1_ALL/tor-browser", options=options)


def get_product_info(driver, asin):
    driver.get('https://www.amazon.it/dp/' + str(asin))
    price = driver.find_element(
        By.CLASS_NAME, "a-price-whole").text
    decimal = driver.find_element(
        By.CLASS_NAME, "a-price-fraction").text
    currency = driver.find_element(
        By.CLASS_NAME, "a-price-symbol").text
    price = str(price)+'.'+str(decimal)+str(currency)
    title = driver.find_element(
        By.ID, "productTitle").text
    print('-------------------')
    print('Title: '+str(title))
    print('Price: '+str(price))


def ip_is_banned(driver):
    if check_exists_by_xpath(driver, '/html/body/center/p[1]/font/font/b'):
        return True
    return False


def calculate_discount(db, item):
    old_price = db.get_price(item)
    if old_price == 0 or item['price'] == 0:
        return 0
    else:
        return round((old_price-item['price'])/old_price*100)


def go_to_page(driver, dom, product, page):
    driver.get('https://www.amazon.'+dom+'/s?k=' +
               product+'&i=computers&page=' + str(page))


def get_item_list(driver, product):
    amazon = ['it', 'de', 'fr', 'es', 'co.uk']
    items = []

    for dom in amazon:
        print('=>Domain: '+dom)
        page = 1
        go_to_page(driver, dom, product, page)
        while not ip_is_banned(driver) and int(len(driver.find_elements(
                By.XPATH, "//div[@data-component-type='s-search-result']")) > 0) and page < 400:
            elements = driver.find_elements(
                By.XPATH, "//div[@data-component-type='s-search-result']")
            print('Page: '+str(page)+' Items found: '+str(len(elements)))

            n = len(items)
            for e in elements:
                asin = str(e.get_attribute("data-asin"))
                try:
                    price = float((e.find_element(
                        By.CLASS_NAME, "a-price-whole").text).replace(".", "").replace(",", "."))
                    dic = {'asin': asin, 'domain': dom,
                           'price': price, 'discount': 0}
                    items.append(dic)

                except:
                    price = 0

            print('Salvati :'+str(len(items)-n))
            page += 1
            go_to_page(driver, dom, product, page)

    return items


def add_discount(db, items):
    for item in items:
        item['discount'] = calculate_discount(db, item)
        if item['discount'] > 50:
            print('---------ALERT----------')
            print(item)
            print('------------------------')
            telegram().send_message('---------------ALERT---------------\n'
                                    + 'Product: https://www.amazon.'+str(item['domain'])+'/dp/'+str(item['asin'])+'\n Price: '+str(item['price'])+'\n Discount: '+str(item['discount'])+'%')
    return items


def remove_duplicates(items):
    asin_list = []
    for item in items:
        asin_list.append(item['asin'])
    asin_list = list(dict.fromkeys(asin_list))
    new_items = []
    for asin in asin_list:
        for item in items:
            if item['asin'] == asin:
                new_items.append(item)
                break
    return new_items


def loop(driver, d, tracking_list, seconds=60*10):
    print('----------Loop started--------------')
    while True:
        for product in tracking_list:
            print('----->'+product)
            items = get_item_list(driver, product)
            if len(items) == 0:
                print('Restart...')
                driver.quit()
                driver = start()
                loop(driver, d, seconds)
                return
            items = add_discount(d, items)
            # items = remove_duplicates(items)
            d.save_or_update(items)
            print('Waiting...')
            driver.quit()
            time.sleep(seconds)
            driver = start()


def main():
    import random
    tracking_list = ['gpu', 'laptop']
    random.shuffle(tracking_list)

    d = db()
    driver = start(False)
    try:
        d.create_db()
    except:
        loop(driver, d, tracking_list)


if __name__ == "__main__":
    main()
