from kivy.app import App
from kivymd.uix.screen import Screen
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
import json

class MainWindow(Screen):
    pass

class CalcWindow(Screen):
    brutt_earn = ObjectProperty(None)

    def calculate(self):
        psd_rate = 0.0698
        vsd_rate = 0.1252
        pension_rate = 0.045
        if self.ids.brutt_earn.text is not '':
            profit = float(self.ids.brutt_earn.text) - float(self.ids.brutt_earn.text)*0.3
            psd_tax = (profit*0.9)*psd_rate
            vsd_tax = (profit*0.9)*vsd_rate
            pension_tax = (profit*0.9)*pension_rate
            total_tax = psd_tax + vsd_tax + pension_tax
            nett_earn = float(self.ids.brutt_earn.text) - total_tax


class EarnWindow(Screen):
    pass

class StatWindow(Screen):
    pass

class SettWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass


class TaxCalc(App):
    def get_sett():
        with open('settings.json') as f:
            settings = json.load(f)
        return settings
    
    def get_lang(lang = get_sett()['language']):
        with open('language.json', encoding='utf-8') as f:
            lang_data = json.load(f)
            lang_data = lang_data[lang]
        return lang_data

    lang_data = get_lang()



TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75