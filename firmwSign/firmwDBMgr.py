#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        firmwDBMgr.py
#
# Purpose:     firmware Sign dataBase manager. 
# Author:      Yuancheng Liu
#
# Created:     2019/05/08
# Copyright:   YC
# License:     YC
#-----------------------------------------------------------------------------

import os
import sqlite3
from sqlite3 import Error

dirpath = os.getcwd()
#DB_PATH = "".join([dirpath, "\\firmwSign\\firmwDB.db"])
DB_PATH = "".join([dirpath, "\\firmwDB.db"])

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class firmwDBMgr(object):
    """ firmware Sign system dataBase manager. 
    """
    def __init__(self):
        """ Check whether the data base has been created and connect to DB+table if needed.
        """
        self.sql_firwareInfo_table = None
        if not os.path.exists(DB_PATH):
            print("Data base file is missing, create new data base file")
            self.sql_firwareInfo_table = """CREATE TABLE IF NOT EXISTS firmwareInfo (
                                id integer PRIMARY KEY,
                                sensorID integer NOT NULL,
                                challenge text NOT NULL,
                                swatt text NOT NULL,
                                date text NOT NULL,
                                type text,
                                version text NOT NULL
                            );"""

        self.conn = self.createConnection(DB_PATH)
        # create the table if the BD is first time created one.
        if self.sql_firwareInfo_table and self.conn:
            self.createTable(self.conn, self.sql_firwareInfo_table)

#-----------------------------------------------------------------------------
    def createTable(self, conn, create_table_sql):
        """ Create a table
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

#-----------------------------------------------------------------------------
    def createConnection(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)

#-----------------------------------------------------------------------------
    def createFmSignRcd(self, rcdArgs):
        if len(rcdArgs) != 6: 
            print("The firmware sign inforamtion <%s> element missing." %str(rcdArgs))

        sql = ''' INSERT INTO firmwareInfo( sensorID, challenge, swatt, date, type, version)
                VALUES(?,?,?,?,?,?) '''
        #rcdArgs = ( 203, 'default challenge', '0x1245', '2015-01-01', 'XKAK_PPL_COUNT', '1.01')
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(sql, rcdArgs)
            print("This is the cursir UD: %s" %str(cur.lastrowid))
            return cur.lastrowid

#-----------------------------------------------------------------------------
    def updateRecd(self,rcd):
        sql = ''' UPDATE firmwareInfo
                SET sensorID = ? ,
                    challenge = ? ,
                    swatt = ?
                WHERE id = ?'''
        with self.conn:
            cur = self.conn.cursor()
            cur.execute(sql, rcd)

#def testCase():
#    if conn is not None: 
#         createTable(conn, sql_firwareInfo_table)
#    
#    with conn:
#        signRecord = ( 203, 'default challenge', '0x1245', '2015-01-01', 'XKAK_PPL_COUNT', '1.01')
#        signIdx = createFmSignRcd(conn, signRecord)
#        print("this is signIdx"+str(signIdx))
#        #changedRcd = ()
#        updateRecd(conn, (202, 'change challenge', '0X234',1))
    #else:
    #    print("Error! Can not create the database connection.")
    
if __name__ == '__main__':
    pass
    #testCase()
