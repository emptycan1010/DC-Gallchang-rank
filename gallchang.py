import pandas as pd
import numpy as np
import sys,re,collections,imgkit
from bs4 import BeautifulSoup
pd.set_option('display.max_columns', -1);pd.set_option('display.max_rows', -1);pd.set_option('display.max_colwidth', -1)
config = imgkit.config(wkhtmltoimage=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe')

#압축파일 경로
cssloc = 'D:/DC'
css = cssloc+'/css.css'

gall = 'weatherbaby';gallname = '날갤' #갤러리 id, 갤러리 이름

year=2021;month=8 #현재
baseloc = 'D:/DC' + '/%s/%s/%s/' % (gall,year,month)
idf = pd.read_json(baseloc+'post.json');cdf = pd.read_json(baseloc+'comment.json')
pastyear=2021;pastmonth = 8 #비교대상. 주로 한달 전. 필요없으면 위랑 똑같이
baseloc = 'D:/DC' + '/%s/%s/%s/' % (gall,pastyear,pastmonth)
pastidf = pd.read_json(baseloc+'post.json');pastcdf = pd.read_json(baseloc+'comment.json')


#날짜 필터링. 필요없으면 (수집기간이 한달이 아니라던가 등) 주석처리
#idf[u'날짜'] = pd.to_datetime(idf[u'날짜'],format='%Y.%m.%d %H:%M')
#cdf[u'날짜'] = pd.to_datetime(cdf[u'날짜'],format='%Y.%m.%d %H:%M')
#idf = idf[(idf[u'날짜'].dt.month == month)];cdf = cdf[(cdf[u'날짜'].dt.month == month)]
#idf = idf[(idf[u'날짜'].dt.year == year)];cdf = cdf[(cdf[u'날짜'].dt.year == year)]

#pastidf[u'날짜'] = pd.to_datetime(pastidf[u'날짜'],format='%Y.%m.%d %H:%M')
#pastcdf[u'날짜'] = pd.to_datetime(pastcdf[u'날짜'],format='%Y.%m.%d %H:%M')
#pastidf = pastidf[(pastidf[u'날짜'].dt.month == pastmonth)];pastcdf = pastcdf[(pastcdf[u'날짜'].dt.month == pastmonth)]
#pastidf = pastidf[(pastidf[u'날짜'].dt.year == pastyear)];pastcdf = pastcdf[(pastcdf[u'날짜'].dt.year == pastyear)]

#통신사 IP 묶음. 개별적으로 처리하고 싶다면 주석처리. 주석처리하면 notongpi 펑션 사용불가(알아서 고치셈)
for i in ['39.7','110.70','175.223','175.252','211.246','210.125']:
    idf.loc[:,'ID/IP'] = idf.loc[:,'ID/IP'].replace(i,'KT.');cdf.loc[:,'ID/IP'] = cdf.loc[:,'ID/IP'].replace(i,'KT.')
    pastidf.loc[:,'ID/IP'] = pastidf.loc[:,'ID/IP'].replace(i,'KT.');pastcdf.loc[:,'ID/IP'] = pastcdf.loc[:,'ID/IP'].replace(i,'KT.')
for i in ['203.226','211.234','115.161','121.190','122.202','122.32','175.202','223.32','223.33','223.62','223.38','223.39','223.57']:
    idf.loc[:,'ID/IP'] = idf.loc[:,'ID/IP'].replace(i,'SKT.');cdf.loc[:,'ID/IP'] = cdf.loc[:,'ID/IP'].replace(i,'SKT.')
    pastidf.loc[:,'ID/IP'] = pastidf.loc[:,'ID/IP'].replace(i,'SKT.');pastcdf.loc[:,'ID/IP'] = pastcdf.loc[:,'ID/IP'].replace(i,'SKT.')
for i in ['61.43','211.234','114.200','117.111','211.36','106.102','125.188']:
    idf.loc[:,'ID/IP'] = idf.loc[:,'ID/IP'].replace(i,'LG U+.');cdf.loc[:,'ID/IP'] = cdf.loc[:,'ID/IP'].replace(i,'LG U+.')
    pastidf.loc[:,'ID/IP'] = pastidf.loc[:,'ID/IP'].replace(i,'LG U+.');pastcdf.loc[:,'ID/IP'] = pastcdf.loc[:,'ID/IP'].replace(i,'LG U+.')

#왜 넣은건지 기억안남
idf.loc[:,'idtype'] = idf.loc[:,'idtype'].astype(np.uint8);cdf.loc[:,'idtype'] = cdf.loc[:,'idtype'].astype(np.uint8)
pastidf.loc[:,'idtype'] = pastidf.loc[:,'idtype'].astype(np.uint8);pastidf.loc[:,'idtype'] = pastidf.loc[:,'idtype'].astype(np.uint8)

#이미지 설정. 알아서
options = {
    'format': 'jpg',
    'encoding': "UTF-8",
    'quality' : '70',
    'width' : '1280',
}
def notongpi(df): #통피 제외하고 처리
    df = df.reset_index(); df = df[~df['ID/IP'].isin(['KT.','SKT.','LG U+.'])]
    return df
def tongpi(df): #통피 포함하고 처리
    df = df.reset_index()
    return df
def getanswerrank(nick,ip,idf2,cdf2): #답글 비율
    if '.' in ip:cdf2 = cdf2[cdf2[u'닉네임'] == nick[5:]];cdf2 = cdf2[cdf2['ID/IP'] == ip]
    else:cdf2 = cdf2[cdf2['ID/IP'] == ip]
    cdf2 = cdf2[~cdf2['답글 대상'].isnull()]
    if len(cdf2) == 0:return '-'
    cdf2['count'] = 1
    nickcheck = cdf2.groupby(['답글 대상']).sum().reset_index()
    nickcheck['count'] = 100*nickcheck['count']/len(cdf2)
    ql = nickcheck.sort_values('count',ascending=False).head(5)
    docomrank = ''
    for e,i in zip(ql[u'답글 대상'],ql['count']): docomrank = docomrank+e+': '+'{0:.2f}%'.format(i)+'<br>'
    return docomrank[:-4]
def getcomrank(nick,ip,idf2,cdf2): #단 댓글 비율
    if '.' in ip:cdf2 = cdf2[cdf2[u'닉네임'] == nick[5:]];cdf2 = cdf2[cdf2['ID/IP'] == ip]
    else:cdf2 = cdf2[cdf2['ID/IP'] == ip]
    if len(cdf2) == 0: return '-'
    idf2['count'] = 1
    idf2 = idf2[idf2[u'번호'].isin(cdf2[u'번호'].values)]
    nickcheck = idf2.groupby(['ID/IP',u'닉네임']).sum().reset_index()
    nickcheck['count'] = 100*nickcheck['count']/len(idf2)
    nickcheck[u'닉네임'] = nickcheck[u'닉네임']+'('+nickcheck['ID/IP'].map(str)+')'
    ql = nickcheck.sort_values('count',ascending=False).head(5)
    docomrank = ''
    for e,i in zip(ql[u'닉네임'],ql['count']): docomrank = docomrank+e+': '+'{0:.2f}%'.format(i)+'<br>'
    return docomrank[:-4]
def getgotcomrank(nick,ip,idf2,cdf2): #달린 댓글 비율
    if '.' in ip:idf2 = idf2[idf2[u'닉네임'] == nick[5:]]; idf2 = idf2[idf2['ID/IP'] == ip]
    else:idf2 = idf2[idf2['ID/IP'] == ip]
    cdf2['count'] = 1
    alist = idf2[u'번호'].tolist()
    cdf2 = cdf2[cdf2[u'번호'].isin(alist)]
    if len(idf2) == 0 or len(cdf2) == 0:return '-'
    totalcomment = len(cdf2)
    nickcheck = cdf2.groupby([u'닉네임','ID/IP']).sum()
    nickcheck['count'] = 100*nickcheck['count']/totalcomment
    nickcheck2 = nickcheck.reset_index()
    nickcheck2[u'닉네임'] = nickcheck2[u'닉네임']+'('+nickcheck2['ID/IP'].map(str)+')'
    nickcheck2 = nickcheck2.drop('ID/IP',1)
    ql = nickcheck2.sort_values('count',ascending=False).head(5)
    docomrank = ''
    for e,i in zip(ql[u'닉네임'],ql['count']):docomrank = docomrank+e+': '+'{0:.2f}%'.format(i)+'<br>'
    return docomrank[:-4]
def make_html(ch,col,ascending): #표 생성. 이젠 나도 어떻게 왜 작동하는지 모름
    acol = col
    if ' 비' in col or '비율' in col:acol = col+'1'
    html = BeautifulSoup(ch,'lxml')
    table = html.find('table')
    table['style'] = u'font-family:맑은 고딕;border-collapse:collapse;border: 1px solid transparent'
    thead = html.find('thead')
    for i, th in enumerate(thead.find_all('th')):
        i=i+1
        if i == 1:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121); background-color: rgb(23, 23, 23); height: 1px;width: 120px; border-left: 3px solid rgb(121, 121, 121); border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
        elif i == 2:#닉네임
            th['style'] = 'font-weight:bolder;color:white;font-size:18pt; background-color: rgb(23, 23, 23); width: 600px; border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
        elif i == 3:
            th['style'] = 'font-weight:bolder;color:white;font-size:14pt; background-color: rgb(23, 23, 23); width: 120px; border-right: 2px solid rgb(121, 121, 121);border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
        elif len(thead.find_all('th'))-2==i:
            th['style'] = 'font-weight:bolder;color:white;font-size:18pt; background-color: rgb(23, 23, 23); width: 600px;border-left: 1px solid rgb(121, 121, 121); border-right: 1px solid rgb(121, 121, 121);border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
        elif len(thead.find_all('th'))-1==i:
            th['style'] = 'font-weight:bolder;color:white;font-size:18pt; background-color: rgb(23, 23, 23); width: 600px;border-left: 1px solid rgb(121, 121, 121); border-right: 1px solid rgb(121, 121, 121);border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
        elif len(thead.find_all('th'))==i:
            th['style'] = 'font-weight:bolder;color:white;font-size:18pt; background-color: rgb(23, 23, 23); width: 600px; border-top: 3px solid rgb(121, 121, 121); border-right: 3px solid rgb(121, 121, 121);border-bottom: 3px solid rgb(121, 121, 121);'
        else:
            th['style'] = 'font-weight:bolder;color:white;font-size:14pt; background-color: rgb(23, 23, 23); width: 130px; border-right: 1px solid rgb(121, 121, 121);border-top: 3px solid rgb(121, 121, 121); border-bottom: 3px solid rgb(121, 121, 121);'
    tbody = html.find('tbody')
    for i, th in enumerate(tbody.find_all('th')):
        i=i+1
        if check.iloc[i-1][acol+'pct']==1:
            temp = th.text
            th.clear()
            h1= html.new_tag("h1")
            th.append(h1)
            th.h1.string = temp
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121); background-color: rgb(53, 53, 53); border-bottom:1px solid rgb(121, 121, 121);border-left: 3px solid rgb(121, 121, 121); '
        elif len(tbody.find_all('th'))==i:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt; background-color: rgb(43, 43, 43); border-left: 3px solid rgb(121, 121, 121);border-bottom: 3px solid rgb(121, 121, 121);'
        elif i%2==0:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt; background-color: rgb(43, 43, 43); border-left: 3px solid rgb(121, 121, 121);border-bottom: 1px solid rgb(121, 121, 121);'
        elif i%2==1:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt; background-color: rgb(53, 53, 53); border-left: 3px solid rgb(121, 121, 121);border-bottom: 1px solid rgb(121, 121, 121);'
        else:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt; background-color: rgb(43, 43, 43);  border-left: 3px solid rgb(121, 121, 121);border-bottom: 1px solid rgb(121, 121, 121);'
    trs = tbody.find_all('tr')
    for tri, tr in enumerate(trs):
        for i, td in enumerate(tr.find_all('td')):
            i=i+1
            backcolor='rgb(53, 53, 53)' if tri%2==0 else 'rgb(43, 43, 43)'
            bottom='1' if tri+1!=len(trs) else '3'
            if i == 1:#닉
                if check.iloc[tri][acol+'pct']==1:
                    for br in td.find_all("br"):
                        br.replace_with("\n")
                    temp = td.text;td.clear();
                    for nick in temp.split('\n'):
                        if nick.count('%') < 4:h1= html.new_tag("h1");td.append(h1);td.h1.string = nick;continue
                        idtype = int(nick[2])
                        if idtype == 1:
                            h1= html.new_tag("h1");img= html.new_tag("img",src='file:///%s/g_fix.gif'%cssloc);td.append(h1);
                            h1.string=nick[5:]+' ';h1.append(img)
                        elif idtype == 2:
                            h1= html.new_tag("h1");img= html.new_tag("img",src='file:///%s/g_default.gif'%cssloc);td.append(h1);
                            h1.string=nick[5:]+' ';h1.append(img)
                        else:
                            h1= html.new_tag("h1");td.append(h1);
                            h1.string=nick[5:]
                else:
                    for br in td.find_all("br"):br.replace_with("\n")
                    temp = td.text;td.clear();
                    for nick in temp.split('\n'):
                        if nick.count('%') < 4:h2= html.new_tag("h2");td.append(h2);td.h2.string = nick;continue
                        idtype = int(nick[2])
                        if idtype == 1:
                            h2= html.new_tag("h2");img= html.new_tag("img",src='file:///%s/g_fix.gif'%cssloc);td.append(h2);
                            h2.string=nick[5:]+' ';h2.append(img)
                        elif idtype == 2:
                            h2= html.new_tag("h2");img= html.new_tag("img",src='file:///%s/g_default.gif'%cssloc);td.append(h2);
                            h2.string=nick[5:]+' ';h2.append(img)
                        else:
                            h2= html.new_tag("h2");td.append(h2);
                            h2.string=nick[5:]
                td['style'] = u'<color:violet;font-size: 13pt; background-color:'+backcolor+'; border-bottom:'+bottom+'px solid rgb(121, 121, 121);'
            elif i == 2:#아이디
                if check.iloc[tri][acol+'pct']==1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp;
                td['style'] = u'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 11pt; background-color:'+backcolor+'; border-bottom:'+bottom+'px solid rgb(121, 121, 121);'
            elif len(tr.find_all('td'))==i:
                td['style'] = 'border-right: 3px solid rgb(121, 121, 121);color:white;font-size:8pt; background-color:'+backcolor+';border-bottom: '+bottom+'px solid rgb(121, 121, 121);border-left: 1px solid rgb(121, 121, 121);'
            elif len(tr.find_all('td'))-1==i:
                td['style'] = 'color:white;font-size:8pt; background-color:'+backcolor+';border-bottom: '+bottom+'px solid rgb(121, 121, 121);border-left: 1px solid rgb(121, 121, 121);'
            elif len(tr.find_all('td'))-2==i:
                td['style'] = 'color:white;font-size:8pt; background-color:'+backcolor+';border-bottom: '+bottom+'px solid rgb(121, 121, 121);border-left: 1px solid rgb(121, 121, 121);'

            elif i == 3:#col
                td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ;border-left: 1px solid rgb(121, 121, 121);  border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                if col in ['글댓 비','달린 댓글 수 평균','조회 수 평균']:
                    pct = check.iloc[tri][u'글 수pct']
                    
                    if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                    elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                    elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                    elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                    elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                    elif pct == 1:temp = td.text;td.clear(); h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp
                else:
                    pct = check.iloc[tri][acol+'pct']
                    
                    if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                    elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                    elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                    elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                    elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                    elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp;
            else:
                td['style'] = 'font-weight:bold;color:lightgray;font-size: 13pt; background-color:'+backcolor+' ;border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                if i==4:#글댓 비율
                    td['style'] = 'border-right: 1px solid rgb(121, 121, 121);font-weight:bold;color:orange;font-size: 13pt; background-color:'+backcolor+' ; border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                    pct = check.iloc[tri][u'글댓 비1pct']
                    
                    if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                    elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                    elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                    elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                    elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                    elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp;
                if i==5:#댓글 수 평균
                    td['style'] = 'border-right: 1px solid rgb(121, 121, 121);font-weight:bold;color:orange;font-size: 13pt; background-color:'+backcolor+' ; border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                    pct = check.iloc[tri][u'달린 댓글 수 평균pct']
                    if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                    elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                    elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                    elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                    elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                    elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp;
                if i==6:#조회수 평균
                    pct = check.iloc[tri][u'조회 수 평균pct']
                    td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ; border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                    if pct < 0.3: td['style'] = td['style']+'color:tomato;'#71%~100%
                    elif pct < 0.5:td['style'] = td['style']+'color:orange;'#51%~70%
                    elif pct < 0.7:td['style'] = td['style']+'color:yellow;'#31%~50%
                    elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'#11%~30%
                    elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'#~10%
                    elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp;
                        
    ch = str(html).replace('(▲','<br><a style="color:lightgray;font-size:8pt">(<a style="color:MediumSeaGreen ;font-size:8pt">▲</a><a style="color:lightgray;font-size:8pt">').replace('(▼','<br><a style="color:lightgray;font-size:8pt">(<a style="color:tomato;font-size:8pt">▼</a><a style="color:lightgray;font-size:8pt">')
    ch = ch.replace('(N)','<br><a style="color:lightgray;font-size:8pt">(<a style="color:orange;font-size:8pt;font-weight:bolder">NEW</a><a style="color:lightgray;font-size:8pt">)').replace('(-)','<br><a style="color:lightgray;font-size:8pt">(-)').replace('달린 댓글 수 평균','달린<br>댓글<br>평균').replace('조회 수 평균','조회 수<br>평균').replace('단 댓글 수','단<br>댓글 수')
    aa = '<header><p>'+str(year)+'년 '+str(month)+'월 ' + gallname + '</p><h3>'+col+' 랭킹</h3><golda>■: 1등</golda> <ta style="color:TURQUOISE">■: ~10%</ta> <ta style="color:lawngreen">■: 11%~30%</ta> <ta style="color:yellow">■: 31%~50%</ta> <ta style="color:orange;">■: 51%~70%</ta> <ta style="color:tomato;">■: 71%~100%</ta>'
    # aa = '<header><p>'+str(year)+'년 '+ gallname + '</p><h3>'+col+' 랭킹</h3><golda>■: 1등</golda> <ta style="color:TURQUOISE">■: ~10%</ta> <ta style="color:lawngreen">■: 11%~30%</ta> <ta style="color:yellow">■: 31%~50%</ta> <ta style="color:orange;">■: 51%~70%</ta> <ta style="color:tomato;">■: 71%~100%</ta>'
    if ascending == False:aa = aa+'<h4 style="color: white;">내림차순 <a style="color: rgb(229,21,21);">▼</a></h4></header>'
    else:aa = aa+'<h6 style="color: white;">오름차순 <a style="color: rgb(21, 135, 229);">▲</a></h6></header>'
    return aa+ch
def makerank(col,maxrank,isnotongpi,ascend): #랭킹 생성
    if isnotongpi == True: finaldf = notongpivv;pastfinaldf = notongpipastvv
    else:finaldf = tongpivv;pastfinaldf = tongpipastvv
    checkdf = finaldf.replace('inf%', np.nan).dropna(subset=[col], how="all")
    pastcheckdf = pastfinaldf.replace('inf%', np.nan).dropna(subset=[col], how="all")
    if u' 비' in col or u'비율' in col:acol = col+'1'
    else: acol = col
    check = checkdf.sort_values(acol,ascending=ascend).reset_index(drop=True)
    check.index +=1
    check.loc[:,'index'] = check.index

    pastcheck = pastcheckdf.sort_values(acol,ascending=ascend).reset_index(drop=True)
    pastcheck.index +=1
    pastcheck.loc[:,'index'] = pastcheck.index
    
    checkip = check.loc[check['ID/IP'].str.count('\.')==1].reset_index(drop=True).set_index([u'닉네임','ID/IP'])
    
    pastcheckip = pastcheck.loc[pastcheck['ID/IP'].str.count('\.')==1].reset_index(drop=True).set_index([u'닉네임','ID/IP'])
    checkip.loc[:,'pastindex'] = pastcheckip.loc[:,'index']
    aa = checkip.loc[:,'index'].map(str)+' '+checkip.loc[:,'pastindex'].map(str)
    for i in aa.index.tolist():
        index1 = i[0];index2 = i[1]
        curin = aa[index1][index2].split(' ')[0];pastin = aa[index1][index2].split(' ')[1].replace('.0','')
        if pastin == 'nan':newin = curin+'(N)'
        elif int(pastin) > int(curin):newin = curin+'(▲ '+str(int(pastin)-int(curin))+')'
        elif int(pastin) < int(curin):newin = curin+'(▼ '+str(int(curin)-int(pastin))+')'
        elif int(pastin) == int(curin):newin = curin+'(-)'
        aa[(index1,index2)] = newin
    checkip.loc[:,'lastindex'] = aa
    checkip = checkip.reset_index().set_index([u'닉네임','ID/IP'])
    
    checkid = check.loc[check['ID/IP'].str.count('\.')!=1].reset_index(drop=True).set_index(['ID/IP'])
    pastcheckid = pastcheck.loc[pastcheck['ID/IP'].str.count('\.')!=1].reset_index(drop=True).set_index(['ID/IP'])
    checkid.loc[:,'pastindex'] = pastcheckid.loc[:,'index'].astype(str)
    aa = checkid.loc[:,'index'].map(str)+' '+checkid.loc[:,'pastindex'].map(str)
    for i in aa.index.tolist():
        curin = aa[i].split(' ')[0];pastin = aa[i].split(' ')[1].replace('.0','')
        if pastin == 'nan':newin = curin+'(N)'
        elif int(pastin) > int(curin):newin = curin+'(▲ '+str(int(pastin)-int(curin))+')'
        elif int(pastin) < int(curin):newin = curin+'(▼ '+str(int(curin)-int(pastin))+')'
        elif int(pastin) == int(curin):newin = curin+'(-)'
        aa[i] = newin
    checkid.loc[:,'lastindex'] = aa
    checkid = checkid.reset_index().set_index([u'닉네임','ID/IP'])
    
    cont = pd.concat([checkip,checkid],sort=False)
    dd = cont.reset_index().sort_values('index',ascending=True).set_index('index').rename_axis(None)
    for prefix in [u'글 수',u'조회 수 평균',u'달린 댓글 수 평균',u'글댓 비1',acol]:
        dd[prefix+u'pct'] = dd[prefix].rank(pct=True)
    dd = dd.head(maxrank)
    for i in dd.index:
        nick = dd.loc[i][u'닉네임']
        if '<br>' in nick:nick = nick.split('<br>')[0]
        dd.loc[i,u'단 댓글'] = getcomrank(nick,dd.loc[i]['ID/IP'],idf,cdf)
        dd.loc[i,u'달린 댓글'] = getgotcomrank(nick,dd.loc[i]['ID/IP'],idf,cdf)
        dd.loc[i,u'답글'] = getanswerrank(nick,dd.loc[i]['ID/IP'],idf,cdf)
    dd = dd.reset_index(drop=True).set_index('lastindex').rename_axis(None)
    return dd
idf1 = idf;cdf1 = cdf
idf1.loc[:,u'달린 댓글 수'] = idf1[u'달린 댓글 수'].astype(np.uint32)
idf1.loc[(idf1.loc[:,u'달린 댓글 수']==0),u'무플 수'] = 1
cont = pd.concat([idf1, cdf1],sort=False)
cont.loc[:,u'날짜'] = pd.to_datetime(cont[u'날짜'],format='%Y.%m.%d %H:%M')
cont.loc[cont.loc[:,u'날짜'].dt.dayofweek >= 4, 'holi'] = 1
cont.loc[cont.loc[:,u'날짜'].dt.dayofweek < 4, 'work'] = 1
cdfcount = cdf1.groupby([u'닉네임','ID/IP','idtype'])[u'번호'].count().to_frame(name=u'단 댓글 수').fillna(0).astype(np.uint32)
postc = idf1.groupby([u'닉네임','ID/IP','idtype'])[u'번호'].count().to_frame(name=u'글 수').fillna(0).astype(np.uint32)
for e in [u'달린 댓글 수',u'추천 수',u'조회 수',u'비추 수',u'무플 수','mobile','dccon',u'개념글 수','holi','work']:
    cont.loc[:,e] = cont[e].fillna(0).astype(np.uint32)
oo_id = cont.drop(u'번호',axis=1).groupby([u'닉네임','ID/IP','idtype']).sum()
oo_id = pd.concat([oo_id, cdfcount,postc],axis=1).reset_index()

oo_id.loc[:,u'닉네임'] = '%%'+oo_id.loc[:,'idtype'].astype(str)+'%%'+oo_id.loc[:,u'닉네임']
oo_id=oo_id.reset_index().set_index(['ID/IP'])

indexes = oo_id[(oo_id.index.value_counts()>1)]
indexes = indexes[indexes['idtype']!=3].index
for turn,o in enumerate(indexes):
    nicks = list(set(oo_id.loc[o].reset_index().set_index('닉네임').index))
    oo_id.loc[o,u'닉네임'] = '<br>'.join(nicks)

oo = oo_id.reset_index().groupby(['닉네임','ID/IP']).sum()
for prefix in [u'추천 수',u'비추 수',u'조회 수',u'달린 댓글 수']:
    oo.loc[:,prefix+u' 평균'] = (oo[prefix]/oo[u'글 수']).map('{:.2f}'.format).astype(float)

idf1 = pastidf;cdf1 = pastcdf
idf1.loc[:,u'달린 댓글 수'] = idf1[u'달린 댓글 수'].astype(np.uint32)
idf1.loc[(idf1.loc[:,u'달린 댓글 수']==0),u'무플 수'] = 1
cont = pd.concat([idf1, cdf1],sort=False)
cont.loc[:,u'날짜'] = pd.to_datetime(cont[u'날짜'],format='%Y.%m.%d %H:%M')
cont.loc[cont.loc[:,u'날짜'].dt.dayofweek >= 4, 'holi'] = 1
cont.loc[cont.loc[:,u'날짜'].dt.dayofweek < 4, 'work'] = 1

cdfcount = cdf1.groupby([u'닉네임','ID/IP','idtype'])[u'번호'].count().to_frame(name=u'단 댓글 수').fillna(0).astype(np.uint32)
postc = idf1.groupby([u'닉네임','ID/IP','idtype'])[u'번호'].count().to_frame(name=u'글 수').fillna(0).astype(np.uint32)
for e in [u'달린 댓글 수',u'추천 수',u'조회 수',u'비추 수',u'무플 수','mobile','dccon',u'개념글 수','holi','work']:
    cont.loc[:,e] = cont[e].fillna(0).astype(np.uint32)
oo_id = cont.drop(u'번호',axis=1).groupby([u'닉네임','ID/IP','idtype']).sum()
oo_id = pd.concat([oo_id, cdfcount,postc],axis=1).reset_index()

oo_id.loc[:,u'닉네임'] = '%%'+oo_id.loc[:,'idtype'].astype(str)+'%%'+oo_id.loc[:,u'닉네임']
oo_id=oo_id.reset_index().set_index(['ID/IP'])

indexes = oo_id[(oo_id.index.value_counts()>1)]
indexes = indexes[indexes['idtype']!=3].index
for turn,o in enumerate(indexes):
    nicks = list(set(oo_id.loc[o].reset_index().set_index('닉네임').index))
    oo_id.loc[o,u'닉네임'] = '<br>'.join(nicks)

pastoo = oo_id.reset_index().groupby(['닉네임','ID/IP']).sum()
for prefix in [u'추천 수',u'비추 수',u'조회 수',u'달린 댓글 수']:
    pastoo.loc[:,prefix+u' 평균'] = (oo[prefix]/oo[u'글 수']).map('{:.2f}'.format).astype(float)

postlimit = 1 ; commentlimit = 5 #도배나 철새 거르는용. 갤러리규모에 따라 알아서 설정해준다. 0 0 해도된다.
pastoo = pastoo[(pastoo[u'단 댓글 수'] >= commentlimit)];pastvv = pastoo[(pastoo[u'글 수'] >= postlimit)]
oo = oo[(oo[u'단 댓글 수'] >= commentlimit)];vv = oo[(oo[u'글 수'] >= postlimit)]
vv = vv.reset_index();pastvv = pastvv.reset_index()
vv = vv.set_index([u'닉네임','ID/IP']);pastvv = pastvv.set_index([u'닉네임','ID/IP'])

vv.loc[:,u'글댓 비1'] = (vv[u'단 댓글 수']/vv[u'글 수'])
pastvv.loc[:,u'글댓 비1'] = (pastvv[u'단 댓글 수']/pastvv[u'글 수'])
vv.loc[:,u'글댓 비'] = '1:'+vv[u'글댓 비1'].map('{:.2f}'.format)
pastvv.loc[:,u'글댓 비'] = '1:'+pastvv[u'글댓 비1'].map('{:.2f}'.format)

vv.loc[:,u'글댓 비 (디시콘 제외)1'] = ((vv[u'단 댓글 수']-vv[u'dccon'])/vv[u'글 수'])
pastvv.loc[:,u'글댓 비 (디시콘 제외)1'] = ((pastvv[u'단 댓글 수']-pastvv[u'dccon'])/pastvv[u'글 수'])
vv.loc[:,u'글댓 비 (디시콘 제외)'] = '1:'+vv[u'글댓 비 (디시콘 제외)1'].map('{:.2f}'.format)
pastvv.loc[:,u'글댓 비 (디시콘 제외)'] = '1:'+pastvv[u'글댓 비 (디시콘 제외)1'].map('{:.2f}'.format)

vv.loc[:,u'디시콘 비율1'] = (vv['dccon']/vv[u'단 댓글 수'])
pastvv.loc[:,u'디시콘 비율1'] = (pastvv['dccon']/pastvv[u'단 댓글 수'])
vv.loc[:,u'디시콘 비율'] = vv[u'디시콘 비율1'].map('{:.2%}'.format)
pastvv.loc[:,u'디시콘 비율'] = pastvv[u'디시콘 비율1'].map('{:.2%}'.format)

pastvv.loc[:,u'모바일 비율1'] = (pastvv['mobile']/pastvv[u'글 수'])
pastvv.loc[:,u'모바일 비율'] = pastvv[u'모바일 비율1'].map('{:.2%}'.format)
vv.loc[:,u'모바일 비율1'] = (vv['mobile']/vv[u'글 수'])
vv.loc[:,u'모바일 비율'] = vv[u'모바일 비율1'].map('{:.2%}'.format)

pastvv.loc[:,u'무플 비율1'] = (pastvv[u'무플 수']/pastvv[u'글 수'])
pastvv.loc[:,u'무플 비율'] = pastvv[u'무플 비율1'].map('{:.2%}'.format)
vv.loc[:,u'무플 비율1'] = (vv[u'무플 수']/vv[u'글 수'])
vv.loc[:,u'무플 비율'] = vv[u'무플 비율1'].map('{:.2%}'.format)
pastvv.loc[:,u'평일-주말 비1'] = (pastvv['holi']/pastvv['work']).replace(np.inf,0)
pastvv.loc[:,u'평일-주말 비'] = '1:'+pastvv[u'평일-주말 비1'].map('{:.2f}'.format).replace(np.inf,0)
vv.loc[:,u'평일-주말 비1'] = (vv['holi']/vv['work']).replace(np.inf,0)
vv.loc[:,u'평일-주말 비'] = '1:'+vv[u'평일-주말 비1'].map('{:.2f}'.format).replace(np.inf,0)

for e in ['글 수',u'단 댓글 수',u'달린 댓글 수',u'추천 수',u'조회 수',u'비추 수','mobile','dccon',u'개념글 수',u'무플 수',u'개념글 수']:
    vv.loc[:,e] = vv.loc[:,e].astype(np.uint32)
    pastvv.loc[:,e] = pastvv.loc[:,e].astype(np.uint32)

notongpivv = notongpi(vv)
notongpipastvv = notongpi(pastvv)
tongpivv = tongpi(vv)
tongpipastvv = tongpi(pastvv)
check = makerank('글 수',250,False,False) #글 수 랭킹을 250위까지 생성. 통피포함, 내림차순
ch = make_html(check[['닉네임','ID/IP','글 수','글댓 비','달린 댓글 수 평균','조회 수 평균','단 댓글','달린 댓글','답글']].to_html(escape=False),'글 수',False)
imgkit.from_string(ch, baseloc+'/table/'+'글 수 내림차.jpg',options=options,config=config,css=css) #이미지 생성
wkhtmltopdf_options = {
    'enable-local-file-access': None,
    'javascript-delay': 2000000
}

maxrank = 100 #100위까지 표시
for col in ['조회 수','조회 수 평균','추천 수','추천 수 평균','비추 수','비추 수 평균','달린 댓글 수','달린 댓글 수 평균','무플 비율','단 댓글 수','모바일 비율','글댓 비','글댓 비 (디시콘 제외)','디시콘 비율','평일-주말 비','개념글 수']:
    #내림차순 랭킹 생성
    check = makerank(col,maxrank,True,False)
    if col in ['조회 수 평균','달린 댓글 수 평균','글댓 비']: ch = make_html(check[['닉네임','ID/IP','글 수','글댓 비','달린 댓글 수 평균','조회 수 평균','단 댓글','달린 댓글','답글']].to_html(escape=False),col,False)
    else: ch = make_html(check[['닉네임','ID/IP',col,'글댓 비','달린 댓글 수 평균','조회 수 평균','단 댓글','달린 댓글','답글']].to_html(escape=False),col,False)
    imgkit.from_string(ch, baseloc+'/table/'+col.replace(': ','-')+" 내림차.jpg",options=options,config=config,css=css)
    
    if col in ['조회 수','추천 수','비추 수','단 댓글 수','개념글 수','달린 댓글 수']: continue #오름차순으로 뽑아도 별 의미 없는것들 스킵 
    
    #오름차순 랭킹 생성
    check = makerank(col,maxrank,True,True) 
    if col in ['조회 수 평균','달린 댓글 수 평균','글댓 비']: ch = make_html(check[['닉네임','ID/IP','글 수','글댓 비','달린 댓글 수 평균','조회 수 평균','단 댓글','달린 댓글','답글']].to_html(escape=False),col,True)
    else: ch = make_html(check[['닉네임','ID/IP',col,'글댓 비','달린 댓글 수 평균','조회 수 평균','단 댓글','달린 댓글','답글']].to_html(escape=False),col,True)
    imgkit.from_string(ch, baseloc+'/table/'+col.replace(': ','-')+" 오름차.jpg",options=options,config=config,css=css)
