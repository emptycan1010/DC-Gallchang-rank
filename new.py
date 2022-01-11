import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()
import re,requests,sys,time,html,random
from bs4 import BeautifulSoup
from gevent.pool import Pool
import numpy as np
import pandas as pd
from base64 import b64encode
from hashlib import sha256
import json
import time
print("Started")
def get_app_id(): #공앱에서 사용하는 app_id 값 받아오기. 주기적으로 새로 발급해야함
    while True:
        try:
            date = requests.get('http://json2.dcinside.com/json0/app_check_A_rina.php').json()[0]['date']
            value_token = sha256(('dcArdchk_%s' % date).encode('ascii')).hexdigest()
            app_id = requests.post('https://msign.dcinside.com/auth/mobile_app_verification', data = {"value_token": value_token,"signature":'ReOo4u96nnv8Njd7707KpYiIVYQ3FlcKHDJE046Pg6s=','client_token':'asdf'}).json()['app_id']
            return app_id
        except Exception as e:e = str(e)
def gethtml(no): #글 수집
    count = 0 #에러 체크용 카운트, 10 넘으면 스크랩 패스
    url = "http://app.dcinside.com/api/gall_view_new.php?id="+gall+"&no="+str(no)+"&app_id="+app_id
    while True:
        try:
            a = session.get('http://m.dcinside.com/api/redirect.php?hash='+ b64encode(url.encode('utf-8')).decode('utf-8'),headers={"User-Agent": "dcinside.app"},timeout=5)
            if r'\uae00\uc5c6\uc74c' in a.text: return 0; #삭제된 글 체크
            if r'\uc571\uc2a4\ud1a0\uc5b4\uc758 \uc57d\uad00' in a.text: return 0; 
            intro = a.json(strict=False)[0]['view_info'];view = a.json(strict=False)[0]['view_main']
            postcontent = view['memo'] #글 내용
            postIP = intro['user_id'] if len(intro['ip'])==0 else intro['ip'] #작성자 IP
            mobile = False if intro['write_type']=='W' else True #모바일 체크
            recom = False if intro['recommend_chk'] == 'N' else True #개념글 체크
            break
        except requests.exceptions.RequestException as e:pass
        except requests.Timeout as e:pass
        except Exception as e:
            if not('<!DOCTYPE html>' in a.text or a.text == ''):print(no,'idf', end=' ');print(str(e));print(a.text)
            count+=1
            if count > 10:sys.exit()
        
    print(str(no) + "글수집완료")
    # time.sleep(0.00001)
    #댓글
    replypage = 1;total_comment = 0;passnick = 'deleted';passIP = 'deleted'
    while True:
        mobileurl = "http://m.dcinside.com/api/redirect.php?hash="+b64encode(("http://app.dcinside.com/api/comment_new.php?csort=new&id="+gall+"&no="+str(no)+"&re_page="+str(replypage)+"&app_id="+app_id+"=").encode('utf-8')).decode('utf-8')+"%3D%3D"
        count=0 #에러 체크용 카운트, 10 넘으면 스크랩 패스
        while True:
            try:
                a = session.get(mobileurl,headers={"User-Agent": "dcinside.app"},timeout=5)
                comment = a.json(strict=False)[0]
                for comm in comment['comment_list']:
                    if not('ipData' in comm.keys()): comm['ipData'] = ''
                    if 'under_step' in comm.keys(): target = '%s (%s)' % (passnick,passIP);
                    else: passnick = comm['name']; passIP = comm['user_id'] if len(comm['ipData'])==0 else comm['ipData']; target = None
                    IP = comm['user_id'] if len(comm['ipData'])==0 else comm['ipData']
                    dccon = True if 'dccon' in comm.keys() else False
                    if 'is_delete_flag' in comm.keys():
                        if '작성자' in comm['is_delete_flag']: removed_by_writer = True
                        else: removed_by_writer = False
                    else: removed_by_writer = False
                        
                    content = comm['comment_memo'] if dccon==False else comm['dccon']
                    commlist.append({u'번호':no,u'날짜':comm['date_time'],u'닉네임':comm['name'],'ID/IP':IP,'idtype':comm['member_icon'],'content':content, 'dccon':dccon,
                                     '답글 대상':target, '댓삭 당한 횟수':removed_by_writer})
                break
            except requests.exceptions.RequestException as e:pass
            except requests.Timeout as e:pass
            except Exception as e:
                if not('<!DOCTYPE html>' in a.text or a.text == ''): print(no,'cdf', end=' ');print(str(e)); print(a.text)
                count+=1
                if count > 10:sys.exit()

        if len(comment['comment_list']) == 0: break
        else: total_comment+= len(comment['comment_list'])
        replypage+=1
    postlist.append({u'번호':no,u'제목':intro['subject'],u'날짜':intro['date_time'],u'닉네임':intro['name'],'ID/IP':postIP,'idtype':intro['member_icon'],
                     u'조회 수':intro['hit'],u'달린 댓글 수':total_comment,u'추천 수':view['recommend'],u'비추 수':view['nonrecommend'],
                     'content':postcontent,'mobile':mobile,u'개념글 수':recom})



                
print(get_app_id())
# start = 813000 #시작 번호 (젤 최근 게시글 번호)
start = 813087
end = 699010 # 종료 번호
gall = 'weatherbaby';year = 2021 ;month = 8 # 갤러리, 연, 월
baseloc = 'D:/DC' + '/%s/%s/%s/' % (gall,year,month) # 경로
turn = 500 # step 한국어로 뭐라하는지 모름
session = requests.Session()
pool = Pool(1000)
idf = pd.read_json(baseloc+'post.json');cdf = pd.read_json(baseloc+'comment.json')
app_id=get_app_id()
exit=False
while True:
    start_time = time.time() # 시간 측정용 현재 시간 저장
    commlist = [];postlist = [] # dataframe 변환용 list 초기화
    pl = list(range(start+1-turn,start+1)); pl.reverse()
    postnums = idf[u'번호'].values.tolist() # 중복 글 체크용 번호 목록 생성
    for postnum in pl:
        if postnum < end: exit = True;continue # 종료 번호보다 오래된 글 일시 패스
        if postnum in idf[u'번호'].values.tolist(): continue # 중복 글 체크용인데 보통은 안 쓰니 주석처리 해놓는게 처리속도 더 빠름
        pool.spawn(gethtml,postnum)
    pool.join()
    print(len(postlist), end=' ')
    print("%.2f" % (time.time() - start_time) +u' 초 |', end=' ') # 수집 글 갯수, 소요 시간 출력
    start = start - turn
    if len(postlist) != 0: pd.concat([idf, pd.DataFrame(postlist)],sort=False).reset_index(drop=True).to_json(baseloc+'post.json')
    if len(commlist) != 0: pd.concat([cdf, pd.DataFrame(commlist)],sort=False).reset_index(drop=True).to_json(baseloc+'comment.json') #저장
    if exit==True: sys.exit()
    if len(postlist) != 0: app_id=get_app_id();idf = pd.read_json(baseloc+'post.json');cdf = pd.read_json(baseloc+'comment.json') # db에 추가된 거 있을시 다시 로드