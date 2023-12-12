from django.shortcuts import render,HttpResponse
# from sqlite3 import Date
from tokenize import Number
from textrank4zh import TextRank4Keyword
# import requests
# from bs4 import BeautifulSoup
import pymysql
import math
from six import u
import datetime
# from datetime import datetime
import requests
import re
from bs4 import BeautifulSoup
from six import u
from django.http import JsonResponse
from django.shortcuts import render
from PttCrawlerWordCloud.models import PTT,Keywords

def analyzedata():
    data = PTT.objects.filter(id__gte="0",id__lte="7")
    datanumcount=0

    turnbackdata = []
    for txt in data:
        tr4w = TextRank4Keyword()
        datanumcount=datanumcount+1
        tr4w.analyze(text=str(txt.content), lower=True, window=2)
        count=0
        for item in tr4w.get_keywords(20, word_min_len=1):
            if(len(item.word) > 1):
                dictdata={"text":str(item.word),"size":math.floor(item.weight*1000)}
                turnbackdata.append(dictdata)
            count=count+1							#資料長度不管有沒有大於一都COUNT+1
            if(count==5):
                break
        # print(str(len(data))+"/"+str(datanumcount))
    
    return turnbackdata

def runptt():
    PTT_URL = 'https://www.ptt.cc'
    BOARD_NAME = "Gossiping"
    Start_page = ""
    End_page = ""
    maxid=""

    db = pymysql.connect(host='127.0.0.1', port=3306, user='johnny', passwd='123456', db='text_mining')
    cursor = db.cursor()
    cursor.execute("select value from config where Name='history_page'")
    history_page=int(cursor.fetchall()[0][0])

    cursor.execute("select * from PTT order by id DESC limit 1")
    last_article_ID = cursor.fetchall()[0][1]
    print(last_article_ID)

    cursor.execute("select article_id from PTT where id>=(select Max(id) from PTT)-5 order by date desc")
    for page_id in cursor.fetchall():
        page = requests.get(
        url = PTT_URL + '/bbs/' + BOARD_NAME + '/' + str(page_id[0]) + '.html',
        cookies={'over18': '1'}, verify=True, timeout=30
        )
        if page.status_code == 200:
            maxid=page_id[0]
            break
    print(maxid)

    for page_index in range(history_page+1,50000,1):
        print("runningpage",page_index)
        page = requests.get(
        url = PTT_URL + '/bbs/' + BOARD_NAME + '/index' + str(page_index) + '.html',
        cookies={'over18': '1'}, verify=True, timeout=30
        )
        if page.status_code == 404:
            break
        if page.status_code != 200:
            continue
        else:
            End_page=page_index
        soup = BeautifulSoup(page.text,"html.parser")
        divs = soup.find_all("div","r-ent")
        print("running loop")
        for div in divs:
            try:
                article_href = div.find('a')['href']
                article_link = PTT_URL + article_href
                article_id = re.sub('\.html', '', article_link.split('/')[-1])
                if maxid == article_id:
                    Start_page=page_index
            except:
                continue
        if Start_page != "":
            break

    if Start_page == "":
        for page_index in range(history_page,0,-1):
            print("runningpage",page_index)
            page = requests.get(
            url = PTT_URL + '/bbs/' + BOARD_NAME + '/index' + str(page_index) + '.html',
            cookies={'over18': '1'}, verify=True, timeout=30
            )
            if page.status_code != 200:
                continue
            else:
                if End_page=="":
                    End_page=page_index
            soup = BeautifulSoup(page.text,"html.parser")
            divs = soup.find_all("div","r-ent")
            print("running loop")
            for div in divs:
                try:
                    article_href = div.find('a')['href']
                    article_link = PTT_URL + article_href
                    article_id = re.sub('\.html', '', article_link.split('/')[-1])
                    if maxid == article_id:
                        Start_page=page_index
                except:
                    continue
            if Start_page != "":
                break
    print("起始頁",Start_page)
    print("最後一頁",End_page)

    for page_index in range(Start_page, End_page+1):

        db = pymysql.connect(host='127.0.0.1', port=3306, user='johnny', passwd='123456', db='text_mining')
        cursor = db.cursor()
        # 連接到每頁並確認滿18歲
        page = requests.get(
            url = PTT_URL + '/bbs/' + BOARD_NAME + '/index' + str(page_index) + '.html',
            cookies={'over18': '1'}, verify=True, timeout=30
        )

        # 確認每頁都是有效的連接
        if page.status_code != 200:
            continue

        cursor.execute("UPDATE `config` SET `value`=%s WHERE `Name`='history_page'",str(page_index))
        db.commit()

        soup = BeautifulSoup(page.text, 'html.parser')
        divs = soup.find_all("div", "r-ent")
        print(page_index)
        for div in divs:
            try:
                # 如果已刪文，連href都會沒有
                # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                article_href = div.find('a')['href']
                article_link = PTT_URL + article_href
                article_id = re.sub('\.html', '', article_link.split('/')[-1])

                article_link = PTT_URL + '/bbs/' + BOARD_NAME + '/' + article_id + '.html'

                article_resp = requests.get(url=article_link, cookies={'over18': '1'}, verify=True, timeout=3)
                # 確認文章連結無誤
                if article_resp.status_code == 200:
                    soup = BeautifulSoup(article_resp.text, 'html.parser')
                    main_content = soup.find(id="main-content")
                    metas = main_content.select('div.article-metaline')

                    author = ''
                    title = ''
                    date = ''
                    if metas:
                        author = metas[0].select('span.article-meta-value')[0].string if metas[0].select('span.article-meta-value')[0] else author
                        title = metas[1].select('span.article-meta-value')[0].string if metas[1].select('span.article-meta-value')[0] else title
                        date = metas[2].select('span.article-meta-value')[0].string if metas[2].select('span.article-meta-value')[0] else date
                        # remove meta nodes
                        for meta in metas:
                            meta.extract()
                        for meta in main_content.select('div.article-metaline-right'):
                            meta.extract()
                    
                    try:
                        ip = main_content.find(text=re.compile(u'※ 發信站:'))
                        ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
                    except:
                        ip = "None"
                    
                    # 移除 '※ 發信站:' (starts with u'\u203b'), '◆ From:' (starts with u'\u25c6'), 空行及多餘空白
                    # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
                    filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
                    expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
                    for i in range(len(filtered)):
                        filtered[i] = re.sub(expr, '', filtered[i])

                    filtered = [_f for _f in filtered if _f]  # remove empty strings
                    filtered = [x for x in filtered if article_id not in x]  # remove last line containing the url of the article
                    content = ' '.join(filtered)
                    content = re.sub(r'(\s)+', ' ', content)

                    try:
                        content = content.split(" 推")[0]
                    except:
                        content = content.split(" 噓")[0]

                    # https://stackoverflow.com/questions/47167369/converting-31-oct-17-03-58-50-454-pm-to-datetime-format-using-pandas
                    date = date.split(" ")
                    try:
                        # 過十號以後的格式
                        print(date)
                        trans_date = datetime.datetime.strptime("{}-{}-{} {}".format(date[-1], date[1], date[2], date[3]), '%Y-%b-%d %H:%M:%S')
                    except:
                        # 十號以前格式
                        print(date)
                        trans_date = datetime.datetime.strptime("{}-{}-{} {}".format(date[-1], date[1], date[2], date[3]), '%Y-%b-%d %H:%M:%S')
                    
                    article_sql = "INSERT INTO PTT (article_id, author, title, content, date, ip) VALUES (%s,%s,%s,%s,%s,%s)"
                    article_val = (article_id, author, title, content, trans_date, ip)
                    cursor.execute(article_sql, article_val)
                    print("Process article ID : {}".format(article_id))
                    # db.commit()

                
            except:
                print("已刪文!!!")
                continue
        
        # print(len(each_page_articleID))
        db.commit()
        db.close()

def index(request):
    data = analyzedata()
    return render(request, 'index.html', {"data":data})

def getdata(request):
    data = analyzedata()
    # return render(request, 'home/getdata.html',{'form':{'message': 'success'}})
    return JsonResponse({"data":data})

def crawler(request):
    runptt()
    return "done"

def test(request):
    # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')

    # if x_forwarded_for:
    #     print(x_forwarded_for.split(',')[0])     
    # else:
    #     print(request.META.get('REMOTE_ADDR'))

    print(request.META.get('REMOTE_ADDR'))
    return JsonResponse({"data":"aaaaaaa"})


    

            
