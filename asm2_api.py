# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 18:06:12 2019

@author: danielm
"""

import os
import time

import psycopg2
from psycopg2 import sql
from flask import Flask, flash, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = "super secret key"


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/PVuur/<loc>")
def get_PVuur(loc):
    query = """
SELECT array_to_json(array_agg(row_to_json(tab))) 
FROM (
    SELECT dag*24 + uur AS x, (a.percentage_pvpower * b.benut_potentieel) AS y
    FROM asm2_zon_2020.pv_profiel2_uur a
    JOIN asm2_zon_2020.pvhuidig_buurt b
    ON b.code = %s
    ORDER BY dag, uur
) tab
    """
    connection = psycopg2.connect(user = "danielm",
                                  password = "",
                                  host = "localhost",
                                  port = "5432",
                                  database = "pico")
    cursor = connection.cursor()
    cursor.execute(query, (loc,))
    result = cursor.fetchone()[0]
    connection.close()
    return jsonify(result)


@app.route("/PVdag/<loc>")
def get_PVdag(loc):
    query = """
SELECT array_to_json(array_agg(row_to_json(tab))) 
FROM (
    SELECT dag AS x, SUM(a.percentage_pvpower * b.benut_potentieel) AS y
    FROM asm2_zon_2020.pv_profiel2_uur a
    JOIN asm2_zon_2020.pvhuidig_buurt b
    ON b.code = %s
    GROUP BY dag
    ORDER BY dag
) tab
    """
    connection = psycopg2.connect(user = "danielm",
                                  password = "",
                                  host = "localhost",
                                  port = "5432",
                                  database = "pico")
    cursor = connection.cursor()
    cursor.execute(query, (loc,))
    result = cursor.fetchone()[0]
    connection.close()
    return jsonify(result)

@app.route("/buurt/<z>/<x>/<y>")
def get_buurt_tiles(z, x, y):
    query = """
    SELECT ST_AsMVT(q, 'buurt', 4096, 'mvt_geom')
         FROM (
                 SELECT
                 id, name, gemeente,
                 ST_AsMVTGeom(
                         geom_3857,
                         TileBBox(%(z)s, %(x)s, %(y)s),
                         4096,
                         256,
                         false
                 ) mvt_geom
                 FROM danielm.buurten_tiles  
                 WHERE geom_3857 && TileBBox(%(z)s, %(x)s, %(y)s)
                 AND ST_Intersects(geom_3857, TileBBox(%(z)s, %(x)s, %(y)s))
         ) q;
    """
    connection = psycopg2.connect(user = "danielm", password = "", host = "localhost", port = "5432", database = "pico")
    cursor = connection.cursor()
    cursor.execute(query, {'z': z, 'x': x, 'y': y})
    result = cursor.fetchone()[0]
    connection.close()
    response = app.make_response(bytes(result))
    response.headers['Content-Type'] = 'application/x-protobuf'
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response


@app.route("/winddag/<loc>")
def get_winddag(loc):
    query = """
SELECT array_to_json(array_agg(row_to_json(tab))) 
FROM (
	SELECT c.jaardag AS x, SUM(c.yield_kwh) * MAX(d.fractie) AS y
    FROM resgebieden.resgebieden2018 a
    JOIN asm2_wind_2020.wind_turbine_locations_present b
    ON ST_WITHIN(b.geom, a.geom)
    JOIN danielm.buurt_res_fractie d
	ON a.res_code = d.res_code
	AND d.bu_code = %s
    JOIN asm2_wind_2020.wind_turbine_profile c
    ON b.turbine_id = c.turbine_id
    GROUP BY c.jaardag
    ORDER BY c.jaardag
) tab
    """
    connection = psycopg2.connect(user = "danielm",
                                  password = "",
                                  host = "localhost",
                                  port = "5432",
                                  database = "pico")
    cursor = connection.cursor()
    cursor.execute(query, (loc,))
    result = cursor.fetchone()[0]
    connection.close()
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1700)



