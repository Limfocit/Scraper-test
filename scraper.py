#!/usr/bin/python
# -*- coding: utf-8 -*-
from selenium import webdriver
import time
import logging
import hashlib
from pymongo.errors import DuplicateKeyError
from pymongo import MongoClient
from ConfigParser import SafeConfigParser


def save_product_to_mongo(product_dict):
    if product_dict:
        try:
            mongo_db.product.insert(product_dict)
        except DuplicateKeyError:
            logger.error("Duplicate key %s" % product_dict['link'])


def process_product_type(driver):
    if len(driver.find_elements_by_xpath('//div[@class="breadcrumb"]/ul/li/a')) > 0:
        resulting_product_type = ""
        flag_not_start_until_top_category = False
        for link in driver.find_elements_by_xpath('//div[@class="breadcrumb"]/ul/li/a'):
            category_link_text = link.text.strip()
            # check for top category, after which we can start aggregating categories
            if category_link_text in ["Women", "Men", "Girls", "Boys", "Baby"]:
                flag_not_start_until_top_category = True
            if flag_not_start_until_top_category:
                if len(resulting_product_type) > 0:
                    resulting_product_type += " > "
                resulting_product_type += category_link_text
        if len(resulting_product_type) == 0:
            raise ProductPageException("Empty result product type")
        return resulting_product_type
    else:
        raise ProductPageException("No product type breadcrumbs")


def get_basic_info_from_product_page(driver, product_dict):
    # TODO add more basic data
    name = driver.find_element_by_class_name("pdpProductTitle").text
    product_dict["title"] = name
    product_dict["description"] = ""
    if len(driver.find_elements_by_id("pm-productDescription")) > 0:
        product_dict["description"] = driver.find_element_by_id("pm-productDescription").text[:5000]
    product_dict["productType"] = process_product_type(driver)
    # TODO for google product category we need dictionary


def process_product_page(driver, product_url):
    product_dict = {"link": product_url}
    driver.get(product_url)
    if len(driver.find_elements_by_class_name("notFoundCopy")) > 0:
        logger.debug("not found %s" % product_url)
        return None
    name = driver.find_element_by_class_name("pdpProductTitle").text
    product_dict["_id"] = hashlib.sha1(name).hexdigest()
    try:
        get_basic_info_from_product_page(driver, product_dict)
        # TODO load prices and sizes
        return product_dict
    except ProductPageException, ppe:
        logger.error(ProductPageException("%s: %s" % (product_url, ppe.message)))
        return None


def scroll_window_and_load_elements(driver, product_xpath):
    """
    scrolls catalog to XHR the list, while adding visible(because of Angular) elements to output set
    :param driver: selenium driver
    :param product_xpath: xpath for identifying product item in products list
    :return: product urls from this page
    """
    last_count_elements = -1
    product_urls = set()
    while len(product_urls) > last_count_elements:
        last_count_elements = len(product_urls)
        for i in range(10):
            driver.execute_script("window.scrollBy(0,750);")
            time.sleep(0.5)
            visible_product_elements = [link.get_attribute('href')
                                        for link in driver.find_elements_by_xpath(product_xpath)]
            product_urls = product_urls.union(visible_product_elements)
    return product_urls


def extract_product_links_from_sections(driver, sections_urls):
    product_urls = []
    for section_title, section_url in sections_urls:
        driver.get(section_url)
        product_xpath = '//div[@class="product-image"]//a'
        product_urls += (scroll_window_and_load_elements(driver, product_xpath))
    return set(product_urls)


def extract_subcategories_urls(driver):
    links_to_subcategories = []
    for top_category in ['Womens-Clothing', 'Mens-Clothing', 'Girls-1H-12yrs-Clothing',
                         'Girls-9-16yrs-Clothing', 'Boys-1H-12yrs-Clothing',
                         'Boys-9-16yrs-Clothing', 'Baby-0-3yrs-Clothing']:
        driver.get("http://www.boden.co.uk/en-US/%s" % top_category)
        links_to_subcategories += [(link.get_attribute('innerHTML'), link.get_attribute("href"))
                                   for link in
                                   driver.find_element_by_class_name("MainCategoryMenu").find_elements_by_tag_name("a")
                                   if "new in" not in link.get_attribute('innerHTML').lower()]
    return links_to_subcategories


def extract_christmas_gifts_urls(driver):
    driver.get("http://www.boden.co.uk/en-US/Christmas")
    links_to_subcategories = driver.find_elements_by_xpath("//div[@id=\"dropdownChristmas\"]//ul/li/a")
    return [(link.get_attribute('innerHTML'), link.get_attribute("href"))
            for link in links_to_subcategories if "gift vouchers" not in link.get_attribute('innerHTML').lower()]


def scraper_process():
    driver = webdriver.Chrome(executable_path="./chromedriver")
    sections_urls = extract_subcategories_urls(driver) + extract_christmas_gifts_urls(driver)
    product_urls = extract_product_links_from_sections(driver, sections_urls)
    for product_url in product_urls:
        product_dict = process_product_page(driver, product_url)
        save_product_to_mongo(product_dict)
        # driver.close()


class ProductPageException(Exception):
    pass


if __name__ == "__main__":
    logging.basicConfig(filename='debug.log', level=logging.ERROR)
    logger = logging.getLogger()

    config = SafeConfigParser()
    config.read('local.ini')
    mongo_client = MongoClient(host=config.get("mongo", "host"), port=int(config.get("mongo", "port")))
    mongo_db = mongo_client.boden
    # scraper_process()

    # test code
    product = process_product_page(webdriver.Chrome(executable_path="./chromedriver"),
                                   "http://www.boden.co.uk/en-GB/Girls-1H-12yrs-Dresses/Special-Occasion-Dresses/33394-GLD/Girls-1H-12yrs-Sparkly-Gold-Sparkly-Jersey-Party-Dress.html")
    save_product_to_mongo(product)
