
from threading import Thread
import time
from tbselenium.tbdriver import TorBrowserDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from db import db
from telegram_bot import telegram
import os

words = []
with open(os.path.join(os.getcwd(), 'black_list.txt'), 'r') as f:
    # Read the lines of the file into a list of strings
    words = f.readlines()
for i, word in enumerate(words):
    # Remove the newline character from the end of the word and convert it to lowercase
    modified_word = word.strip().lower()
    # Update the original word in the list with the modified version
    words[i] = modified_word
path_to_tor = os.path.join(
    os.getcwd(), 'tor-browser-linux64-12.0.1_ALL/tor-browser')
path_to_db = os.path.join(os.getcwd(), 'items.db')


def start(is_headless=True):
    options = Options()
    options.headless = is_headless

    options.set_preference("permissions.default.image", 2)  # too mutch greedy
    return TorBrowserDriver(path_to_tor, options=options)


def restart_driver(driver, url=''):
    frist = True
    while ip_is_banned(driver) or frist:
        frist = False
        driver.quit()
        driver = start()
        if url != '':
            driver.get(url)
    return driver


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(
            By.XPATH, xpath)
    except:
        return False
    return True


def ip_is_banned(driver):
    try:
        if check_exists_by_xpath(driver, '/html/body/center/p[1]/font/font/b') or check_exists_by_xpath(driver, '/html/body/div/div[1]/div[2]/div/h4'):
            print('IP BANNED')
            return True
    except:
        return False


def calculate_discount(db, item):
    #old_discount = db.get_discount(item)
    old_price = db.get_price(item)
    if old_price == 0 or item['price'] == 0:
        return 0
    else:
        di = round((old_price-item['price'])/old_price*100)
        return di

# page handling


def go_to_page(driver, dom, product, page):
    try:
        driver.get('https://www.amazon.'+dom+'/s?k=' +
                   product+'&i=computers&page=' + str(page))
        return driver
    except:
        driver = restart_driver(driver)
        driver.get('https://www.amazon.'+dom+'/s?k=' +
                   product+'&i=computers&page=' + str(page))
        return driver


def add_discount(db, items):
    if items != None:
        for item in items:
            item['discount'] = calculate_discount(db, item)

            if item['discount'] > 50 and item['price'] < 300:
                print('---------ALERT----------')
                print(item)
                print('------------------------')
                telegram().send_message(item)
        return items
    return []


def is_blacklisted(title, dom):
    if title != None or title != '':
        for word in words:
            title = title.strip().lower()
            # Check if the word is contained in the target string
            if word in title:
                return True

    return False


def update(amazon_dom, start_page, final_page, product='laptop'):
    driver = start()
    page = start_page
    items = []
    jump = (final_page-start_page)//10

    driver = go_to_page(driver, amazon_dom, product, page)

    while page < final_page:
        elements = driver.find_elements(
            By.XPATH, "//div[@data-component-type='s-search-result']")

        while ip_is_banned(driver) or int(len(elements)) == 0:
            driver = restart_driver(driver)
            driver = go_to_page(driver, amazon_dom, product, page)
            elements = driver.find_elements(
                By.XPATH, "//div[@data-component-type='s-search-result']")

        print('Page: '+str(page) + ' of '+str(final_page)+' Dom: '+str(amazon_dom) +
              ' Items found: '+str(len(elements)))

        for e in elements:
            asin = str(e.get_attribute("data-asin"))
            title = e.text
            if is_blacklisted(title, amazon_dom):
                continue
            try:
                s = e.find_element(
                    By.CLASS_NAME, "a-price-whole").text
                s = (s.encode('ascii', 'ignore')).decode("utf-8")
                price = parse_price(s)

                dic = {'asin': asin, 'domain': amazon_dom,
                       'price': price, 'discount': 0}
                items.append(dic)
            except NoSuchElementException:
                continue
        if jump == page:
            driver = restart_driver(driver)
            items = save_current_items_and_empity_list(items)
            jump += jump

        page += 1
        driver = go_to_page(driver, amazon_dom, product, page)

    save_current_items_and_empity_list(items)
    driver.quit()
    print('Thread finished '+amazon_dom+' pages: ' +
          str(page) + ' of '+str(final_page))
    return items


def save_current_items_and_empity_list(items):
    if items != None and len(items) > 0:
        d = db(path_to_db)
        items = add_discount(d, items)
        d.save_or_update(items)
        print(str(len(items))+' items saved at domain ' +
              str(items[0]['domain']))
        del d
    return []


def parse_price(price):
    if price != '':
        price = price.replace(' ', '')
        dotted_price = ''
        index = price.replace('.', '').find(',')
        index = len(price.replace('.', ''))-1-index
        if index != -1:
            if index == 2:
                dotted_price = price.replace('.', '').replace(',', '.')
            else:
                dotted_price = price.replace(',', '')

        if dotted_price.find(',') != -1:
            return 0

        index = dotted_price.find('.')
        if index != -1:
            index = len(dotted_price)-1-index
            if index == 2:
                dotted_price = dotted_price
            elif index == 3:
                dotted_price = dotted_price.replace('.', '')
            else:
                dotted_price = dotted_price.replace('', '')
        return float(dotted_price)
    else:
        return 0


def loop(number_of_threads=1, tot_pages=400, product='laptop', is_headless=True):
    amazon = ['it', 'de', 'fr', 'es', 'co.uk']
    threads = []
    for amazon_dom in amazon:
        for i in range(number_of_threads):
            t = Thread(target=update, args=(
                amazon_dom, tot_pages//number_of_threads*i, tot_pages//number_of_threads*(i+1), product))
            t.start()
            threads.append(t)
        print('Thread started for domain: '+amazon_dom)

    for t in threads:
        t.join()
    print('All threads finished')

    # implementare somma di sconti continui


def main():
    import random
    tracking_list = ['gpu', 'laptop', 'ram']
    random.shuffle(tracking_list)
    d = db(path_to_db)
    # d.create_db()  # uncomment to create db
    # d.print_discount()
    # d.print_items()
    d.count_items()
    # print(d.get_price({'asin': 'B07RM39V5F', 'domain': 'co.uk',
    #                    'price': 'price', 'discount': 0}))
    del d
    start_time = time.time()
    loop(1, 250, 'laptop')  # there are 400 pages but the last 200 are trash
    end_time = time.time()
    print('Time elapsed: '+str(end_time-start_time//60))
    d = db(path_to_db).count_items()
    del d


if __name__ == "__main__":
    main()
