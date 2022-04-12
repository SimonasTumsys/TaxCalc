from kivymd.uix.screen import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window
from kivymd.toast import toast
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ToggleButtonBehavior
import os
import json
import pdfplumber
import datetime
import sqlite3
import kivymd
import kivy


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
            nett_earn, total_tax]

            output = ['€{:.2f}'.format(x) for x in output]
            output.append(str(total_tax_perc))
        return output
    
    def useless(self):
        pass

class FileManager(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=False,
            search='dirs',
        )

    def file_manager_open(self):
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
            path = pdf_paths['main_path']

        self.file_manager.show(path)  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        self.exit_manager()
        toast(path)

        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
            pdf_paths['main_path'] = path
        with open('pdf_paths.json', 'w') as f:
            json.dump(pdf_paths, f, indent=2)

        ## Updating hint_text label:
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
            path = pdf_paths['main_path']

        self.ids.path_label.hint_text = str(path)



    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True

class EarnWindow(Screen):

    ##Function to scan filesystem for Bolt Food (bf) and
    # Wolt (w) PDFs
    def scan_fs(self):
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)

        pdf_paths['bf'] = []
        pdf_paths['wolt'] = []
        pdf_paths['meta_list'] = []
        bf_paths = pdf_paths['bf']
        wolt_paths = pdf_paths['wolt']
        meta_list = pdf_paths['meta_list']
        temp_paths = []

        fs_path = pdf_paths['main_path']
        fs_fixed_path = fs_path.replace('\\', '/')

    ##Scanning specified directory for Bolt Food and Wolt PDFs and their metadata:
        for root,dirs,files in os.walk(fs_fixed_path):
            temp_paths.extend((os.path.join(root,f) for f in files if '.pdf' in f))
            for temp_path in temp_paths:
                fixed_temp_path = temp_path.replace('\\', '/')
                with pdfplumber.open(fixed_temp_path) as temp_pdf:
                    pdf_text = temp_pdf.pages[0].extract_text()
    ##Validation to avoid including duplicate PDFs into json   
                if pdf_text.find('Bolt Operations') != -1 and pdf_text.find('Papildoma pristatymo kaina') == -1:
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
    def handle_pdf(self):
        # pb = ProgressBar(max = 1000)
        # self.ids.pb_container.add_widget(pb)
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()

        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
        ## Handling Bolt Food pdfs:
        for bf_path in pdf_paths['bf']:
            try:
                fixed_bf_path = bf_path.replace('\\', '/')
                with pdfplumber.open(fixed_bf_path) as temp:
                    pdf_meta = temp.metadata
                    pages = []
                    for page in temp.pages:
                        pages.append(page.extract_text())
                        pdf_text = ''.join(pages)

                date_start_index = pdf_text.find('Ataskaita už laikotarpį: ') + 25
                date_end_index = pdf_text.find('Ataskaita už laikotarpį: ') + 48
                date = pdf_text[date_start_index:date_end_index]
                start_date_string = date[0:10]
                end_date_string = date[13:23]

                earn_start_index = pdf_text.find('Savaitinis uždarbis') + 20
                earn_end_index = pdf_text.find('Savaitinis uždarbis') + 26

                earnings_no_cash = float(pdf_text[earn_start_index:earn_end_index])
                try:
                    cash_start_index = pdf_text.rfind('Grynieji pinigai iš kliento') + 28
                    cash_end_index = pdf_text.rfind('Grynieji pinigai iš kliento') + 47

                    cash_raw = pdf_text[cash_start_index:cash_end_index]
                    cash_cutoff = cash_raw.find('0.00') + 6
                    cash = float(cash_raw[cash_cutoff:len(cash_raw)])
                except ValueError:
                    cash = 0.0

                earnings = round((earnings_no_cash + cash), 2)
                meta_string = pdf_meta['CreationDate']
                b_identifier = 'Bolt Food'

                c.execute('INSERT INTO dated_earnings VALUES (?, ?, ?, ?, ?)',
                    (b_identifier, start_date_string, end_date_string, earnings, meta_string))

            except sqlite3.IntegrityError:
                continue

            conn.commit()

        ## Handling Wolt pdfs:
        for w_path in pdf_paths['wolt']:
            try:
                fixed_w_path = w_path.replace('\\', '/')
                with pdfplumber.open(fixed_w_path) as w_temp:
                    w_pdf_meta = w_temp.metadata
                    w_pages = []
                    for w_page in w_temp.pages:
                        w_pages.append(w_page.extract_text())
                        w_pdf_text = ''.join(w_pages)

                w_date_start_index = w_pdf_text.find('Periodas: ') + 10
                w_date_end_index = w_pdf_text.find('Periodas: ') + 31
                w_date = w_pdf_text[w_date_start_index:w_date_end_index]

                w_start_date = w_date[0:10].replace('.', '-')
                w_start_date_string = str(datetime.datetime.strptime(w_start_date,
                    '%d-%m-%Y').strftime('%Y-%m-%d'))

                w_end_date = w_date[11:21].replace('.', '-')
                w_end_date_string = str(datetime.datetime.strptime(w_end_date,
                    '%d-%m-%Y').strftime('%Y-%m-%d'))

                w_earn_start_index = w_pdf_text.find('Suma (EUR)') + 11
                w_earn_end_index = w_pdf_text.find('Suma (EUR)') + 17
                w_earnings = float(w_pdf_text[w_earn_start_index:w_earn_end_index])
                if w_earnings > 100:
                    w_earn_end_index = w_pdf_text.find('Suma (EUR)') + 18
                    w_earnings = float(w_pdf_text[w_earn_start_index:w_earn_end_index])

                w_meta_string = w_pdf_meta['CreationDate']
                w_identifier = 'Wolt'

                c.execute('INSERT INTO dated_earnings VALUES (?, ?, ?, ?, ?)',
                    (w_identifier, w_start_date_string, w_end_date_string, w_earnings, w_meta_string))

            except sqlite3.IntegrityError:
                continue

            conn.commit() 
        conn.close()

 

    def reset_db():
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS dated_earnings''')
        c.execute("""CREATE TABLE IF NOT EXISTS dated_earnings (
            platform text,
            start_date text,
            end_date text,
            earnings real,
            pdf_meta text unique
        )""")
        conn.commit()
        conn.close()



    def fetch_data(self):
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()
        date_earn_obj = c.execute("""SELECT platform,
        start_date,
        end_date,
        earnings
        FROM dated_earnings""")
        earn_data = date_earn_obj.fetchall()
        conn.close()
        return earn_data

        

    def show_smaller_table(self):
        data = EarnWindow().fetch_data()
        container = self.ids.db_container
        header_container = self.ids.db_header_container
        if data != []:
            headerButtonPlatform = TableButton(
                text='[b]'+ TaxCalc().get_lang()[2]['platform'] +'[/b]',
                markup=True)
            headerButtonWeek = TableButton(
                text='[b]'+ TaxCalc().get_lang()[2]['week'] +'[/b]',
                markup=True)
            headerButtonEarn = TableButton(
                text='[b]'+ TaxCalc().get_lang()[2]['earnings'] +'[/b]',
                markup=True)
            header_container.add_widget(headerButtonPlatform)
            header_container.add_widget(headerButtonWeek)
            header_container.add_widget(headerButtonEarn)
        for row in data:
            counter = 0
            formatted_vals = []
            platform = row[0]
            earnings = row[3]
            start_date = datetime.datetime.strptime(row[1], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(row[2], '%Y-%m-%d')
            wk_start = start_date.isocalendar()[1]
            wk_end = end_date.isocalendar()[1]

            formatted_vals.append(platform)

            if wk_start == wk_end:
                formatted_vals.append(str(wk_start))
            else:
                week_nr_string = str(wk_start) + '-' + str(wk_end)
                formatted_vals.append(week_nr_string)
            
            formatted_vals.append(earnings)
            for val in formatted_vals:
                if counter == 0:
                    tableButton = TableButton(text=str(val))
                    container.add_widget(tableButton)
                    counter += 1
                elif counter == 1:
                    tableButton = TableButtonDate(text=str(val), week = val,
                    date = row[1] + ' -\n' + row[2])
                    container.add_widget(tableButton)
                    counter += 1
                else:
                    tableButton = TableButton(text=str(val))
                    container.add_widget(tableButton)
                    counter = 0



class TableButton(Button):
    pass

class TableButtonDate(TableButton, ToggleButtonBehavior):
    def __init__(self, week, date, **kwargs):
        super().__init__(**kwargs)
        self.date = date
        self.week = week
    
    def on_state(self, widget, value):
            if value == 'down':
                self.text = self.date
            else:
                self.text = self.week


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

class AboutWindow(Screen):
    pass


class WindowManager(ScreenManager):
    pass

class TaxCalc(MDApp):

    def build(self):
        self.theme_cls.primary_palette = 'Green'

    def get_sett(self):
        with open('settings.json') as f:
            settings = json.load(f)
        return settings
    
    def get_col():
        with open('colors.json') as f:
            colors = json.load(f)
            return colors

    def get_path():
        with open('pdf_paths.json') as f:
            path = json.load(f)
            return path
    
    def get_lang(self):
        lang = TaxCalc().get_sett()['language']
        with open('language.json', encoding='utf-8') as f:
            lang_data = json.load(f)
            lang_data = lang_data[lang]
        return lang_data
    
    colors = get_col()
    path = get_path()

TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75