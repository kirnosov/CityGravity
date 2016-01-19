from __future__ import print_function
from flask import render_template,request
from app import app
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
from decimal import *
import mysql.connector as MySQLdb
import pandas.io.sql as psql
import time
import datetime

import keys
import sys

# connect to the database
conn = MySQLdb.connect(user=keys.SQL_user, host="localhost", db=keys.SQL_db, passwd=keys.SQL_password, 
                       charset='utf8',unix_socket="/tmp/mysql.sock")
cur = conn.cursor()
results = None

# pull available cities to make the input searchable
sql = "SELECT City FROM hotels GROUP BY City;"
results=psql.read_sql(sql, conn)


sql='SELECT attraction_type FROM attr_type;'
attr_types=list(DataFrame(psql.read_sql(sql, conn))['attraction_type'])
attr_types.append('ALL')
attr_types.sort()

@app.route('/')
@app.route('/index')
@app.route('/input')
def hotels_input():
    return render_template("input.html",results=results,attr_types=attr_types)

@app.route('/talk')
def talk():
    return render_template("talk.html")

@app.route('/output')
def hotels_output():

  #pull info from input field and store it
  wrong_codes=[]
  region = request.args.get('ID')
  attr_type_user=request.args.getlist('attr_types_user')
  user_stars=request.args.getlist('stars')
  user_rate=request.args.getlist('rate')
  if ('ALL' in attr_type_user): attr_type_user=attr_types[1:]
  user_input=[region,user_stars[0],user_rate[0],attr_type_user]
  other_attr=[x for x in attr_types if (x not in user_input[3])]

  #check that everything went smoothly, protect against injection
  for i in range(len(user_input)):
    if ( not user_input[i]): 
      wrong_codes.append(wrong_dict[i+1])
  if len(wrong_codes)>1 : return render_template("input_wrong.html",user_input=user_input,
        results=results,attr_types=attr_types,wrong_codes=wrong_codes,
        other_attr=other_attr)

  #connect to the db 
  cur = conn.cursor()

  #prepare temp table and calculate cluster weights
  cur.callproc('make_weights1', [user_input[0],"','".join(user_input[3])])

  #pull attractions
  cur.callproc('get_attractions1', ["','".join(user_input[3])])
  attractions = DataFrame(cur.stored_results().next().fetchall())

  #pull hotels (sorted)
  cur.callproc('hotel_torques', [user_input[1],user_input[2]])
  hotels=DataFrame(cur.stored_results().next().fetchall())

  #check that the result is not empty
  if len(hotels.index)<1: return render_template("input_wrong.html",user_input=user_input,
    results=results,attr_types=attr_types,wrong_codes=['No accomodations found to match your request'],
    other_attr=other_attr)
  if attractions.empty: return render_template("input_wrong.html",user_input=user_input,
    results=results,attr_types=attr_types,wrong_codes=['There are no attractions of this type in this area'],
    other_attr=other_attr)

  #give column names
  attractions.columns =['RegionName','Latitude','Longitude','ClusterNum']
  hotels.columns =['EANHotelID','Name','LowRate','Latitude','Longitude','StarRating','TimeOverWeight']

  #choose max number of hotels to show
  number_h = 10
  h_top=hotels[0:number_h]

  marker_lat=list(h_top.Latitude)
  marker_lon=list(h_top.Longitude)
  marker_ID=list(h_top.EANHotelID)
  marker_name=list(h_top.Name)


  return render_template("output.html",
        hotels = h_top,
        results=results,
        user_input=user_input,
        marker_lat=marker_lat, 
        marker_lon=marker_lon, 
        marker_ID=marker_ID,
        attractions=attractions,
        marker_name=marker_name,
        center_lat=np.mean(marker_lat),
        center_lon=np.mean(marker_lon),
        other_attr=other_attr)


############################################################################
wrong_dict = {
  1:'Specify city',
  2:'Specify star rating',
  3:'Specify rate per night',
  4:'Specify attractions',
  5:'No accomodations found to match your request',
  6:'There are no attractions of this type in this area'
}
#user_input=[region,user_stars[0],user_rate[0],attr_type_user]


