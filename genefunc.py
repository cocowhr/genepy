# coding=gbk
"""
genefunc.py
~~~~~~~~~~~~~~~~
使用遗传算法挖掘数据
输入：ref 行为模式库
codes: 行为的序号和权重，目前所有行为权重都相同，可改成该行为出现的频率
输出：
用户的正常行为模式序列
可能的提示错误：用户的正常行为模式序列输出到mysql数据库时会因为重复数据插入报警告(但是不会影响插入结果)
"""
import random
import copy
import time
import pymysql

NS = 1#所有可能的行为数目，目前样例为42个，在readcodes中获取
ST = 1#行为模式库的大小,在readref中获得
LEN = 4#行为模式序列的长度,在readref中获得
CNUM = 16#群体规模
NUM = 30#迭代次数

#个体
class Chrom:
    def __init__(self):
        self.seq = [0] * LEN#行为模式序列
        self.M = 0#序列在表中出现次数
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

def getConnection():
    conn = pymysql.connect(host='localhost',db='supervision', user='root', passwd='root', port=3306, charset='utf8')#之后可以放到配置文件中读取
    return conn
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
        # if random.randint(0,1)>0:
        #     chrom.seq[random.randint(0,LEN-1)]=0#部分规则
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
                c1 = Chrom()
                c2 = Chrom()
                crosspoint = random.randint(0, LEN - 1)
                k = 0
                while k < crosspoint:
                    c1.seq[k] = popcurrent[i].seq[k]
                    c2.seq[k] = popcurrent[j].seq[k]
                    k += 1
                while k < LEN:
                    c1.seq[k] = popcurrent[j].seq[k]
                    c2.seq[k] = popcurrent[i].seq[k]
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
            if random.randint(0, 99) < 25:
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
    # E = LEN
    ci = 0.0
    i = 0
    while i < LEN:
        if chrom.seq[i] != 0:
            ci += codes[chrom.seq[i] - 1].count
        # else:
        #     E -= 1
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
    # chrom.fit = ci * chrom.M * pow(NS, E) / ST
    chrom.fit = ci * chrom.M

#读取ref 获得LEN和ST
def readref(target):
    ref = []
    try:
        conn =getConnection()
        cur = conn.cursor()
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

#读取codes 获得NS
def readcodes(target):
    codes = []
    conn = getConnection()
    cur = conn.cursor()
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
#查看pop中是否所有种群已经全部相同，全部相同则停止迭代
def checkequal(pop):
    c=pop[0].seq
    eq=True
    for chrom in pop:
        if chrom.seq !=c:
            eq=False
            break
    return eq

#输出正常行为模式到数据库
def writerules(popcurrent,target,codes,field):
    conn = getConnection()
    cur = conn.cursor()
    basesql2 = "SELECT * FROM "
    basesql2+= codes
    basesql2+= " where id="
    basesql="INSERT IGNORE INTO "+target+"("
    for i in range(len(field)):
        basesql+="`"+field[i]+"`,"
    basesql+="`fit`) VALUES("
    for chrom in popcurrent:
        sql=basesql
        for i in range(len(field)):
            csql=basesql2
            csql+=str(chrom.seq[i])
            cur.execute(csql)
            res=cur.fetchall()
            sql+="'%s',"%(res[0][1])
        sql+='%lf)'%(chrom.fit)
        cur.execute(sql)
    cur.close()
    conn.commit()
    conn.close()
def getrules(target,field):
    ref = readref(target)
    codes = readcodes(target+"_count")
    popcurrent = evpop(codes, ref)
    dd = 0
    while dd < NUM:
        print "当前为第%d轮迭代" % (dd)
        if checkequal(popcurrent):
            break
        popnext = crossover(popcurrent, codes)
        mutation(popnext, codes, ref)
        popnext = pickchroms(popcurrent, popnext)
        popcurrent = popnext
        dd += 1
    writerules(popcurrent,target+"_generules",target+"_codes",field)
def get_ip_packet_rules():
    field=["time","host_id","send_mac_address","recv_mac_address","send_ip","send_port","recv_ip","recv_port"]
    getrules("data_process_ippacket",field)
def get_warning_information_rules():
    field=["time","userid","description","rank","species"]
    getrules("warning_information",field)
def get_data_process_fileinfo_file_rules():
    field=["time","file_name","user","operate_type","host_id"]
    getrules("data_process_fileinfo_file",field)
def get_data_process_fileinfo_type_rules():
    field=["time","file_type","user","operate_type","host_id"]
    getrules("data_process_fileinfo_type",field)
def get_data_process_resource_warning_rules():
    field = ["time", "user", "process_name", "resources_name", "warning_rank"]
    getrules("data_process_resource_warning", field)

#查询行为模式的适应度值，之后根据阈值进行判断是否正常
def search_fit(target,seq):
    chrom=Chrom()
    chrom.seq=seq
    ref=readref(target)
    codes=readcodes(target+"_count")
    calculatefit(chrom,codes,ref)
    print(chrom.fit)
if __name__ == '__main__':
    start = time.clock()
    for i in range(0,5):
        #get_ip_packet_rules()
        get_warning_information_rules()
        #get_data_process_fileinfo_file_rules()
    #get_data_process_fileinfo_type_rules()
    #get_data_process_resource_warning_rules()
    #search_fit("warning_information",[2,9,20,7,21])
    end = time.clock()
    print str(end - start) + "s"
