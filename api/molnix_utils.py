import requests
import json

class MolnixApi:

    access_token = None

    def __init__(self, url='https://api.ifrc-staging.rpm.molnix.com/api/', username=None, password=None):
        if username is None or password is None:
            raise Exception('username or password not supplied')
        self.url = url
        self.username = username
        self.password = password

    def call_api(self, path, method='GET', params={}):
        url = self.url + path
        headers = {}
        if self.access_token:
            headers['Authorization'] = 'Bearer %s' % self.access_token
        if method == 'GET':
            res = requests.get(url, params=params, headers=headers)
        if method == 'POST':
            res = requests.post(url, json=params, headers=headers)
        if res.status_code > 300:
            raise Exception('call to %s failed' % url) #FIXME: print msg from API
        return res.json()

    def call_api_paginated(self, path, response_key=None, params={}):
        page = 1
        next_page = True
        results = []
        while next_page:
            params['page'] = page
            data = self.call_api(path=path, params=params)
            if response_key:
                data = data[response_key]['data']
            results += data
            if len(data) == 0:
                next_page = False
            else:
                page += 1
        return results

    def login(self):
        params = {
            'username': self.username,
            'password': self.password
        }
        response = self.call_api('login', 'POST', params)
        if not 'access_token' in response.keys():
            raise Exception('unexpected response to login')
        self.access_token = response['access_token']
        return True

    def get_tags(self):
        return self.call_api(path='tags')['tags']

    def get_tag_groups(self, id):
        return self.call_api(path='tags/edit/%d' % id)['tag']['groups']

    def get_open_positions(self):
        #return self.call_api_paginated(path='positions', response_key='positions')
        return self.call_api(path='positions/open')

    def get_deployments(self):
        deployments_filter = {
            "persontags":[],
            "personoperator":"",
            "deploymenttags":[],
            "deploymentoperator":"",
            "orderBy":"ID",
            "orderType":"DESC",
            "userroles":[],
            "criterias":"[]"
        }
        params = {
            'filter': json.dumps(deployments_filter)
        }
        return self.call_api_paginated(path='deployments', response_key='deployments', params=params)

    '''
        WARNING: If position is not found or generates an error, we return None
    '''
    def get_position(self, id):
        try:
            return self.call_api(path='positions/%d' % id)
        except:
            return None

    def get_countries(self):
        countries = self.call_api(path='countries')
        countries_list = countries['countries']
        countries_dict = {}
        for country in countries_list:
            countries_dict[country['id']] = country['code']
        return countries_dict

    def logout(self):
        self.call_api('logout')
        return True