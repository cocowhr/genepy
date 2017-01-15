# coding=gbk
import random
import copy

import pymysql

NS = 42
ST = 1285
LEN = 4
CNUM = 8
NUM = 5


class Chrom:
    def __init__(self):
        self.seq = [0] * LEN
        self.M = 0
        self.fit = 0.0

    def Ccopy(self, a):
        self.seq = copy.copy(a.seq)
        self.M = a.M
        self.fit = a.fit

    def show(self):
        print self.seq
        print self.M
        print self.fit


class Code:
    def __init__(self, _id, _count):
        self.id = _id
        self.count = _count


def printLar(Lar):
    for Large in Lar:
        for index in range(len(Large)):
            print "%d" % (Large[index])


def evpop(codes, ref):
    pop = []
    i = 0
    while (i < CNUM):
        chrom = Chrom()
        j = 0
        while (j < LEN):
            chrom.seq[j] = codes[random.randint(0, NS - 1)].id
            j += 1
        chrom.seq[0] = 4
        chrom.seq[1] = 5
        chrom.seq[3] = random.randint(0, 3) + 1
        calculatefit(chrom, codes, ref)
        pop += [chrom]
        i += 1
    return pop


def crossover(popcurrent, codes):
    popnext = []
    i = 0
    while i < CNUM - 1:
        j = i + 1
        while j < CNUM:
            if 120 > random.randint(1, 100):
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


def mutation(popnext, codes, ref):
    for chrom in popnext:
        i = 0
        while i < LEN:
            if random.randint(0, 99) < 5:
                chrom.seq[i] = random.randint(1, NS)
            i += 1
        calculatefit(chrom, codes, ref)


def pickchroms(popcurrent, popnext):
    ret = popcurrent + popnext
    ret.sort(key=lambda obj: obj.fit, reverse=True)
    ret = ret[:CNUM]
    return ret


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


def readref():
    ref = []
    try:
        conn = pymysql.connect(host='localhost', user='root', passwd='root', port=3306, charset='utf8')
        cur = conn.cursor()
        cur.execute("USE genet")
        cur.execute("SELECT * FROM seq2;")
        res = cur.fetchall()
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


def readcodes():
    i = 1
    codes = []
    while i <= NS:
        a = Code(i, 0.1)
        codes += [a]
        i += 1
    return codes


def writerules(popcurrent):
    try:
        conn = pymysql.connect(host='localhost', user='root', passwd='root', port=3306, charset='utf8')
        cur = conn.cursor()
        cur.execute("USE genet")
        for chrom in popcurrent:
            cur.execute(
                "INSERT IGNORE INTO  rules2 (`seq1`, `seq2`, `seq3`, `seq4`, `fit`)  VALUES ('%d', '%d', '%d', '%d','%lf')" % (
                chrom.seq[0], chrom.seq[1], chrom.seq[2], chrom.seq[3], chrom.fit))
        cur.close()
        conn.commit()
        conn.close()
    except  Exception:
        print("error")


if __name__ == '__main__':
    ref = readref()
    codes = readcodes()
    popcurrent = evpop(codes, ref)
    dd = 0
    while dd < 5:
        print "当前为第%d轮迭代" % (dd)
        popnext = crossover(popcurrent, codes)
        mutation(popnext, codes, ref)
        popnext = pickchroms(popcurrent, popnext)
        popcurrent = popnext
        dd += 1
    writerules(popcurrent)
