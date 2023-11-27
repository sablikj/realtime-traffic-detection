from dash import dcc, html
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import dash_bootstrap_components as dbc
import os
import cv2
from utils import getTitle


title = getTitle()
def getBG():
    path = './application/resources/canvas_bg.png'
    # For creating detection polygons and mask
    if os.path.exists(path):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        fig = px.imshow(img)
        fig.update_layout(coloraxis_showscale=False, paper_bgcolor='#1e1e1e', autosize=True, dragmode="drawclosedpath")
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_layout(
            newshape=dict(fillcolor="red", opacity=0.5, line=dict(color="red", width=4)),
        )
    else:
        fig = {}
   
    return fig

config = {
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawclosedpath",
        "drawcircle",
        "drawrect",
        "eraseshape",
    ],
}

def layout():
    layout = dbc.Container(
        children=[
            dcc.Location(id='url', refresh=True),
            # Main modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Settings"), close_button=False),                    
                    dbc.ModalBody(children=[
                        # URL
                        html.Div(children=[
                            html.Div(children=[
                                html.P('Webcam URL' ),
                                ],
                                style={'display': 'inline-block', 'width': '25%'}
                            ),                   
                            html.Div(children=[                            
                                dcc.Input(
                                    placeholder='Enter a webcam URL...',
                                    type='text',
                                    id='urlInput',
                                    value=os.getenv('CAM_URL'),
                                    debounce=True,
                                    style={'width': '100%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),
                        html.Hr(),
                        
                        # DATABASE - Server
                        html.Div(children=[
                            html.Div(children=[
                                html.P('DB Server' ),
                                ],
                                style={'display': 'inline-block', 'width': '25%'}
                            ),                   
                            html.Div(children=[                            
                                dcc.Input(
                                    placeholder='Enter a database server...',
                                    type='text',
                                    id='serverInput',
                                    value=os.getenv('DB_SERVER'),
                                    debounce=True,
                                    style={'width': '100%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),

                        # DATABASE - Name
                        html.Div(children=[
                            html.Div(children=[
                                html.P('DB Name' ),
                                ],
                                style={'display': 'inline-block', 'width': '25%'}
                            ),                   
                            html.Div(children=[                            
                                dcc.Input(
                                    placeholder='Enter a database name...',
                                    type='text',
                                    id='nameInput',
                                    value=os.getenv('DB_DATABASE'),
                                    debounce=True,
                                    style={'width': '100%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),
                        # DATABASE - User
                        html.Div(children=[
                            html.Div(children=[
                                html.P('DB User' ),
                                ],
                                style={'display': 'inline-block', 'width': '25%'}
                            ),                   
                            html.Div(children=[                            
                                dcc.Input(
                                    placeholder='Enter a database user name...',
                                    type='text',
                                    id='usernameInput',
                                    value=os.getenv('DB_USERNAME'),
                                    debounce=True,
                                    style={'width': '100%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),
                        # DATABASE - Password
                        html.Div(children=[
                            html.Div(children=[
                                html.P('DB Password' ),
                                ],
                                style={'display': 'inline-block', 'width': '25%'}
                            ),                   
                            html.Div(children=[                            
                                dcc.Input(
                                    placeholder='Enter an user password...',
                                    type='password',
                                    id='passwordInput',
                                    value=os.getenv('DB_PASSWORD'),
                                    debounce=True,
                                    style={'width': '100%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),                        
                    dbc.ModalFooter(children=[                        
                        html.Button("Done", id="SettingsModalClose",style={'justify': 'right', 'marginTop': '15px'}),
                        ],
                        style={'display': 'flex', 'justifyContent': 'middle'}
                    ),                     
                    ]),
                ],
                id="settingsModal",
                size="md",
                is_open=False                
            ),
            # Polygon modal                  
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Create detection areas"), close_button=False),                    
                    dbc.ModalBody(children=[
                        # POLYGON NAME
                        html.Div(children=[
                            html.Div(children=[
                                html.P('Area Name', style={'textAlign':'right', 'marginRight':'2rem'}),
                                ],
                                style={'display': 'inline-block', 'width': '25%', 'horizontalAlign': 'middle'}
                            ),                   
                            html.Div(children=[   
                                html.P('Enter names for the detection areas separated by commas (i.e. name1, name2, name3).', style={'width':'85%'}),  
                                html.P('Shapes on the canvas must be created in the same order as the names.', style={'width':'85%'}),                       
                                dcc.Input(
                                    placeholder='Enter area names...',
                                    type='text',
                                    id='areaInput',
                                    value='',
                                    debounce=True,
                                    style={'width': '85%', 'height': '75%'}
                                ),
                                ],
                                style={'display': 'flex', 'justifyContent': 'center', 'display': 'inline-block', 'width': '75%'}
                            ),    
                        ],
                        ),
                        # CANVAS
                        dcc.Graph(id="fig-poly", figure=getBG(), config=config, style={'width': '100%', 'height': '100%'}),
                        html.Pre(id="annotations-prePoly"),  
                        dbc.Alert(
                            "Detection areas cleared.",
                            id="area-clr",
                            is_open=False,
                            duration=2000,
                            color="success"
                        ),             
                    ]),
                    dbc.ModalFooter(children=[  
                        html.Button("Clear Areas", id="PolygonModalClear",style={'justify': 'right', 'marginTop': '15px', 'color':'red'}),                      
                        html.Button("Done", id="PolygonModalClose",style={'justify': 'right', 'marginTop': '15px'}),
                        ],
                        style={'display': 'flex', 'justifyContent': 'middle'}
                    ),   
                ],
                id="polygonModal",
                keyboard=False,
                size="lg",
                is_open=False                
            ),
            # Mask modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Create mask areas"), close_button=False),                    
                    dbc.ModalBody(children=[
                        html.P("Create one or more mask areas where traffic won't be detected."),
                        dcc.Graph(id="fig-mask", figure=getBG(), config=config, style={'width': '100%', 'height': '100%'}),
                        html.Pre(id="annotations-preMask"),     
                        dbc.Alert(
                            "Mask cleared.",
                            id="mask-clr",
                            is_open=False,
                            duration=2000,
                            color="success"
                        ),          
                    ]),
                    dbc.ModalFooter(children=[         
                        html.Button("Clear Mask", id="MaskModalClear",style={'justify': 'right', 'marginTop': '15px', 'color':'red'}),                                       
                        html.Button("Done", id="MaskModalClose",style={'justify': 'right', 'marginTop': '15px'}),
                        ],
                        style={'display': 'flex', 'justifyContent': 'middle'}
                    ),   
                ],
                id="maskModal",
                size="lg",
                is_open=False,                
            ),
            html.Div(
                className="row",
                children=[
                    # Column for user controls
                    html.Div(
                        className="three columns div-user-controls",
                        children=[                            
                            html.H1("Real-time traffic analysis app"),
                            html.P(
                                """Traffic detection and analysis app created mainly as tool for gathering data related to traffic."""
                            ),
                            html.Hr(),
                            html.Div(
                                children=[
                                    html.Div(
                                        children=[
                                            html.Button("Settings", id="open-settingsModal", style={'width': '15rem'}),
                                        ],
                                        style = {'horizontalAlign': 'middle'}
                                    ),
                                    html.Div(
                                        children=[                                            
                                            html.Button("Detection Areas", id="open-polygonModal",style={'marginTop': '10px', 'width': '15rem'}),
                                        ],
                                        style = {'horizontalAlign': 'middle'}
                                    ),
                                     html.Div(
                                        children=[
                                            html.Button("Mask", id="open-maskModal",style={'marginTop': '10px', 'width': '15rem'}),                                           
                                        ],
                                        style = {'horizontalAlign': 'middle'}
                                    ),                                                                                                
                                ],
                                style={'textAlign': 'center'}
                            ),  
                            html.Hr(),    
                            # Confidence slider                                                  
                            html.Div(
                                children=[
                                    html.H5("Confidence"),
                                    dcc.Slider(0, 1,
                                               step=None,
                                               id='confidenceSlider',
                                               marks={
                                                   0: '0',
                                                   0.2: '0.2',
                                                   0.4: '0.4',
                                                   0.6: '0.6',
                                                   0.8: '0.8',
                                                   1: '1.0',
                                               },
                                               value=0.20,
                                               className='slider'
                                               )
                                ],
                            ),
                            # Show tracks
                            html.Div(
                                className='div-for-booleanSwitch',
                                children=[
                                    html.Div(
                                        className='row',
                                        children=[
                                            daq.BooleanSwitch(
                                                on=True,
                                                label="Show tracks",
                                                labelPosition="bottom",
                                                id='showTracks',
                                                color='#f78400',
                                                style={'paddingTop': '5px'}
                                            )
                                        ],
                                        style={'display': 'inline-block',
                                               'width': '33%'}
                                    ),
                                    # Show areas
                                    html.Div(
                                        className='row',
                                        children=[
                                            daq.BooleanSwitch(
                                                on=False,
                                                label="Show Areas",
                                                id='showPolygons',
                                                labelPosition="bottom",
                                                color='#f78400'
                                            ),                                            
                                        ],
                                        style={'display': 'inline-block',
                                               'width': '33%'}
                                    ),
                                    #Save to DB
                                    html.Div(
                                        className='row',
                                        children=[
                                            daq.BooleanSwitch(
                                                on=True,
                                                label="Save to DB",
                                                labelPosition="bottom",
                                                id='saveDB',
                                                color='#f78400',
                                                style={'paddingTop': '5px'}
                                            )
                                        ],
                                        style={'display': 'inline-block',
                                               'width': '33%'}
                                    ),
                                ],
                                style={'textAlign': 'center'}
                            ),
                           # Detection class select
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="div-for-dropdown",
                                        children=[
                                            html.H5('Detection classes'),
                                            dcc.Dropdown(
                                                ['Car', 'Bus',
                                                    'Truck', 'Motorcycle', 'Bicycle'],
                                                ['Car', 'Bus', 'Truck',
                                                    'Motorcycle'],
                                                multi=True,
                                                id='classSelect'
                                            )
                                        ],
                                    ),
                                    # Just for callbacks
                                    html.Div(id='emptyDiv1'),
                                    html.Div(id='emptyDiv2'),
                                    html.Div(id='emptyDiv3'),
                                    html.Div(id='emptyDiv4'),
                                    html.Div(id='emptyDiv5'),
                                    html.Div(id='emptyDiv6'),
                                    html.Div(id='emptyDiv7'),
                                    html.Div(id='emptyDiv8'),
                                    html.Div(id='emptyDiv9'),
                                    html.Div(id='emptyDiv10'),
                                    html.Div(id='emptyDiv11'),
                                    html.Div(id='emptyDiv12'),   
                                    html.Div(id='emptyDiv13'),    
                                    html.Div(id='emptyDiv14'),                                                  
                                ],
                            ),
                            html.Hr(),
                            # Download
                            html.H4("Download data", style={'marginBottom':'15px'}),
                            html.Div(
                                className='row',
                                children=[                                    
                                    dcc.Dropdown(options=['Vehicles', 'Points'], value='Vehicles', id='download-dropdown'),
                                ],
                                style={'marginBottom': '10px','textAlign': 'center'}
                            ),
                            html.Div(
                                className='row',
                                children=[         
                                    # Calendar                                                                                                 
                                    dcc.DatePickerRange(
                                        id='date-picker-range',
                                        start_date=date.today(),
                                        min_date_allowed=date(2020, 1, 1),
                                        max_date_allowed=date(2025, 12, 31),
                                        display_format='DD/MM/YYYY',
                                        end_date=date.today(),
                                        with_portal=True,
                                        day_size=32,
                                    ),     
                                    html.Div(children = [
                                        html.Button("Download", id="btn-download-data", style={'width': '40%'}),
                                        ],
                                        style = {'horizontalAlign': 'middle'}
                                    ),                                    
                                    dcc.Download(id="download-data"),                               
                                ],     
                                style={'textAlign': 'center'}                                                       
                            ),                            
                        ],
                    ),
                    # Column for app graphs and plots
                    html.Div(
                        className="nine columns div-for-charts bg-grey",
                        children=[
                            # First Row
                            html.Div(
                                className='row bg-grey',
                                children=[
                                    html.Div(
                                        children=[
                                            # Video
                                            html.Div(
                                                className='row',
                                                children=[
                                                    html.H4(f'{getTitle()}'),
                                                    html.Img(src="/video_stream", style={'height':'30em'}),
                                                ],
                                                style={'display': 'inline-block',
                                                    'width': '60%', 'marginRight':'5px', 'height':'50%', 'verticalAlign': 'top'}
                                            ),
                                            # Info
                                            html.Div(
                                                className='row',
                                                children=[
                                                     # FPS
                                                    html.Div(children=[
                                                        html.H5('FPS: ', style={'display': 'inline-block', 'width':'50%'}),
                                                        html.H5(id='fpsCounter', style={'display': 'inline-block','width':'50%', 'textAlign':'right'})
                                                    ],
                                                    style={'height':'25%', 'width':'95%','verticalAlign':'middle', 'horizontalAlign':'left', 'marginLeft':'10px', 'backgroundColor': '#1E1E1E'}),

                                                    # Detection areas
                                                    html.Div(children=[
                                                        html.H5('Detection areas: ', style={'display': 'inline-block', 'width':'50%'}),
                                                        html.H5(id='definedAreas', style={'display': 'inline-block','width':'50%', 'textAlign':'right'})
                                                    ],
                                                    style={'height':'25%', 'width':'95%','verticalAlign':'middle', 'horizontalAlign':'left', 'marginLeft':'10px', 'marginTop': '20px', 'backgroundColor': '#1E1E1E'}),


                                                    # Traffic flow
                                                    html.Div(children=[
                                                        html.H5('Traffic Flow [v/min]: ', style={'display': 'inline-block', 'width':'75%'}),
                                                        html.H5(id='trafficFlow', style={'display': 'inline-block','width':'25%', 'textAlign':'right'})
                                                    ],
                                                    style={'height':'25%', 'width':'95%','verticalAlign':'bottom', 'horizontalAlign':'left', 'marginLeft':'10px', 'marginTop': '165px', 'backgroundColor': '#1E1E1E'}),

                                                ],
                                                style={'display': 'inline-block',
                                                    'width': '40%', 'marginLeft':'5px','height':'15em', 'font-size': '1.2rem', 'marginTop':'40px'}
                                            ),
                                        ],
                                    ),
                                ],
                                style={'margin': '20px'}
                            ),

                           # Second row
                            html.Div(
                                className='row bg-grey',
                                children=[
                                    # Intervals for UI updates
                                    dcc.Interval(id='interval-updating-oneSec', interval=1000, n_intervals=0),
                                    dcc.Interval(id='interval-updating-fiveSec', interval=5000, n_intervals=0),
                                    dcc.Interval(id='interval-updating-tenMin', interval=600000, n_intervals=0),
                                    html.Div(
                                        children=[
                                            html.Div(
                                                className='row',
                                                children=[
                                                dcc.Upload(
                                                    id='upload-image',
                                                    children=html.Div([
                                                        'Drag and Drop or ',
                                                        html.A('Select Files')
                                                    ]),
                                                    style={
                                                        'width': '100%',
                                                        'height': '60px',
                                                        'lineHeight': '60px',
                                                        'borderWidth': '1px',
                                                        'borderStyle': 'dashed',
                                                        'borderRadius': '5px',
                                                        'textAlign': 'center',
                                                        'margin': '10px'
                                                    },
                                                    # Allow multiple files to be uploaded
                                                    multiple=True
                                                ),
                                                html.Div(id='output-image-upload'),
                                            ])
                                        ],
                                    ),
                                ],
                                style={'margin': '20px'}
                            )
                        ]
                    ),
                ],
            )
        ],
        fluid=True
    )
    return layout
