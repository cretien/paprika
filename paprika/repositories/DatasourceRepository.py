from paprika.repositories.Repository import Repository
from paprika.connectors.Helper import Helper
import os


class DatasourceRepository(Repository):
    def __init__(self, connector):
        Repository.__init__(self, connector)

    def get_by_name(self, name):
        connection = self.get_connection()
        cursor = connection.cursor()

        param = dict()
        param['name'] = name
        param['passphrase'] = os.environ.get('paprika_passphrase')

        statement = "select name, type, host, sid, db, username, aes_decrypt( password, sha2( :passphrase, 512)) password "\
                    "from datasources where name = :name"
        statement, parameters = self.statement(statement, param)

        cursor.execute(statement, parameters)
        result = Helper.cursor_to_json(cursor)

        if len(result) == 0:
            return None
        return result[0]

    def insert(self, datasource):
        connection = self.get_connection()
        cursor = connection.cursor()

        params = dict()
        params['name'] = datasource.get('name')
        params['type'] = datasource.get('type')
        params['host'] = datasource.get('host')
        params['sid'] = datasource.get('sid')
        params['db'] = datasource.get('db')
        params['username'] = datasource.get('username')
        params['password'] = self.encrypt(datasource.get('password'))

        statement = "insert into datasources(name, type, host, sid, db, username, password) values (:name, :type, :host, :sid, :db, :username, :password)"
        statement, parameters = self.statement(statement, params)

        cursor.execute(statement, parameters)
        datasource['id'] = cursor.lastrowid
        connection.commit()
        cursor.close()

        return datasource

    def delete(self, name):
        connection = self.get_connection()
        cursor = connection.cursor()

        params = dict()
        params['name'] = name

        statement = "delete from datasources where name = :name"
        statement, parameters = self.statement(statement, params)

        cursor.execute(statement, parameters)
        connection.commit()
        cursor.close()

    def encrypt(self, string):
        connection = self.get_connection()
        cursor = connection.cursor()
        statement = "select aes_encrypt( '" + string + "', sha2( '" + os.environ.get('paprika_passphrase') \
                    + "' , 512)) string"
        cursor.execute(statement)
        result = Helper.cursor_to_json(cursor)
        cursor.close()
        if len(result) == 0:
            return None
        return result[0].get('string')
