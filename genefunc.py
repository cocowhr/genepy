# coding=gbk
"""
genefunc.py
~~~~~~~~~~~~~~~~
ʹ���Ŵ��㷨�ھ�����
���룺ref ��Ϊģʽ��
codes: ��Ϊ����ź�Ȩ�أ�Ŀǰ������ΪȨ�ض���ͬ���ɸĳɸ���Ϊ���ֵ�Ƶ��
�����
�û���������Ϊģʽ����
���ܵ���ʾ�����û���������Ϊģʽ���������mysql���ݿ�ʱ����Ϊ�ظ����ݲ��뱨��
���㣺code���Է������� ��Ⱥ��ʼ����������������ĸ���
NS��ST LEN �����Զ���ȡ
"""
import random
import copy

import pymysql

NS = 1#���п��ܵ���Ϊ��Ŀ��Ŀǰ����Ϊ42��
ST = 1#��Ϊģʽ��Ĵ�С
LEN = 4#��Ϊģʽ���еĳ���
CNUM = 8#Ⱥ���ģ
NUM = 5#��������

#����
class Chrom:
    def __init__(self):
        self.seq = [0] * LEN#��Ϊģʽ����
        self.M = 0
        self.fit = 0.0#��Ӧ��

    def Ccopy(self, a):
        self.seq = copy.copy(a.seq)
        self.M = a.M
        self.fit = a.fit

    def show(self):
        print self.seq
        print self.M
        print self.fit


class Code:
    def __init__(self, _id, _count,_column):
        self.id = _id
        self.count = _count
        self.column=_column
#��ʼ��Ⱥ��
def evpop(codes, ref):
    pop = []
    i = 0
    codes_column={}
    for c in codes:
        codes_column.setdefault(c.column,[])
        codes_column[c.column]+=[c.id]
    while (i < CNUM):
        chrom = Chrom()
        j = 0
        while (j < LEN):
            chrom.seq[j] = codes_column[j][random.randint(0, len(codes_column[j]) - 1)]
            j += 1
        calculatefit(chrom, codes, ref)
        pop += [chrom]
        i += 1
    return pop

#�������
def crossover(popcurrent, codes):
    popnext = []
    i = 0
    while i < CNUM - 1:
        j = i + 1
        while j < CNUM:
            if 80 > random.randint(1, 100):
                E1 = LEN
                E2 = LEN
                c1 = Chrom()
                c2 = Chrom()
                ci1 = 0
                ci2 = 0
                crosspoint = random.randint(0, LEN - 1)
                k = 0
                while k < crosspoint:
                    c1.seq[k] = popcurrent[i].seq[k]
                    c2.seq[k] = popcurrent[j].seq[k]
                    if c1.seq[k] != 0:
                        ci1 += codes[c1.seq[k] - 1].count
                    else:
                        E1 -= 1
                    if c2.seq[k] != 0:
                        ci2 += codes[c2.seq[k] - 1].count
                    else:
                        E2 -= 1
                    k += 1
                while k < LEN:
                    c1.seq[k] = popcurrent[j].seq[k]
                    c2.seq[k] = popcurrent[i].seq[k]
                    if c1.seq[k] != 0:
                        ci1 += codes[c1.seq[k] - 1].count
                    else:
                        E1 -= 1
                    if c2.seq[k] != 0:
                        ci2 += codes[c2.seq[k] - 1].count
                    else:
                        E2 -= 1
                    k += 1
                popnext += [c1]
                popnext += [c2]
            j += 1
        i += 1
    return popnext

#�������
def mutation(popnext, codes, ref):
    for chrom in popnext:
        i = 0
        while i < LEN:
            if random.randint(0, 99) < 5:
                chrom.seq[i] = random.randint(1, NS)
            i += 1
        calculatefit(chrom, codes, ref)

#��Ȼѡ�����
def pickchroms(popcurrent, popnext):
    ret = popcurrent + popnext
    ret.sort(key=lambda obj: obj.fit, reverse=True)
    ret = ret[:CNUM]
    return ret

#������Ӧ�Ⱥ���
def calculatefit(chrom, codes, ref):
    E = LEN
    ci = 0.0
    i = 0
    while i < LEN:
        if chrom.seq[i] != 0:
            ci += codes[chrom.seq[i] - 1].count
        else:
            E -= 1
        i += 1
    j = 0
    while j < ST:
        eq = True
        k = 0
        while k < LEN:
            pop = chrom.seq[k]
            if 0 != pop and ref[j][k] != pop:
                eq = False
                break
            k += 1
        if eq:
            chrom.M += 1
        j += 1
    chrom.fit = ci * chrom.M * pow(NS, E) / ST

#��ȡref
def readref(target):
    ref = []
    try:
        conn = pymysql.connect(host='localhost', user='root', passwd='root', port=3306, charset='utf8')
        cur = conn.cursor()
        cur.execute("USE supervision")
        sql="SELECT * FROM "
        sql+=target
        cur.execute(sql)
        res = cur.fetchall()
        global ST
        ST= len(res)
        global LEN
        LEN=len(res[0])-1
        for row in res:
            temp = [0] * LEN
            for index in range(len(row) - 1):
                temp[index] = row[index + 1]
            ref += [temp]
        cur.close()
        conn.commit()
        conn.close()
        return ref
    except  Exception:
        print("error")

#��ȡcodes
def readcodes(target):
    codes = []
    conn = pymysql.connect(host='localhost', user='root', passwd='root', port=3306, charset='utf8')
    cur = conn.cursor()
    cur.execute("USE supervision")
    sql="SELECT * FROM "
    sql+=target
    sql+=" order by pid"
    cur.execute(sql)
    res = cur.fetchall()
    for row in res:
        id=row[0]
        percent=(float)(row[1])/ST
        a = Code(id,percent,row[2])
        codes += [a]
    global NS
    NS=len(codes)
    cur.close()
    conn.commit()
    conn.close()
    return codes

#���������Ϊģʽ�����ݿ�
def writerules(popcurrent,target,field):
    try:
        conn = pymysql.connect(host='localhost', user='root', passwd='root', port=3306, charset='utf8')
        cur = conn.cursor()
        cur.execute("USE supervision")
        sql="INSERT IGNORE INTO "+target+"("
        for i in range(len(field)):
            sql+="`"+field[i]+"`,"
        sql+="`fit`) VALUES("
        for chrom in popcurrent:
            csql=sql
            for i in range(len(field)):
                csql+="%d,"%(chrom.seq[i])
            csql+='%lf)'%(chrom.fit)
            cur.execute(csql)
        cur.close()
        conn.commit()
        conn.close()
    except  Exception:
        print("error")
def get_ip_packet_rules():
    ref = readref("ip_packet")
    codes = readcodes("ip_packet_count")
    popcurrent = evpop(codes, ref)
    dd = 0
    while dd < NUM:
        print "��ǰΪ��%d�ֵ���" % (dd)
        popnext = crossover(popcurrent, codes)
        mutation(popnext, codes, ref)
        popnext = pickchroms(popcurrent, popnext)
        popcurrent = popnext
        dd += 1
    field=["time","host","user","recvip"]
    writerules(popcurrent,"ip_packet_generules",field)
def get_warning_information_rules():
    ref = readref("warning_information")
    codes = readcodes("warning_information_count")
    popcurrent = evpop(codes, ref)
    dd = 0
    while dd < NUM:
        print "��ǰΪ��%d�ֵ���" % (dd)
        popnext = crossover(popcurrent, codes)
        mutation(popnext, codes, ref)
        popnext = pickchroms(popcurrent, popnext)
        popcurrent = popnext
        dd += 1
    field=["time","userid","description","rank","species"]
    writerules(popcurrent,"warning_information_generules",field)

if __name__ == '__main__':
    #get_ip_packet_rules()
    get_warning_information_rules()
