#!/usr/bin/python
from nagioscheck import NagiosCheck, UsageError
from nagioscheck import PerformanceMetric, Status
import urllib2
import optparse
import base64

try:
    import json
except ImportError:
    import simplejson as json


class ESShardsCheck(NagiosCheck):

    def __init__(self):

        NagiosCheck.__init__(self)

        self.add_option('H', 'host', 'host', 'The cluster to check')
        self.add_option('P', 'port', 'port', 'The ES port - defaults to 9200')
        self.add_option('u', 'username', 'username', 'username to login into ES port')
        self.add_option('p', 'password', 'password', 'password to login into ES port')

    def check(self, opts, args):
        host = opts.host
        port = int(opts.port or '9200')
        username = opts.username
        password = opts.password

        try:
            url=urllib2.Request(r'http://%s:%d/_cluster/health' % (host, port))
            if username and password:
                base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
                url.add_header("Authorization","Basic %s" % base64string)
            response = urllib2.urlopen(url)

        except urllib2.HTTPError, e:
            raise Status('unknown', ("API failure", None,
                         "API failure:\n\n%s" % str(e)))
        except urllib2.URLError, e:
            raise Status('critical', (e.reason))

        response_body = response.read()

        try:
            es_cluster_health = json.loads(response_body)
        except ValueError:
            raise Status('unknown', ("API returned nonsense",))

        unassigned_shards = es_cluster_health['unassigned_shards']

        if unassigned_shards != 0:
            raise Status('CRITICAL',
                         "There are '%s' unassigned shards in the cluster"
                         % (unassigned_shards))
        else:
            raise Status('OK',
                         "All shards in the cluster are currently assigned")


if __name__ == "__main__":
    ESShardsCheck().run()
