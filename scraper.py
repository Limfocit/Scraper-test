#!/usr/bin/python
# -*- coding: utf-8 -*-
from selenium import webdriver
import time


def scroll_window_and_load_elements(driver, product_xpath):
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
    for top_category in ["Womens-Clothing", "Mens-Clothing", "Girls-1H-12yrs-Clothing",
                      "Girls-9-16yrs-Clothing", "Boys-1H-12yrs-Clothing",
                      "Boys-9-16yrs-Clothing", "Baby-0-3yrs-Clothing"]:
        driver.get("http://www.boden.co.uk/en-GB/%s" % top_category)
        links_to_subcategories += [(link.get_attribute('innerHTML'), link.get_attribute("href"))
                for link in driver.find_element_by_class_name("MainCategoryMenu").find_elements_by_tag_name("a")
                if "new in" not in link.get_attribute('innerHTML').lower()]
    return links_to_subcategories


def extract_christmas_gifts_urls(driver):
    driver.get("http://www.boden.co.uk/en-GB/Christmas")
    links_to_subcategories = driver.find_elements_by_xpath("//div[@id=\"dropdownChristmas\"]//ul/li/a")
    return [(link.get_attribute('innerHTML'), link.get_attribute("href"))
            for link in links_to_subcategories if "gift vouchers" not in link.get_attribute('innerHTML').lower()]


def scraper_process():
    driver = webdriver.Chrome(executable_path="./chromedriver")
    sections_urls = extract_subcategories_urls(driver) + extract_christmas_gifts_urls(driver)
    extract_product_links_from_sections(driver, sections_urls)
    # driver.close()


if __name__ == "__main__":
    scraper_process()