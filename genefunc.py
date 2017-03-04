# coding=gbk
"""
genefunc.py
~~~~~~~~~~~~~~~~
使用遗传算法挖掘数据
输入：ref 行为模式库
codes: 行为的序号和权重，目前所有行为权重都相同，可改成该行为出现的频率
输出：
用户的正常行为模式序列
可能的提示错误：用户的正常行为模式序列输出到mysql数据库时会因为重复数据插入报错
不足：code可以分种类存放 种群初始化按种类可以收敛的更快
NS和ST LEN 可以自动提取
"""
import random
import copy

import pymysql

NS = 1#所有可能的行为数目，目前样例为42个
ST = 1#行为模式库的大小
LEN = 4#行为模式序列的长度
CNUM = 8#群体规模
NUM = 5#迭代次数

#个体
class Chrom:
    def __init__(self):
        self.seq = [0] * LEN#行为模式序列
        self.M = 0
        self.fit = 0.0#适应度

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
#初始化群体
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

#交叉操作
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

#变异操作
def mutation(popnext, codes, ref):
    for chrom in popnext:
        i = 0
        while i < LEN:
            if random.randint(0, 99) < 5:
                chrom.seq[i] = random.randint(1, NS)
            i += 1
        calculatefit(chrom, codes, ref)

#自然选择操作
def pickchroms(popcurrent, popnext):
    ret = popcurrent + popnext
    ret.sort(key=lambda obj: obj.fit, reverse=True)
    ret = ret[:CNUM]
    return ret

#计算适应度函数
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

#读取ref
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

#读取codes
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

#输出正常行为模式到数据库
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
        print "当前为第%d轮迭代" % (dd)
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
        print "当前为第%d轮迭代" % (dd)
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
