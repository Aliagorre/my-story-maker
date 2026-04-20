from core.utils import clear_screen

def what_do_you_play():
        clear_screen()
        print("À quoi jouez vous ?")
        input()
        clear_screen()
        return False

init_story_option = {"Annuler":what_do_you_play}