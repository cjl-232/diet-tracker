import re
from datetime import date, datetime, timedelta

import customtkinter as ctk
import matplotlib.pyplot as plt
import pandas as pd
from CTkMessagebox import CTkMessagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter

import backend
    
class WeightTrackerTab(ctk.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        target_1 = 102.68
        target_2 = 85.56
        target_3 = 63.32
        
        self.controls_frame = ctk.CTkFrame(
            master = master,
            border_width = 2,
        )
        controls_font = ('Arial', 16)
        
        self.progress_header_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Progress:',
            font = controls_font + ('bold',),
        )
        self.progress_1_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Target 1 Progress:',
            font = controls_font,
        )
        self.progress_2_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Target 2 Progress:',
            font = controls_font,
        )
        self.progress_3_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Target 3 Progress:',
            font = controls_font,
        )
        self.progress_1 = ctk.CTkLabel(
            master = self.controls_frame,
            font = controls_font,
        )
        self.progress_2 = ctk.CTkLabel(
            master = self.controls_frame,
            font = controls_font,
        )
        self.progress_3 = ctk.CTkLabel(
            master = self.controls_frame,
            font = controls_font,
        )
        self.queries_header_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Queries:',
            font = controls_font + ('bold',)
        )
        self.append_button = ctk.CTkButton(
            master = self.controls_frame,
            text = 'Append Observation',
            font = controls_font,
        )
        self.export_button = ctk.CTkButton(
            master = self.controls_frame,
            text = 'Export as CSV',
            font = controls_font,
        )
        
        self.plot_frame = ctk.CTkFrame(
            master = master,
            border_width = 2,
        )
        self.figure = Figure(figsize = (7, 6), dpi = 100)
        self.figure.patch.set_fill('transparent')
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_frame)
        self.toolbar = NavigationToolbar2Tk(
            canvas = self.canvas, 
            window = self.plot_frame,
            pack_toolbar = False,
        )
        
        self.controls_frame.grid(
            row = 1,
            column = 1,
            padx = 5,
            sticky = 'nws',
        )
        self.progress_header_label.grid(
            row = 1,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'nw',
        )
        self.progress_1_label.grid(
            row = 2,
            column = 1,
            padx = 10,
            pady = (0, 5),
            sticky = 'nw',
        )
        self.progress_2_label.grid(
            row = 3,
            column = 1,
            padx = 10,
            pady = (0, 5),
            sticky = 'nw',
        )
        self.progress_3_label.grid(
            row = 4,
            column = 1,
            padx = 10,
            pady = (0, 5),
            sticky = 'nw',
        )
        self.progress_1.grid(
            row = 2,
            column = 2,
            padx = (0, 10),
            pady = (0, 5),
            sticky = 'ne',
        )
        self.progress_2.grid(
            row = 3,
            column = 2,
            padx = (0, 10),
            pady = (0, 5),
            sticky = 'ne',
        )
        self.progress_3.grid(
            row = 4,
            column = 2,
            padx = (0, 10),
            pady = (0, 5),
            sticky = 'ne',
        )
        self.queries_header_label.grid(
            row = 5,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'nw',
        )
        self.append_button.grid(
            row = 6,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'ew',
        )
        self.export_button.grid(
            row = 7,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'ew',
        )
        
        self.plot_frame.grid(
            row = 1,
            column = 2,
            padx = 5,
            sticky = 'nes',
        )
        self.canvas.get_tk_widget().grid(
            row = 1,
            column = 1,
            padx = 5,
            pady = (5, 0),
            sticky = 'ew',
        ) 
        self.toolbar.grid(
            row = 2,
            column = 1,
            padx = 5,
            pady = (0, 5),
            sticky = 'ew',
        )
        
        def update_dynamic_elements():
            df = pd.DataFrame(
                data = backend.get_weight_history(),
                columns = ['weight', 'timestamp'],
            ).assign(
                date = lambda x: pd.to_datetime(
                    x['timestamp'], unit = 's'
                ).dt.floor('d'),
            ).groupby(
                'date',
            ).aggregate(
                {'weight': 'mean'},
            )
            
            #Update labels:
            start_value = df['weight'][df.index.min()]
            latest_value = df['weight'][df.index.max()]
            loss_to_date = start_value - latest_value
            def update_progress_label(label, new_value):
                label.configure(
                   text = f'{min(new_value, 1):.1%}',
                )
            argument_sets = [
                (self.progress_1, loss_to_date / (start_value - target_1)),
                (self.progress_2, loss_to_date / (start_value - target_2)),
                (self.progress_3, loss_to_date / (start_value - target_3)),
            ]
            for args in argument_sets:
                update_progress_label(args[0], args[1])

            #Update graph:
            self.figure.clear()
            axes = self.figure.add_subplot()
            axes.plot(
                'weight',
                'o-b', 
                data = df, 
                label = 'Weight (kg)'
            )
            axes.axhline(
                y = target_3,
                linestyle = '--',
                color = '#00a499',
                label = 'Minimum Healthy Weight',
            )
            axes.axhline(
                y = target_2,
                linestyle = '--',
                color = '#ffb81c',
                label = 'Overweight',
            )
            axes.axhline(
                y = target_1,
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
            axes.yaxis.set_major_formatter(StrMethodFormatter('{x:.2f}'))
            box = axes.get_position()
            axes.set_position([
                box.x0,
                box.y0 + box.height * 0.1,
                box.width,
                box.height * 0.9,
            ])
            axes.legend(
                ncols = 2,
                loc = 'upper center',
                bbox_to_anchor = (0.5, -0.075),
                fancybox = True,
                shadow = True,
            )
            
            self.canvas.draw()
            self.toolbar.update()
        update_dynamic_elements()
        
        def append_button_event():
            dialog = ctk.CTkInputDialog(
                title = 'Append Observation',
                text = 'Enter a value (in kg):',
            )
            string = dialog.get_input()
            if re.search('^\\d+(\\.\\d*)?$', string) is not None:
                msg = CTkMessagebox(
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
                    update_dynamic_elements()
            else:
                CTkMessagebox(
                    title = 'Invalid Value',
                    message = ' '.join([
                        "'" + string + "'",
                        'is not a valid numeric value.',
                    ]),
                    icon = 'warning',
                    options = ['Close'],
                    justify = 'right',
                )
        self.append_button.configure(command = append_button_event)
        
        def export_button_event():
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
                title = 'Export Successful',
                message = 'Weight observations exported to ' + path + '.',
                icon = 'info',
                options = ['Okay'],
                button_width = 200,
                justify = 'right',
            )
        self.export_button.configure(command = export_button_event)

    
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
        self.weight_tab = WeightTrackerTab(master = self.tab('Weight'))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        backend.create_tables()
        self.title('Diet Tracker')
        self.geometry('1024x768')
        #self.grid_columnconfigure(0, weight = 1)
        #self.grid_rowconfigure(0, weight = 1)
        
        #self.tab_view = WeightTrackerFrame(master = self)
        #self.tab_view2 = WeightTrackerFrame(master = self)
        #self.tab_view3 = WeightTrackerFrame(master = self)
        #self.tab_view.grid(row=0, column=0, padx=0, pady=0, sticky = 'nw')
        self.tab_view = TabView(master=self, anchor = 'nw')#, corner_radius = 10, width = 1024 + 10, height = 768 + 10)
        self.tab_view.grid(row=0, column=0, padx=0, pady=0, stick = 'news')
        
        #self.tab_view.add('Weight')
        
        #self.button = ctk.CTkButton(self, command = self.button_click)
        #self.button.grid(row=0, column=0, padx=20, pady=10)
        
    def button_click(self):
        print("button click")
        
app = App()

app.mainloop()