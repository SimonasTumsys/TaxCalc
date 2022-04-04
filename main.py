from logging import root
from kivy.app import App
from kivymd.uix.screen import Screen
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
import os
import json


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

    # def scan_fs():
    #     with open('pdf_paths.json', 'r') as f:
    #         pdf_paths = json.load(f)

    #     bf_paths = []
    #     for root,dirs,files in os.walk("/"):
    #         bf_paths.extend((os.path.join(root,f) for f in files if f.endswith("Weekly Report.pdf")))
        
    #     for path in bf_paths:
    #         pdf = open(path, 'rb')
    #         pdfReader = PdfFileReader(pdf)

    #         print("PDF File name: " + str(pdfReader.getDocumentInfo().title))

    #         bf_obj = {path:"text"}

    #         numOfPages = pdfReader.getNumPages()

    #         for i in range(0, numOfPages):
    #             print("Page Number: " + str(i))
    #             print("- - - - - - - - - - - - - - - - - - - -")
    #             pageObj = pdfReader.getPage(i)
    #             print(pageObj.extractText())
    #             print("- - - - - - - - - - - - - - - - - - - -")
    #         # close the PDF file object
    #         pdf.close()
            
    # scan_fs()
            
        
    
    
    # def handle_pdf():
    #     for path in bf_paths:
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
    
    # def build(self):
    #     self.icon = 'temp_icon.jpg'


    lang_data = get_lang()
    settings = get_sett()
    colors = get_col()


TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75