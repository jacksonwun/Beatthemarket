from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from pathlib import Path
from webdriver_manager.chrome import ChromeDriverManager
import os , time

BASE_DIR = Path(__file__).resolve().parent.parent
SOFTWARE_ROOT = os.path.join(BASE_DIR.parent, 'software')
print(SOFTWARE_ROOT)

def get_gelong_hui():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-extensions")
    options.add_argument("--incognito")

    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=options)

    driver.get('https://www.gelonghui.com/live/')
    news = []
    news_time = []
    news_output = []

    soup = BeautifulSoup(driver.page_source, 'lxml')

    for ele in soup.select('.g-container__left ul li'): 
        news.append(ele.text.replace("分享  微信  微博", ""))

    del news[0]

    driver.close()
    return news

if __name__ == "__main__":
    news_list = get_gelong_hui()
    for i in news_list:
        print(i)
