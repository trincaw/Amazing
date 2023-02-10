import unittest
from unittest.mock import Mock
import main
from db import db
from selenium.webdriver.common.by import By


def test_parse_price():
    assert main.parse_price('2 999') == 2999
    assert main.parse_price('1.234,56') == 1234.56
    assert main.parse_price('1.234') == 1234.0
    assert main.parse_price('1.234,') == 1234.0
    assert main.parse_price('1.234,5') == 1234.5
    assert main.parse_price('1.234,56') == 1234.56
    assert main.parse_price('1.234,567') == 1234.567
    assert main.parse_price('1.234,5678') == 1234.5678
    assert main.parse_price('1234,5678') == 1234.5678
    assert main.parse_price('12345678') == 12345678
    assert main.parse_price('12.345.678') == 12345678
    assert main.parse_price('1234,5678') == 1234.5678


def test_calculate_discount():
    d = db()
    d.get_price = Mock(return_value=100)
    item = {'price': 50}
    assert main.calculate_discount(d, item) == 50

    item = {'price': 0}
    assert main.calculate_discount(d, item) == 0

    d.get_price = Mock(return_value=0)
    item = {'price': 0}
    assert main.calculate_discount(d, item) == 0

    d.get_price = Mock(return_value=43.22)
    item = {'price': 43}
    assert main.calculate_discount(d, item) == 1

    d.get_price = Mock(return_value=43.22)
    item = {'price': 43.22}
    assert main.calculate_discount(d, item) == 0

    d.get_price = Mock(return_value=5555.55)
    item = {'price': 2222.22}
    assert main.calculate_discount(d, item) == 60


def test_update():
    driver = main.start()
    amazon_dom = 'it'
    start_page = 1
    final_page = 30
    product = 'gpu'
    driver.get('https://www.amazon.'+amazon_dom+'/s?k=' +
               product+'&i=computers&page=' + str(start_page))

    elements = driver.find_elements(
        By.XPATH, "//div[@data-component-type='s-search-result']")

    # driver.get_attribute = Mock(
    # return_value='https://www.amazon.it/dp/B08HJTH61J')
    # driver.get_attribute = Mock(
    #     return_value='https://www.amazon.it/dp/B09LYTHSYH')
    assert len(elements) > 20
    for e in elements:
        asin = str(e.get_attribute("data-asin"))
        assert asin != ''
        s = (e.find_element(
            By.CLASS_NAME, "a-offscreen").text).replace(".", "").replace(",", ".").replace('£', '').replace('€', '')
        if s == '':
            s = '0.0'
        assert '.' in s
        price = float(s)
        assert price >= 0


if __name__ == '__main__':
    unittest.main()
