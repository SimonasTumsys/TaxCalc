from logging import root
from kivy.app import App
from kivymd.uix.screen import Screen
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
import json
import kivymd



class CalculatedLayout(GridLayout):
    pass


class MainWindow(Screen):
    pass

class CalcWindow(Screen):

    def add_customWidget(self):
        customWidget = CalculatedLayout()
        self.ids.calc_container.add_widget(customWidget)
        
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    def calculate(self, settings = settings):
        psd_relative_rate = 0.0698
        vsd_rate = 0.1252
        pension_rate = float(settings['pension'])

        if self.ids.total_earn.text is not '':
            total_earn = float(self.ids.total_earn.text)
            if settings['spend_30_percent'] == True:
                total_costs = total_earn*0.3
            else:
                if self.ids.costs.text is not '':
                    total_costs = float(self.ids.costs.text)                

            profit = total_earn - total_costs

            if settings['psd_fixed'] == True:
                psd_tax = 50.95
            else:  
                psd_tax = (profit*0.9)*psd_relative_rate

            vsd_tax = (profit*0.9)*vsd_rate
            pension_tax = (profit*0.9)*(pension_rate/100)
            if profit <= 20000:
                gpm_tax = profit * 0.05
            elif profit > 20000 and profit < 35000:
                gpm_tax = profit * 0.15 - profit * (0.1-2/300000 *
                (profit - 20000))
            else:
                gpm_tax = profit*0.15

            total_tax = psd_tax + vsd_tax + pension_tax + gpm_tax
            nett_earn = total_earn - total_tax
            total_tax_perc = round(total_tax/nett_earn*100, 2)

            return {"total_earn":total_earn,"total_costs":total_costs,
                "profit":profit,"vsd_tax":vsd_tax,"psd_tax":psd_tax,
                "pension_tax":pension_tax, "gpm_tax":gpm_tax,
                "total_tax":total_tax,"nett_earn":nett_earn,
                "total_tax_perc": total_tax_perc}


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
    
    def get_col():
        with open('colors.json') as f:
            colors = json.load(f)
            return colors
    
    def get_lang(lang = get_sett()['language']):
        with open('language.json', encoding='utf-8') as f:
            lang_data = json.load(f)
            lang_data = lang_data[lang]
        return lang_data
    
    def build(self):
        self.icon = 'temp_icon.jpg'


    lang_data = get_lang()
    settings = get_sett()
    colors = get_col()


TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75