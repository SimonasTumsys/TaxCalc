from logging import root
from kivy.app import App
from kivymd.uix.screen import Screen
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
import os
import json
import pdfplumber
from datetime import datetime


class CalculatedLayout(GridLayout):
    pass
    
class MainWindow(Screen):
    pass

class CalcWindow(Screen):
    def add_calcLayoutWidget(self):
        calcLayout = CalculatedLayout()
        self.ids.calc_container.add_widget(calcLayout)
        
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    def calculate(self, settings = settings):
        psd_relative_rate = 0.0698
        vsd_rate = 0.1252
        pension_rate = float(settings['pension'])

        if self.ids.total_earnings.text is not '':
            total_earn = float(self.ids.total_earnings.text)
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
            total_tax_perc = round(total_tax/total_earn*100, 2)

            output = [total_earn, profit, total_costs, 
            psd_tax, vsd_tax, pension_tax, gpm_tax, 
            nett_earn, total_tax, total_tax_perc]

            str_output = ['€{:.2f}'.format(x) for x in output]
        return str_output
    
    def useless(self):
        pass






class EarnWindow(Screen):

    def scan_fs():
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)

        bf_paths = pdf_paths['bf']
        bf_dates = pdf_paths['bf_dates']
        temp_bf_paths = []
        temp_w_paths = []
        
        for root,dirs,files in os.walk("/"):
            temp_bf_paths.extend((os.path.join(root,f) for f in files if 'Weekly Report' in f and '.pdf' in f))
            for temp_bf_path in temp_bf_paths:
                if temp_bf_path not in bf_paths:
                    bf_paths.append(temp_bf_path)

        
        pdf_paths['bf'] = bf_paths
        pdf_paths['bf_dates'] = bf_dates

        with open('pdf_paths.json', 'w') as f:
            json.dump(pdf_paths, f, indent=2)

    def handle_pdf():
        ed_dict = {}
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
## Handling Bolt Food pdfs - extracting date and earnings:
        for path in pdf_paths['bf']:
            fixed_path = path.replace('\\', '/')
            with pdfplumber.open(fixed_path) as temp:
                pages = []
                for page in temp.pages:
                    pages.append(page.extract_text())
                    pdf_text = ''.join(pages)

            date_start_index = pdf_text.find('Ataskaita už laikotarpį: ') + 25
            date_end_index = pdf_text.find('Ataskaita už laikotarpį: ') + 48
            date = pdf_text[date_start_index:date_end_index]

            earn_start_index = pdf_text.find('Savaitinis uždarbis') + 20
            earn_end_index = pdf_text.find('Savaitinis uždarbis') + 26

            earnings_no_cash = float(pdf_text[earn_start_index:earn_end_index])
            try:
                cash_start_index = pdf_text.rfind('Grynieji pinigai iš kliento') + 28
                cash_end_index = pdf_text.find('Savaitinis uždarbis') - 3

                cash_raw = pdf_text[cash_start_index:cash_end_index]
                cash_cutoff = cash_raw.find('0.00') + 6
                cash = float(cash_raw[cash_cutoff:len(cash_raw)])
            except ValueError:
                cash = 0.0

            earnings = earnings_no_cash + cash

            ed_dict[date] = earnings
        return ed_dict

    print(handle_pdf())




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
    
    # def build(self):
    #     self.icon = 'temp_icon.jpg'


    lang_data = get_lang()
    settings = get_sett()
    colors = get_col()


TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75