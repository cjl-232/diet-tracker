#Need to work in dynamic dropdown creation for this, probably stored bool for 
#IS_LAST

import re
import statistics
from collections import defaultdict
from dataclasses import dataclass
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

#Defaultdict for list?

#Left side for meal selection and choices, right for calorie count & confirm


#Highly consider replacing junk arguments with self.consumables, self.unit_labels
class MealConsumablesList(ctk.CTkFrame):

    font = ('Arial', 16)
    
    #Struct of necessary components
    #Have a get_calories function that takes a dict?
    #Still use a LIST of these, not a dictionary
    @dataclass
    class Component:
        master: ctk.CTkFrame
        var: ctk.StringVar
        dropdown: ctk.CTkOptionMenu
        entry: ctk.CTkEntry
        unit_label: ctk.CTkLabel
        
        def get_calories(self, calorie_counts: dict[str, float]) -> float:
            if self.dropdown.get() != 'None' and self.entry.get() != '':
                unit_calories = calorie_counts[self.dropdown.get()]
                quantity = float(self.entry.get())
                return unit_calories * quantity
            return 0.0
            
        def update_unit_label(self, unit_labels: dict[str, str]) -> None:
            if self.dropdown.get() in unit_labels.keys():
                self.unit_label.configure(
                    text = self.unit_labels[self.dropdown.get()],
                )
            else:
                self.unit_label.configure(text = 'units')
                
        def text_var_trace_callback(self, *args):
            if re.search('^(\\d+(\\.\\d+)?)?$', self.var.get()) is not None:
                self.master.render_components()
            
                
    def get_calorie_sum(self):
        result = 0.0
        for component in self.components:
            result += component.get_calories(self.calorie_counts)
        return result
        
    def get_components(self):
        result = []
        for component in self.components[:-1]:
            result += [(
                self.identifiers[component.dropdown.get()],
                float(component.entry.get())
            )]
        return result
    
    def render_components(self, value = None) -> None:
        for component in self.components:
            component.dropdown.grid_forget()
            component.entry.grid_forget()
            component.unit_label.grid_forget()
        subset = filter(lambda x: x.dropdown.get() != 'None', self.components)
        self.components = list(subset)
        self.components += [self.create_component()]
        for index, value in enumerate(self.components):
            if value.dropdown.get() != 'None':
                value.entry.configure(state = 'normal')
                label_text = self.unit_labels[value.dropdown.get()]
            else:
                value.entry.configure(state = 'disabled')
                longest_label = max(self.unit_labels.values(), key = len)
                label_text = ' ' * len(longest_label)
            value.unit_label.configure(text = label_text)
            value.dropdown.grid(
                row = index,
                column = 1,
                padx = 5,
                pady = 5,
                sticky = 'ew',
            )
            value.entry.grid(
                row = index,
                column = 2,
                padx = 5,
                pady = 5,
                sticky = 'ew',
            )
            value.unit_label.grid(
                row = index,
                column = 3,
                padx = 5,
                pady = 5,
                sticky = 'w',
            )
        self.master.calorie_summary.configure(text = self.get_calorie_sum())
    
    def create_component(self) -> Component:
    
        def entry_callback(entry):
            return re.search('^(\\d+(\\.\\d*)?)?$', entry) is not None
            
        def entry_change_callback(var, *args):
            print(var.get())
            if re.search('^(\\d+(\\.\\d+)?)?$', var) is not None:
                self.render_components()
            
        component = self.Component(
            master = self,
            var = ctk.StringVar(),
            dropdown = ctk.CTkOptionMenu(
                master = self,
                values = ['None'] + self.consumables,
                font = self.font,
                dropdown_font = self.font,
                command = self.render_components,
            ),
            entry = ctk.CTkEntry(
                master = self,
                font = self.font,
                validate = 'key',
                validatecommand = (self.register(entry_callback), '%P'),
            ),
            unit_label = ctk.CTkLabel(
                master = self,
                anchor = 'w',
                font = self.font,
            )
        )
        component.entry.configure(textvariable = component.var)
        component.var.trace('w', component.text_var_trace_callback)
        return component
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        consumables_df = pd.DataFrame(
            data = backend.get_consumables(),
            columns = ['id', 'name', 'calories', 'unit_label'],
        )
        self.components = []
        self.consumables = sorted(consumables_df['name'].tolist())
        self.identifiers = {}
        self.calorie_counts = {}
        self.unit_labels = {}
        for index, value in enumerate(consumables_df['name'].tolist()):
            self.identifiers[value] = consumables_df['id'][index]
            self.calorie_counts[value] = consumables_df['calories'][index]
            self.unit_labels[value] = consumables_df['unit_label'][index]


class MealAppendWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Append Meal')
        self.geometry('800x600')
        
        consumables = pd.DataFrame(
            data = backend.get_consumables(),
            columns = ['id', 'name', 'calories', 'unit_label'],
        ).set_index(
            'id'
        )
        font = ('Arial', 16)
        
        self.components_frame = MealConsumablesList(
            master = self,
            border_width = 2,
        )
        
        self.summary_frame = ctk.CTkFrame(
            master = self,
            border_width = 2,
        )
        self.calorie_summary_label = ctk.CTkLabel(
            master = self.summary_frame,
            text = 'Total Calories:',
            font = font,
        )
        self.calorie_summary = ctk.CTkLabel(
            master = self.summary_frame,
            font = font,
        )
        self.confirm_button = ctk.CTkButton(
            master = self.summary_frame,
            text = 'Confirm',
            font = font,
        )
        self.components_frame.render_components()
        
        def confirm_button_event():
            components = self.components_frame.get_components()
            msg = CTkMessagebox(
                title = 'Confirm Weight',
                message = ' '.join([
                    'Are you sure you wish to append this meal',
                    'to the database?',
                ]),
                icon = 'question',
                options = ['Confirm', 'Cancel'],
                button_width = 200,
                justify = 'right',
            )
            if msg.get() == 'Confirm':
                backend.append_meal(components)
                self.master.update_dynamic_elements()
                self.destroy()
                    
                        
        self.confirm_button.configure(
            command = confirm_button_event,
        )
        
        self.components_frame.grid(
            row = 1,
            column = 1,
            padx = 5,
            pady = 5,
            sticky = 'nws',
        )
        #render_components()
        self.summary_frame.grid(
            row = 1,
            column = 2,
            padx = 5,
            pady = 5,
            sticky = 'nes',
        )
        self.calorie_summary_label.grid(
            row = 1,
            column = 1,
            padx = 10,
            pady = 5,
            sticky = 'nw',
        )
        self.calorie_summary.grid(
            row = 1,
            column = 2,
            padx = (0, 10),
            pady = 5,
            sticky = 'ne',
        )
        self.confirm_button.grid(
            row = 2,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'ew',
        )
        self.update()
            
        

class MealTrackerTab(ctk.CTkTabview):
    def update_dynamic_elements(self):
        target_intake = 2000
        df = pd.DataFrame(
            data = backend.get_meal_calories(),
            columns = ['calories', 'timestamp'],
        ).assign(
            date = lambda x: pd.to_datetime(
                x['timestamp'], unit = 's'
            ).dt.floor('d'),
        ).groupby(
            'date',
        ).aggregate(
            {'calories': 'sum'},
        )
        
        #Update labels:
        today = pd.to_datetime('today').normalize()
        if today in df.index:
            intake_today = df.loc[today]['calories']
        else:
            intake_today = 0
        if len(df) != 0:
            average_intake = statistics.mean(df['calories'])
        else:
            average_intake = 0
        self.report_1.configure(
            text = f'{intake_today:,.0f} of {target_intake:,.0f}',
        )
        self.report_2.configure(
            text = f'{average_intake:,.0f} of {target_intake:,.0f}',
        )

        #Update graph:
        self.figure.clear()
        axes = self.figure.add_subplot()
        axes.plot(
            'calories',
            'o-b', 
            data = df, 
            label = 'Calories'
        )
        axes.axhline(
            y = target_intake,
            linestyle = '--',
            color = 'red',
            label = 'Target Limit',
        )
        if len(df) != 0:
            axes.set_xlim(
                left = min(df.index) - pd.tseries.offsets.Day(),
                right = max(df.index) + pd.tseries.offsets.Day()
            )
            axes.set_xticks(
                pd.date_range(
                    start = min(df.index),
                    end = max(df.index),
                    periods = min(len(df.index), 5),
                    normalize = True,
                ),
            )
        axes.set_ylim(bottom = 0)
        axes.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
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
        
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.meal_append_window = None
        
        self.controls_frame = ctk.CTkFrame(
            master = master,
            border_width = 2,
        )
        controls_font = ('Arial', 16)
        
        self.reports_header_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Intake Reports:',
            font = controls_font + ('bold',),
        )
        self.report_1_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = "Today's intake:",
            font = controls_font,
        )
        self.report_2_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Average daily intake:',
            font = controls_font,
        )
        self.report_1 = ctk.CTkLabel(
            master = self.controls_frame,
            font = controls_font,
        )
        self.report_2 = ctk.CTkLabel(
            master = self.controls_frame,
            font = controls_font,
        )
        self.queries_header_label = ctk.CTkLabel(
            master = self.controls_frame,
            text = 'Queries:',
            font = controls_font + ('bold',)
        )
        self.append_meal_button = ctk.CTkButton(
            master = self.controls_frame,
            text = 'Append Meal',
            font = controls_font,
        )
        self.append_consumable_button = ctk.CTkButton(
            master = self.controls_frame,
            text = 'Define Consumable',
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
        self.reports_header_label.grid(
            row = 1,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'nw',
        )
        self.report_1_label.grid(
            row = 2,
            column = 1,
            padx = 10,
            pady = (0, 5),
            sticky = 'nw',
        )
        self.report_2_label.grid(
            row = 3,
            column = 1,
            padx = 10,
            pady = (0, 5),
            sticky = 'nw',
        )
        self.report_1.grid(
            row = 2,
            column = 2,
            padx = (0, 10),
            pady = (0, 5),
            sticky = 'ne',
        )
        self.report_2.grid(
            row = 3,
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
        self.append_meal_button.grid(
            row = 6,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'ew',
        )
        self.append_consumable_button.grid(
            row = 7,
            column = 1,
            columnspan = 2,
            padx = 10,
            pady = 5,
            sticky = 'ew',
        )
        self.export_button.grid(
            row = 8,
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
        
        self.update_dynamic_elements()
        
        def append_consumable_button_event():
            taken_names = pd.DataFrame(
                data = backend.get_consumables(),
                columns = ['id', 'name', 'calories', 'unit_label'],
            )['name']
            name = ctk.CTkInputDialog(
                title = 'Define Consumable',
                text = 'Enter a name:',
            ).get_input()
            if name is None:
                return
            elif taken_names.str.contains('^' + name + '%').any():
                CTkMessagebox(
                    title = 'Invalid Value',
                    message = "The name '" + name + "' is already taken.",
                    icon = 'warning',
                    options = ['Close'],
                    justify = 'right',
                )
                return
            calorie_count = ctk.CTkInputDialog(
                title = 'Define Consumable',
                text = 'Enter a (per-unit) calorie value:',
            ).get_input()
            if calorie_count is None:
                return
            elif re.search('^\\d+(\\.\\d*)?$', calorie_count) is None:
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
                return
            unit_label = ctk.CTkInputDialog(
                title = 'Define Consumable',
                text = 'Enter a unit label, or leave blank:',
            ).get_input()
            if unit_label is None:
                return
            elif unit_label == '':
                unit_label = 'unit'
            unit_label = unit_label.lower()
            
            confirmation_choice = CTkMessagebox(
                title = 'Confirm Weight',
                message = ' '.join([
                    'Are you sure you wish to append consumable',
                    "'" + name.lower() + "'",
                    'with',
                    calorie_count,
                    'calories per unit',
                    "and unit label '" + unit_label + "'",
                    'to the database?',
                ]),
                icon = 'question',
                options = ['Confirm', 'Cancel'],
                button_width = 200,
                justify = 'right',
            ).get()
            if confirmation_choice == 'Confirm':
                calorie_count = float(calorie_count)
                backend.append_consumable(name, calorie_count, unit_label)
            
        self.append_consumable_button.configure(
            command = append_consumable_button_event,
        )
        
        def append_meal_button_event():
            if self.meal_append_window is None or not self.meal_append_window.winfo_exists():
                self.meal_append_window = MealAppendWindow(master = self)
            self.meal_append_window.focus()
            
        self.append_meal_button.configure(
            command = append_meal_button_event,
        )
        
        def export_button_event():
            path = 'exports/calorie_intakes_'
            path += datetime.now().strftime('%Y.%m.%d_%H.%M.%S')
            path += '.csv'
            pd.DataFrame(
                data = backend.get_meal_calories(),
                columns = ['calories', 'timestamp'],
            ).assign(
                date = lambda x: pd.to_datetime(
                    x['timestamp'], unit = 's'
                ).dt.floor('d'),
            ).groupby(
                'date',
            ).aggregate(
                {'calories': 'sum'},
            ).reset_index(
            ).to_csv(
                path_or_buf = path,
                index = False,
            )
            CTkMessagebox(
                title = 'Export Successful',
                message = 'Daily calorie intake exported as ' + path + '.',
                icon = 'info',
                options = ['Okay'],
                button_width = 200,
                justify = 'right',
            )
        self.export_button.configure(command = export_button_event)
    
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
                    periods = min(len(df.index), 5),
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
            ).assign(
                date = lambda x: pd.to_datetime(
                    x['timestamp'], unit = 's'
                ).dt.floor('d'),
            ).groupby(
                'date',
            ).aggregate(
                {'weight': 'mean'},
            ).reset_index(
            ).to_csv(
                path_or_buf = path,
                index = False,
            )
            CTkMessagebox(
                title = 'Export Successful',
                message = 'Weight observations saved as ' + path + '.',
                icon = 'info',
                options = ['Okay'],
                button_width = 200,
                justify = 'right',
            )
        self.export_button.configure(command = export_button_event)

    
class OverviewTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label = ctk.CTkButton(master, text = 'click me')
        self.label.grid(row=0, column=0, sticky = 'e')

class MealsTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        #self.grid_columnconfigure(0, weight=1)
        
        self.label = ctk.CTkButton(master, text = 'click me')
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
        self.meals_tab = MealTrackerTab(master = self.tab('Meals'))
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