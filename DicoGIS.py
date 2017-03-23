# -*- coding: UTF-8 -*-
#!/usr/bin/env python
from __future__ import (absolute_import, print_function, unicode_literals)
# -----------------------------------------------------------------------------
# Name:         DicoGIS
# Purpose:      Automatize the creation of a dictionnary of geographic data
#               contained in a folders structures.
#               It produces an Excel output file (.xlsx)
#
# Author:       Julien Moura (@geojulien)
#
# Python:       2.7.x
# Created:      14/02/2013
# Updated:      19/03/2017
#
# Licence:      GPL 3
# ------------------------------------------------------------------------------

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from Tkinter import Tk, StringVar, IntVar, Image    # GUI
from Tkinter import W, PhotoImage, ACTIVE, DISABLED, END
from tkFileDialog import askdirectory
from tkMessageBox import showinfo as info, showerror as avert
from ttk import Combobox, Progressbar, Style, Labelframe, Frame
from ttk import Label, Button, Entry, Checkbutton, Notebook  # widgets
import tkFont   # font library

import locale
from sys import exit, platform as opersys
from os import listdir, walk, path         # files and folder managing
from os import environ as env
from time import strftime
from webbrowser import open_new
import threading    # handling various subprocesses

import platform  # about operating systems

import logging  # log files
from logging.handlers import RotatingFileHandler

# Python 3 backported
from collections import OrderedDict  # ordered dictionary

# 3rd party libraries
from isogeo_pysdk import Isogeo

# Custom modules
from modules import ReadRasters    # for rasters files
from modules import ReadVectorFlatDataset  # for various vectors flat dataset
from modules import ReadGXT    # for Geoconcept eXport Text
from modules import ReadPostGIS    # for PostGIS databases
from modules import ReadGDB        # for Esri FileGeoDataBase
from modules import ReadSpaDB      # for Spatialite DB
from modules import ReadDXF        # for AutoCAD DXF
from modules import ReadGeoPDF     # for Geospatial PDF
from modules import ReadLYR  # Esri LYR files

from modules import CheckNorris
from modules import md2xlsx
from modules import Utilities
# from modules import MetricsManager
from modules import OptionsManager
from modules import TextsManager

# custom UI
from modules import MiscButtons


# ##############################################################################
# ############ Globals ############
# #################################

utils_global = Utilities()

# LOG
logger = logging.getLogger("DicoGIS")
logging.captureWarnings(True)
logger.setLevel(logging.INFO)  # all errors will be get
log_form = logging.Formatter("%(asctime)s || %(levelname)s || %(module)s || %(message)s")
logfile = RotatingFileHandler("LOG_DicoGIS.log", "a", 5000000, 1)
logfile.setLevel(logging.INFO)
logfile.setFormatter(log_form)
logger.addHandler(logfile)

# ##############################################################################
# ############ Classes #############
# ##################################


class DicoGIS(Tk):
    # attributes
    DGversion = "2.5.0-beta4"

    def __init__(self):
        u""" Main window constructor
        Creates 1 frame and 2 labelled subframes"""
        logger.info('\t============== DicoGIS =============')
        logger.info('Version: {0}'.format(self.DGversion))

        # manage settings outside the main class
        self.settings = OptionsManager(r"options.ini")
        # Invoke Check Norris
        checker = CheckNorris()

        # basics settings
        Tk.__init__(self)               # constructor of parent graphic class
        self.title(u'DicoGIS {0}'.format(self.DGversion))
        if opersys == 'win32':
            logger.info('Operating system: {0}'.format(platform.platform()))
            self.iconbitmap('DicoGIS.ico')    # windows icon
            self.uzer = env.get(u'USERNAME')
        elif opersys == 'linux2':
            logger.info('Operating system: {0}'.format(platform.platform()))
            self.uzer = env.get(u'USER')
            icon = Image("photo", file=r'data/img/DicoGIS_logo.gif')
            self.call('wm', 'iconphoto', self._w, icon)
            self.style = Style().theme_use('clam')
        elif opersys == 'darwin':
            logger.info('Operating system: {0}'.format(platform.platform()))
            self.uzer = env.get(u'USER')
        else:
            logger.warning('Operating system unknown')
            logger.info('Operating system: {0}'.format(platform.platform()))
        self.resizable(width=False, height=False)
        self.focus_force()

        # GDAL settings
        checker.check_gdal()

        # # Variables
        # settings
        self.num_folders = 0
        self.def_rep = ""       # default folder to search for
        self.def_lang = 'EN'    # default language to start
        self.today = strftime("%Y-%m-%d")   # date of the day
        li_lang = [lg[5:-4] for lg in listdir(r'data/locale')]  # languages
        self.blabla = OrderedDict()      # texts dictionary

        # formats / type: vectors
        self.li_vectors_formats = (".shp", ".tab", ".kml",
                                   ".gml", ".geojson")  # vectors handled
        self.li_shp = []        # list for shapefiles path
        self.li_tab = []        # list for MapInfo tables path
        self.li_kml = []        # list for KML path
        self.li_gml = []        # list for GML path
        self.li_geoj = []       # list for GeoJSON paths
        self.li_gxt = []       # list for GXT paths
        self.li_vectors = []    # list for all vectors
        # formats / type: rasters
        self.li_raster = []     # list for rasters paths
        self.li_raster_formats = (".ecw", ".tif", ".jp2")   # raster handled
        # formats / type: file databases
        self.li_fdb = []        # list for all files databases
        self.li_egdb = []       # list for Esri File Geodatabases
        self.li_spadb = []      # list for Spatialite Geodatabases
        # formats / type: CAO/DAO
        self.li_cdao = []     # list for all CAO/DAO files
        self.li_dxf = []      # list for AutoCAD DXF paths
        self.li_dwg = []      # list for AutoCAD DWG paths
        self.li_dgn = []      # list for MicroStation DGN paths
        # formats / type: maps documents
        self.li_mapdocs = []  # list for all map & documents
        self.li_pdf = []      # list for GeoPDF path
        self.li_lyr = []      # list for LYR path
        self.li_mxd = []      # list for MXD path
        self.li_qgs = []      # list for QGS path

        # dictionaries to store informations
        self.dico_layer = OrderedDict()      # dict for vectors informations
        self.dico_fields = OrderedDict()     # dict for fields informations
        self.dico_raster = OrderedDict()     # dict for rasters global informations
        self.dico_bands = OrderedDict()      # dict for bands informations
        self.dico_fdb = OrderedDict()        # dict for Esri FileGDB
        self.dico_cdao = OrderedDict()       # dict for CAO/DAO
        self.dico_pdf = OrderedDict()        # dict for Geospatial PDF
        self.dico_err = OrderedDict()        # errors list

        # metrics
        self.dico_metrics = OrderedDict()
        self.global_total_layers = 0
        self.global_total_fields = 0
        self.global_total_features = 0
        self.global_total_errors = 0
        self.global_total_warnings = 0
        self.global_total_srs_proj = 0
        self.global_total_srs_geog = 0
        self.global_total_srs_none = 0
        self.global_ignored = 0    # files ignored by an user filter
        self.global_dico_fields = OrderedDict()

        # GUI fonts
        ft_tit = tkFont.Font(family="Times", size=10, weight=tkFont.BOLD)

        # Notebook
        self.nb = Notebook(self)
        # tabs
        self.tab_files = Frame(self.nb)         # tab_id = 0
        self.tab_sgbd = Frame(self.nb)          # tab_id = 1
        self.tab_webservices = Frame(self.nb)   # tab_id = 2
        self.tab_isogeo = Frame(self.nb)        # tab_id = 3
        self.tab_options = Frame(self.nb)       # tab_id = 4

        # fillfulling text
        TextsManager().load_texts(dico_texts=self.blabla,
                                  lang=self.def_lang,
                                  locale_folder=r'data/locale')

# =================================================================================
        # ## TAB 1: FILES ##
        self.nb.add(self.tab_files,
                    text=self.blabla.get('gui_tab1'),
                    padding=3)

        # Frame: target folder
        self.FrPath = Labelframe(self.tab_files,
                                 name='files',
                                 text=self.blabla.get('gui_fr1'))
        # target folder
        self.labtarg = Label(self.FrPath, text=self.blabla.get('gui_path'))
        self.target = Entry(master=self.FrPath, width=35)
        self.browsetarg = Button(self.FrPath,       # browse button
                                 text=self.blabla.get('gui_choix'),
                                 command=lambda: self.setpathtarg(),
                                 takefocus=True)
        self.browsetarg.focus_force()               # force the focus on

        # widgets placement
        self.labtarg.grid(row=1, column=1, columnspan=1,
                          sticky="NSWE", padx=2, pady=2)
        self.target.grid(row=1, column=2, columnspan=1,
                         sticky="NSWE", padx=2, pady=2)
        self.browsetarg.grid(row=1, column=3,
                             sticky="NSWE", padx=2, pady=2)

        # Frame: filters of formats
        self.FrFilters = Labelframe(self.tab_files,
                                    name='filters',
                                    text=self.blabla.get('gui_fr3'))
        # formats options
        self.opt_shp = IntVar(self.FrFilters)   # able/disable shapefiles
        self.opt_tab = IntVar(self.FrFilters)   # able/disable MapInfo tables
        self.opt_kml = IntVar(self.FrFilters)   # able/disable KML
        self.opt_gml = IntVar(self.FrFilters)   # able/disable GML
        self.opt_geoj = IntVar(self.FrFilters)  # able/disable GeoJSON
        self.opt_gxt = IntVar(self.FrFilters)  # able/disable GXT
        self.opt_egdb = IntVar(self.FrFilters)  # able/disable Esri FileGDB
        self.opt_spadb = IntVar(self.FrFilters)  # able/disable Spatalite DB
        self.opt_rast = IntVar(self.FrFilters)  # able/disable rasters
        self.opt_cdao = IntVar(self.FrFilters)  # able/disable CAO/DAO files
        self.opt_pdf = IntVar(self.FrFilters)   # able/disable Geospatial PDF
        self.opt_lyr = IntVar(self.FrFilters)   # able/disable Geospatial Lyr
        self.opt_mxd = IntVar(self.FrFilters)   # able/disable Geospatial MXD
        self.opt_qgs = IntVar(self.FrFilters)   # able/disable Geospatial QGS

        # format choosen: check buttons
        caz_shp = Checkbutton(self.FrFilters,
                              text=u'.shp',
                              variable=self.opt_shp)
        caz_tab = Checkbutton(self.FrFilters,
                              text=u'.tab',
                              variable=self.opt_tab)
        caz_kml = Checkbutton(self.FrFilters,
                              text=u'.kml',
                              variable=self.opt_kml)
        caz_gml = Checkbutton(self.FrFilters,
                              text=u'.gml',
                              variable=self.opt_gml)
        caz_geoj = Checkbutton(self.FrFilters,
                               text=u'.geojson',
                               variable=self.opt_geoj)
        caz_gxt = Checkbutton(self.FrFilters,
                              text=u'.gxt',
                              variable=self.opt_gxt)
        caz_egdb = Checkbutton(self.FrFilters,
                               text=u'Esri FileGDB',
                               variable=self.opt_egdb)
        caz_spadb = Checkbutton(self.FrFilters,
                                text=u'Spatialite',
                                variable=self.opt_spadb)
        caz_rast = Checkbutton(self.FrFilters,
                               text=u'rasters ({0})'.format(', '.join(self.li_raster_formats)),
                               variable=self.opt_rast)
        caz_cdao = Checkbutton(self.FrFilters,
                               text=u'CAO/DAO',
                               variable=self.opt_cdao)
        caz_pdf = Checkbutton(self.FrFilters,
                              text=u'Geospatial PDF',
                              variable=self.opt_pdf)
        caz_lyr = Checkbutton(self.FrFilters,
                              text=u'.lyr',
                              variable=self.opt_lyr)
        caz_mxd = Checkbutton(self.FrFilters,
                              text=u'.mxd',
                              variable=self.opt_mxd)
        caz_qgs = Checkbutton(self.FrFilters,
                              text=u'.qgs',
                              variable=self.opt_qgs)
        # widgets placement
        caz_shp.grid(row=1,
                     column=0,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_tab.grid(row=1,
                     column=1,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_kml.grid(row=1,
                     column=2,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_gml.grid(row=1,
                     column=3,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_geoj.grid(row=1,
                      column=4,
                      sticky="NSWE",
                      padx=2, pady=2)
        caz_gxt.grid(row=1,
                     column=7,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_pdf.grid(row=1,
                     column=5,
                     columnspan=2,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_rast.grid(row=2,
                      column=0,
                      columnspan=2,
                      sticky="NSWE",
                      padx=2, pady=2)
        caz_egdb.grid(row=2,
                      column=2,
                      columnspan=2,
                      sticky="NSWE",
                      padx=2, pady=2)
        caz_cdao.grid(row=2,
                      column=4,
                      columnspan=1,
                      sticky="NSWE",
                      padx=2, pady=2)
        caz_spadb.grid(row=2,
                       column=5,
                       columnspan=2,
                       sticky="NSWE",
                       padx=2, pady=2)
        caz_lyr.grid(row=3,
                     column=0,
                     columnspan=2,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_mxd.grid(row=3,
                     column=1,
                     columnspan=2,
                     sticky="NSWE",
                     padx=2, pady=2)
        caz_qgs.grid(row=3,
                     column=2,
                     columnspan=2,
                     sticky="NSWE",
                     padx=2, pady=2)

        # frames placement
        self.FrPath.grid(row=3, column=1,
                         padx=2, pady=2, sticky="NSWE")
        self.FrFilters.grid(row=4, column=1,
                            padx=2, pady=2, sticky="NSWE")

# =================================================================================

        # ## TAB 2: Database ##
        self.nb.add(self.tab_sgbd,
                    text=self.blabla.get('gui_tab2'), padding=3)

        # subframe
        self.FrDb = Labelframe(self.tab_sgbd,
                               name='database',
                               text=self.blabla.get('gui_fr2'))

        # DB variables
        self.opt_pgvw = IntVar(self.FrDb)   # able/disable PostGIS views
        self.host = StringVar(self.FrDb, 'localhost')
        self.port = IntVar(self.FrDb, 5432)
        self.dbnb = StringVar(self.FrDb)
        self.user = StringVar(self.FrDb, 'postgres')
        self.pswd = StringVar(self.FrDb)

        # Form widgets
        self.ent_H = Entry(self.FrDb, textvariable=self.host)
        self.ent_P = Entry(self.FrDb, textvariable=self.port, width=5)
        self.ent_D = Entry(self.FrDb, textvariable=self.dbnb)
        self.ent_U = Entry(self.FrDb, textvariable=self.user)
        self.ent_M = Entry(self.FrDb, textvariable=self.pswd, show='*')

        caz_pgvw = Checkbutton(self.FrDb,
                               text=self.blabla.get('gui_views'),
                               variable=self.opt_pgvw)

        # Label widgets
        self.lb_H = Label(self.FrDb, text=self.blabla.get('gui_host'))
        self.lb_P = Label(self.FrDb, text=self.blabla.get('gui_port'))
        self.lb_D = Label(self.FrDb, text=self.blabla.get('gui_db'))
        self.lb_U = Label(self.FrDb, text=self.blabla.get('gui_user'))
        self.lb_M = Label(self.FrDb, text=self.blabla.get('gui_mdp'))
        # widgets placement
        self.ent_H.grid(row=1, column=1, columnspan=2,
                        sticky="NSEW", padx=2, pady=2)
        self.ent_P.grid(row=1, column=3, columnspan=1,
                        sticky="NSE", padx=2, pady=2)
        self.ent_D.grid(row=2, column=1, columnspan=1,
                        sticky="NSEW", padx=2, pady=2)
        self.ent_U.grid(row=2, column=3, columnspan=1,
                        sticky="NSEW", padx=2, pady=2)
        self.ent_M.grid(row=3, column=1, columnspan=3,
                        sticky="NSEW", padx=2, pady=2)
        self.lb_H.grid(row=1, column=0,
                       sticky="NSEW", padx=2, pady=2)
        self.lb_P.grid(row=1, column=3,
                       sticky="NSW", padx=2, pady=2)
        self.lb_D.grid(row=2, column=0,
                       sticky="NSW", padx=2, pady=2)
        self.lb_U.grid(row=2, column=2,
                       sticky="NSW", padx=2, pady=2)
        self.lb_M.grid(row=3, column=0,
                       sticky="NSWE", padx=2, pady=2)
        caz_pgvw.grid(row=4, column=0,
                      sticky="NSWE", padx=2, pady=2)

        # frame position
        self.FrDb.grid(row=3, column=1, sticky="NSWE", padx=2, pady=2)

# =================================================================================
        # ## TAB 3: web services ##
        self.nb.add(self.tab_webservices,
                    text=self.blabla.get('gui_tab3'), padding=3)
        # variables
        self.url_service = StringVar(self.tab_webservices,
                                     'http://suite.opengeo.org/geoserver/wfs?request=GetCapabilities')

        # widgets
        self.lb_url_service = Label(self.tab_webservices,
                                    text='OpenCatalog')
        self.ent_url_service = Entry(self.tab_webservices,
                                     width=75,
                                     textvariable=self.url_service)

        # widgets placement
        self.ent_url_service.grid(row=0, column=1,
                                  sticky="NSWE", padx=2, pady=2)

# =================================================================================

        # ## TAB 4: Isogeo ##
        self.nb.add(self.tab_isogeo,
                    text='Isogeo', padding=3)
        # variables
        self.url_OpenCatalog = StringVar(self.tab_isogeo, 'http://open.isogeo.com')
        # widgets
        self.lb_urlOC = Label(self.tab_isogeo,
                              text='OpenCatalog')
        self.ent_urlOC = Entry(self.tab_isogeo,
                               width=75,
                               textvariable=self.url_OpenCatalog)
        # widgets placement
        self.lb_urlOC.grid(row=0, column=1,
                           sticky="NSWE", padx=2, pady=2)
        self.ent_urlOC.grid(row=0, column=2, columnspan=2,
                            sticky="NSWE", padx=2, pady=2)

# =================================================================================

        # ## TAB 5: Options ##
        self.nb.add(self.tab_options,
                    text='Options', padding=3)

        # subframes

        self.FrOptProxy = Frame(self.tab_options,
                                name='settings-proxy',
                                # text=self.blabla.get('gui_fr2')
                                )
        self.FrOptIsogeo = Frame(self.tab_options,
                                 name='settings-isogeo',
                                 # text='Isogeo'
                                 )

        # options values
        self.opt_proxy = IntVar(self.tab_options)  # proxy option
        self.opt_isogeo = IntVar(self.tab_options)  # Isogeo option

        # Options form widgets
        caz_prox = Checkbutton(self.tab_options,
                               text=u'Proxy',
                               variable=self.opt_proxy,
                               command=lambda: self.ui_switch(self.opt_proxy,
                                                              self.FrOptProxy))
        caz_isogeo = Checkbutton(self.tab_options,
                                 text=u'Isogeo',
                                 variable=self.opt_isogeo,
                                 command=lambda: self.ui_switch(self.opt_isogeo,
                                                                self.FrOptIsogeo))

        # positionning
        caz_prox.grid(row=0, column=0,
                      sticky="NSWE", padx=2, pady=2)
        self.FrOptProxy.grid(row=0, column=1, columnspan=8,
                             sticky="NSWE", padx=2, pady=2,
                             rowspan=3)
        caz_isogeo.grid(row=3, column=0,
                        sticky="NSWE", padx=2, pady=2)
        self.FrOptIsogeo.grid(row=3, column=1, columnspan=8,
                              sticky="NSWE", padx=2, pady=2,
                              rowspan=4)

        # ------------------------------------------------------------------------
        # proxy specific variables
        self.opt_ntlm = IntVar(self.FrOptProxy, 0)  # proxy NTLM protocol option
        self.prox_server = StringVar(self.FrOptProxy, 'proxy.server.com')
        self.prox_port = IntVar(self.FrOptProxy, 80)
        self.prox_user = StringVar(self.FrOptProxy, 'proxy_user')
        self.prox_pswd = StringVar(self.FrOptProxy, '****')

        # widgets
        self.prox_ent_H = Entry(self.FrOptProxy, textvariable=self.prox_server)
        self.prox_ent_P = Entry(self.FrOptProxy, textvariable=self.prox_port)
        self.prox_ent_M = Entry(self.FrOptProxy, textvariable=self.prox_pswd, show='*')

        self.prox_lb_H = Label(self.FrOptProxy, text=self.blabla.get('gui_prox_server'))
        self.prox_lb_P = Label(self.FrOptProxy, text=self.blabla.get('gui_port'))
        caz_ntlm = Checkbutton(self.FrOptProxy,
                               text=u'NTLM',
                               variable=self.opt_ntlm)
        self.prox_lb_M = Label(self.FrOptProxy, text=self.blabla.get('gui_mdp'))

        # proxy widgets position
        self.prox_lb_H.grid(row=1, column=0,
                            sticky="NSEW", padx=2, pady=2)
        self.prox_ent_H.grid(row=1, column=1, columnspan=2,
                             sticky="NSEW", padx=2, pady=2)
        self.prox_lb_P.grid(row=1, column=2,
                            sticky="NSEW", padx=2, pady=2)
        self.prox_ent_P.grid(row=1, column=3, columnspan=2,
                             sticky="NSEW", padx=2, pady=2)
        caz_ntlm.grid(row=2, column=0,
                      sticky="NSEW", padx=2, pady=2)
        self.prox_lb_M.grid(row=2, column=1,
                            sticky="NSEW", padx=2, pady=2)
        self.prox_ent_M.grid(row=2, column=2, columnspan=2,
                             sticky="NSEW", padx=2, pady=2)

        # ------------------------------------------------------------------------
        # Isogeo application variables
        self.isog_app_id = StringVar(self.FrOptIsogeo, 'application_id')
        self.isog_app_tk = StringVar(self.FrOptIsogeo, 'secret')

        # widgets
        isog_ent_id = Entry(self.FrOptIsogeo,
                            textvariable=self.isog_app_id)
        isog_ent_tk = Entry(self.FrOptIsogeo,
                            textvariable=self.isog_app_tk)

        isog_lb_id = Label(self.FrOptIsogeo, text="Application ID")
        isog_lb_tk = Label(self.FrOptIsogeo, text="Application secret")

        # Isogeo widgets position
        isog_lb_id.grid(row=1, column=1,
                        sticky="NSEW", padx=2, pady=2)
        isog_ent_id.grid(row=1, column=2, columnspan=2,
                         sticky="NSEW", padx=2, pady=2)
        isog_lb_tk.grid(row=2, column=1,
                        sticky="NSEW", padx=2, pady=2)
        isog_ent_tk.grid(row=2, column=2, columnspan=2,
                         sticky="NSEW", padx=2, pady=2)


# =================================================================================
        # ## MAIN FRAME ##
        # welcome message
        self.welcome = Label(self,
                             text=self.blabla.get('hi') + self.uzer,
                             font=ft_tit,
                             foreground="blue")

        # Frame: Output
        self.FrOutp = Labelframe(self,
                                 name='output',
                                 text=self.blabla.get('gui_fr4'))
        # widgets
        self.nameoutput = Label(self.FrOutp,
                                text=self.blabla.get('gui_fic'))
        self.output = Entry(self.FrOutp, width=35)
        # widgets placement
        self.nameoutput.grid(row=0, column=1,
                             sticky="NSWE", padx=2, pady=2)
        self.output.grid(row=0, column=2, columnspan=2,
                         sticky="NSWE", padx=2, pady=2)

        # Frame: Progression bar
        self.FrProg = Labelframe(self,
                                 name='progression',
                                 text=self.blabla.get('gui_prog'))
        # variables
        self.status = StringVar(self.FrProg, '')
        # widgets
        self.prog_layers = Progressbar(self.FrProg,
                                       orient="horizontal")
        Label(master=self.FrProg,
              textvariable=self.status,
              foreground='DodgerBlue').pack()
        # widgets placement
        self.prog_layers.pack(expand=1, fill='both')

        # logo
        self.icone = PhotoImage(file=r'data/img/DicoGIS_logo.gif')
        Label(self,
              borderwidth=2,
              image=self.icone).grid(row=1, rowspan=2,
                                     column=0, padx=2,
                                     pady=2, sticky=W)
        # credits
        s = Style(self)
        s.configure('Kim.TButton', foreground='DodgerBlue', borderwidth=0)
        Button(self,
               text='by @GeoJulien\nGPL3 - 2016',
               style='Kim.TButton',
               command=lambda: open_new('https://github.com/Guts/DicoGIS')).grid(row=3,
                                                                                 padx=2,
                                                                                 pady=2,
                                                                                 sticky="WE")
        # miscellaneous
        misc_frame = MiscButtons(self)
        misc_frame.grid(row=4,
                        padx=2,
                        pady=2,
                        sticky="NSWE")
        # language switcher
        self.ddl_lang = Combobox(self,
                                 values=li_lang,
                                 width=5)
        self.ddl_lang.current(li_lang.index(self.def_lang))
        self.ddl_lang.bind("<<ComboboxSelected>>", self.change_lang)

        # Basic buttons
        self.val = Button(self,
                          text=self.blabla.get('gui_go'),
                          state=ACTIVE,
                          command=lambda: self.process())
        self.can = Button(self, text=self.blabla.get('gui_quit'),
                          command=lambda: self.destroy())

        # widgets placement
        self.welcome.grid(row=1, column=1, columnspan=1, sticky="NS",
                          padx=2, pady=2)
        self.ddl_lang.grid(row=1, column=1, sticky="NSE", padx=2, pady=2)
        self.nb.grid(row=2, column=1)    # notebook
        self.FrProg.grid(row=3, column=1, sticky="NSWE", padx=2, pady=2)
        self.FrOutp.grid(row=4, column=1, sticky="NSWE", padx=2, pady=2)
        self.val.grid(row=5, column=1, columnspan=2,
                      sticky="NSWE", padx=2, pady=2)
        self.can.grid(row=5, column=0, sticky="NSWE", padx=2, pady=2)

        # loading previous options
        if not self.settings.first_use:
            try:
                self.settings.load_settings(parent=self)
            except:
                logger.error("Load settings failed: option or section is missing.")
        else:
            pass
        self.ddl_lang.set(self.def_lang)
        self.change_lang(1)

        # set UI options tab
        self.ui_switch(self.opt_proxy,
                       self.FrOptProxy)
        self.ui_switch(self.opt_isogeo,
                       self.FrOptIsogeo)

        # check ArcPy
        if opersys != 'win32' or not checker.check_arcpy()[0]:
            caz_lyr.config(state=DISABLED)
            caz_mxd.config(state=DISABLED)
            self.opt_lyr.set(0)
            self.opt_mxd.set(0)
        else:
            pass

        # checking connection
        if not checker.check_internet_connection():
            self.nb.tab(2, state=DISABLED)
            self.nb.tab(3, state=DISABLED)
        elif self.opt_isogeo.get() == 0:
            self.nb.tab(3, state=DISABLED)
        else:
            # checking Isogeo
            try:
                isogeo = Isogeo(client_id=self.isog_app_id.get(),
                                client_secret=self.isog_app_tk.get(),
                                lang=self.def_lang)
                self.isogeo_token = isogeo.connect()
            except ValueError as e:
                if e[0] == 1:
                    self.nb.tab(3, state=DISABLED)
                elif e[0] == 2:
                    self.nb.tab(3, state=DISABLED)
                else:
                    pass

# =================================================================================

    def ui_switch(self, cb_value, parent):
        """Change state of  all children widgets within a parent class.

        cb_value=boolean
        parent=Tkinter class with children (Frame, Labelframe, Tk, etc.)
        """
        if cb_value.get():
            for child in parent.winfo_children():
                child.configure(state=ACTIVE)
        else:
            for child in parent.winfo_children():
                child.configure(state=DISABLED)
        # end of function
        return

    def change_lang(self, event):
        u"""Update the texts dictionary with the language selected."""
        new_lang = self.ddl_lang.get()
        # change to the new language selected
        TextsManager().load_texts(dico_texts=self.blabla,
                                  lang=new_lang,
                                  locale_folder=r'data/locale')
        # update widgets text
        self.welcome.config(text=self.blabla.get('hi') + self.uzer)
        self.can.config(text=self.blabla.get('gui_quit'))
        self.FrPath.config(text=self.blabla.get('gui_fr1'))
        self.FrDb.config(text=self.blabla.get('gui_fr2'))
        self.FrFilters.config(text=self.blabla.get('gui_fr3'))
        self.FrOutp.config(text=self.blabla.get('gui_fr4'))
        self.FrProg.config(text=self.blabla.get('gui_prog'))
        self.labtarg.config(text=self.blabla.get('gui_path'))
        self.browsetarg.config(text=self.blabla.get('gui_choix'))
        self.val.config(text=self.blabla.get('gui_go'))
        self.nameoutput.config(text=self.blabla.get('gui_fic'))
        self.lb_H.config(text=self.blabla.get('gui_host'))
        self.lb_P.config(text=self.blabla.get('gui_port'))
        self.lb_D.config(text=self.blabla.get('gui_db'))
        self.lb_U.config(text=self.blabla.get('gui_user'))
        self.lb_M.config(text=self.blabla.get('gui_mdp'))

        # setting locale according to the language passed
        try:
            if opersys == 'win32':
                if new_lang.lower() == "fr":
                    locale.setlocale(locale.LC_ALL, str("fra_fra"))
                elif new_lang.lower() == "es":
                    locale.setlocale(locale.LC_ALL, str("esp_esp"))
                else:
                    locale.setlocale(locale.LC_ALL, str("uk_UK"))
            else:
                if new_lang.lower() == "fr":
                    locale.setlocale(locale.LC_ALL, str("fr_FR.utf8"))
                elif new_lang.lower() == "es":
                    locale.setlocale(locale.LC_ALL, str("es_ES.utf8"))
                else:
                    locale.setlocale(locale.LC_ALL, str("en_GB.utf8"))

            logger.info("Language switched to: {0}"\
                         .format(self.ddl_lang.get()))
        except locale.Error:
            logger.error('Selected locale is not installed')

        # End of function
        return self.blabla

    def setpathtarg(self):
        """Browse and insert the path of target folder."""
        foldername = askdirectory(parent=self,
                                  initialdir=self.def_rep,
                                  mustexist=True,
                                  title=self.blabla.get('gui_cible'))
        # deactivate Go button
        self.val.config(state=DISABLED)
        # check if a folder has been choosen
        if foldername:
            try:
                self.target.delete(0, END)
                self.target.insert(0, foldername)
            except:
                info(title=self.blabla.get('nofolder'),
                     message=self.blabla.get('nofolder'))
                return
        else:
            pass
        # set the default output file
        self.output.delete(0, END)
        self.output.insert(0,
                           "DicoGIS_{0}_{1}.xlsx".format(path.split(self.target.get())[1],
                                                        self.today))
        # count geofiles in a separated thread
        proc = threading.Thread(target=self.ligeofiles,
                                args=(foldername, ))
        proc.daemon = True
        proc.start()
        # end of function
        return foldername

    def ligeofiles(self, foldertarget):
        u"""List compatible geo-files stored into a folder structure."""
        # reseting global variables
        self.li_shp = []
        self.li_tab = []
        self.li_kml = []
        self.li_gml = []
        self.li_geoj = []
        self.li_gxt = []
        self.li_vectors = []
        self.li_dxf = []
        self.li_dwg = []
        self.li_dgn = []
        self.li_cdao = []
        self.li_raster = []
        self.li_fdb = []
        self.li_egdb = []
        self.li_spadb = []
        self.li_pdf = []
        self.li_lyr = []
        self.li_mxd = []
        self.li_qgs = []
        self.browsetarg.config(state=DISABLED)

        # Looping in folders structure
        self.status.set(self.blabla.get('gui_prog1'))
        self.prog_layers.start()
        logger.info('Begin of folders parsing')
        for root, dirs, files in walk(foldertarget):
            self.num_folders = self.num_folders + len(dirs)
            for d in dirs:
                """ looking for File Geodatabase among directories """
                try:
                    unicode(path.join(root, d))
                    full_path = path.join(root, d)
                except UnicodeDecodeError:
                    full_path = path.join(root, d.decode('latin1'))
                if full_path[-4:].lower() == '.gdb':
                    # add complete path of Esri FileGeoDatabase
                    self.li_egdb.append(path.abspath(full_path))
                else:
                    pass
            for f in files:
                """ looking for files with geographic data """
                try:
                    unicode(path.join(root, f))
                    full_path = path.join(root, f)
                except UnicodeDecodeError:
                    full_path = path.join(root, f.decode('latin1'))
                # Looping on files contained
                if path.splitext(full_path.lower())[1].lower() == '.shp'\
                   and (path.isfile('{0}.dbf'.format(full_path[:-4]))
                        or path.isfile('{0}.DBF'.format(full_path[:-4])))\
                   and (path.isfile('{0}.shx'.format(full_path[:-4]))
                        or path.isfile('{0}.SHX'.format(full_path[:-4]))):
                    """ listing compatible shapefiles """
                    # add complete path of shapefile
                    self.li_shp.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.tab'\
                    and (path.isfile(full_path[:-4] + '.dat')
                         or path.isfile(full_path[:-4] + '.DAT'))\
                    and (path.isfile(full_path[:-4] + '.map')
                         or path.isfile(full_path[:-4] + '.MAP'))\
                    and (path.isfile(full_path[:-4] + '.id')
                         or path.isfile(full_path[:-4] + '.ID')):
                    """ listing MapInfo tables """
                    # add complete path of MapInfo file
                    self.li_tab.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.kml'\
                    or path.splitext(full_path.lower())[1] == '.kmz':
                    """ listing KML and KMZ """
                    # add complete path of KML file
                    self.li_kml.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.gml':
                    """ listing GML """
                    # add complete path of GML file
                    self.li_gml.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.geojson':
                    """ listing GeoJSON """
                    # add complete path of GeoJSON file
                    self.li_geoj.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.pdf':
                    """ listing GeoPDF """
                    # add complete path of PDF file
                    self.li_pdf.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.lyr':
                    """ listing Esri Layer Definition """
                    # add complete path of LYR file
                    self.li_lyr.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.mxd':
                    """ listing Esri map document """
                    # add complete path of PDF file
                    self.li_mxd.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.qgs':
                    """ listing QGIS map document """
                    # add complete path of QGS file
                    self.li_qgs.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.gxt':
                    """ listing Geoconcept eXport Text (GXT) """
                    # add complete path of GXT file
                    self.li_gxt.append(full_path)
                elif path.splitext(full_path.lower())[1] in self.li_raster_formats:
                    """ listing compatible rasters """
                    # add complete path of raster file
                    self.li_raster.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.dxf':
                    """ listing DXF """
                    # add complete path of DXF file
                    self.li_dxf.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.dwg':
                    """ listing DWG """
                    # add complete path of DWG file
                    self.li_dwg.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.dgn':
                    """ listing MicroStation DGN """
                    # add complete path of DGN file
                    self.li_dgn.append(full_path)
                elif path.splitext(full_path.lower())[1] == '.sqlite':
                    """ listing Spatialite DB """
                    # add complete path of DGN file
                    self.li_spadb.append(full_path)
                else:
                    continue

        # grouping CAO/DAO files
        self.li_cdao.extend(self.li_dxf)
        self.li_cdao.extend(self.li_dwg)
        self.li_cdao.extend(self.li_dgn)
        # grouping File geodatabases
        self.li_fdb.extend(self.li_egdb)
        self.li_fdb.extend(self.li_spadb)
        # grouping map & docs
        self.li_mapdocs.extend(self.li_pdf)
        self.li_mapdocs.extend(self.li_lyr)
        self.li_mapdocs.extend(self.li_qgs)
        self.li_mapdocs.extend(self.li_mxd)
        # end of listing
        self.prog_layers.stop()
        logger.info("End of folders parsing: {0} shapefiles - "
                     "{1} tables (MapInfo) - "
                     "{2} KML - "
                     "{3} GML - "
                     "{4} GeoJSON"
                     "{5} rasters - "
                     "{6} Esri FileGDB - "
                     "{7} Spatialite - "
                     "{8} CAO/DAO - "
                     "{9} PDF - "
                     "{10} GXT - in {11}{12}"
                     .format(len(self.li_shp), len(self.li_tab),
                             len(self.li_kml), len(self.li_gml),
                             len(self.li_geoj), len(self.li_raster),
                             len(self.li_egdb), len(self.li_spadb),
                             len(self.li_cdao), len(self.li_pdf),
                             len(self.li_gxt),
                             self.num_folders,
                             self.blabla.get('log_numfold')))
        # grouping vectors lists
        self.li_vectors.extend(self.li_shp)
        self.li_vectors.extend(self.li_tab)
        self.li_vectors.extend(self.li_kml)
        self.li_vectors.extend(self.li_gml)
        self.li_vectors.extend(self.li_geoj)
        self.li_vectors.extend(self.li_gxt)

        # Lists ordering and tupling
        self.li_shp.sort()
        self.li_shp = tuple(self.li_shp)
        self.li_tab.sort()
        self.li_tab = tuple(self.li_tab)
        self.li_raster.sort()
        self.li_raster = tuple(self.li_raster)
        self.li_kml.sort()
        self.li_kml = tuple(self.li_kml)
        self.li_gml.sort()
        self.li_gml = tuple(self.li_gml)
        self.li_geoj.sort()
        self.li_geoj = tuple(self.li_geoj)
        self.li_gxt.sort()
        self.li_gxt = tuple(self.li_gxt)
        self.li_egdb.sort()
        self.li_egdb = tuple(self.li_egdb)
        self.li_spadb.sort()
        self.li_spadb = tuple(self.li_spadb)
        self.li_fdb.sort()
        self.li_fdb = tuple(self.li_fdb)
        self.li_dxf.sort()
        self.li_dxf = tuple(self.li_dxf)
        self.li_dwg.sort()
        self.li_dwg = tuple(self.li_dwg)
        self.li_dgn.sort()
        self.li_dgn = tuple(self.li_dgn)
        self.li_cdao.sort()
        self.li_cdao = tuple(self.li_cdao)
        self.li_pdf.sort()
        self.li_pdf = tuple(self.li_pdf)
        self.li_lyr.sort()
        self.li_lyr = tuple(self.li_lyr)
        self.li_mxd.sort()
        self.li_mxd = tuple(self.li_mxd)
        self.li_qgs.sort()
        self.li_qgs = tuple(self.li_qgs)
        self.li_mapdocs.sort()
        self.li_mapdocs = tuple(self.li_mapdocs)
        # status message
        self.status.set("{0} shapefiles - "
                        "{1} tables (MapInfo) - "
                        "{2} KML - "
                        "{3} GML - "
                        "{4} GeoJSON - "
                        "{5} GXT"
                        "\n{6} rasters - "
                        "{7} file databases - "
                        "{8} CAO/DAO - "
                        "{9} PDF - "
                        "{10} LYR - "
                        "{11} QGS - "
                        "{12} MXD - "
                        "in {13}{14}"
                        .format(len(self.li_shp),
                                len(self.li_tab),
                                len(self.li_kml),
                                len(self.li_gml),
                                len(self.li_geoj),
                                len(self.li_gxt),
                                len(self.li_raster),
                                len(self.li_fdb),
                                len(self.li_cdao),
                                len(self.li_pdf),
                                len(self.li_lyr),
                                len(self.li_qgs),
                                len(self.li_mxd),
                                self.num_folders,
                                self.blabla.get('log_numfold')))

        # reactivating the buttons
        self.browsetarg.config(state=ACTIVE)
        self.val.config(state=ACTIVE)
        # End of function
        return foldertarget, self.li_shp, self.li_tab, self.li_kml,\
            self.li_gml, self.li_geoj, self.li_gxt, self.li_raster,\
            self.li_egdb, self.li_dxf, self.li_dwg, self.li_dgn,\
            self.li_cdao, self.li_fdb, self.li_spadb

    def process(self):
        """Check needed info and launch different processes."""
        # saving settings
        self.settings.save_settings(self)

        # get the active tab ID
        self.typo = self.nb.index(self.nb.select())

        # disabling UI to avoid unattended actions
        self.val.config(state=DISABLED)
        self.nb.tab(0, state=DISABLED)
        self.nb.tab(1, state=DISABLED)
        self.nb.tab(2, state=DISABLED)
        self.nb.tab(3, state=DISABLED)

        # creating the Excel workbook
        self.wb = md2xlsx(texts=self.blabla)
        logger.info('Excel file created')

        # process files or PostGIS database
        if self.typo == 0:
            self.nb.select(0)
            logger.info('PROCESS LAUNCHED: files')
            self.process_files()
        elif self.typo == 1:
            self.nb.select(1)
            self.wb.set_worksheets(has_sgbd=1)
            logger.info('PROCESS LAUNCHED: SGBD')
            self.check_fields()
        elif self.typo == 2:
            self.nb.select(2)
            logger.info('PROCESS LAUNCHED: services')
            # self.check_fields()
        elif self.typo == 3:
            self.nb.select(3)
            logger.info('PROCESS LAUNCHED: Isogeo')
            self.process_isogeo()
        else:
            pass
        self.val.config(state=ACTIVE)
        # end of function
        return self.typo

    def process_files(self):
        u"""Launch the different processes."""
        # check if at least a format has been choosen
        if (self.opt_shp.get() + self.opt_tab.get() + self.opt_kml.get() +
           self.opt_gml.get() + self.opt_geoj.get() + self.opt_rast.get() +
           self.opt_egdb.get() + self.opt_cdao.get() + self.opt_pdf.get() +
           self.opt_lyr.get()):
            pass
        else:
            avert('DicoGIS - User error', self.blabla.get('noformat'))
            return
        # check if there are some layers into the folder structure
        if (len(self.li_vectors) +
            len(self.li_raster) +
            len(self.li_fdb) +
            len(self.li_cdao) +
            len(self.li_pdf) +
            len(self.li_mapdocs) +
            len(self.li_lyr)):
            pass
        else:
            avert('DicoGIS - User error', self.blabla.get('nodata'))
            return
        # georeaders
        georeader_vector = ReadVectorFlatDataset()
        georeader_egdb = ReadGDB()

        # sheets and progress bar
        total_files = 0
        if self.opt_shp.get() and len(self.li_shp):
            total_files += len(self.li_shp)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_tab.get() and len(self.li_tab):
            total_files += len(self.li_tab)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_kml.get()and len(self.li_kml):
            total_files += len(self.li_kml)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_gml.get() and len(self.li_gml):
            total_files += len(self.li_gml)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_geoj.get() and len(self.li_geoj):
            total_files += len(self.li_geoj)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_gxt.get() and len(self.li_gxt):
            total_files += len(self.li_gxt)
            self.wb.set_worksheets(has_vector=1)
        else:
            pass
        if self.opt_rast.get() and len(self.li_raster):
            total_files += len(self.li_raster)
            self.wb.set_worksheets(has_raster=1)
        else:
            pass
        if self.opt_egdb.get() and len(self.li_egdb):
            total_files += len(self.li_egdb)
            self.wb.set_worksheets(has_filedb=1)
        else:
            pass
        if self.opt_spadb.get() and len(self.li_spadb):
            total_files += len(self.li_spadb)
            self.wb.set_worksheets(has_filedb=1)
        else:
            pass
        if self.opt_cdao.get() and len(self.li_cdao):
            total_files += len(self.li_cdao)
            self.wb.set_worksheets(has_cad=1)
        else:
            pass
        if self.opt_pdf.get() and len(self.li_pdf):
            total_files += len(self.li_pdf)
            self.wb.set_worksheets(has_mapdocs=1)
        else:
            pass
        if self.opt_lyr.get() and len(self.li_lyr):
            total_files += len(self.li_lyr)
            self.wb.set_worksheets(has_lyr=1)
        else:
            pass

        self.prog_layers["maximum"] = total_files
        self.prog_layers["value"]

        # initializing metrics
        # getting the infos from files selected
        # line_vectors = 1    # line rank of vectors dictionary
        line_rasters = 1    # line rank of rasters dictionary
        line_fdb = 1        # line rank of File DB dictionary
        line_cdao = 1       # line rank of CAO/DAO dictionary
        line_maps = 1       # line rank of maps & plans dictionary

        if self.opt_shp.get() and len(self.li_shp) > 0:
            logger.info('\n\tProcessing shapefiles: start')
            for shp in self.li_shp:
                """ looping on shapefiles list """
                self.status.set(path.basename(shp))
                logger.info('\n' + shp)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(path.abspath(shp),
                                                   self.dico_layer,
                                                   self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)

                logger.info('\t Wrote into the dictionary')
                # getting for metrics analysis
                logger.info('\t Added to global metrics')
        else:
            logger.info('\tIgnoring {0} shapefiles'.format(len(self.li_shp)))
            pass

        if self.opt_tab.get() and len(self.li_tab) > 0:
            logger.info('\n\tProcessing MapInfo tables: start')
            for tab in self.li_tab:
                """ looping on MapInfo tables list """
                self.status.set(path.basename(tab))
                logger.info('\n' + tab)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                print(self.dico_layer.get("err_gdal"))
                # getting the informations
                try:
                    georeader_vector.infos_dataset(path.abspath(tab),
                                                   self.dico_layer,
                                                   self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel file
                self.wb.store_md_vector(self.dico_layer)

                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} MapInfo tables'.format(len(self.li_tab)))
            pass

        if self.opt_kml.get() and len(self.li_kml) > 0:
            logger.info('\n\tProcessing KML-KMZ: start')
            for kml in self.li_kml:
                """ looping on KML/KMZ list """
                self.status.set(path.basename(kml))
                logger.info('\n' + kml)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(path.abspath(kml),
                                                   self.dico_layer,
                                                   self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} KML'.format(len(self.li_kml)))
            pass

        if self.opt_gml.get() and len(self.li_gml) > 0:
            logger.info('\n\tProcessing GML: start')
            for gml in self.li_gml:
                """ looping on GML list """
                self.status.set(path.basename(gml))
                logger.info('\n' + gml)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(path.abspath(gml),
                                                   self.dico_layer,
                                                   self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} GML'.format(len(self.li_gml)))
            pass

        if self.opt_geoj.get() and len(self.li_geoj) > 0:
            logger.info('\n\tProcessing GeoJSON: start')
            for geojson in self.li_geoj:
                """ looping on GeoJSON list """
                self.status.set(path.basename(geojson))
                logger.info('\n' + geojson)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_vector.infos_dataset(path.abspath(geojson),
                                                   self.dico_layer,
                                                   self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} GeoJSON'.format(len(self.li_geoj)))
            pass

        if self.opt_gxt.get() and len(self.li_gxt) > 0:
            logger.info('\n\tProcessing GXT: start')
            for gxtpath in self.li_gxt:
                """ looping on gxt list """
                self.status.set(path.basename(gxtpath))
                logger.info('\n' + gxtpath)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    ReadGXT(path.abspath(gxtpath),
                            self.dico_layer,
                            'Geoconcept eXport Text',
                            self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_vector(self.dico_layer)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} Geoconcept eXport Text'.format(len(self.li_gxt)))
            pass

        if self.opt_rast.get() and len(self.li_raster) > 0:
            logger.info('\n\tProcessing rasters: start')
            for raster in self.li_raster:
                """ looping on rasters list """
                self.status.set(path.basename(raster))
                logger.info('\n' + raster)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_raster.clear()
                self.dico_bands.clear()
                # getting the informations
                try:
                    ReadRasters(path.abspath(raster),
                                self.dico_raster,
                                self.dico_bands,
                                path.splitext(raster)[1],
                                 self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_raster(self.dico_raster,
                                        self.dico_bands)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} rasters'.format(len(self.li_raster)))
            pass

        if self.opt_egdb.get() and len(self.li_egdb) > 0:
            logger.info('\n\tProcessing Esri FileGDB: start')
            for gdb in self.li_egdb:
                """ looping on FileGDB list """
                self.status.set(path.basename(gdb))
                logger.info('\n' + gdb)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_fdb.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    georeader_egdb.infos_dataset(path.abspath(gdb),
                                                 self.dico_fdb,
                                                 self.blabla,
                                                 tipo="Esri FileGDB")
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_fdb(self.dico_fdb)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} Esri FileGDB'.format(len(self.li_egdb)))
            pass

        if self.opt_spadb.get() and len(self.li_spadb) > 0:
            logger.info('\n\tProcessing Spatialite DB: start')
            for spadb in self.li_spadb:
                """ looping on Spatialite DBs list """
                self.status.set(path.basename(spadb))
                logger.info('\n' + spadb)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_fdb.clear()
                self.dico_fields.clear()
                # getting the informations
                try:
                    ReadSpaDB(path.abspath(spadb),
                              self.dico_fdb,
                              'Spatialite',
                              self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_fdb(self.dico_fdb)
                logger.info('\t Wrote into the dictionary')
        else:
            logger.info('\tIgnoring {0} Spatialite DB'.format(len(self.li_spadb)))
            pass

        if self.opt_cdao.get() and len(self.li_cdao) > 0:
            logger.info('\n\tProcessing CAO/DAO: start')
            for dxf in self.li_dxf:
                """ looping on DXF list """
                self.status.set(path.basename(dxf))
                logger.info('\n' + dxf)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_cdao.clear()
                # getting the informations
                try:
                    ReadDXF(path.abspath(dxf),
                            self.dico_cdao,
                            'AutoCAD DXF',
                            self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_cad(self.dico_cdao)
                logger.info('\t Wrote into the dictionary')

            # for dwg in self.li_dwg:
            #     """ looping on DWG list """
            #     self.status.set(path.basename(dwg))
            #     logger.info('\n' + dwg)
            #     # increment the progress bar
            #     self.prog_layers["value"] = self.prog_layers["value"] + 1
            #     self.update()
            #     # just writing filename and link to parent folder
            #     self.feuyCDAO.write(line_cdao, 0, path.basename(dwg))

            #     # Path of parent folder formatted to be a hyperlink
            #     try:
            #         link = 'HYPERLINK("{0}"; "{1}")'.format(path.dirname(dwg),
            #                                                 self.blabla.get('browse'))
            #     except UnicodeDecodeError:
            #         # write a notification into the log file
            #         logger.warning('Path name with special letters: {}'.format(path.dirname(dwg).decode('utf8')))
            #         # decode the fucking path name
            #         link = 'HYPERLINK("{0}"; "{1}")'.format(path.dirname(dwg).decode('utf8'),
            #                                                 self.blabla.get('browse'))

            #     self.feuyCDAO.write(line_cdao, 1, Formula(link), self.url)

            #     # Name of parent folder
            #     self.feuyCDAO.write(line_cdao, 2, path.basename(path.dirname(dwg)))

            #     # logger
            #     logger.info('\t Wrote into the dictionary')
            #     # increment the line number
            #     line_cdao += 1
        else:
            logger.info('\tIgnoring {0} CAO/DAO files'.format(len(self.li_cdao)))
            pass

        if self.opt_pdf.get() and len(self.li_pdf) > 0:
            logger.info('\n\tProcessing Geospatial PDF: start')
            for pdf in self.li_pdf:
                """ looping on PDF list """
                self.status.set(path.basename(pdf))
                logger.info('\n' + pdf)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_pdf.clear()
                # getting the informations
                try:
                    ReadGeoPDF(path.abspath(pdf),
                                self.dico_pdf,
                                'Geospatial PDF',
                                self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.wb.store_md_mapdoc(self.dico_pdf)

                logger.info('\t Wrote into the dictionary')
                # increment the line number
                # line_maps += self.dico_pdf.get('layers_count') + 1
        else:
            logger.info('\tIgnoring {0} Geospatial PDF'.format(len(self.li_pdf)))
            pass

        if self.opt_lyr.get() and len(self.li_lyr) > 0:
            logger.info('\n\tProcessing Esri LYR : start')
            for lyr in self.li_lyr:
                """ looping on lyr list """
                self.status.set(path.basename(lyr))
                logger.info('\n' + lyr)
                # increment the progress bar
                self.prog_layers["value"] = self.prog_layers["value"] + 1
                self.update()
                # reset recipient data
                self.dico_layer.clear()
                self.dico_fields.clear()
                self.dico_bands.clear()
                # getting the informations
                try:
                    ReadLYR(path.abspath(lyr),
                            self.dico_layer,
                            'Esri LYR',
                            self.blabla)
                    logger.info('\t Infos OK')
                except (AttributeError, RuntimeError, Exception) as e:
                    """ empty files """
                    logger.error(e)
                    self.prog_layers["value"] = self.prog_layers["value"] + 1
                    continue
                # writing to the Excel dictionary
                self.dictionarize_lyr(self.dico_layer,
                                      self.feuyMAPS,
                                      line_maps)
                # self.wb.store_md_mapdoc(self.dico_layer)
                if self.dico_layer.get(u'type') == 'Feature':
                    self.wb.store_md_vector(self.dico_layer)
                    line_vectors = line_vectors + 1
                elif self.dico_layer.get(u'type') == 'Raster':
                    self.wb.store_md_raster(self.dico_layer, self.dico_bands)
                    line_rasters = line_rasters + 1


                logger.info('\t Wrote into the dictionary')
                # increment the line number
                line_maps += self.dico_layer.get('layers_count')
        else:
            logger.info('\tIgnoring {0} Esri LYR'.format(len(self.li_lyr)))
            pass

        # saving dictionary
        self.bell()
        self.val.config(state=ACTIVE)
        self.wb.tunning_worksheets()
        saved = utils_global.safe_save(wb=self.wb,
                                       dest_dir=self.target.get(),
                                       dest_filename=self.output.get(),
                                       ftype="Excel Workbook",
                                       dlg_title=self.blabla.get('gui_excel'))
        logger.info('\n\tWorkbook saved: %s', self.output.get())

        # quit and exit
        utils_global.open_dir_file(saved[1])
        self.destroy()
        exit()

        # End path.abspath(of) function
        return

    def process_db(self, sgbd_reader):
        u"""Process PostGIS DB analisis."""
        # getting the info from shapefiles and compile it in the excel
        logger.info('\tPostGIS table processing...')
        # setting progress bar
        self.prog_layers["maximum"] = sgbd_reader.conn.GetLayerCount()
        # parsing the layers
        for layer in sgbd_reader.conn:
            # reset recipient data
            self.dico_dataset.clear()
            sgbd_reader.infos_dataset(layer)
            logger.info('Table examined: {}'.format(layer.GetName()))
            self.wb.store_md_sgdb(self.dico_dataset)
            logger.info('\t Wrote into the dictionary')
            # increment the progress bar
            self.prog_layers["value"] = self.prog_layers["value"] + 1
            self.update()

        # saving dictionary
        self.bell()
        self.val.config(state=ACTIVE)
        self.wb.tunning_worksheets()
        saved = utils_global.safe_save(wb=self.wb,
                                       dest_dir=self.target.get(),
                                       dest_filename=self.output.get(),
                                       ftype="Excel Workbook",
                                       dlg_title=self.blabla.get('gui_excel'))
        logger.info('\n\tWorkbook saved: %s', self.output.get())

        # quit and exit
        utils_global.open_dir_file(saved[1])
        self.destroy()
        exit()

        # End of function
        return

    def check_fields(self):
        u""" Check if required fields are not empty """
        # error counter
        # checking empty fields
        if self.host.get() == u''\
           or self.host.get() == self.blabla.get("err_pg_empty_field"):
            self.ent_H.configure(foreground="red")
            self.ent_H.delete(0, END)
            self.ent_H.insert(0, self.blabla.get("err_pg_empty_field"))
            return
        else:
            pass
        if not self.ent_P.get():
            self.ent_P.configure(foreground='red')
            self.ent_P.delete(0, END)
            self.ent_P.insert(0, 0000)
            return
        else:
            pass
        if self.dbnb.get() == u''\
           or self.host.get() == self.blabla.get("err_pg_empty_field"):
            self.ent_D.configure(foreground='red')
            self.ent_D.delete(0, END)
            self.ent_D.insert(0, self.blabla.get("err_pg_empty_field"))
            return
        else:
            pass
        if self.user.get() == u''\
           or self.host.get() == self.blabla.get("err_pg_empty_field"):
            self.ent_U.configure(foreground='red')
            self.ent_U.delete(0, END)
            self.ent_U.insert(0, self.blabla.get("err_pg_empty_field"))
            return
        else:
            pass
        if self.pswd.get() == u''\
           or self.pswd.get() == self.blabla.get("err_pg_empty_field"):
            self.ent_M.configure(foreground="red")
            self.ent_M.delete(0, END)
            self.ent_M.insert(0, self.blabla.get("err_pg_empty_field"))
            return
        else:
            pass
        # no error detected: let's test connection
        logger.info("Required fields are OK.")
        self.test_connection()
        # End of function
        return

    def test_connection(self):
        """Test database connection and handling specific
        settings : proxy, DB views, etc.
        """
        self.dico_dataset = OrderedDict()
        # check if a proxy is needed
        # more information about the GDAL HTTP proxy options here:
        # http://trac.osgeo.org/gdal/wiki/ConfigOptions#GDALOGRHTTPoptions
        if self.opt_proxy.get():
            logger.info("Proxy configured.")
            gdal.SetConfigOption('GDAL_HTTP_PROXY', '{0}:{1}'.format(self.prox_server.get(),
                                                                     self.prox_port.get()))
            if self.opt_ntlm.get():
                # if authentication needs ...\
                # username/password or not (NTLM)
                gdal.SetConfigOption('GDAL_PROXY_AUTH', 'NTLM')
                gdal.SetConfigOption('GDAL_HTTP_PROXYUSERPWD', ' : ')
            else:
                pass
        else:
            logger.info("No proxy configured.")

        # testing connection settings
        sgbd_reader = ReadPostGIS(host=self.host.get(), port=self.port.get(),
                                  db_name=self.dbnb.get(), user=self.user.get(),
                                  password=self.pswd.get(),
                                  views_included=self.opt_pgvw.get(),
                                  dico_dataset=self.dico_dataset,
                                  txt=self.blabla)

        # check connection state
        if not sgbd_reader.conn:
            fail_reason = self.dico_dataset.get("conn_state")
            self.status.set("Connection failed: {0}."
                            .format(fail_reason))
            avert(title=self.blabla.get("err_pg_conn_fail"),
                  message=fail_reason)
            return None
        else:
            # connection succeeded
            pass

        self.status.set("{} tables".format(len(sgbd_reader.conn)))
        # set the default output file
        self.output.delete(0, END)
        self.output.insert(0, "DicoGIS_{0}-{1}_{2}.xlsx"
                              .format(self.dbnb.get(),
                                      self.host.get(),
                                      self.today))
        # launching the process
        self.process_db(sgbd_reader)
        # end of function
        return sgbd_reader

    def process_isogeo(self):
        """Extract Isogeo metadata catalog into an Excel worksheet."""
        # getting and checking the OpenCatalog given
        url_oc = self.url_OpenCatalog.get()
        if url_oc[:4] != "http":
            print(url_oc[:4])
        else:
            pass

        # extracting metadata with the API
        dico_md = OrderedDict()
        lang = self.ddl_lang.get()
        ReadIsogeoOpenCatalog(url_oc, lang, dico_md)

        # creating the Excel file
        sheet_isogeo = self.book._Workbook__worksheets[0]

        offset = 0
        # fillfulling metadata
        for md in dico_md.get('resources'):
            # incrémente le numéro de ligne
            offset += 1
            # extraction des mots-clés et thématiques
            tags = md.get("tags")
            li_motscles = [tags.get(tag) for tag in tags.keys() if tag.startswith('keyword:isogeo')]
            li_theminspire = [tags.get(tag) for tag in tags.keys() if tag.startswith('keyword:inspire-theme')]

            # formatage des liens pour visualiser et éditer
            link_visu = 'HYPERLINK("{0}"; "{1}")'.format(url_oc + "/m/" + md.get('_id'),
                                                         "Visualiser")
            link_edit = 'HYPERLINK("{0}"; "{1}")'.format("https://app.isogeo.com/resources/" + md.get('_id'),
                                                         "Editer")
            # écriture des informations dans chaque colonne correspondante
            sheet_isogeo.write(offset, 0, md.get("title"))
            sheet_isogeo.write(offset, 1, md.get("name"))
            sheet_isogeo.write(offset, 2, md.get("path"))
            sheet_isogeo.write(offset, 3, " ; ".join(li_motscles))
            sheet_isogeo.write(offset, 4, md.get("abstract"))
            sheet_isogeo.write(offset, 5, " ; ".join(li_theminspire))
            sheet_isogeo.write(offset, 6, md.get("type"))
            sheet_isogeo.write(offset, 7, md.get("format"))
            sheet_isogeo.write(offset, 7, md.get("coordinate-system"))
            sheet_isogeo.write(offset, 9, md.get("features"))
            sheet_isogeo.write(offset, 10, Formula(link_visu), self.url)
            sheet_isogeo.write(offset, 11, Formula(link_edit), self.url)

        # saving dictionary
        self.savedico()
        logger.info('\n\tWorkbook saved: %s', self.output.get())

        # quit and exit
        utils_global.open_dir_file(self.output.get())
        self.destroy()
        exit()

        # end of function
        return

    def dictionarize_lyr(self, mapdoc_infos, sheet, line):
        u""" write the infos of the map document into the Excel workbook """
        # in case of a source error
        if mapdoc_infos.get('error'):
            logger.warning('\tproblem detected')
            # source name
            sheet.write(line, 0, mapdoc_infos.get('name'))
            # link to parent folder
            link = 'HYPERLINK("{0}"; "{1}")'.format(mapdoc_infos.get(u'folder'),
                                                    self.blabla.get('browse'))
            sheet.write(line, 1, Formula(link), self.url)
            sheet.write(line, 2, self.blabla.get(mapdoc_infos.get('error')),
                        self.xls_erreur)
            # incrementing line
            mapdoc_infos['layers_count'] = 0
            # exiting function
            return sheet, line
        else:
            pass

        # PDF source name
        sheet.write(line, 0, mapdoc_infos.get('name'))

        # Path of parent folder formatted to be a hyperlink
        try:
            link = 'HYPERLINK("{0}"; "{1}")'.format(mapdoc_infos.get(u'folder'),
                                                    self.blabla.get('browse'))
        except UnicodeDecodeError:
            # write a notification into the log file
            logger.warning('Path name with special letters: {}'.format(mapdoc_infos.get(u'folder').decode('utf8')))
            # decode the fucking path name
            link = 'HYPERLINK("{0}"; "{1}")'.format(mapdoc_infos.get(u'folder').decode('utf8'),
                                                    self.blabla.get('browse'))

        sheet.write(line, 1, Formula(link), self.url)

        # Name of parent folder
        sheet.write(line, 2, path.basename(mapdoc_infos.get(u'folder')))

        # Document title
        sheet.write(line, 3, mapdoc_infos.get(u'title'))

        # Type of lyr
        sheet.write(line, 4, mapdoc_infos.get(u'type'))

        # Type of lyr
        sheet.write(line, 5, mapdoc_infos.get(u'license'))

        # subject
        sheet.write(line, 6, mapdoc_infos.get(u'description'))

        # total size
        sheet.write(line, 8, mapdoc_infos.get(u'total_size'))

        # Creation date
        sheet.write(line, 9, mapdoc_infos.get(u'date_crea'), self.xls_date)
        # Last update date
        sheet.write(line, 10, mapdoc_infos.get(u'date_actu'), self.xls_date)

        if mapdoc_infos.get(u'type') in ['Feature', 'Raster']:
            # Spatial extent
            emprise = u"Xmin : {0} - Xmax : {1} \
                       \nYmin : {2} - Ymax : {3}".format(unicode(mapdoc_infos.get(u'Xmin')),
                                                         unicode(mapdoc_infos.get(u'Xmax')),
                                                         unicode(mapdoc_infos.get(u'Ymin')),
                                                         unicode(mapdoc_infos.get(u'Ymax'))
                                                         )
            sheet.write(line, 11, emprise, self.xls_wrap)

            # SRS name
            sheet.write(line, 13, mapdoc_infos.get(u'srs'))
            # Type of SRS
            sheet.write(line, 14, mapdoc_infos.get(u'srs_type'))
            # EPSG code
            sheet.write(line, 15, mapdoc_infos.get(u'EsriSRS')[0])
        else:
            pass

        if mapdoc_infos.get(u'type') == u'Group':
            # Layers count
            sheet.write(line, 16, mapdoc_infos.get(u'layers_count'))
            # layer's name
            sheet.write(line + 1, 16, ' ; '.join(mapdoc_infos.get(u'layers_names')))
        else:
            pass

        if mapdoc_infos.get(u'type') == u'Feature':
            # number of fields
            sheet.write(line, 17, mapdoc_infos.get(u'num_fields'))

            # number of objects
            sheet.write(line, 18, mapdoc_infos.get(u'num_obj'))

            # definition query
            sheet.write(line, 7, mapdoc_infos.get(u'defquery'))

            # fields domain
            fields_info = mapdoc_infos.get(u'fields')
            champs = ""
            for chp in fields_info.keys():
                tipo = fields_info.get(chp)[0]
                # concatenation of field informations
                try:
                    champs = champs + chp +\
                              u" (" + tipo + self.blabla.get(u'longueur') +\
                              unicode(fields_info.get(chp)[1]) +\
                              self.blabla.get(u'precision') +\
                              unicode(fields_info.get(chp)[2]) + u") ; "
                except UnicodeDecodeError:
                    # write a notification into the log file
                    self.dico_err[layer_infos.get('name')] = self.blabla.get(u'err_encod')\
                                                        + chp.decode('latin1') \
                                                        + u"\n\n"
                    logger.warning('Field name with special letters: {}'.format(chp.decode('latin1')))
                    # decode the fucking field name
                    champs = champs + chp.decode('latin1') \
                    + u" ({}, Lg. = {}, Pr. = {}) ;".format(tipo,
                                                            fields_info.get(chp)[1],
                                                            fields_info.get(chp)[2])
                    # then continue
                    continue

            # Once all fieds explored, write them
            sheet.write(line, 19, champs)

            # write layer's name into the log
            # logger.info('\t -- {0} = OK'.format(mapdoc_layer.get(u'title')))

        else:
            pass

        # End of function
        return self.feuyMAPS, line

# ############################################################################
# #### Stand alone program ########
# #################################

if __name__ == '__main__':
    """ standalone execution """
    app = DicoGIS()
    app.mainloop()
