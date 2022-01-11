import pandas as pd
import numpy as np
import sys,re,collections,imgkit
from IPython.core.display import display, HTML
from bs4 import BeautifulSoup
pd.set_option('display.max_columns', -1);pd.set_option('display.max_rows', -1);pd.set_option('display.max_colwidth', -1)
options = {
    'format': 'jpg',
    'encoding': "UTF-8",
    'quality' : '70'
}
config = imgkit.config(wkhtmltoimage=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe')
css=r'D:\DC\css.css'

gall = 'weatherbaby'; gallname = '날갤'
year=2021;month = 8
period=30
baseloc = 'D:/DC' + '/%s/%s/%s/' % (gall,year,month)
idf = pd.read_json(baseloc+'post.json')[['닉네임','ID/IP','idtype','날짜']];cdf = pd.read_json(baseloc+'comment.json')[['닉네임','ID/IP','idtype','날짜']]
cont = pd.concat([idf, cdf],sort=False)
cont[u'날짜'] = pd.to_datetime(cont[u'날짜'],format='%Y.%m.%d %H:%M:%S')
cont['idtype'] = cont['idtype'].astype(np.uint8)
kt = ['39.7','110.70','175.223','175.252','211.246','210.125']
skt = ['203.226','211.234','115.161','121.190','122.202','122.32','175.202','223.32','223.33','223.62','223.38','223.39','223.57']
lgu = ['61.43','211.234','114.200','117.111','211.36','106.102','125.188']
cont = cont[~cont['ID/IP'].isin(kt+skt+lgu)]
groupby = cont.groupby(['닉네임','ID/IP','idtype']).count()
#groupby = groupby[groupby[u'날짜'] > 500]
#갤러리에 유저가 너무 많을경우, 처리시간을 줄이기위해
#글,댓글 포함 500개 이상 작성한 사람만을 뽑아내는 방법등을 사용하자.
groupby = groupby.sort_values(u'날짜',ascending=False).reset_index().set_index('ID/IP')
groupby = groupby[groupby['닉네임']!='']
groupby.loc[:,u'닉네임'] = '%%'+groupby.loc[:,'idtype'].astype(str)+'%%'+groupby.loc[:,u'닉네임']
groupby = groupby.reset_index().set_index([u'닉네임','ID/IP','idtype'])
groupby=groupby.reset_index().set_index(['ID/IP'])

indexes = groupby[(groupby.index.value_counts()>1)]
indexes = list(set(indexes[indexes['idtype']!=3].index))
for o in indexes:
    nicks = list(set(groupby.loc[o].reset_index().set_index('닉네임').index))
    groupby.loc[o,u'닉네임'] = '<br>'.join(nicks)
    
groupby = groupby.reset_index().groupby([u'닉네임','ID/IP']).sum().sort_values(u'날짜',ascending=False)#.head(500)
#여기서도 끝에 head(500) 등을 사용함으로써 기록이 가장 많은 500명 만을 처리할 수도있다.
print(len(groupby.index)) #유저 수 출력
for en,o in enumerate(groupby.index):
    nick = ([i[5:] for i in (o[0].split('<br>'))]);id = o[1]
    acont = cont[(cont[u'닉네임'].isin(nick)) & (cont['ID/IP'] == id)].drop_duplicates(u'날짜')
    
    holicont = acont[(acont[u'날짜'].dt.dayofweek == 6)|(acont[u'날짜'].dt.dayofweek == 5)].sort_values(u'날짜',ascending=False)
    workcont = acont[(acont[u'날짜'].dt.dayofweek != 6)&(acont[u'날짜'].dt.dayofweek != 5)].sort_values(u'날짜',ascending=False)
    work=0
    if len(workcont)<=1:groupby.loc[o,u'평일 플탐'] = 0;groupby.loc[o,u'평일 플탐1'] = 0;groupby.loc[o,u'평일 플탐 평균'] = 0;groupby.loc[o,u'평일 플탐 평균1'] = 0
    else:
        last = (workcont.iloc[0][u'날짜'] - workcont.iloc[1][u'날짜']).total_seconds()
        for i in range(1,len(workcont)-1):
            check = (workcont.iloc[i][u'날짜'] - workcont.iloc[i+1][u'날짜']).total_seconds()
            if check > period*60 or check < 0:pass
            else: work += check  # n초 추가
            last = check
        groupby.loc[o,u'평일 플탐'] = '{0:.2f} 시간'.format(work/3600)
        groupby.loc[o,u'평일 플탐1'] = (work/3600)
        groupby.loc[o,u'평일 플탐 평균'] = '{0:.2f} 시간'.format(work/3600/len(workcont[u'날짜'].dt.date.value_counts().index))
        groupby.loc[o,u'평일 플탐 평균1'] = (work/3600/len(workcont[u'날짜'].dt.date.value_counts().index))

    holi = 0
    if len(holicont)<=1:groupby.loc[o,u'주말 플탐'] = 1;groupby.loc[o,u'주말 플탐1'] = 0;groupby.loc[o,u'주말 플탐 평균'] = 0;groupby.loc[o,u'주말 플탐 평균1'] = 0
    else:
        last = (holicont.iloc[0][u'날짜'] - holicont.iloc[1][u'날짜']).total_seconds()
        for i in range(0,len(holicont)-1):
            check = (holicont.iloc[i][u'날짜'] - holicont.iloc[i+1][u'날짜']).total_seconds()
            if check > period*60 or check < 0: pass
            else: holi += check  # n초 추가
            last = check
        groupby.loc[o,u'주말 플탐'] = '{0:.2f} 시간'.format(holi/3600)
        groupby.loc[o,u'주말 플탐1'] = (holi/3600)
        groupby.loc[o,u'주말 플탐 평균'] = '{0:.2f} 시간'.format(holi/3600/len(holicont[u'날짜'].dt.date.value_counts().index))
        groupby.loc[o,u'주말 플탐 평균1'] = (holi/3600/len(holicont[u'날짜'].dt.date.value_counts().index))

    
    days = acont[u'날짜'].dt.hour.value_counts()

    groupby.loc[o,u'주요 활동 시간대'] = ' '.join(days.head(5).sort_index().index.astype(str).tolist())
    groupby.loc[o,u'전체 플탐'] = '{0:.2f} 시간'.format((work+holi)/3600)
    groupby.loc[o,u'전체 플탐1'] = ((work+holi)/3600)
    groupby.loc[o,u'전체 플탐 평균'] = '{0:.2f} 시간'.format((work+holi)/3600/len(acont[u'날짜'].dt.date.value_counts().index))
    groupby.loc[o,u'전체 플탐 평균1'] = ((work+holi)/3600/len(acont[u'날짜'].dt.date.value_counts().index))
    #print (nick,id,'{0:.2f} 시간'.format((work+holi)/3600),'{0:.2f} 시간'.format((work+holi)/3600/(len(acont[u'날짜'].dt.date.value_counts().index))))
    print('%s'%(en+1),end=' ')
def make_html(ch,col,ascending):
    html = BeautifulSoup(ch,'lxml')
    table = html.find('table')
    table['style'] = u'font-family:맑은 고딕;border-collapse:collapse;border: 1px solid transparent'
    thead = html.find('thead')
    for i, th in enumerate(thead.find_all('th')):
        i=i+1
        th['style'] = 'font-weight:bolder;border-top: 3px solid rgb(121, 121, 121);border-bottom: 3px solid rgb(121, 121, 121);font-size:13pt;color:white;background-color: rgb(23, 23, 23);'
        if i == 1:
            th['style'] =  th['style']+'''width: 33px;border-right: 1px solid rgb(121, 121, 121);border-left: 3px solid rgb(121, 121, 121); '''
        elif i == 2:#닉
            th['style'] =  th['style']+'''width: 100px; '''
        elif i == 3:#ID
            th['style'] =  th['style']+'''width: 120px; border-right: 1px solid rgb(121, 121, 121);'''
        elif i == 4:#전체플탐
            th['style'] = th['style']+ '''width: 110px;border-right: 1px solid rgb(121, 121, 121);'''
        elif i == 8:#전체플탐
            th['style'] =  th['style']+ ''' border-right: 3px solid rgb(121, 121, 121);width: 150px;'''  
        else:
            th['style'] =  th['style']+ '''border-right: 1px solid rgb(121, 121, 121);width: 90px;'''
    tbody = html.find('tbody')
    for i, th in enumerate(tbody.find_all('th')):
        i=i+1
        if i==1:
            temp = th.text
            th.clear()
            h1= html.new_tag("h1")
            th.append(h1)
            th.h1.string = temp
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);text-align: center; background-color: rgb(53, 53, 53); border-bottom:1px solid rgb(121, 121, 121);border-left: 3px solid rgb(121, 121, 121); '
        elif len(tbody.find_all('th'))==i:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt;text-align: center; background-color: rgb(43, 43, 43); border-left: 3px solid rgb(121, 121, 121);border-bottom: 3px solid rgb(121, 121, 121);'
        elif i%2==0:
            th['style'] = '''
            border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt;text-align: center; background-color: rgb(43, 43, 43); border-left: 3px solid rgb(121, 121, 121);
            border-bottom: 1px solid rgb(121, 121, 121);'''
        elif i%2==1:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt;text-align: center; background-color: rgb(53, 53, 53); border-left: 3px solid rgb(121, 121, 121);border-bottom: 1px solid rgb(121, 121, 121);'
        else:
            th['style'] = 'border-right: 1px solid rgb(121, 121, 121);color:white;font-size: 12pt;text-align: center; background-color: rgb(43, 43, 43);  border-left: 3px solid rgb(121, 121, 121);border-bottom: 1px solid rgb(121, 121, 121);'
    trs = tbody.find_all('tr')
    for tri, tr in enumerate(trs):
        for i, td in enumerate(tr.find_all('td')):
            i=i+1
            backcolor='rgb(53, 53, 53)' if tri%2==0 else 'rgb(43, 43, 43)'
            bottom='1' if tri+1!=len(trs) else '3'
            if i == 1:#닉
                if check.iloc[tri][u'전체 플탐1pct']==1:
                    for br in td.find_all("br"):br.replace_with("\n")
                    temp = td.text;td.clear();
                    for nick in temp.split('\n'):
                        idtype = int(nick[2])
                        if idtype == 1:
                            h1= html.new_tag("h1");img= html.new_tag("img",src='file:///D:/DC/g_fix.gif');td.append(h1);
                            h1.string=nick[5:]+' ';h1.append(img)
                        elif idtype == 2:
                            h1= html.new_tag("h1");img= html.new_tag("img",src='file:///D:/DC/g_default.gif');td.append(h1);
                            h1.string=nick[5:]+' ';h1.append(img)
                        else:
                            h1= html.new_tag("h1");td.append(h1);h1.string=nick[5:]+' ';
                else:
                    for br in td.find_all("br"):br.replace_with("\n")
                    temp = td.text;td.clear();
                    for nick in temp.split('\n'):
                        idtype = int(nick[2])
                        if idtype == 1:
                            h2= html.new_tag("h2");img= html.new_tag("img",src='file:///D:/DC/g_fix.gif');td.append(h2);
                            h2.string=nick[5:]+' ';h2.append(img)
                        elif idtype == 2:
                            h2= html.new_tag("h2");img= html.new_tag("img",src='file:///D:/DC/g_default.gif');td.append(h2);
                            h2.string=nick[5:]+' ';h2.append(img)
                        else:
                            h1= html.new_tag("h2");td.append(h1);h1.string=nick[5:]+' ';
                td['style'] = u'<color:violet;font-size: 13pt; background-color:'+backcolor+'; border-bottom:'+bottom+'px solid rgb(121, 121, 121);'
            elif i == 2:#아이디
                if check.iloc[tri][u'전체 플탐1pct']==1:
                    temp = td.text;td.clear();h1= html.new_tag("h1");td.append(h1);td.h1.string = temp
                td['style'] = 'color:white;border-right: 1px solid rgb(121, 121, 121);background-color:'+backcolor+'; border-bottom:'+bottom+'px solid rgb(121, 121, 121);'
            elif len(tr.find_all('td'))==i:
                td['style'] = 'border-right: 3px solid rgb(121, 121, 121);color:white;font-size:14pt; background-color:'+backcolor+';border-bottom: '+bottom+'px solid rgb(121, 121, 121);border-left: 1px solid rgb(121, 121, 121);'
            elif i == 3:#col
                td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ;border-left: 1px solid rgb(121, 121, 121);  border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                pct = check.iloc[tri][u'전체 플탐1pct']
                if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp
                

            elif i == 4:#col
                td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ;border-left: 1px solid rgb(121, 121, 121);  border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                pct = check.iloc[tri][u'전체 플탐 평균1pct']
                if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp
            elif i == 5:#col
                td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ;border-left: 1px solid rgb(121, 121, 121);  border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                pct = check.iloc[tri][u'평일 플탐 평균1pct']
                if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp
            elif i == 6:#col
                td['style'] = 'font-weight:bold;font-size: 13pt; background-color:'+backcolor+' ;border-left: 1px solid rgb(121, 121, 121);  border-right: 1px solid rgb(121, 121, 121); border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
                pct = check.iloc[tri][u'주말 플탐 평균1pct']
                if pct < 0.3:td['style'] = td['style']+'color:tomato;'
                elif pct < 0.5:td['style'] = td['style']+'color:orange;'
                elif pct < 0.7:td['style'] = td['style']+'color:yellow;'
                elif pct < 0.9:td['style'] = td['style']+'color:lawngreen;'
                elif pct < 1:td['style'] = td['style']+'color:TURQUOISE;'
                elif pct == 1:temp = td.text;td.clear();h1= html.new_tag("smallh1");td.append(h1);td.smallh1.string = temp
            else:
                td['style'] = 'font-weight:bold;color:lightgray;font-size: 13pt; background-color:'+backcolor+' ;border-bottom: '+bottom+'px solid rgb(121, 121, 121);'
    ch = str(html)
    aa = '<header><p>%s년 %s월 %s</p><h3>%s 랭킹</h3><br>' % (year,month,gallname,col)
    ch = aa+ch
    return ch
check=groupby.reset_index()
check = check.sort_values(u'전체 플탐1',ascending=False).reset_index().head(100)
check.index+=1
for prefix in ['전체 플탐1','전체 플탐 평균1','평일 플탐 평균1','주말 플탐 평균1',]: check[prefix+u'pct'] = check[prefix].rank(pct=True)
ch = make_html(check[['닉네임',u'ID/IP',u'전체 플탐','전체 플탐 평균',u'평일 플탐 평균','주말 플탐 평균','주요 활동 시간대']].to_html(escape=False),'플탐',False)
imgkit.from_string(ch, baseloc+'/table/'+'플탐 랭킹.jpg',options=options,config=config,css=css)