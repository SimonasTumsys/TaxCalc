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
        pension_rate = 0.03
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
    def save_settings(self):
        with open('settings.json', 'r') as f:
            settings = json.load(f)

        if self.ids.lng_button_lt.state == 'down':
            settings['language'] = 'lt'
        else: 
            settings['language'] = 'en'

        if self.ids.psd_button_true.state == 'down':
            settings['psd_fixed'] = True
        else:
            settings['psd_fixed'] = False
        
        if self.ids.spend_button_true.state == 'down':
            settings['spend_30_percent'] = True
        else:
            settings['spend_30_percent'] = False

        if self.ids.pension0.state == 'down':
            settings['pension'] = 0
        elif self.ids.pension27.state == 'down':
            settings['pension'] = 2.7
        else:
            settings['pension'] = 3

        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=2)


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
    settings = get_sett()

TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75