#
# -*- coding: utf-8 -*-
#
# LICENSE: BSD-3
#
# by arxiv.org
#

import random
import string
from os.path import dirname, join

class DataSource:
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r', encoding="UTF-8") as fd:
            self.data = [line.strip() for line in fd.readlines()]
        self.row_count = len(self.data)

    def pick(self) -> str:
        num = int(random.uniform(0, len(self.data)))
        return self.data[num]
