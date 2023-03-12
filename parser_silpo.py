import urllib.request
from selenium import webdriver
from selenium.webdriver.common.by import By
import concurrent.futures
import time
import os
import logging

logging.basicConfig(level=logging.INFO, filename='parser.log', format='parser %(asctime)s - %(levelname)s - %(message)s')

DRIVER = webdriver.Chrome()
XPATH_PRODUCT_LIST_SELECTOR = '//*[@id="id-b01cc0e8-74ff-0f66-bcc9-9e3596616ba4"]/div[1]/div[2]/div[1]/ul/div[*]'
XPATH_IMAGE_PRODUCT_SELECTOR = 'li/div/div[2]/div/a/img'
# XPATH_PRODUCT_LIST_SELECTOR = '//*[@id="main"]/div/div[2]/div/div[2]/div[4]/div[3]/div/div/div[2]/div/div[2]/div[3]/span[*]'
# XPATH_IMAGE_PRODUCT_SELECTOR = 'div/div/div/div/div[1]/a/picture/img'
MAX_THREAD_WORKERS = 8

CATEGORIES_TO_URL = {

    'Meat': 'https://shop.silpo.ua/category/svizhe-m-iaso-278?to=8&from=1',
    'Mushrooms': 'https://shop.silpo.ua/category/gryby-svizhi-376',
    'Green': 'https://shop.silpo.ua/category/zelen-377?to=2&from=1',
    'Salad': 'https://shop.silpo.ua/category/salat-379?to=2&from=1',
    'Vegetables': 'https://shop.silpo.ua/category/ovochi-378?to=3&from=1',
    'Fruits': 'https://shop.silpo.ua/category/frukty-381?to=2&from=1',
    'Nuts': 'https://shop.silpo.ua/category/susheni-frukty-gryby-gorikhy-382?to=100&from=1',
    'Fish' : 'https://shop.silpo.ua/category/prygotovlena-ryba-ta-moreprodukty-279?to=100&from=1',
    'Fresh fish' : 'https://shop.silpo.ua/category/zhyva-ta-okholodzhena-ryba-ta-moreprodukty-280?to=100&from=1',
    'Cheese' : 'https://shop.silpo.ua/category/syry-1468?to=100&from=1',
    'Bread' : 'https://shop.silpo.ua/category/khlib-ta-khlibobulochni-vyroby-486?to=100&from=1',
    'Sausage' : 'https://shop.silpo.ua/category/m-iaso-kovbasni-vyroby-316?filter_SUB=(322__320__318__321__319)&to=100&from=1'
    
}

def is_default_image_url(url_image):
    if '/default/' in url_image:
        return True
    return False

def get_products_image_url(category_url):
    DRIVER.get(category_url)
    #TODO need to wait to load page
    n = 0
    time.sleep(3)
    SCROLL_PAUSE_TIME = 0.1

    # Get scroll height
    last_height = DRIVER.execute_script("return document.body.scrollHeight")

    for i in range(500):
        # Scroll down to bottom
        DRIVER.execute_script(f"window.scrollTo(0, document.body.scrollHeight * 1 * {i + 1}/500 );")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)
        
    for i in range(500):
        # Scroll down to bottom
        DRIVER.execute_script(f"window.scrollTo(0, document.body.scrollHeight - (document.body.scrollHeight * 1 * {i + 1}/500));")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

    elememnts = DRIVER.find_elements(By.XPATH, XPATH_PRODUCT_LIST_SELECTOR)
    url_images = []
    for i, element in enumerate(elememnts):
        image = element.find_element(By.XPATH, XPATH_IMAGE_PRODUCT_SELECTOR)
        img_url = image.get_attribute('src')
        if is_default_image_url(img_url):
            continue
        url_images.append(img_url)
    
    return url_images


def save_images(url_images, name_category):
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREAD_WORKERS) as executor:
        future_to_url = {executor.submit(save_image, url, f"{name_category}/{i}.png"): url for i, url in enumerate(url_images)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                logging.error(f'{url} generated an exception: {exc}')
            else:
                logging.info(f'Finished {url}')


def save_image(url_image, name_image_for_save):
    urllib.request.urlretrieve(url_image, name_image_for_save)

for category, category_url in CATEGORIES_TO_URL.items():
    if os.path.exists(category):
        logging.warning(f"{category} folder already exists, skip downloading")
        continue
    
    img_urls = get_products_image_url(category_url)
    os.mkdir(category)
    save_images(img_urls, category)
