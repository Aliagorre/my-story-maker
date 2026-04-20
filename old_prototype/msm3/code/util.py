from genericpath import exists
import ast
import os

NON = ["non","no","nn","n","0","false"]
OUI = ["oui","ou","oi","ui","o","1","true"]

def est_solvable(appelation):
    try :
        if type(eval(appelation)) == bool:
            return True
        else :
            return False
    except :
        return False