#
#from ENV import *
import os
import asyncio
import psycopg2
from telethon import TelegramClient, sync, events
import re
import zipfile
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ChromeOptions, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup
from urllib import request
from time import sleep
from datetime import datetime, timedelta
#todo try DeeplTranslator instead GoogleTranslator
from deep_translator import GoogleTranslator

import configparser
# todo вынести встендозависимые???
config_path = 'config.ini'
config = configparser.ConfigParser()
# config.sections()
config.read(config_path, encoding="utf-8")


# Use your own values from my.telegram.org
#config['telethon']['name'], config['telethon']['api_id'], config['telethon']['api_hash']
#api_id = 15723016
#api_hash = 'fd10c198eaa94bc4fe3f82415eb46ee6'
client = TelegramClient(config['telethon']['name'], int(config['telethon']['api_id']), config['telethon']['api_hash'], system_version="4.16.30-vxASPA")
#make message from html
client.parse_mode = 'html'
# Proxy for selenium webdriver
#PROXY_HOST = '38.154.89.230'  # rotating proxy or host
#PROXY_PORT = 8000 # port
#PROXY_USER = 'nSMJ7N' # username
#PROXY_PASS = 'HQhCVD' # password

# def WritetoDB(sender, text):
#     f = open('message.txt', 'a')
#     string = str(sender) + "|" + str(text) + "|0\n"
#     f.write(string)
#     f.close()

# todo вынести в отдельный файл - это костыль для использования плагинов в headless браузере, а также скрипт под использование прокси

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"76.0.0"
}
"""

background_js = """
let config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}
chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (config['proxy']['proxy_host'], config['proxy']['proxy_port'], config['proxy']['proxy_user'], config['proxy']['proxy_pass'])

# подлючение webdriver
def get_chromedriver(use_proxy=False, user_agent=config['general']['user_agent'], exec_path=config['general']['driver_path'] ):
    chrome_options = webdriver.ChromeOptions()

    if use_proxy:
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    chrome_options.add_argument(f"--window-size=1366,768") # HD 1280×720(16: 9) WXGA 1366×768(16: 9) FullHD 1920×1080(16: 9) WQHD 2560×1440(16: 9) UWQHD 3100×1440(21: 9) 4K UHD 3840×2160(16: 9) 8K UHD 7680×4320(16: 9)

    """        
        options.add_argument(f"--window-size=1366,768")
        options.add_argument(
            f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--password-store=basic")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--enable-automation")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-software-rasterizer")
            options.add_argument("--headless")  # Run in headless mode
        options.add_argument(f"--user-data-dir=PATH_TO_CHROME_PROFILE")
        options.add_argument('--proxy-server=IP_ADRESS:PORT')
    """

    s = Service(
        executable_path=exec_path
    )
    driver = webdriver.Chrome(
        service=s,
        options=chrome_options
    )
    return driver
# получить и запостить Heatmap
# todo получение и пстинг нужно разделить, возможно выделить специфичную функцию SmartLab
async def getHeatmap(channel_to_post=int(config['telethon']['channel_to_post']), heatmap_sl_url=config['heatmaps']['heatmap_sl_url_1'], heatmap_sl_xpath=config['heatmaps']['heatmap_sl_xpath_1'], heatmap_sl_comment=config['heatmaps']['heatmap_sl_comment_1'] ):
    try:
        driver = get_chromedriver(use_proxy=False, user_agent=config['general']['user_agent'], exec_path=config['general']['driver_path'])
        #hardcode
        driver.get(heatmap_sl_url)
        await asyncio.sleep(10)
        s = datetime.now()
        path_to_file = config['general']['path_to_bot'] + '/images/' + s.strftime("%d_%m_%Y") + '/smartlab'
        if not os.path.exists(path_to_file):
            os.makedirs(path_to_file)
        ts = s.strftime(("%f"))
        hour = s.strftime(("%H"))


        path = path_to_file + '/hmmb' + ts + '.png'
        catch = driver.find_element("xpath", heatmap_sl_xpath)  # мосбиржа
        catch.screenshot(path)
        # совмещен гет и пост - нужно поменять
        await client.send_message(channel_to_post, heatmap_sl_comment, file=path)

        print('done heatmap')
        driver.close()
        driver.quit()

    except Exception as ex:
        print(ex)
    finally:
        print("getHeatmap done")
# посмотреть самое комментируемое на SmartLab и скопировать пост
# todo получение и пстинг нужно разделить, возможно выделить специфичную функцию SmartLab
async def getURL(channel_to_post=int(config['telethon']['channel_to_post']), site_to_scrap=config['smart-lab']['heatmap_sl'], heatmap_sl_xpath_1=config['smart-lab']['heatmap_sl_xpath_1'], heatmap_sl_xpath_2=config['smart-lab']['heatmap_sl_xpath_2'], heatmap_sl_xpath_3=config['smart-lab']['heatmap_sl_xpath_3']):
    try:
        driver = get_chromedriver(use_proxy=False, user_agent=config['general']['user_agent'], exec_path=config['general']['driver_path'])
        #hardcode
        # 1 comment
        driver.get(site_to_scrap)
        await asyncio.sleep(10)
        comm_1=driver.find_element("xpath", heatmap_sl_xpath_1)
        comm_1.click()
        driver.find_element("xpath", heatmap_sl_xpath_1_1)

        # 2 comment
        driver.get(site_to_scrap)
        await asyncio.sleep(10)
        comm_2=driver.find_element("xpath", heatmap_sl_xpath_2)
        # 3 comment
        driver.get(site_to_scrap)
        await asyncio.sleep(10)
        comm_3=driver.find_element("xpath", heatmap_sl_xpath_3)


        # совмещен гет и пост - нужно поменять
        await client.send_message(channel_to_post, heatmap_sl_comment, file=path, parse_mode="html")

        print('done heatmap')
        driver.close()
        driver.quit()

    except Exception as ex:
        print(ex)
    finally:
        print("getHeatmap done")




# todo изменить алгоритм работы с твиттером (может насильный клик мышью по полю ввода?)
async def getTwitterMessages(proxy_user = config['proxy']['proxy_user'], proxy_pass = config['proxy']['proxy_pass'], proxy_host=config['proxy']['proxy_host'], proxy_port=config['proxy']['proxy_port']):
    hdr = {'User-Agent': 'Yandex'}

#hardcode
    #PROXY_HOST = '5.101.34.214'  # rotating proxy or host
    #PROXY_PORT = 8000  # port
    #PROXY_USER = 'QncvkH'  # username
    #PROXY_PASS = 'j3U9yK'  # password

    proxy_url = 'https://'+ proxy_user + ':' + proxy_pass +'@' + proxy_host + ':' + str(proxy_port)
    proxy = request.ProxyHandler({
        'https': proxy_url,
        'http': proxy_url
    })
    try:
        driver = get_chromedriver(use_proxy=True,
                                  user_agent=config['general']['user_agent'])
        driver.implicitly_wait(25)
        #hardcode
        url = "https://x.com/"
        driver.get(url)
        await asyncio.sleep(10)

        try:
            # Find and input enter button
            enter_button = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//a[@href='/login']")))
            enter_button.click()
            # Find and input the username
            username_input = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
            username_input.send_keys(tw_username)
            username_input.send_keys(Keys.ENTER)
            # Find and input the password
            password_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
            password_input.send_keys(tw_password)
            password_input.send_keys(Keys.ENTER)
            sleep(1)
        except:
            sleep(10)
        # finally:
        #    sleep(1)

        # twitter scrape

        # click  home
        # <a href="/home" aria-label="Home" role="link" class="css-175oi2r r-6koalj r-eqz5dr r-16y2uox r-1habvwh r-oyd9sg r-13qz1uu r-1ny4l3l r-1loqt21" data-testid="AppTabBar_Home_Link"><div class="css-175oi2r r-sdzlij r-dnmrzs r-1awozwy r-18u37iz r-1777fci r-xyw6el r-o7ynqc r-6416eg"><div class="css-175oi2r"><svg viewBox="0 0 24 24" aria-hidden="true" class="r-4qtqp9 r-yyyyoo r-dnmrzs r-bnwqim r-1plcrui r-lrvibr r-18jsvk2 r-lwhw9o r-cnnz9e"><g><path d="M21.591 7.146L12.52 1.157c-.316-.21-.724-.21-1.04 0l-9.071 5.99c-.26.173-.409.456-.409.757v13.183c0 .502.418.913.929.913H9.14c.51 0 .929-.41.929-.913v-7.075h3.909v7.075c0 .502.417.913.928.913h6.165c.511 0 .929-.41.929-.913V7.904c0-.301-.158-.584-.408-.758z"></path></g></svg></div><div dir="ltr" class="css-1rynq56 r-dnmrzs r-1udh08x r-3s2u2q r-bcqeeo r-qvutc0 r-37j5jr r-adyw6z r-135wba7 r-b88u0q r-88pszg r-1joea0r r-18jsvk2" style="text-overflow: unset;"><span class="css-1qaijid r-bcqeeo r-qvutc0 r-poiln3" style="text-overflow: unset;">Home</span></div></div></a>
        home_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//a[@href='/home']")))
        home_button.click()
        sleep(1)
        # click folowing
        # <a href="/home" role="tab" aria-selected="true" class="css-175oi2r r-1awozwy r-6koalj r-eqz5dr r-16y2uox r-1h3ijdo r-1777fci r-s8bhmr r-i023vh r-1qhn6m8 r-o7ynqc r-6416eg r-1ny4l3l r-1loqt21"><div class="css-175oi2r"><div dir="ltr" class="css-1rynq56 r-bcqeeo r-qvutc0 r-37j5jr r-a023e6 r-rjixqe r-b88u0q r-1awozwy r-6koalj r-18u37iz r-1pi2tsx r-1777fci r-1l7z4oj r-95jzfe r-bnwqim" style="text-overflow: unset; color: rgb(15, 20, 25);"><span class="css-1qaijid r-bcqeeo r-qvutc0 r-poiln3" style="text-overflow: unset;">Following</span><div class="css-175oi2r r-xoduu5 r-1kihuf0 r-sdzlij r-1p0dtai r-hdaws3 r-s8bhmr r-u8s1d r-13qz1uu" style="background-color: rgb(29, 155, 240);"></div></div></div></a>
        following_button = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Following')]")))
        following_button.click()
        sleep(1)

        # wait for data to load
        marker = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@data-testid='cellInnerDiv']")))
        sleep(10)  # you don't need it if proxy is fast

        data = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@aria-label='Timeline: Your Home Timeline']")))

        # parse loaded data with soup
        soup = BeautifulSoup(data.get_attribute('outerHTML'), "html.parser")

        # check if directory exists
        s = datetime.now()
        # !!!! hardcoded path !!!!
        path_to_file = path_to_bot + '/images/' + s.strftime("%d_%m_%Y") + '/twitter'
        if not os.path.exists(path_to_file):
            os.makedirs(path_to_file)
        # start SQL query
        query = "INSERT INTO TWITTER (SCREENSHOT, AVATAR, TWITTERUSERLINK, TWITTERUSER, TIME, AD, TEXT, IMAGES, IMAGEOVERTEXT, COMMENTS, REPOSTS, LIKES, VIEWS, STATUS, TYPE) VALUES"
        # find all tweets
        elements = soup.findAll(lambda tag: tag.name == 'article')
        counter_elem = 0
        # process each tweet
        for element in elements:
            print(element)
            print("-------------------------------------")
            # catch screenshot of tweet

            ts = datetime.now().strftime(("%f"))
            screen_path = path_to_file + '/' + ts + '.png'
            element_id = element['aria-labelledby']
            catch = driver.find_element("xpath", "//article[@aria-labelledby='" + element_id + "']")
            catch.screenshot(screen_path)

            # avatar
            avatar = element.find('div', attrs={'data-testid': 'Tweet-User-Avatar'})
            avatar_src = avatar.find('img').get("src")
            # !!!! do we really need this shit? !!!!

            # user
            user = element.find('div', attrs={'data-testid': 'User-Name'})
            user_a = user.find('a').get('href')

            user_a_t = user.find('a').text.strip()
            # tweet time + check if tweet is an ad
            try:
                time = user.find('time').attrs['datetime']
                ad = 0
            except:
                # if there is no time, tweet is an ad
                time = ''
                ad = 1
                continue
            # finally:
            #    sleep(1)
            # how to scrape ads???
            # text
            text = element.find('div', attrs={'data-testid': 'tweetText'}).contents[0]
            # are there any images?
            try:
                # image
                image_wrapper = element.find('div', attrs={'data-testid': 'card.wrapper'})
                # print(image_wrapper)
                images = image_wrapper.findAll('img')
                print('*********')
                print(images)
                print('*********')
                img_arr = []
                for image in images:
                    ts = datetime.now().strftime(("%f"))
                    path = path_to_file + '/' + ts + '.jpg'

                    # shit with image download with proxy

                    req = request.Request(image['src'], headers=hdr)
                    opener = request.build_opener(proxy)
                    request.install_opener(opener)
                    resp = request.urlopen(req, timeout=5)
                    out = open(path, 'wb')
                    out.write(resp.read())
                    out.close()

                    img_arr_tmp = [path, image['src'], image['alt']]
                    print(img_arr_tmp)
                    print('*********')
                    # image-alt
                    img_arr.append(img_arr_tmp)
                try:
                    image_over = image_wrapper.find('div', attrs={'dir': 'ltr'}).text.strip()
                except Exception as e:
                    raise
                    image_over = "none"
                # finally:
                #    print("*************")
            except:
                img_arr = []
                image_over = "error"
            finally:
                img_arr = json.dumps({'image': img_arr})

            # comments
            comments_count = element.find('div', attrs={'data-testid': 'reply'}).text.strip()
            # reposts
            reposts_count = element.find('div', attrs={'data-testid': 'retweet'}).text.strip()
            # likes
            likes_count = element.find('div', attrs={'data-testid': 'like'}).text.strip()

            # views
            views_count = element.find('a', attrs={'aria-label': re.compile(r'View post analytics$')}).text.strip()
            status = 0
            type = 2

            if counter_elem > 0:
                query = query + ","
            counter_elem = counter_elem + 1

            query = query + "('" + screen_path + "', '" + avatar_src + "', '" + user_a + "', '" + user_a_t + "', '" + str(
                time) + "', " + str(ad) + ", '" + str(text) + "', '" + str(
                img_arr) + "', '" + image_over + "', '" + str(comments_count) + "', '" + str(
                reposts_count) + "', '" + str(likes_count) + "', '" + str(views_count) + "', " + str(
                status) + ", " + str(type) + ")"
        # query=query+



    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()
        try:
            connection = psycopg2.connect(dbname=db_name, user=db_user,
                                          password=db_password, host=db_host)
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
            connection.close()
        except Exception as ex:
            print(ex)
    print("getTwitterMessages done")


# собрать посты по отобранным доменам
async def getDomainsPosts(proxy_user=config['proxy']['proxy_user'], proxy_pass=config['proxy']['proxy_pass'],
                                 proxy_host=config['proxy']['proxy_host'], proxy_port=config['proxy']['proxy_port']):





# messages processing
#todo обновить списки изменяемых смайликов
def replaceMessage(message):
    REPLACEMENTS = [
        ("🔸", "💥"),
        ("Blast", "😤"),
        ("♨️", ""),
        ("💉", ""),
        ("🧩", ""),
        ("⚱️", ""),
        ("📊", ""),
        ("🏦", ""),
        ("🌆", ""),
        ("🔘", ""),
        ("🌏", ""),
        ("🔴", "💥"),
        ("🟢", "💥"),
        ("🕵️‍♀️", ""),
        ("🪨", ""),
        ("🛒", ""),
        ("😔", ""),
        ("💪♀️", ""),
        ("📉", "💥"),
        ("📈", "💥"),
        ("📰", ""),
        ("💻", ""),
        ("📜", "💥"),
        ("⚠️", "💥"),
        ("🛢", ""),
        ("👉", ""),
        ("☕️", ""),
        ("☕", ""),
        ("Что да как? \n", ""),
        ("Что да как? \n\n", ""),
        # ("🔥Акции и инвестиции\n", ""),

    ]

    for old, new in REPLACEMENTS:
        message = message.replace(old, new)
    # RegExp= "Обзор важных событий на утро 2 февраля: \n([^#]*)#новости\n"
    message = re.sub(r"Обзор важных событий на утро([^#]*)#новости\n", "", message)
    message = re.sub(r"([^🔥]*)🔥Акции и инвестиции\n\n", "", message)
    message = re.sub(r"Комментируйте на Смартлабе:*", "", message)
    message = re.sub(r"Пишите свои мысли в комментарии:*", "", message)
    message = re.sub(r"Пишите свое мнение в комментарии, все графики в источнике:", "", message)
    message = re.sub(r"Автор: *", "", message)
    return (message)

# clear text from HTML tags
def clearHTML(text):
    '''clear text from HTML tags'''
    text=re.sub(r'\<[^>]*\>', '', text)
    return (text)

# translate text from source language to targe language
def translate(text):
    text = GoogleTranslator(source='en', target='ru').translate(text)
    return (text)

# day number to day name
#!!!!!
def int_value_from_num_day(day_num):
    RU_DAY_VALUES = {
        'понедельник': 0,
        'вторник': 1,
        'среда': 2,
        'четверг': 3,
        'пятница': 4,
        'суббота': 5,
        'воскресенье': 6,
    }

    for k, v in RU_DAY_VALUES.items():
        day_num = str(day_num).replace(str(v), k)

    return day_num

# установить высоту и ширину браузера для webdriver
def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
        """, width, height)
    driver.set_window_size(*window_size)

# преобразуем месяц в цифру
def int_value_from_ru_month(date_str):
    RU_MONTH_VALUES = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12,
    }

    for k, v in RU_MONTH_VALUES.items():
        date_str = date_str.replace(k, str(v))

    return date_str

# преобразовать в единый формат
def date_format(date_str, datetype):
    if datetype == 1:
        date_str = int_value_from_ru_month(date_str)
        # приводим к формату '%d %m %Y, %H:%M' для strptime и превращения в datetime
    # if datetype == 2:
    # if datetype == 3:
    # if datetype == 4:
    # разные форматы приводим к единому ('%d %m %Y, %H:%M') для дальнейшей

    date_str = datetime.strptime(date_str, '%d %m %Y, %H:%M')
    date_str = date_str.strftime('%d %B %Y, %H:%M')

    return date_str


# delete this shit
xpath_to_grab_dict['ECpresence'] = "/html/body/div[2]/div[4]/div[3]/div[2]/div[1]/div[1]"
xpath_to_grab_dict['domain'] =
xpath_to_grab_dict['titlexp'] = "/html/body/div[2]/div[4]/div[3]/div[2]/div[1]/h1"
xpath_to_grab_dict['authorxp'] = "/html[1]/body[1]/div[2]/div[4]/div[3]/div[2]/div[1]/ul[1]/ul[1]/li[3]/a[1]"
xpath_to_grab_dict['datexp'] = "/html[1]/body[1]/div[2]/div[4]/div[3]/div[2]/div[1]/ul[1]/ul[1]/li[1]"
xpath_to_grab_dict['textxp'] = "/html/body/div[2]/div[4]/div[3]/div[2]/div[1]/div[1]"
xpath_to_grab_dict['imagesxp'] = ""
xpath_to_grab_dict['commentsxp'] = "/html[1]/body[1]/div[2]/div[4]/div[3]/div[2]/div[2]/div[2]"
xpath_to_grab_dict['likesxp'] = "/html/body/div[2]/div[4]/div[3]/div[2]/div[1]/ul[3]"
xpath_to_grab_dict['viewsxp'] = "/html/body/div[2]/div[4]/div[3]/div[2]/div[1]/div[2]/span[1]"
xpath_to_grab_dict['page_url'] = ""
xpath_to_grab_dict['datetype'] = 1




def (driver, xpath_to_grab_dict)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(("xpath", xpath_to_grab_dict['ECpresence']))
        # ecpresence
    )
    current_url = driver.current_url
    # print(current_url)
    result_page_content_array = {}
    if 'page_url' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_url'] = driver.current_url
            result_page_content_array['page_domain'] = urlparse(result_page_content_array['page_url']).netloc
        except NoSuchElementException:
            result_page_content_array['page_url'] = ''
            result_page_content_array['page_domain'] = ''
            print("no page_url !")

    if 'titlexp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_title'] = driver.find_element("xpath",
                                                                          xpath_to_grab_dict['titlexp']).text
        except NoSuchElementException:
            result_page_content_array['page_title'] = ''
            print("no page_title !")

    if 'authorxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_author'] = driver.find_element("xpath",
                                                                           xpath_to_grab_dict['authorxp']).text
        except NoSuchElementException:
            result_page_content_array['page_author'] = ''
            print("no page_author !")

    if 'datexp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_date'] = driver.find_element("xpath",
                                                                         xpath_to_grab_dict['datexp']).text

            result_page_content_array['page_date'] = (date_format(result_page_content_array['page_date'], xpath_to_grab_dict['datetype']))

        except NoSuchElementException:
            result_page_content_array['page_date'] = ''
            print("no page_date !")

    if 'textxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_text'] = driver.find_element("xpath",
                                                                         xpath_to_grab_dict['textxp']).text
        except NoSuchElementException:
            result_page_content_array['page_text'] = ''
            print("no page_text !")

    if 'imagesxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_images'] = ""
        except NoSuchElementException:
            result_page_content_array['page_images'] = ""
            print("no page_images !")

    if 'commentsxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_comments'] = driver.find_element("xpath",
                                                                             xpath_to_grab_dict['commentsxp']).text
        except NoSuchElementException:
            result_page_content_array['page_comments'] = ''
            print("no page_comments !")

    if 'likesxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_likes'] = driver.find_element("xpath",
                                                                          xpath_to_grab_dict['likesxp']).text
        except NoSuchElementException:
            result_page_content_array['page_likes'] = ''
            print("no page_likes !")

    if 'viewsxp' in xpath_to_grab_dict:
        try:
            result_page_content_array['page_views'] = driver.find_element("xpath",
                                                                          xpath_to_grab_dict['viewsxp']).text
        except NoSuchElementException:
            result_page_content_array['page_views'] = ''
            print("no page_views !")

    return(result_page_content_array)

# прокликать по координатам

# todo ОСТАНОВИЛСЯ ТУТ убрать query и далее рвем на разные функции
def click_coords(coords_array, driver, xpath_to_grab_dict):
    query = "INSERT INTO POSTS (DOMAIN, URL, TITLE, AUTHOR, DATE, TEXT, IMAGES, COMMENTS, LIKES, VIEWS, STATUS, TYPE) VALUES"
    count = 0
    for coords in range(0, len(coords_array)):
        action = ActionBuilder(driver)
        action.pointer_action.move_to_location(coords_array[coords][0], coords_array[coords][1])
        action.pointer_action.click()
        action.perform()
        #print(coords_array[coords][0], coords_array[coords][1])

        try:

            driver.switch_to.window(driver.window_handles[1])


            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            result_page_content_array['page_status'] = 0
            result_page_content_array['page_type'] = 3
            # DOMAIN, URL, TITLE, AUTHOR, DATE, TEXT, IMAGES, COMMENTS, LIKES, VIEWS, STATUS, TYPE

            if count == 0:
                query = query + ", "

            count = count + 1

            query = query + "('" + str(result_page_content_array['page_domain']) + "', '" + str(
                result_page_content_array['page_url']) + "', '" + str(
                result_page_content_array['page_title']) + "', '" + str(
                result_page_content_array['page_author']) + "', '" + str(
                result_page_content_array['page_date']) + "', '" + str(
                result_page_content_array['page_text']) + "', '" + str(
                result_page_content_array['page_images']) + "', '" + str(
                result_page_content_array['page_comments']) + "', '" + str(
                result_page_content_array['page_likes']) + "', '" + str(
                result_page_content_array['page_views']) + "', '" + str(
                result_page_content_array['page_status']) + "', '" + str(result_page_content_array['page_type']) + "')"

            print(result_page_content_array)

        except IndexError:
            print("no page opened ! ", coords_array[coords][0], coords_array[coords][1])
            print(IndexError)
        print("!!!!!")
        print(query)
        print("!!!!!")
    # это смартлаб хитмэпы (раз в час)



#db tg
# tg messages processing (replace simbols, emoticons, catch phrases)
async def DBprocessing_tg(db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT ID, TEXT FROM MESSAGES WHERE (STATUS=0 AND (TYPE=2))"
    cursor.execute(SQLquery)
    selectedrecords = cursor.fetchall()

    for row in selectedrecords:
        id = row[0]
        text = replaceMessage(row[1])
        status = 1
        cursor.execute(f"UPDATE MESSAGES SET TEXT = '{text}', STATUS = {status} WHERE id = {id}")

    connection.commit()
    cursor.close()
    connection.close()

#db tg posting
# tg messages posting
async def DBposting_tg(db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host'],channel_to_post=int(config['telethon']['channel_to_post']),path_to_tg_image=config['telethon']['path_to_tg_image']):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT ID, TEXT, IMAGE FROM MESSAGES WHERE (STATUS=1 AND (TYPE=2))"

    cursor.execute(SQLquery)
    selectedrecords = cursor.fetchall()

    for row in selectedrecords:
        id = row[0]
        text = row[1]
        image = path_to_tg_image + str(row[2])
        if image == '' or len(text)>= 1000:
            await client.send_message(channel_to_post, text)
        else:
            await client.send_message(channel_to_post, text, file=image)
        status = 8
        cursor.execute(f"UPDATE MESSAGES SET STATUS = {status} WHERE id = {id}")
        await asyncio.sleep(20) #todo пдумать нужно ли это

    connection.commit()
    cursor.close()
    connection.close()

# сейчас оптимизирую это
# db collect twitter messages
# todo изменить алгоритм работы с твиттером
async def DBprocessing_tw(db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT ID, TEXT, IMAGEOVERTEXT FROM TWITTER WHERE (STATUS=0 AND (TYPE=2))"
    cursor.execute(SQLquery)
    selectedrecords = cursor.fetchall()
    for row in selectedrecords:
        id = row[0]
        text = translate(clearHTML(row[1]))
        over = row[2]
        if over != '':
            over=translate(over)
        status = 1
        cursor.execute(f"UPDATE TWITTER SET TEXT = '{text}', IMAGEOVERTEXT = '{over}',STATUS = {status} WHERE id = {id}")
    connection.commit()
    cursor.close()
    connection.close()
# db post twitter messages
# todo изменить алгоритм работы с твиттером
async def DBposting_tw(db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host'],channel_to_post=int(config['telethon']['channel_to_post'])):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT ID, SCREENSHOT, TEXT, TWITTERUSER, IMAGEOVERTEXT FROM TWITTER WHERE (STATUS=1 AND (TYPE=2))"
    cursor.execute(SQLquery)
    selectedrecords = cursor.fetchall()

    for row in selectedrecords:
        id = row[0]
        image = str(row[1])
        text = row[2]
        over = row[4]
        user = row[3]
        # change this shit!!!!
        text = user+':<br>' + text + '<br>' + over
        if image == '' or len(text)>= 1000:
            await client.send_message(channel_to_post, text)
        else:
            await client.send_message(channel_to_post, text, file=image)
        status = 8
        cursor.execute(f"UPDATE TWITTER SET STATUS = {status} WHERE id = {id}")
        await asyncio.sleep(20)
    connection.commit()
    cursor.close()
    connection.close()
#db tg
# tg posted/processed messages count
async def CheckDB_tg(status=1, db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT COUNT (ID) FROM MESSAGES WHERE (STATUS=status)"
    cursor.execute(SQLquery)
    quantity = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return(quantity)
#db tw
# tw posted/processed messages count
# todo изменить алгоритм работы с твиттером
async def CheckDB_tw(status=1, db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    SQLquery = "SELECT COUNT (ID) FROM TWITTER WHERE (STATUS=status)"
    cursor.execute(SQLquery)
    quantity = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return(quantity)

# запись в базу данных сообщения телеграмм
# todo бъединить в одну функцию  запись в таблцы TG, TW, VK
# todo скорректировать SQLquery на множество записей
async def WritetoDB_tg(senderid, sendertitle, text, status=0, type=0, image='', db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    SQLquery = f"INSERT INTO MESSAGES (SENDERID,SENDERNAME,TEXT,STATUS,TYPE,IMAGE,TIMER) VALUES ('{senderid}', '{sendertitle}', '{text}', {status}, {type}, '{image}', CURRENT_TIMESTAMP)"
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    cursor.execute(SQLquery)
    connection.commit()
    cursor.close()
    connection.close()

#запись в базу данных сообщения twitter
# todo объединить в одну функцию  запись в таблцы TG, TW, VK
# todo скорректировать SQLquery на множество записей
async def WritetoDB_tw(screen_path, avatar_src, user_a, user_a_t, time, ad, text, img_arr, image_over, comments_count, reposts_count, likes_count, views_count, status, type, db_name=config['database']['db_name'],db_user=config['database']['db_user'],db_password=config['database']['db_password'],db_host=config['database']['db_host']):
    SQLquery = f"INSERT INTO TWITTER (SCREENSHOT, AVATAR, TWITTERUSERLINK, TWITTERUSER, TIME, AD, TEXT, IMAGES, IMAGEOVERTEXT, COMMENTS, REPOSTS, LIKES, VIEWS, STATUS, TYPE) VALUES ({screen_path}, {avatar_src}, {user_a}, {user_a_t}, {time}, {ad}, {text}, {img_arr}, {image_over}, {comments_count}, {reposts_count}, {likes_count}, {views_count}, {status}, {type})"
    connection = psycopg2.connect(dbname=db_name, user=db_user,
                                  password=db_password, host=db_host)
    cursor = connection.cursor()
    cursor.execute(SQLquery)
    connection.commit()
    cursor.close()
    connection.close()

# hardcode
# включение бота на прослушивание каналов
@client.on(events.NewMessage(chats=json.loads(config['telethon']['chats_to_read'])))

# hardcode
# условия для сохранения сообщения
# todo вынести в отдельный конфигурационный файл
# todo провести нагрузочное тестирование склько можно за 1 раз
async def handler(event):
    # тестовое слово с командой 1
    if 'hello 1' in event.raw_text:
        text = event.raw_text
        sender = await event.get_sender()
        status = 0
        type = 1
        image = "/images/static/1.jpg"
        await WritetoDB_tg(sender.id, sender.title, text, status, type, image)
    # Мастерская финансов
    elif 'Обзор важных событий на' in event.raw_text:
        text = event.raw_text
        sender = await event.get_sender()
        status = 0
        type = 2
        image = "/images/static/masters.jpg"
        await WritetoDB_tg(sender.id, sender.title, text, status, type, image)
    # Профита нет. А если найду?
    elif 'Что да как? \n' in event.raw_text:
        text = event.raw_text
        sender = await event.get_sender()
        status = 0
        type = 2
        image = "/images/static/profit.jpg"
        await WritetoDB_tg(sender.id, sender.title, text, status, type, image)
        print('Что да как?')
    # СМАРТЛАБ
    elif '🔥Акции и инвестиции\n' in event.raw_text:
        text = event.raw_text
        sender = await event.get_sender()
        status = 0
        type = 2
        image = "/images/static/smartlab.jpg"
        await WritetoDB_tg(sender.id, sender.title, text, status, type, image)
    # Сигналы для торговли
    elif 'Какие события нас ждут сегодня? Доброе утро' in event.raw_text:
        text = event.raw_text
        sender = await event.get_sender()
        status = 0
        type = 2
        image = "/images/static/signal.jpg"
        await WritetoDB_tg(sender.id, sender.title, text, status, type, image)
    # после теста необходимо удалить
    else:
        senderid = '0'
        text = event.raw_text
        sender = await event.get_sender()
        status = 2
        type = 0
        image = "/images/static/2.jpg"
        await WritetoDB_tg(senderid, sender.title, text, status, type, image)



async def main():
    #подключение TG бота
    async with client:

        # сброс таймеров
        startTime = datetime.now()
        currentTime = datetime.now()
        lastTimeTgGather = datetime.now()
        lastTimeTgPost = datetime.now()
        lastTimeTwGather = datetime.now()
        lastTimeTwPost = datetime.now()
        lastTimeHMGather = datetime.now()
        lastTimeDoGather = datetime.now()
        lastTimeDoPost = datetime.now()
        #сбор статистики
        lastHour=0
        cycle=0
        postedTG=0
        postedPosts=0
        operatingTime=0

        # основной цикл
        while True:
            print('Время работы бота')
            currentTime = datetime.now()
            print('Текущее время':)
            print currentTime.strftime("%d-%m-%Y %H:%M")
            print(int_value_from_num_day(datetime.weekday(currentTime)))
            operatingTime=currentTime - startTime
            print('Работа без перерыва:')
            print(operatingTime)
            cycle = cycle+1
            #старт итерации цикла, сброс переменных

            #unProcessedQuantity = 0
            #unPostedQuantity = 0

            #проверка количества необработанных сообщений
            # unProcessedQuantity - количество сообщений ТГ
            # unProcessedQuantity_tw - количество сообщений twitter
            # unProcessedQuantity_vk - количество сообщений VK

            #проверка, включен ли функционал
            # 1 tg включен
            #config['telethon']['flag_on']
            #     1.1 сбор
            #config['telethon']['flag_gather']
            #     1.2 публикация
            #config['telethon']['flag_post']
            # 2 tw включен
            #config['twitter']['flag_on']
            #     2.1 сбор
            #config['twitter']['flag_gather']
            #     2.2 публикация
            #config['twitter']['flag_post']
            # 3 wp
            #config['wordpress']['flag_on']
            #     3.1 сбор
            #config['wordpress']['flag_gather']
            #     3.2 публикация
            #config['wordpress']['flag_post']
            # 4 vk
            #config['vk']['flag_on']
            #     4.1 сбор
            #config['vk']['flag_gather']
            #     4.2 публикация
            #config['vk']['flag_post']
            # 5 ig
            #config['ig']['flag_on']
            #     5.1 сбор
            #config['ig']['flag_gather']
            #     5.2 публикация
            #config['ig']['flag_post']



            # todo перенести из JNB бота VK
            # VK

            # TG
            if (config['telethon'].getboolean('flag_on')):
                unProcessedQuantity_tg = await CheckDB_tg(status=0)
                if unProcessedQuantity_tg > 0:
                    await DBprocessing_tg()
                    print('processed processed_tg')
                unPostedQuantity_tg = await CheckDB_tg(status=1)
                if unPostedQuantity_tg >0:
                    print('ready for send tg messages ', unPostedQuantity_tg)
                    if (config['telethon'].getboolean('flag_post') and (currentTime-lastTimeTgPost) > timedelta(minutes=int(config['twitter']['timeout_post']))):
                        await DBposting_tg()
                        print('posted post_tg')
                        lastTimeTgPost = datetime.now()



            # TW
            if (config['twitter'].getboolean('flag_on')):
                unProcessedQuantity_tw = await CheckDB_tw(0)
                if unProcessedQuantity_tw > 0:
                    await DBprocessing_tw()
                    print('processed processed_tw')
                unPostedQuantity_tw = await CheckDB_tw(1)
                if unPostedQuantity_tw > 0:
                    if (config['twitter'].getboolean('flag_post') and (currentTime-lastTimeTwPost) > timedelta(minutes=int(config['twitter']['timeout_post']))):
                        await DBposting_tw()
                        print('posted post_tw')
                        lastTimeTwPost = datetime.now()
                    print('ready for send tw messages', unPostedQuantity_tw)
                print("unProcessedQuantity_tw -",unProcessedQuantity_tw, "   ", "unPostedQuantity_tw -", unPostedQuantity_tw)
                if (config['twitter'].getboolean('flag_gather') and (currentTime-lastTimeTwGather) > timedelta(minutes=int(config['twitter']['timeout_gather']))):
                    await getTwitterMessages()
                    lastTimeTwGather = datetime.now()




            # domains
            # todo collect urls and xpath then throw to function

            if (config['domains'].getboolean('flag_on')):
                # unProcessedQuantity_tw = await CheckDB_tw(0)
                # if unProcessedQuantity_tw > 0:
                #     await DBprocessing_tw()
                #     print('processed processed_tw')
                # unPostedQuantity_tw = await CheckDB_tw(1)
                # if unPostedQuantity_tw > 0:
                #     if (config['twitter'].getboolean('flag_post') and (currentTime-lastTimeTwPost) > timedelta(minutes=int(config['twitter']['timeout_post']))):
                #         await DBposting_tw()
                #         print('posted post_tw')
                #         lastTimeTwPost = datetime.now()
                #     print('ready for send tw messages', unPostedQuantity_tw)
                # print("unProcessedQuantity_tw -",unProcessedQuantity_tw, "   ", "unPostedQuantity_tw -", unPostedQuantity_tw)
                if (config['domains'].getboolean('flag_gather') and (currentTime-lastTimeDoGather) > timedelta(minutes=int(config['domains']['timeout_gather']))):
                     await getDomainsPosts()
                     lastTimeDoGather = datetime.now()

            # posts
            # todo единый цикл
            # todo вывести в стенозависимые
            # todo режим работы heatmaps

            #текущее время и проверка на возможность отправкии (бот работает с 9 до 18)
            #if (config['general'].getboolean('operating_time_flag') and (currentTime - lastTimeHMGather) > timedelta(
            #        minutes=int(config['heatmaps']['timeout_gather']))):
            #tmp hardcode to test
            if (config['heatmaps'].getboolean('flag_on') and (currentTime-lastTimeHMGather) > timedelta(minutes=int(config['heatmaps']['timeout_gather'])) ) :
                print('Heatmap todo')
                if int(currentTime.strftime("%H")) > int(config['general']['operating_time_start']) and int(currentTime.strftime("%H")) < int(config['general']['operating_time_finish']) :
                    print('heatmap start')
                    # heatmap Мосбиржа
                    await getHeatmap(heatmap_sl_url=config['heatmaps']['heatmap_sl_url_1'],
                                     heatmap_sl_xpath=config['heatmaps']['heatmap_sl_xpath_1'],
                                     heatmap_sl_comment=config['heatmaps']['heatmap_sl_comment_1'])
                    # heatmap СПБбиржа
                    await getHeatmap(heatmap_sl_url=config['heatmaps']['heatmap_sl_url_2'],
                                     heatmap_sl_xpath=config['heatmaps']['heatmap_sl_xpath_2'],
                                     heatmap_sl_comment=config['heatmaps']['heatmap_sl_comment_2'])
                    # heatmap Обсуждаемое
                    await getHeatmap(heatmap_sl_url=config['heatmaps']['heatmap_sl_url_3'],
                                     heatmap_sl_xpath=config['heatmaps']['heatmap_sl_xpath_3'],
                                     heatmap_sl_comment=config['heatmaps']['heatmap_sl_comment_3'])
                    lastTimeHMGather = datetime.now()
                    print('Heatmap done')


            print('-------------')
            print("unProcessedQuantity_tg -", unProcessedQuantity_tg, "   ", "unPostedQuantity_tg -",
                  unPostedQuantity_tg)

            print(cycle)
            print('-------------')



# todo тут требуется тест с парсером selenium не будет ли конфликта при частых циклах (если уже запущен сбрщик)
# todo тут требуется тест с teegraph, выцепит ли он сообщения если сборщик на паузе (например стоит цикл проверки раз в час)
# Повторяется цикл раз в n секунд, например 300, но кажется излише часто (3600 секунд = 1 час, 14400 секунд = 4 часа)

            await asyncio.sleep(int(config['general']['timeout_bot_main_cicle'])) # остановка только корутины main, остальное будет работать фоном

if __name__ == '__main__':
    #workflow =
    asyncio.run(main())


# todo здесь собираем список долгосрочных задач

# todo собрать посты со SmartLab
# DONE in JNB
# todo придумать как обогащать таблицу domains, может загрузка csv?
# todo собирать статистику "успешно gathered" и "успешно posted" в отдельную таблицу
# todo twitter does't work via proxy
# todo variables to ENV ()
# todo proxy for download img to ENV
# todo VK
# todo instagram
# todo triggers to switch functions
# todo gather used CPU, Memory and Network


# todo определить условия для асинхронного запуска функций бота
# todo определить условия для запуска нескольких экземпляров бота единовременно
# todo переработка бота в callable объект @bot.on