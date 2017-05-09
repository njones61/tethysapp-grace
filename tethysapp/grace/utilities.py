import rasterio
from rasterio.tools.mask import mask
import os
from netCDF4 import Dataset
import os,os.path
import datetime
import numpy as np
import shapefile as sf
import os, tempfile, shutil,sys
import gdal
import ogr
import osr
import requests
import csv
from grace import get_netcdf_info


def create_global_geotiffs(file_dir,geotiff_dir):

    # Specify the relative file location
    start_date = '01/01/2002'  # Date that GRACE data is available from

    for file in os.listdir(file_dir): #Looping through the directory
        if file is None:
            print "No files to parse"
            sys.exit()
        nc_fid = Dataset(file_dir+file,'r') #Reading the netcdf file
        nc_var = nc_fid.variables #Get the netCDF variables
        nc_var.keys() #Getting variable keys
        time = nc_var['time'][:] #Get the all the avaialable timesteps. Timestep increment value is x days after startdate

        lwe_thickness = nc_var['lwe_thickness'][:,:,:] #Array with the all the values for lwe_thickness

        date_str = datetime.datetime.strptime(start_date, "%m/%d/%Y") #Start Date string.


        var = "lwe_thickness" #Specifying the variable key. This parameter will be used to retrieve information about the netCDF file
        xsize, ysize, GeoT, Projection, NDV = get_netcdf_info(file_dir+file, var) #Get information about the netCDF file

        ts_one = nc_var['lwe_thickness'][0,:,:]




        unique_vals = set()
        for i in ts_one:
            for j in i:
                if float(j) not in unique_vals:
                    unique_vals.add(float(j))

        x = []
        y = []
        for i in unique_vals:
            idx = np.where(nc_var['lwe_thickness'][0,:,:] == float(i))
            x = x + idx[0].tolist()
            y = y + idx[1].tolist()

        x_y = zip(x,y)

        grace_points = []
        for i in x_y:
            grace_json = {}  # Empty json object to store the corresponding latitude, longitude and lwe thickness value
            latitude = nc_var['lat'][i[0]]
            longitude = nc_var['lon'][i[1]]
            thickness = nc_var['lwe_thickness'][0, i[0], i[1]]

            # Saving all the values to the jon dictionary
            grace_json["latitude"] = latitude
            grace_json["longitude"] = longitude
            grace_json["thickness"] = thickness
            grace_points.append(grace_json)

            # Creating the shapefile from the json dictionaries, then converting it to a raster
        try:
            file_name = 'grace_sites'
            temp_dir = tempfile.mkdtemp()  # Creating a temporary directory to save the shapefile
            file_location = temp_dir + "/" + file_name

            w = sf.Writer(sf.POINT)  # Creating a point shapefile
            w.field('thickness')  # Creating an attribute field called thickness for storing the variable value

            # Looping through the list of json dictionaries to create points
            for item in grace_points:
                w.point(float(item['longitude']), float(item['latitude']))  # Creating the point
                w.record(item['thickness'], 'Point')  # Assigning value to the point
            w.save(file_location)

            # Creating a projection file for the shapefile
            prj = open("%s.prj" % file_location, "w")
            epsg = 'GEOGCS["WGS84",DATUM["WGS_1984",SPHEROID["WGS84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
            prj.write(epsg)
            prj.close()

            # Begin the conveersion to a raster

            NoData_value = -9999  # Specifying no data value
            shp_file = file_location + ".shp"  # Find the shapefile location

            out_loc = geotiff_dir + "tsone" + ".tif"  # Specify the GeoTiff name and output

            source_ds = ogr.Open(shp_file)  # Reading the shapefile
            source_layer = source_ds.GetLayer()  # Getting the actual layer
            spatialRef = source_layer.GetSpatialRef()  # Get the Spatial Reference

            raster_layer = gdal.GetDriverByName('GTiff').Create(out_loc, xsize, ysize, 1,
                                                                gdal.GDT_Float32)  # Initializing an empty GeoTiff
            raster_layer.SetProjection(
                spatialRef.ExportToWkt())  # Set the projection based on the shapefile projection
            raster_layer.SetGeoTransform(GeoT)  # Set the Geotransform.
            band = raster_layer.GetRasterBand(1)  # Specifying the number of bands
            band.SetNoDataValue(NoData_value)  # Setting no data values

            band.FlushCache()  # This call will recover memory used to cache data blocks for this raster band, and ensure that new requests are referred to the underlying driver.

            gdal.RasterizeLayer(raster_layer, [1], source_layer,
                                options=["ATTRIBUTE=thickness"])  # Create the GeoTiff layer
        except:
            print "Error parsing the data. Please check directory and try again."
            sys.exit()
            return False

def get_netcdf_info_global(filename,var_name):

    nc_file = gdal.Open(filename)

    if nc_file is None:
        print "Failed to open file, check directory and try again."
        sys.exit()

    #There are more than two variables, so specifying the lwe_thickness variable

    if nc_file.GetSubDatasets() > 1:
        subdataset = 'NETCDF:"'+filename+'":'+var_name #Specifying the subset name
        src_ds_sd = gdal.Open(subdataset) #Reading the subset
        NDV = src_ds_sd.GetRasterBand(1).GetNoDataValue() #Get the nodatavalues
        xsize = src_ds_sd.RasterXSize #Get the X size
        ysize = src_ds_sd.RasterYSize #Get the Y size
        GeoT = src_ds_sd.GetGeoTransform() #Get the GeoTransform
        Projection = osr.SpatialReference() #Get the SpatialReference
        Projection.ImportFromWkt(src_ds_sd.GetProjectionRef()) #Setting the Spatial Reference
        src_ds_sd = None #Closing the file
        nc_file = None #Closing the file


        return xsize,ysize,GeoT,Projection,NDV #Return data that will be used to convert the shapefile



def clip_raster():
    geoms = [{
        "type": "Polygon",
        "coordinates": [
          [
            [
              79.78271484375,
              25.997549919572112
            ],
            [
              88.57177734375,
              25.997549919572112
            ],
            [
              88.57177734375,
              30.713503990354965
            ],
            [
              79.78271484375,
              30.713503990354965
            ],
            [
              79.78271484375,
              25.997549919572112
            ]
          ]
        ]
      }]

    file_input_dir = '/home/tethys/geotiff/'
    file_outut_dir = '/home/tethys/geotiff_clipped/'
    for file in os.listdir(file_input_dir):
        with rasterio.open(file_input_dir+file) as src:
            out_image, out_transform = mask(src, geoms, crop=True)
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        with rasterio.open(file_outut_dir+file, "w", **out_meta) as dest:
            dest.write(out_image)

