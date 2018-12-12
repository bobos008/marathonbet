# coding=utf-8

import requests
import json
import time
import re
from bs4 import BeautifulSoup

_PATH_COOKIE = './cookies/marathonbet'
_COOKIE = ''

class Marathonbet:

    def __init__(self, username=None, password=None):
        self._username = username
        self._password = password

    def get_all_live_football_match_url(self):
        '''
        获取所有足球直播url
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/live/popular.htm'
        other_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'upgrade-insecure-requests': '1',
        }
        
        if _COOKIE:
            cookies = _COOKIE
        else:
            cookies = ''
        headers = self.make_headers(other_headers)
        response = self.is_success_request('get', url, headers, cookies=cookies)
        if response:
            html_str = response.content
            if html_str:
                pattern = ' reactData = (.*?)//]]>>'
                header_data_str_obj = re.search(pattern, html_str, re.S)
                if header_data_str_obj:
                    try:
                        react_data_str = header_data_str_obj.group(1).replace(';\n', '')
                        react_data = json.loads(react_data_str)
                        live_url_list = []
                        for react in react_data['liveMenuEvents']['childs']:
                            if react['label'] == 'Football':
                                childs = react['childs']
                                for child in childs:
                                    child_data = child['childs']
                                    for cd in child_data:
                                        one_bet = {}
                                        one_bet['label'] = cd['label']
                                        one_bet['href'] = cd['href']
                                        live_url_list.append(one_bet)
                        return live_url_list
                    except Exception as err:
                        print 'get_live_football_match_url:', err
                        return ''
        return ''

    def get_all_data(self):
        '''
        获取所有的盘口的数据
        '''
        global _COOKIE
        if not _COOKIE:
            _COOKIE = self.get_login_cookie()
        all_live_url_list = self.get_all_live_football_match_url()
        for alul in all_live_url_list:
            print alul
            one_match_data = self.get_one_match_handicap_data(alul.get('href', ''))
            alul['one_match_data'] = one_match_data
        print all_live_url_list 

    def get_one_match_handicap_data(self, live_url):
        '''
        获取一场比赛所有的盘口数据
        '''
        global _COOKIE
        if not live_url:
            return ''
        init_url = 'https://www.marathonbet.com'
        url = init_url + live_url
        other_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'referer': url,
            'upgrade-insecure-requests': '1',
        }
        headers = self.make_headers(other_headers)
        response = self.is_success_request('get', url, headers=headers, cookies=_COOKIE)
        html = response.content
        match_info = {}
        soup = BeautifulSoup(html, 'lxml')
        # 获取联赛的名称
        leagues = soup.select('h2[class="category-label"] > span')
        league_name = ''
        for league in leagues:
            league_name += league.string
        match_info['league'] = league_name
        # 获取队伍名称
        teams = soup.select('div[class="live-today-member-name nowrap "] > span')
        if teams:
            home = teams[0].string
            away = teams[1].string
        else:
            return ''
        match_info['home'] = home
        match_info['away'] = away        
        # 获取当前比分
        current_scores = soup.select('div[class="cl-left red"]')
        if current_scores:
            score_time_str = str(current_scores[0])
        else:
            return ''
        pattern_score = '\n  (.+?)   '
        current_score= re.findall(pattern_score, score_time_str)[0]
        match_info['current_score'] = current_score
        # 获取比赛时间
        pattern_time = '\n  (.+?)\n  '
        current_time = re.findall(pattern_time, score_time_str)[0]
        match_info['current_time'] = current_time
        # 获取所有的盘口的数据
        data_pattern = r'<td.*class="price height-column-with-price.*data-sel=(.+).*>?'
        handicap_data_list = re.findall(data_pattern, html, re.M)
        dsk_pattern = r'data-selection-key="(.+?)"'
        data_selection_key_list = re.findall(dsk_pattern, html, re.M)
        handicap_len = len(handicap_data_list)
        if len(data_selection_key_list) != handicap_len:
            return ''
        handicap_list = []
        try:
            for i in range(handicap_len):
                data_selection_key = data_selection_key_list[i]
                home_away = home + 'vs' + away
                mid = data_selection_key.split('@')[0]
                new_data_selection_key = data_selection_key.replace('@', ',')
                handicap_data = handicap_data_list[i]
                new_handicap_data = handicap_data[1:len(handicap_data)-1]
                new_handicap_data = json.loads(new_handicap_data)
                new_handicap_data['mid'] = mid
                new_handicap_data['u'] = new_data_selection_key
                new_handicap_data['en'] = home_away
                new_handicap_data['l'] = 'true'
                handicap_list.append(new_handicap_data)
            print len(handicap_list)
        except Exception as err:
            print err
            return ''
        match_info['handicap_list'] = handicap_list
        return match_info

    def is_success_request(self, methods, url, headers, cookies=None, formData=None, params=None):
        '''
        methods: 请求是get，post方法，值：post, get
        url: 请求的路径 
        headers: 请求头信息
        cookies: 请求的cookie
        formData: post请求要传的值,以字典的形式进行传值
        params: get请求要带的参数，以字典的形式进行传值
        '''
        try:
            if methods == 'get':
                response = requests.get(url, params=params, headers=headers, cookies=cookies)
            else:
                response = requests.post(url, data=formData, headers=headers, cookies=cookies)
            return response
        except Exception as err:
            print 'is_success_request:', err
            return ''

    def make_headers(self, other_headers):
        '''
        制作头信息
        '''
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'origin': 'https://www.marathonbet.com',            
        }
        if other_headers:
            headers = dict(headers, **other_headers)
        return headers

    '''
    投注
    '''
    def addBet(self, referer, ch):
        '''
        打开付钱页面 
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/betslip/add2.htm'
        other_headers = {
            'accept': 'text/plain, */*; q=0.01',
            # 'content-length': '640',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': referer,
            'x-requested-with': 'XMLHttpRequest',            
        }
        headers = self.make_headers(other_headers)
        formData = {
            'ch': ch,
            'url': referer,
            'ws': 'true'
        }
        cookies = _COOKIE 
        response = self.is_success_request('post', url, headers, formData=formData, cookies=cookies)

    def updateChoice(self, referer, u): 
        '''
        刷新赔率
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/betslip/updatechoices2.htm'
        other_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            # 'content-length': '54',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'referer': referer,
            'x-requested-with': 'XMLHttpRequest'            
        }
        headers = self.make_headers(other_headers)
        formData = {
            # 'selectionsJSON': '["6349525,Match_Result.draw"]'
            'selectionsJSON': '["%s"]'%u
        }
        response = self.is_success_request('post', url, headers=headers, formData=formData) 
        return response.content

    def saveUpdate(self, referer):
        '''
        保留更新
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/betslip/applyactualchoices2.htm'
        other_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-length': '0',
            'referer': referer,
            'x-requested-with': 'XMLHttpRequest'
        }
        headers = self.make_headers(other_headers)
        response = self.is_success_request('post', url, headers=headers, cookies=_COOKIE)

    def placeBet(self, referer, u, stake):
        '''
        付钱
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/betslip/placebet2.htm'
        other_headers = {
            'accept': 'text/plain, */*; q=0.01',
            # 'content-length': '134',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': referer,
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',            
        }
        headers = self.make_headers(other_headers)
        formData = {
            'schd': 'false',
            'p': 'SINGLES',
            # 'b': '[{"url":"6571103,Match_Result.1","stake":%s,"vip":false,"ew":false}]'%stake
            'b': '[{"url":"%s","stake":%s,"vip":false,"ew":false}]'%(u, stake)            
        }
        response = self.is_success_request('post', url, headers=headers, formData=formData, cookies=_COOKIE)

    def placeTicket(self, referer, ticketId):
        '''
        投注结果
        '''
        global _COOKIE
        url = 'https://www.marathonbet.com/en/betslip/placeticket2.htm'
        other_headers = {
            'accept': 'text/plain, */*; q=0.01',
            # 'content-length': '38',
            'content-type': 'application/x-www-form-urlencoded',
            'referer': referer, 
            'x-requested-with': 'XMLHttpRequest',            
        }
        headers = self.make_headers(other_headers)
        formData = {
            't', ticketId
        }
        while True:
            response = self.is_success_request('post', url, headers=headers, formData=formData, cookies=_COOKIE)
            res_json = response.content
            try:
                res = json.loads(res_json)
                if len(res['message']) > 0:
                    print res['message'][0]
                    print res_json
                    break
            except Exception as err:
                print err
            time.sleep(12)


    '''
    用户登录
    '''
    def get_start_cookie(self):
        '''
        获取起始cookie
        '''
        url = 'https://www.marathonbet.com/en/live/popular'
        other_headers = {
            'upgrade-insecure-requests': '1'
        }
        headers = self.make_headers(other_headers)
        response = self.is_success_request('get', url, headers)
        if response:
            cookies = dict(response.cookies)
            return cookies
        else:
            return ''

    def get_login_cookie(self):
        '''
        获取登录的cookie
        '''
        try:
            with open(_PATH_COOKIE, 'r') as f:
                login_cookie_str = f.read()
        except Exception as err:
            print 'get_login_cookie:', err
            return self.login()

        if login_cookie_str:
            login_cookie = json.loads(login_cookie_str)
            if self.is_login(login_cookie):
                return login_cookie
            else:
                return self.login()
        else:
            return self.login()

    def login(self):
        '''
        登录生成cookie
        '''
        url = 'https://www.marathonbet.com/en/login.htm'
        other_headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-length': '110',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'referer': 'https://www.marathonbet.com/zh/live/popular',
            'x-requested-with': 'XMLHttpRequest'
        }
        headers = self.make_headers(other_headers)
        formData = {
            'login': self._username,
            'login_password': self._password,
            'loginUrl': 'https://www.marathonbet.com:443/en/login.htm'
        }
        start_cookie = self.get_start_cookie()
        if not start_cookie:
            return ''
        response = self.is_success_request('post', url, headers, cookies=start_cookie, formData=formData)
        if response:
            login_cookie = dict(response.cookies)
            login_cookie_str = json.dumps(login_cookie)
            try:
                with open(_PATH_COOKIE, 'w') as f:
                    f.write(login_cookie_str)
            except Exception as err:
                return ''
            return login_cookie
        else:
            return ''

    def is_login(self, login_cookie):
        '''
        判断用户是否登录成功
        '''
        url = 'https://www.marathonbet.com/en/live/popular'
        other_headers = {
            'upgrade-insecure-requests': '1'
        }
        headers = self.make_headers(other_headers)
        response = self.is_success_request('get', url, headers, cookies=login_cookie)
        if response:
            html_str = response.content
            soup = BeautifulSoup(html_str, 'lxml')
            name_list = soup.select('div[class="auth"]')
            if name_list:
                name = name_list[0].string
                print name
                if name:
                    return True
        return False

if __name__ == '__main__':
    username = ''
    password = ''
    mb = Marathonbet(username, password)
    # mb.get_login_cookie()
    mb.get_all_live_football_match_url()
    url = '/en/live/7279406'
    print json.dumps(mb.get_one_match_handicap_data(url))
    # mb.get_all_data()
