from bs4 import BeautifulSoup
import urllib2
import MySQLdb
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
def data_import(sql):
    print 'Import into mysql :'+sql
    flag=False
    db = MySQLdb.connect(host='localhost',port=3307,user='root',passwd='',db='py_aliexpress',charset='utf8')
    cursor = db.cursor()
    cursor.execute("SET NAMES utf8mb4;")
    try:
        cursor.execute(sql)
        db.commit()
        flag=True
    except:
        db.rollback()
        flag=False
    db.close()
    return flag

def data_select(sql):
    print sql
    db = MySQLdb.connect(host='localhost',port=3307,user='root',passwd='',db='py_aliexpress',charset='utf8')
    cursor = db.cursor()
    print('Begin select ...')
    try:
        cursor.execute(sql)
        results=cursor.fetchall()
        return results
    except:
        print "Error: unable to fecth data"
        db.close()
        return False
    db.close()
    return results

def url_handle(strs):
    strs = strs.replace("//www", "https://www")
    return strs

def get_urls(url_category,request):
    get_products(url_category, request)
    html_doc=request.get(url_category).text
    soup = BeautifulSoup(html_doc, "html.parser")
    categories=soup.find("div","ui-pagination-navi util-left")
    categories=categories.find_all("a")
    for category in categories:
        category=str(category.attrs['href'])
        print "Start get products of "+str(category)
        category=url_handle(category)
        get_products(category,request)
    print 'Fetch urls and products successfully !!'

def get_products(url_category,request):
    print "Getting Category of "+str(url_category)
    num=0
    num_duplicate=0
    html_doc = request.get(url_category).text
    soup = BeautifulSoup(html_doc, "html.parser")
    products=soup.find_all("div","detail")
    for product in products:
        product=BeautifulSoup(str(product), "html.parser")
        product_url=product.find("a").attrs['href']
        product_url=url_handle(str(product_url))
        sql = "insert into products (product_url,status0) values ('%s',0)" %(product_url)
        sql_select = "select * from products where product_url='%s'"%(product_url)
        if data_select(sql_select):
            num_duplicate = num_duplicate+1
            continue
        try:
            if data_import(sql):
                num = num+1
            else:
                num_duplicate = num_duplicate+1
        except Exception as e:
            print (str(e))
    print 'Get products '+str(num)+'(new) '+str(num_duplicate)+'(duplicate) successfully !!'

def data_handle(datas):
    datas=MySQLdb.escape_string(datas)
    return datas
def get_detail(limit ,request):
    flag=False
    count=1
    if limit==0:
        limit=6000
    sql="select * from products where status0 !=1 order by id limit "+str(limit)
    results=data_select(sql)
    for purl in results:
        url=purl[0]
        print 'Begin Get P_detail of  '+str(url)+' '+str(count)+' of '+str(len(results))
        if get_products_detail(url,request):
            flag=True
        else:
            flag=False
        time.sleep(3)
        count=count+1
    return flag
def get_products_detail(url_product,request):
    flag=False
    print "Getting Details of "+str(url_product)
    html_doc = request.get(url_product).text
    if html_doc==None:
        return flag
    soup = BeautifulSoup(html_doc, "html.parser")
    name = soup.find("h1", "product-name").string
    name=data_handle(name)
    price = soup.find("span", "p-price", id="j-sku-discount-price").string
    image = soup.find("a", "ui-image-viewer-thumb-frame").img.attrs['src']
    image=data_handle(image)
    category_soup=soup.find("div", "module m-sop m-sop-crumb")
    category=""
    for abtext in category_soup.find_all(["a", "b"]):
        category = category + "|" + str(abtext.string)
    category=data_handle(category)
    brand="baellerry"
    sql = "insert into products_detail (pname,price,category,images,brand) values ('%s','%s','%s','%s','%s')" % (name,price,category,image,brand)
    try:
        if data_import(sql):
            flag=True
        else:
            flag = False
    except Exception as e:
        print (str(e))
    print 'Get product detail of '+str(url_product)+' successfully !!'
    if flag:
        sql2 = "update products set status0=1 where product_url ='%s'" % url_product
        data_import(sql2)
    return flag

def setup():
    browser = webdriver.Firefox()
    browser.implicitly_wait(10)
    return browser

def login(username, password,browser=None):
    browser.get("https://login.aliexpress.com/buyer.htm")
    browser.switch_to.frame('alibaba-login-box')
    pwd_btn = browser.find_element_by_name("password")
    act_btn = browser.find_element_by_name("loginId")
    submit_btn = browser.find_element_by_name("submit-btn")
    act_btn.send_keys(username)
    time.sleep(2)
    pwd_btn.send_keys(password)
    time.sleep(5)
    submit_btn.send_keys(Keys.ENTER)
    return browser

def set_sessions(browser):
    request = requests.session()
    #headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64)" "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36"}
    #request.headers.update(headers)
    cookies = browser.get_cookies()
    for cookie in cookies:
        request.cookies.set(cookie['name'], cookie['value'])
    print "request return"
    return request

def prepare():
    print "Preparing sessions"
    browser = login("ayu@hotmail.com", "yourpassword", setup())
    rq = set_sessions(browser)
    print "Sessions ok"
    return rq
if __name__=='__main__':
    str_input1 = int(input("0->Quit;\n 1->Search P_url through Category;\n 2->Get P_detail;\n 3->How many reviews;\n 4->Products Left;\n"))
    if str_input1 == 1:
        rq = prepare()
        while 1:
            print "Start geting new url"
            str_input2 = raw_input("Enter the category you want to scrapy p_url,\n Url after :\nhttp//www.aliexpress.com/\n")
            if len(str_input2) == 1:
                break
            str_input2 = 'https://www.aliexpress.com/' + str(str_input2)
            get_urls(str(str_input2), rq)
    elif str_input1 == 2:
        rq = prepare()
        while 1:
            print "Start geting product details"
            str_input2 = input("How many products:\n")
            if int(str_input2) == 0:
                break
            get_detail(int(str_input2), rq)
    elif str_input1 == 3:
        print "3"
        #total_reviews()
    elif str_input1 == 4:
        print "4"
        #left_products()
    else:
        print 'Quit...'
        #https://www.aliexpress.com/store/520
