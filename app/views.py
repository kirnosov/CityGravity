from __future__ import print_function
from flask import render_template,request
from app import app
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
from decimal import *
import MySQLdb
import pandas.io.sql as psql
import time
import datetime
import urllib2
import json
from MySQLdb.converters import conversions
from MySQLdb.constants import FIELD_TYPE

import keys


conversions[FIELD_TYPE.DECIMAL] = float
conversions[FIELD_TYPE.NEWDECIMAL] = float

conn = MySQLdb.connect(user=keys.SQL_user, host="localhost", db=keys.SQL_db, passwd=keys.SQL_password, 
                       charset='utf8',unix_socket="/tmp/mysql.sock")
cur = conn.cursor()
results = None
sql = "SELECT DISTINCT City  FROM hotels;"
results=psql.read_sql(sql, conn)
sql='SHOW COLUMNS IN clustersobjects'
attr_types=list(DataFrame(psql.read_sql(sql, conn)).Field[:-1]) 
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

  #pull 'ID' from input field and store it
  wrong_codes=[]
  region = request.args.get('ID')
  attr_type_user=request.args.getlist('attr_types_user')
  user_stars=request.args.getlist('stars')
  user_rate=request.args.getlist('rate')
  if ('ALL' in attr_type_user): attr_type_user=attr_types[1:]
  user_input=[region,user_stars[0],user_rate[0],attr_type_user]
  other_attr=[x for x in attr_types if (x not in user_input[3])]

  for i in range(len(user_input)):
    if ( not user_input[i]): 
      wrong_codes.append(wrong_dict[i+1])
  if len(wrong_codes)>1 : return render_template("input_wrong.html",user_input=user_input,
        results=results,attr_types=attr_types,wrong_codes=wrong_codes,
        other_attr=other_attr)

  cur = conn.cursor()
  sql='DROP TEMPORARY TABLE IF EXISTS temp_table;'
  cur.execute(sql)
  sql='CREATE TEMPORARY TABLE temp_table'+\
    ' SELECT SUM(commutetime.CommuteTime*(%s)) AS TimeOverWeight, commutetime.EANHotelID FROM clustersobjects'%('+'.join(user_input[3]))+\
    ' INNER JOIN clusters ON clustersobjects.ClusterNum=clusters.ClusterNum'+\
    ' INNER JOIN commutetime ON commutetime.ClusterNum=clusters.ClusterNum'+\
    ' WHERE clusters.City="%s" GROUP BY commutetime.EANHotelID ORDER BY TimeOverWeight;'%(user_input[0])
  cur.execute(sql)
  sql='SELECT hotels.EANHotelID,hotels.Name,hotels.LowRate,hotels.Latitude,hotels.Longitude,'+\
    ' hotels.StarRating,temp_table.TimeOverWeight'+\
    ' FROM hotels INNER JOIN temp_table ON temp_table.EANHotelID=hotels.EANHotelID'+\
    ' WHERE hotels.StarRating>=%s AND hotels.LowRate BETWEEN 10 AND %s;'%(user_input[1],user_input[2])
  hotels=DataFrame(psql.read_sql(sql, conn))



  sql='DROP TEMPORARY TABLE IF EXISTS temp_table;'
  cur.execute(sql)
  sql='CREATE TEMPORARY TABLE temp_table'+\
    ' SELECT %s AS Weight, clustersobjects.ClusterNum FROM clustersobjects'%('+'.join(user_input[3]))+\
    ' INNER JOIN clusters ON clustersobjects.ClusterNum=clusters.ClusterNum'+\
    ' WHERE clusters.City="%s"'%(user_input[0])
  cur.execute(sql)
  sql='SELECT RegionName,Latitude,Longitude,SubClassification,attractions.ClusterNum '+\
    ' FROM attractions INNER JOIN temp_table ON temp_table.ClusterNum=attractions.ClusterNum'+\
    ' WHERE temp_table.Weight>0 AND SubClassification IN ("%s");'%('","'.join(user_input[3]))
  attractions=DataFrame(psql.read_sql(sql, conn))
  
  if len(hotels.index)<1: return render_template("input_wrong.html",user_input=user_input,
    results=results,attr_types=attr_types,wrong_codes=['No accomodations found to match your request'],
    other_attr=other_attr)
  if attractions.empty: return render_template("input_wrong.html",user_input=user_input,
    results=results,attr_types=attr_types,wrong_codes=['There are no attractions of this type in this area'],
    other_attr=other_attr)

  hhh=hotels.sort('TimeOverWeight')
  hhh_max=max(hhh[0:].TimeOverWeight)
  hhh_mean=np.mean(hhh[0:].TimeOverWeight)
  hhh_top=hhh[0:9].TimeOverWeight

  marker_lat=list(hhh[0:10].Latitude)
  marker_lon=list(hhh[0:10].Longitude)
  marker_ID=list(hhh[0:10].EANHotelID)
  marker_name=list(hhh[0:10].Name)


  return render_template("output.html",
        hotels = hhh[0:10],
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
