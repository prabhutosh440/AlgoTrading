from bokeh.plotting import figure, output_file, show
from bokeh.models import Legend, LegendItem, ColumnDataSource
from bokeh.palettes import Spectral11
from bokeh.models.tools import HoverTool

class Visualize():

    def init(self):
        pass

    def plot_multiple_line_chart(self,dataFrame, indexName, title, y_axis_label, subsetCol=None,
                                 x_axis_type="datetime", type='line'):
        '''
        dataFrame (pandas DataFrame): dataFrame containing various columns needs to be plotted and index as indexName
        indexName (str): name of the pandas dataframe index
        title (str): title of the plot
        y_axis_label (str): label for the yaxis
        subsetCol (list): List containing the columns which neeeds to be plotted
        x_axis_type (str): type of the xaxis
        '''
        p = figure(title=title, x_axis_label='date', y_axis_label=y_axis_label,
                   x_axis_type=x_axis_type, width=1000, height=500)
        numlines = 12
        mypalette = Spectral11[0:numlines]

        if subsetCol is None:
            subsetCol = dataFrame.columns

        temp = dataFrame[subsetCol]
        source = ColumnDataSource(temp.reset_index())
        items = []

        for ind, col in enumerate(temp.columns):
            r = p.line(x=indexName, y=col, color=mypalette[ind % 10], source=source)
            #         p.add_tools(HoverTool(tooltips=[('(Date, res)', '(@source['Date'], @source[col])') ]))
            items.append(LegendItem(label=col, renderers=[r]))

        legend = Legend(items=items)
        p.add_layout(legend, 'right')
        p.legend.click_policy = "hide"
        p.add_tools(HoverTool())
        show(p)
