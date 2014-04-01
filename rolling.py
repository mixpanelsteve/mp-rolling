#! /usr/bin/env python
#
# Mixpanel, Inc. -- http://mixpanel.com/
#
# Python API client library to consume mixpanel.com analytics data.
#
# Copyright 2010-2013 Mixpanel, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import hashlib
import urllib
import time
try:
    import json
except ImportError:
    import simplejson as json

class Mixpanel(object):

    ENDPOINT = 'http://mixpanel.com/api'
    VERSION = '2.0'

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, methods, params, format='json'):
        """
            methods - List of methods to be joined, e.g. ['events', 'properties', 'values']
                      will give us http://mixpanel.com/api/2.0/events/properties/values/
            params - Extra parameters associated with method
        """
        params['api_key'] = self.api_key
        params['expire'] = int(time.time()) + 600   # Grant this request 10 minutes.
        params['format'] = format
        if 'sig' in params: del params['sig']
        params['sig'] = self.hash_args(params)

        request_url = '/'.join([self.ENDPOINT, str(self.VERSION)] + methods) + '/?' + self.unicode_urlencode(params)
        print request_url
        request = urllib.urlopen(request_url)
        data = request.read()

        return json.loads(data)

    def unicode_urlencode(self, params):
        """
            Convert lists to JSON encoded strings, and correctly handle any
            unicode URL parameters.
        """
        if isinstance(params, dict):
            params = params.items()
        for i, param in enumerate(params):
            if isinstance(param[1], list):
                params[i] = (param[0], json.dumps(param[1]),)

        return urllib.urlencode(
            [(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params]
        )

    def hash_args(self, args, secret=None):
        """
            Hashes arguments by joining key=value pairs, appending a secret, and
            then taking the MD5 hex digest.
        """
        for a in args:
            if isinstance(args[a], list): args[a] = json.dumps(args[a])

        args_joined = ''
        for a in sorted(args.keys()):
            if isinstance(a, unicode):
                args_joined += a.encode('utf-8')
            else:
                args_joined += str(a)

            args_joined += '='

            if isinstance(args[a], unicode):
                args_joined += args[a].encode('utf-8')
            else:
                args_joined += str(args[a])

        hash = hashlib.md5(args_joined)

        if secret:
            hash.update(secret)
        elif self.api_secret:
            hash.update(self.api_secret)
        return hash.hexdigest()

if __name__ == '__main__':
    api = Mixpanel(
        api_key = 'API_KEY',
        api_secret = 'SECRET'
    )

    retention_types = [2,7,30]
    retention_returns = {
            'cohorts' : }
    beginning = datetime.date(2014, 03, 15)
    today = datetime.date.today()

    #get the cohorts a.k.a. people who have started games with a certain Created/Signed Up date
    for day in range((today - beginning).days):
        cohort_date = beginning + datetime.timedelta(day)
        lifetime_interval = (today - cohort_date).days + 1
        cohort = api.request(['segmentation'], {
            'event' : 'Game Started',
            #'unit' : 'day',
            'from_date' : cohort_date,
            'to_date' : today,
            'interval' : lifetime_interval, #this is only here because users weren't tagged with Signed Up when they first played games :(
            'type' : 'unique',
            'where' : '"%s" in string(properties["Signup date"]) or "%s" in string(properties["U:Created"])' % (cohort_date.isoformat(), cohort_date.isoformat())
        })
        print cohort['data']['values']['Game Started'][cohort_date.isoformat()]
        retention_returns['cohorts'][cohort_date.isoformat()] = cohort['data']['values']['Game Started'][cohort_date.isoformat()]

    for type in retention_types:
        for day in range((today - beginning).days - type): #for each type this needs to change to make sure we're giving everyone the same time
            cohort_date = beginning + datetime.timedelta(day)
            retention_start = cohort_date + datetime.timedelta(type)
            lifetime_interval = (today - cohort_date).days + 1
            retention_interval = (today - retention_start).days + 1

            #find out how many have come back after (type) days
            churn = api.request(['segmentation'], {
                'event' : 'Game Started',
                #'unit' : 'day',
                'from_date' : retention_start.isoformat(),
                'to_date' : today,
                'interval' : retention_interval,
                'type' : 'unique',
                'where' : '"%s" in string(properties["Signup date"])' % cohort_date.isoformat()
            })
            print churn
            try:
                cohort_size = cohort['data']['values']['Game Started'][cohort_date.isoformat()]
                churn_size = cohort_size - churn['data']['values']['Game Started'][retention_start.isoformat()]
                if cohort_size != 0:
                    print float(churn_size) / cohort_size
            except KeyError:
                print "ouch"
