from logging import root
from turtle import clear
from kivy.app import App
from kivymd.uix.screen import Screen
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
import os
import json
import pdfplumber
from datetime import date, datetime
import sqlite3


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
    ##Function to scan filesystem for Bolt Food (bf) and
    # Wolt (w) PDFs
    def scan_fs():
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)

        pdf_paths['bf'] = []
        pdf_paths['wolt'] = []
        pdf_paths['meta_list'] = []
        bf_paths = pdf_paths['bf']
        wolt_paths = pdf_paths['wolt']
        meta_list = pdf_paths['meta_list']
        temp_paths = []

    ##Need to write a function with FileChooser to let the user choose directory
    # otherwise too slow    
        fs_path = r'C:\Users\PC\Desktop\Bolt Documents'
        fs_fixed_path = fs_path.replace('\\', '/')

    ##Scanning specified directory for Bolt Food and Wolt PDFs and their metadata:
        for root,dirs,files in os.walk(fs_fixed_path):
            temp_paths.extend((os.path.join(root,f) for f in files if '.pdf' in f))
            for temp_path in temp_paths:
                fixed_temp_path = temp_path.replace('\\', '/')
                with pdfplumber.open(fixed_temp_path) as temp_pdf:
                    pdf_text = temp_pdf.pages[0].extract_text()
    ##Validation to avoid including duplicate PDFs into json   
                if pdf_text.find('Bolt Operations') != -1:
                    temp_meta = temp_pdf.metadata
                    if temp_path not in bf_paths and temp_meta not in meta_list:
                        bf_paths.append(temp_path)
                        meta_list.append(temp_meta)
                elif pdf_text.find('UAB Wolt LT') != -1:
                    temp_meta = temp_pdf.metadata
                    if temp_path not in wolt_paths and temp_meta not in meta_list:
                        wolt_paths.append(temp_path)
                        meta_list.append(temp_meta)

        pdf_paths['bf'] = bf_paths
        pdf_paths['wolt'] = wolt_paths
        pdf_paths['meta_list'] = meta_list

        with open('pdf_paths.json', 'w') as f:
            json.dump(pdf_paths, f, indent=2)

    ## Function to extract data from pdfs, save into db:
    def handle_pdf():
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()

        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
        ## Handling Bolt Food pdfs:
        for path in pdf_paths['bf']:
            try:
                fixed_path = path.replace('\\', '/')
                with pdfplumber.open(fixed_path) as temp:
                    pdf_meta = temp.metadata
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

                start_date_string = date[0:10]
                end_date_string = date[13:23]

                meta_string = pdf_meta['CreationDate']

                c.execute('INSERT INTO dated_earnings VALUES (?, ?, ?, ?)',
                    (start_date_string, end_date_string, earnings, meta_string))

            except sqlite3.IntegrityError:
                continue

            conn.commit()
        conn.close()

    def create_db():
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS dated_earnings (
            start_date text,
            end_date text,
            earnings real,
            pdf_meta text unique
        )""")
        conn.commit()
        conn.close()

    def clear_db():
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS dated_earnings''')
        conn.commit()
        conn.close()



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