'''
Created by: Quamez Anderson
Date Created: 08 February 2021
'''

from threading import Thread
from run_forever import run_code
from bot import *
import time

#run_code()
#time.sleep(1)
#print('\n')
ai_trader.stock_run(0, False)
# Multiple threads allow for the running of multiple bots at once
#bot1 = Thread(target=quamez.stock_run, args=[0,True])
#bot1.start()
#bot2 = Thread(target=matthew.stock_run, args=[1,False])
#bot2.start()
