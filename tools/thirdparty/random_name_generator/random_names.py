#! python3
# -*- coding: utf-8 -*-
import random
import string
from os.path import dirname, join

from poetry.console.commands import self

script_dir    = dirname(__file__)
names_dir     = join(script_dir, 'Names')

FirstNames    = join(names_dir, 'FirstNames.txt')
MiddleNames   = join(names_dir, 'MiddleNames.txt')
LastNames     = join(names_dir, 'LastNames.txt')
CountyNames   = join(names_dir, 'CountyNames.txt')
PlaceNames    = join(names_dir, 'PlaceNames.txt')
StateNames    = join(names_dir, 'StateNames.txt')
CountryNames  = join(names_dir, 'CountryNames.txt')
CompanyNames  = join(names_dir, 'CompanyNames.txt')


def Number(start=0, end=100000):
    """
    Returns random integer between range of numbers
    """
    return random.randint(start, end)


def UpperChars(NoOfChars=2):
    """
    UpperChars(NoOfChars=2) Returns 2 random CAPITAL letters.
    """
    _char = ''
    for num in range(NoOfChars):
        _char += random.choice(string.ascii_uppercase)
    return _char


def rawCount(filename):
    """
    Function to get Line Count in txt files.
    rawcount('C:\A.txt') outputs integer value of count of lines.
    """
    with open(filename, 'rb') as f:
        lines = 1
        buf_size = 1024 * 1024
        read_f = f.raw.read

        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b'\n')
            buf = read_f(buf_size)
        return lines


def randomLine(filename):
    """
    Read the given text file and return a random line
    """
    num = int(random.uniform(0, rawCount(filename)))
    with open(filename, 'r', encoding="UTF-8") as f:
        for i, line in enumerate(f, 1):
            if i == num:
                break
    return line.strip('\n')


def First():
    return randomLine(FirstNames)


def Last():
    return randomLine(LastNames)


def Middle():
    return randomLine(MiddleNames)


def States():
    return randomLine(StateNames)


def Places():
    return randomLine(PlaceNames)


def County():
    return randomLine(CountyNames)


def Company():
    return randomLine(CompanyNames)


def Country():
    _Cc = randomLine(CountryNames)
    _Cc = _Cc.split('|')
    return _Cc[1]


def CountryCode():
    _Cc = randomLine(CountryNames)
    _Cc = _Cc.split('|')
    return _Cc[0]


def StateCode():
    return States().split(', ')[1]


def Full():
    """
    Returns a random First Name and Last Name combination
    """
    return ' '.join([First(), Last()])


def Address():
    """
    Returns a Random address in the Format:
    54F - Sauk, Middle, New Mexico, NM, 4292.
    """
    _door = str(Number(11, 99))
    _zip  = str(Number(1000, 9999))
    _adrs = ', '.join([Places(), County(), States(), _zip])
    _adrs = _door + UpperChars(1) + ' - ' + _adrs + '.'
    return _adrs


def ShortAddress():
    """
    Returns a Short Random address in the Format:
    31 Outagamie, Wisconsin, WI, 8281
    """
    _door = str(Number(11, 99))
    _zip  = str(Number(1000, 9999))
    _adrs = ', '.join([County(), States(), _zip])
    _adrs = _door + ' ' + _adrs
    return _adrs


if __name__ == '__main__':
    print(Full(), ' works at ', Company(), ' lives at ', Address(), StateCode(), Country())
