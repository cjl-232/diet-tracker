#Maybe it'll be easier to just have a series of frames switched by button...

import re
from datetime import date, datetime, timedelta

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from CTkMessagebox import CTkMessagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.dates import DayLocator
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, StrMethodFormatter

import backend

def clicker():
    print("Clicked")

    
class WeightTrackerFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        def entry_click_event():
            dialog = ctk.CTkInputDialog(
                title = 'Append Observation',
                text = 'Enter a value (in kg):',
            )
            string = dialog.get_input()
            if re.search('^\\d+(\\.\\d*)?$', string) is not None:
                msg = CTkMessagebox(
                    master = self,
                    title = 'Confirm Weight',
                    message = ' '.join([
                        'Are you sure you wish to append an observation of',
                        string + 'kg',
                        'to the database?',
                    ]),
                    icon = 'question',
                    options = ['Confirm', 'Cancel'],
                    button_width = 200,
                    justify = 'right',
                )
                response = msg.get()
                if response == 'Confirm':
                    value = float(string)
                    backend.append_weight_observation(value)
                    self.render_weight_plot(column = 2, base_row = 1)
            else:
                CTkMessagebox(
                    master = self,
                    title = 'Invalid Value',
                    message = ' '.join([
                        "'" + string + "'",
                        'is not a valid numeric value.',
                    ]),
                    icon = 'warning',
                    options = ['Close'],
                    justify = 'right',
                )
                
        self.entry_button = ctk.CTkButton(
            master = self,
            text = 'Append Observation',
            command = entry_click_event,
        )
        self.entry_button.grid(column = 1, row = 1)
        
        def export_click_event():
            path = 'exports/weight_observations_'
            path += datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
            path += '.csv'
            pd.DataFrame(
                data = backend.get_weight_history(),
                columns = ['weight', 'timestamp'],
            ).to_csv(
                path_or_buf = path,
                index = False,
            )
            CTkMessagebox(
                master = self,
                title = 'Export Successful',
                message = 'Weight observations exported to ' + path + '.',
                icon = 'info',
                options = ['Okay'],
                button_width = 200,
                justify = 'right',
            )
        
        self.export_button = ctk.CTkButton(
            master = self,
            text = 'Export as CSV',
            command = export_click_event,
        )
        self.export_button.grid(column = 1, row = 2)
        
        self.render_weight_plot(column = 2, base_row = 1)
        
    def render_weight_plot(
        self,
        column : int,
        base_row : int = 0,
        limit : timedelta | None = None
    ):
        if limit is not None:
            start_date = (datetime.now() - limit).timestamp()
            query = 'timestamp >= @start_date'
        else:
            query = 'timestamp == timestamp'
            
        df = pd.DataFrame(
            data = backend.get_weight_history(),
            columns = ['weight', 'timestamp'],
        ).assign(
            date = lambda x: pd.to_datetime(
                x['timestamp'], unit = 's'
            ).dt.floor('d'),
        ).query(
            expr = query,
        ).groupby(
            'date'
        ).aggregate(
            {'weight': 'mean'}
        )
        
        figure = Figure(figsize = (6, 5), dpi = 100)
        axes = figure.add_subplot()
        axes.plot(
            'weight',
            'o-b', 
            data = df, 
            label = 'Weight (kg)'
        )
        axes.axhline(
            y = 63.32,
            linestyle = '--',
            color = '#00a499',
            label = 'Healthy Weight',
        )
        axes.axhline(
            y = 85.56,
            linestyle = '--',
            color = '#ffb81c',
            label = 'Overweight',
        )
        axes.axhline(
            y = 102.68,
            linestyle = '--',
            color = '#d5281b',
            label = 'Obese',
        )
        axes.set_xlim(
            left = min(df.index) - pd.tseries.offsets.Day(),
            right = max(df.index) + pd.tseries.offsets.Day()
        )
        axes.set_xticks(
            pd.date_range(
                start = min(df.index),
                end = max(df.index),
                periods = min(len(df.index), 7),
                normalize = True,
            ),
        )
        axes.set_ylim(bottom = 0, top = 120)
        
        #Clear space for a legend:
        box = axes.get_position()
        axes.set_position([
            box.x0,
            box.y0 + box.height * 0.1,
            box.width,
            box.height * 0.9,
        ])
        axes.legend(
            ncols = 4,
            loc = 'upper center',
            bbox_to_anchor = (0.5, -0.1),
            fancybox = True,
            shadow = True,
        )
            

        #TODO: Work out how to set x axis ticks at months only
        #Radio buttons for range
        #Form for adding
        axes.yaxis.set_major_formatter(StrMethodFormatter('{x:.2f}'))
        
        canvas = FigureCanvasTkAgg(figure, self)
        canvas.draw()
        canvas.get_tk_widget().grid(
            column = column,
            row = base_row,
            sticky = 'ew',
        )
        toolbar = NavigationToolbar2Tk(canvas, self, pack_toolbar = False)
        toolbar.update()
        toolbar.grid(
            column = column,
            row = base_row + 1,
            sticky = 'ew',
        )
        
        

class OverviewTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label = ctk.CTkButton(master, text = 'click me', command = clicker)
        self.label.grid(row=0, column=0, sticky = 'e')

class MealsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        #self.grid_columnconfigure(0, weight=1)
        
        self.label = ctk.CTkButton(master, text = 'click me', command = clicker)
        self.label.grid(row=0, column=0, sticky = 'e')
        
        #toolbar = NavigationToolbar2Tk(canvas, self)
        #toolbar.update()
        #canvas.get_tk_widget().pack(side = tk.TOP, fill = tk.BOTH, expand = 1)
        
class WeightTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        
        # df = pd.DataFrame(
            # data = backend.get_weight_history(),
            # columns = ['weight', 'timestamp']
        # ).assign(
            # timestamp = lambda x: pd.to_datetime(x['timestamp'], unit = 's')
        # ).set_index(
            # 'timestamp'
        # )
        # print(df)
        
        
        # figure = Figure(figsize = (5, 5), dpi = 100)
        # figure.add_subplot().plot(df)
        # plot.plot(df)
        
        # canvas = FigureCanvasTkAgg(figure, master)
        # canvas.draw()
        # canvas.get_tk_widget().grid()
        
        # toolbar = NavigationToolbar2Tk(canvas, master, pack_toolbar = False)
        # toolbar.update()
        # toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        

class TabView(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        #Aesthetic properties:
        self.configure(
            #text_color = 'pink',
        )
        self._segmented_button.configure(font = ('Arial', 20, 'bold'), )
        
        self.add('Overview')
        self.add('Meals')
        self.add('Weight')
        self.overview_tab = OverviewTab(master = self.tab('Overview'))
        self.meals_tab = MealsTab(master = self.tab('Meals'))
        self.weight_tab = WeightTab(master = self.tab('Weight'))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        backend.create_tables()
        self.title('Diet Tracker')
        self.geometry('1024x768')
        #self.grid_columnconfigure(0, weight = 1)
        #self.grid_rowconfigure(0, weight = 1)
        
        self.tab_view = WeightTrackerFrame(master = self)
        self.tab_view2 = WeightTrackerFrame(master = self)
        self.tab_view3 = WeightTrackerFrame(master = self)
        self.tab_view.grid(row=0, column=0, padx=0, pady=0, sticky = 'nw')
        #self.tab_view = TabView(master=self, anchor = 'nw', corner_radius = 10, width = 1024 + 10, height = 768 + 10)
        #self.tab_view.grid(row=0, column=0, padx=0, pady=0, stick = 'news')
        
        #self.button = ctk.CTkButton(self, command = self.button_click)
        #self.button.grid(row=0, column=0, padx=20, pady=10)
        
    def button_click(self):
        print("button click")
        
app = App()

app.mainloop()