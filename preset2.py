import pandas as pd
import numpy as np
import os
gall = 'weatherbaby' #갤러리 id
for year in range(2018,2021+1): #2018~2019년 폴더 생성
    for month in range(1,12+1): #1~12월 폴더 생성
        baseloc = 'D:/DC' + '/%s/%s/%s/' % (gall,year,month) # 경로
        if not os.path.exists(baseloc+'table'): os.makedirs(baseloc+'table')
        if not os.path.exists(baseloc+'word'):os.makedirs(baseloc+'word') #table, word 폴더는 다른 통계 코드용
        pd.DataFrame(columns=['번호','제목','날짜','닉네임','ID/IP','조회 수','달린 댓글 수','추천 수','비추 수','content','mobile','개념글 수','idtype']).to_json(baseloc+'post.json')
        pd.DataFrame(columns=['번호','날짜','닉네임','ID/IP','dccon','content','idtype','답글 대상','댓삭 당한 횟수']).to_json(baseloc+'comment.json')