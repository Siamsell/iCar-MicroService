import pymysql

pymysql.version_info = (2, 2, 8, 'final', 0)
pymysql.__version__ = '2.2.8'

pymysql.install_as_MySQLdb()