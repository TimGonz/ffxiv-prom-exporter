from prometheus_client import MetricsHandler
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import prometheus_client
import requests
import re
from http.server import HTTPServer

parms = {"key": "b79c94f18ddc49af8eb9043c"}
baseUrl = "https://xivapi.com"

item_id_lookup = {}
with open("item_id_mapping.csv") as f:
    for line in f:
        (key, val) = line.split(",", 1)
        item_id_lookup[key] = val


class CustomMetricsHandler(MetricsHandler):
    def do_GET(self):
        self.registry = REGISTRY
        params = prometheus_client.exposition.parse_qs(prometheus_client.exposition.urlparse(self.path).query)
        cc = CustomCollector(params.get("server", []), params.get("item_id", []))
        self.registry.register(cc)
        encoder, content_type = prometheus_client.exposition.choose_encoder(self.headers.get('Accept'))
        try:
            output = prometheus_client.exposition.generate_latest(self.registry)
        except:
            self.send_error(500, 'error generating metric output')
            raise
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(output)
        self.registry.unregister(cc)

class CustomCollector(object):
    def __init__(self, servers, item_ids):
        self.servers = servers
        self.item_ids = item_ids

    def collect(self):
        metric_lookup = {}
        for server_name in self.servers:
            for item_id in self.item_ids:
                response = requests.get("{url}/market/{server}/items/{item_id}".format(url=baseUrl, server=server_name, item_id=item_id), params=parms)
                item_name = re.sub(r"[^a-zA-Z0-9]+", '_', str(item_id_lookup[item_id]).lower())
                if metric_lookup.get(item_name, None) is None:
                    metric_lookup[item_name] = GaugeMetricFamily(item_name, "", labels=["server", "town", "quantity", "retainer"])
                var = metric_lookup[item_name]
                for price in response.json()["Prices"]:
                    var.add_metric(labels=[server_name, price["Town"]["Name_en"], str(price["Quantity"]), price["RetainerName"]], value=price["PricePerUnit"])
        for value in metric_lookup.values():
            yield value

if __name__ == '__main__':
    try:
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', 8808), CustomMetricsHandler)
        print ('Started httpserver on port ' , 8808)

        #Wait forever for incoming htto requests
        server.serve_forever()
    except KeyboardInterrupt:
        print ('^C received, shutting down the web server')
        server.socket.close()

