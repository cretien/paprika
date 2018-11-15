class ConnectorUrlBuilder:
    def __init__(self):
        pass

    @staticmethod
    def build(url):
        message = dict()
        message['url'] = url
        message['datasource'] = url.split('://')[0]
        message['db_call'] = url.split('://')[1]
        return message
