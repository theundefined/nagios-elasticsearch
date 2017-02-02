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


class ESSplitBrainCheck(NagiosCheck):

    def __init__(self):

        NagiosCheck.__init__(self)

        self.add_option('N', 'nodes', 'nodes', 'Cluster nodes')
        self.add_option('P', 'port', 'port', 'The ES port - defaults to 9200')
        self.add_option('u', 'username', 'username', 'username to login into ES port')
        self.add_option('p', 'password', 'password', 'password to login into ES port')

    def check(self, opts, args):
        nodes = opts.nodes.split(",")
        port = int(opts.port or '9200')
        username = opts.username
        password = opts.password

        masters = []
        responding_nodes = []
        failed_nodes = []

        for node in nodes:
            try:
                url=urllib2.Request(r'http://%s:%d/_cluster/state/nodes,master_node/' % (node, port))
                if username and password:
                   base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
                   url.add_header("Authorization","Basic %s" % base64string)
                response = urllib2.urlopen(url)

                response_body = response.read()
                response = json.loads(response_body)
            except (urllib2.HTTPError, urllib2.URLError), e:
                failed_nodes.append("%s - %s" % (node, e.reason))
                continue

            if type(response) is dict:
                cluster_name = str(response['cluster_name'])
                master = str(
                        response['nodes'][response['master_node']]['name']
                        )
                responding_nodes.append(node)
                if master not in masters:
                    masters.append(master)

        if len(responding_nodes) == 0:
            raise Status('Unknown',
                        "All cluster nodes unresponsive:\r\n"
                        "%s" % (str("\r\n".join(failed_nodes))))
        elif len(masters) != 1:
            raise Status('Critical', "%d masters (%s) found in %s cluster"
                         % (len(masters),
                            str(", ".join(masters)), cluster_name
                            )
                         )
        else:
            if len(failed_nodes) == 0:
                raise Status('OK', "%d/%d nodes have same master"
                            % (len(responding_nodes), len(nodes)))
            else:
                raise Status('OK', "%d/%d nodes have same master\r\n"
                            "%d unresponsive nodes:\r\n%s"
                            % (len(responding_nodes),
                                len(nodes),
                                len(failed_nodes),
                                str("\r\n".join(failed_nodes))))

if __name__ == "__main__":
    ESSplitBrainCheck().run()
