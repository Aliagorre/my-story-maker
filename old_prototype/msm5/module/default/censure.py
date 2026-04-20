from module.default.__censure_list import _CENSURE_LISTE

def cl() :
    file = open("module/default/__txt_censure_list.txt", "r", encoding="utf-8")
    LIST = file.readlines()
    file.close()
    return LIST + _CENSURE_LISTE


def bad_word() -> bool :
    print("Désolée. Vous ne pouvez pas utiliser ces mots.")
    print("Renseignez vous auprès du module de censure.")
    input()
    return True

def censure_dict() -> dict :
    return {mot:bad_word for mot in cl()}

create_story_option  = censure_dict()
rename_story_option  = censure_dict()

create_save_option = censure_dict()
rename_save_option = censure_dict()
