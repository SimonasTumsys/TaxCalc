from kivymd.uix.screen import Screen
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window
from kivymd.toast import toast
from kivy.uix.button import Button
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.label import Label
from kivymd.uix.label import MDIcon
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
import calendar
import os
import json
import pdfplumber
import datetime
import sqlite3
from kivy.utils import platform
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

class CalculatedLayout(GridLayout):
    pass
    
class MainWindow(Screen):
    pass

class CalcWindow(Screen):
    def add_calcLayoutWidget(self):
        calcLayout = CalculatedLayout()
        self.ids.calc_container.add_widget(calcLayout)
        
    with open('app_settings.json', 'r') as f:
        settings = json.load(f)

    def calculate(self, total_earn_arg, total_costs_arg, settings = settings):
        psd_relative_rate = 0.0698
        pension_rate = float(settings['pension'])

        if settings['ssi_relief'] == False:
            vsd_rate = 0.1252
        else:
            vsd_rate = 0

        if self.ids.total_earnings.text != '':
            total_earn = float(self.ids.total_earnings.text)
        else:
            total_earn = float(total_earn_arg)
        if settings['spend_30_percent'] == True:
            total_costs = total_earn*0.3
        else:
            if self.ids.costs.text != '':
                total_costs = float(self.ids.costs.text)
            else:
                try:
                    try:
                        total_costs = float(total_costs_arg.text)
                    except AttributeError:
                        total_costs = float(total_costs_arg)
                except ValueError:
                    total_costs = 0

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
        try:
            total_tax_perc = round(total_tax/total_earn*100, 2)
        except ZeroDivisionError:
            total_tax_perc = 0

        output = [total_earn, profit, total_costs, 
        psd_tax, vsd_tax, pension_tax, gpm_tax, 
        nett_earn, total_tax]

        output = ['€{:.2f}'.format(x) for x in output]
        output.append(str(total_tax_perc))
        return output
    
    def useless(self):
        pass

    def cost_toaster(self, settings = settings):
        if self.ids.costs.text == '' and settings['spend_30_percent'] == False:
            toast("Please input costs")

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

        self.file_manager.show(path)
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
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
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
    
    def reset_db(self) -> None:
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

        with open('pdf_paths.json') as f:
            pdf_paths = json.load(f)
            pdf_paths['main_path'] = '/'
        return

    def reset_path(self):
        with open('pdf_paths.json', 'r') as f:
            pdf_paths = json.load(f)
            pdf_paths['main_path'] = '/'

        with open('pdf_paths.json', 'w') as f:
            json.dump(pdf_paths, f, indent=2)
        

        self.children[5].children[1].children[0].ids.path_label.hint_text = '/'



    def fetch_data(self):
        conn = sqlite3.connect('pdf_data.db')
        c = conn.cursor()
        date_earn_obj = c.execute("""SELECT platform,
        start_date,
        end_date,
        earnings
        FROM dated_earnings ORDER BY start_date""")
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
                        tableButton = TableButtonDateWeek(text=str(val), week = val,
                        date = row[1] + ' -\n' + row[2])
                        container.add_widget(tableButton)
                        counter += 1
                    else:
                        tableButton = TableButton(text=str(val))
                        container.add_widget(tableButton)
                        counter = 0



class TableButton(Button):
    pass

class TableButtonDateWeek(TableButton, ToggleButtonBehavior):
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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset_picker_json(self):
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)
        picker_json['months'] = []
        picker_json['years'] = []
        picker_json['platform'] = 'all'
        with open('date_picker.json', 'w') as f:
            json.dump(picker_json, f, indent=2)

    def load_date_picker(self):
        self.set_years()

        for i in range(1, 13):
            if i < 10:
                self.ids.date_picker_month_container.add_widget(DatePickerButton(
                    text='0' + str(i), nr=i, type='month'))
            else:
                self.ids.date_picker_month_container.add_widget(DatePickerButton(
                    text=str(i), nr=i, type='month'))


    def set_years(self):
        self.reset_picker_json()
        data = EarnWindow().fetch_data()
        current_year = int(datetime.datetime.now().date().strftime("%Y"))
        years = [current_year]
        if data != []:
            for row in data:
                start_date_db = datetime.datetime.strptime(row[1], '%Y-%m-%d').date().year
                end_date_db = datetime.datetime.strptime(row[2], '%Y-%m-%d').date().year
                if start_date_db not in years:
                    years.append(start_date_db)
                if end_date_db not in years:
                    years.append(end_date_db)
            years.sort(reverse=True)
            for year in years[-5:]:
                self.ids.date_picker_year_container.add_widget(
                    DatePickerButton(text=str(year), nr=year, type='year')
                )
        else:
            self.ids.date_picker_year_container.add_widget(
                    DatePickerButton(text=str(current_year), nr=current_year, type='year')
                )

    def reset_button(self, button):
        button.back_color = get_color_from_hex(TaxCalc().colors['bg_main'])
        button.color = get_color_from_hex(TaxCalc().colors['font_black'])
        button.state = 'normal'


    def reset_color(self):
        month_container = self.ids.date_picker_month_container.children
        year_container = self.ids.date_picker_year_container.children
        if month_container != []:
            for button in month_container:
                self.reset_button(button)
        for button in year_container:
            self.reset_button(button)
        

    def make_date_range_string(self):
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)
        
        if picker_json['years'] != []:
            start_year_str = str(min(picker_json['years']))
            end_year_str = str(max(picker_json['years']))
            start_year_int = min(picker_json['years'])
            end_year_int = max(picker_json['years'])
            if picker_json['months'] != []:
                start_month_int = min(picker_json['months'])
                if start_month_int < 10:
                    start_month_str = '0' + str(start_month_int)
                else:
                    start_month_str = str(start_month_int)

                end_month_int = max(picker_json['months'])
                if end_month_int < 10:
                    end_month_str = '0' + str(end_month_int)
                else:
                    end_month_str = str(end_month_int)
            else:
                start_month_int = 1
                end_month_int = 12
                start_month_str = '01'
                end_month_str = '12'
 
            start_date_days = str(max(calendar.monthcalendar(
                start_year_int, start_month_int)[-1]))
            end_date_days = str(max(calendar.monthcalendar(
                end_year_int, end_month_int)[-1]))

            start_date_str = start_year_str + '-' + start_month_str + '-' + '01'
            end_date_str = end_year_str + '-' + end_month_str + '-' + end_date_days


            return [start_date_str, end_date_str]


    def generate_by_date(self):
        data = EarnWindow().fetch_data()
        date_range = self.make_date_range_string()
        self.ids.main_stat_container.clear_widgets()
        self.ids.platform_toggle_container.clear_widgets()
        if data != [] and date_range != None:
            self.add_platform_buttons()
            togglableStatLayout = TogglableStatLayout(data, date_range)
            self.ids.main_stat_container.add_widget(togglableStatLayout)
        elif data == []:
            data = EarnWindow().fetch_data()
            if data == []:
                toast(TaxCalc().get_lang()[3]['no_pdfs'])
            else:
                self.add_platform_buttons()
                togglableStatLayout = TogglableStatLayout(data, date_range)
                self.ids.main_stat_container.add_widget(togglableStatLayout)
        elif date_range == None:
            toast(TaxCalc().get_lang()[3]['pls_date'])

    def add_platform_buttons(self):
        self.ids.platform_toggle_container.clear_widgets()
        self.ids.platform_toggle_container.add_widget(PlatformButton(
            type='bolt',text='[b]Bolt[/b]'))
        self.ids.platform_toggle_container.add_widget(PlatformButton(
            type='wolt',text='[b]Wolt[/b]'))
        self.ids.platform_toggle_container.add_widget(PlatformButton(
            type='all',text='[b]' + TaxCalc().get_lang()[3]['all']+ '[/b]'))

    def change_by_date(self):
        data = EarnWindow().fetch_data()
        try:
            main_stat_container = self.ids.main_stat_container
            date_button = main_stat_container.children[0].ids.date_button
            earn_button = main_stat_container.children[0].ids.earn_button
            tax_button = main_stat_container.children[0].ids.tax_button

            stat_layout = main_stat_container.children[0]

            if len(main_stat_container.children) != 0:
                date_range = self.make_date_range_string()
                results = stat_layout.extract_earnings_dates(data, date_range)
                main_stat_container.children[0].change_stat_button_text(
                    results[0], results[1], results[2], 
                        date_button, earn_button, tax_button)
        except TypeError:
            toast(TaxCalc().get_lang()[3]['pls_date'])


class StatLabel(Label):
    def __init__(self, type, text, **kwargs):
        super().__init__(**kwargs)
        self.type = type
        self.text = text


class PlatformButton(TableButton, ToggleButtonBehavior):
    def __init__(self, type, text, **kwargs):
        super().__init__(**kwargs)
        self.group = 'platform'
        self.type = type
        self.text = text
        self.markup = True
        self.allow_no_selection = False
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)
        if type == picker_json['platform']:
            self.state = 'down'
            

    def on_state(self, widget, value):
        data = EarnWindow().fetch_data()
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)

        if self.state == 'down':
            picker_json['platform'] = self.type
            with open('date_picker.json', 'w') as f:
                json.dump(picker_json, f, indent=2)
            
            if self.parent != None:
                main_stat_container = self.parent.parent.ids.main_stat_container
                tax_stat_container = self.parent.parent.ids.tax_stat_container

                if len(main_stat_container.children) != 0:
                    date_button = main_stat_container.children[0].ids.date_button
                    earn_button = main_stat_container.children[0].ids.earn_button
                    tax_button = main_stat_container.children[0].ids.tax_button

                    stat_layout = main_stat_container.children[0]

                    date_range = self.parent.parent.make_date_range_string()
                    if data != []:
                        results = stat_layout.extract_earnings_dates(data, date_range)
                    else:
                        data = EarnWindow().fetch_data()
                        results = stat_layout.extract_earnings_dates(data, date_range)
                    try:
                        main_stat_container.children[0].change_stat_button_text(
                            results[0], results[1], results[2], 
                                date_button, earn_button, tax_button)
                    except TypeError:
                        toast(TaxCalc().get_lang()[3]['pls_date'])
                
                if len(tax_stat_container.children) != 0:
                    earnings = float(earn_button.text[1:])
                    taxes = (CalcWindow().calculate(earnings, (earnings*0.3)))[3:8]
                    tax_stat_container.children[0].ids.psd_button.text = str(taxes[0])
                    tax_stat_container.children[0].ids.vsd_button.text = str(taxes[1])
                    tax_stat_container.children[0].ids.pension_button.text = str(taxes[2])
                    tax_stat_container.children[0].ids.gpm_button.text = str(taxes[3])
                    tax_stat_container.children[0].ids.net_button.text = str(taxes[4])



class DatePickerButton(TableButton, ToggleButtonBehavior):

    def __init__(self, text, nr, type, **kwargs):
        super().__init__(**kwargs)
        
        self.text = '[b]' + text + '[/b]'
        self.nr = nr
        self.type = type
        if self.type == 'month':
            self.group = 'first'
            self.text = self.get_month()
        else:
            self.group = 'third'

        if self.type == 'year':
            self.markup = True

    def get_month(self):
        if self.nr == 1:
            return TaxCalc().get_lang()[5]['1']
        elif self.nr == 2:
            return TaxCalc().get_lang()[5]['2']
        elif self.nr == 3:
            return TaxCalc().get_lang()[5]['3']
        elif self.nr == 4:
            return TaxCalc().get_lang()[5]['4']
        elif self.nr == 5:
            return TaxCalc().get_lang()[5]['5']
        elif self.nr == 6:
            return TaxCalc().get_lang()[5]['6']
        elif self.nr == 7:
            return TaxCalc().get_lang()[5]['7']
        elif self.nr == 8:
            return TaxCalc().get_lang()[5]['8']
        elif self.nr == 9:
            return TaxCalc().get_lang()[5]['9']
        elif self.nr == 10:
            return TaxCalc().get_lang()[5]['10']
        elif self.nr == 11:
            return TaxCalc().get_lang()[5]['11']
        elif self.nr == 12:
            return TaxCalc().get_lang()[5]['12']

    def change_color(self, json):
        picker_json = json
        try:
            if len(picker_json['months']) > 1:
                    for button in self.parent.children:    
                        if button.nr > min(picker_json['months']) and button.nr < max(
                            picker_json['months']):
                            button.back_color = get_color_from_hex(TaxCalc().colors['btn_side'])
                            button.color = get_color_from_hex(TaxCalc().colors['font'])
                        else:
                            button.back_color = get_color_from_hex(TaxCalc().colors['bg_main'])
                        
            else:
                if self.parent.children != None:
                    for button in self.parent.children:
                        button.back_color = get_color_from_hex(TaxCalc().colors['bg_main'])
                        button.color = get_color_from_hex(TaxCalc().colors['font_black'])
        except AttributeError:
            pass

    def on_state(self, widget, value):
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)

        if self.state == 'down':
            self.change_color(picker_json)
            if self.type == 'month' and len(picker_json['months']) < 2:
                if self.nr not in picker_json['months']:
                    picker_json['months'].append(self.nr)
            elif self.type == 'year' and len(picker_json['years']) < 2:
                if self.nr not in picker_json['years']:
                    picker_json['years'].append(self.nr)
            elif self.type == 'month' and len(picker_json['months']) >= 2:
                self.state = 'normal'
            elif self.type == 'year' and len(picker_json['years']) >= 2:
                self.state = 'normal'
            if self.type == 'month' and len(picker_json['months']) <= 1:
                self.group = 'second'
            elif self.type == 'year' and len(picker_json['years']) <= 1:
                self.group = 'fourth'

            self.change_color(picker_json)
            with open('date_picker.json', 'w') as f:
                json.dump(picker_json, f, indent=2)


        elif self.state == 'normal':
            if self.type == 'month':
                if self.nr in picker_json['months']:
                    picker_json['months'].remove(self.nr)
                self.group = 'first'
            else:
                if self.nr in picker_json['years']:
                    picker_json['years'].remove(self.nr)
                self.group = 'third'

            self.change_color(picker_json)
            with open('date_picker.json', 'w') as f:
                json.dump(picker_json, f, indent=2)



class TogglableStatLayout(GridLayout):
    def __init__(self, data, date_range, **kwargs):
        super().__init__(**kwargs)
        date_button = self.ids.date_button
        earn_button = self.ids.earn_button
        tax_button = self.ids.tax_button

        earnings = self.extract_earnings_dates(data, date_range)[0]
        start_date = self.extract_earnings_dates(data, date_range)[1]      
        end_date = self.extract_earnings_dates(data, date_range)[2]  
        self.change_stat_button_text(earnings, start_date, end_date, 
            date_button, earn_button, tax_button)
        

    def extract_earnings_dates(self, data, date_range):
        earnings = 0
        with open('date_picker.json', 'r') as f:
            picker_json = json.load(f)
        
        try:
            start_date = datetime.datetime.strptime(date_range[0], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(date_range[-1], '%Y-%m-%d').date()
            for row in data:
                end_date_db = datetime.datetime.strptime(row[2], '%Y-%m-%d').date()

                if start_date <= end_date_db and end_date >= end_date_db:
                    if picker_json['platform'] == 'all':
                        earnings += row[3]
                    elif picker_json['platform'] == 'bolt':
                        if row[0] == 'Bolt Food':
                            earnings += row[3]
                        else:
                            earnings += 0
                    elif picker_json['platform'] == 'wolt':
                        if row[0] == 'Wolt':
                            earnings += row[3]
                        else:
                            earnings += 0
        
            return [earnings, start_date, end_date]
        except TypeError:
            pass


    def change_stat_button_text(self, earnings, start_date, end_date, 
            date_button, earn_button, tax_button) -> None:

        date_button.text = str(start_date) + ' - ' + str(end_date)
        earn_button.text = "€" + str(round(earnings, 2))
        calcWindow = CalcWindow()
        taxes = calcWindow.calculate(earnings, (earnings*0.3))[8]
        tax_button.markup = True
        tax_button.text = str(taxes) + '[size=10sp] ...[/size]'
        

    def tax_button_press(self) -> None:
        tax_stat_container = self.parent.parent.ids.tax_stat_container

        if len(tax_stat_container.children) == 0:
            isanimate = True
        else:
            isanimate = False
        
        tax_stat_container.clear_widgets()
        if self.ids.earn_button.text != '€0.00' and len(
            tax_stat_container.children) == 0:
            earnings = self.ids.earn_button.text
            earnings = float(earnings[1:])
            
            taxes = (CalcWindow().calculate(earnings, (earnings*0.3)))[3:8]
            togglable_tax_layout = TogglableTaxLayout(taxes, isanimate)
            tax_stat_container.clear_widgets()
            tax_stat_container.add_widget(
                togglable_tax_layout)
                
        else:
            pass
    
    def clear_tax_container(self) -> None:
        self.parent.parent.ids.tax_stat_container.clear_widgets()

    def useless(self):
        pass


class TogglableTaxLayout(GridLayout):
 
    def animate_me(self) -> None:
        animate = Animation(opacity = 1)
        animate.start(self)
        
    def __init__(self, taxes, isanimate, **kwargs) -> None:
        super().__init__(**kwargs)
        self.ids.psd_button.text = str(taxes[0])
        self.ids.vsd_button.text = str(taxes[1])
        self.ids.pension_button.text = str(taxes[2])
        self.ids.gpm_button.text = str(taxes[3])
        self.ids.net_button.text = str(taxes[4])
        if isanimate == True:
            self.opacity = 0
            self.animate_me()
        else:
            self.opacity = 1
        

class SettWindow(Screen):
    def save_settings(self) -> None:
        with open('app_settings.json', 'r') as f:
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

        if self.ids.ssi_r_button_yes.state == 'down':
            settings['ssi_relief'] = True
        else:
            settings['ssi_relief'] = False

        with open('app_settings.json', 'w') as f:
            json.dump(settings, f, indent=2)


class AboutWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

class TaxCalc(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"


    def get_sett():
        with open('app_settings.json') as f:
            settings = json.load(f)
        return settings
    
    def get_col():
        with open('app_colors.json') as f:
            colors = json.load(f)
            return colors

    def get_path():
        with open('pdf_paths.json') as f:
            path = json.load(f)
            return path
    
    def get_lang(self, lang = get_sett()['language']):
        with open('language.json', encoding='utf-8') as f:
            lang_data = json.load(f)
            lang_data = lang_data[lang]
        return lang_data
    
    settings = get_sett()
    colors = get_col()
    path = get_path()



TaxCalc().run()


## python main.py -m screen:note2,portrait,scale=.75