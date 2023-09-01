from typing import List
from math import log10
from pathlib import Path

import pygmt
import xarray as xr
import geopandas as gp

from xarray.core.dataarray import DataArray
from shapely.geometry import Polygon

from nzshm_common.location.location import location_by_id

from nzshm_hazlab.store.levels import get_hazard_at_poe
from nzshm_hazlab.data_functions import compute_hazard_at_poe

CPT_FILEPATH = Path('/tmp/tmp.cpt')

def clear_cpt():
    if CPT_FILEPATH.exists():
        CPT_FILEPATH.unlink()


def get_poe_grid(hazard_id, vs30, imt, agg, poe):

    haz_poe = get_hazard_at_poe(hazard_id, vs30, imt, agg, poe)
    haz_poe = haz_poe.pivot(index="lat", columns="lon")
    haz_poe = haz_poe.droplevel(0, axis=1)
    return xr.DataArray(data=haz_poe)


def load_polygons():

    faults = gp.read_file('/home/chrisdc/NSHM/DATA/Crustal_Rupture_Set_RmlsZToxMDAwODc=/fault_sections.geojson')
    ba_poly = Polygon(   [
                                (177.2, -37.715),
                                (176.2, -38.72),
                                (175.375, -39.27),
                                (174.25, -40),
                                (173.1, -39.183),
                                (171.7, -34.76),
                                (173.54, -33.22),
                                (177.2, -37.715),
                                ]
                            )
    backarc = gp.GeoSeries([ba_poly])
    hikurangi = gp.read_file('/home/chrisdc/NSHM/DATA/interface_polygons/subduction_polygon.geojson')
    puysegur = gp.read_file('/home/chrisdc/NSHM/DATA/interface_polygons/puysegur_polygon.geojson')

    return faults, backarc, hikurangi, puysegur


def plot_map(
        grid: DataArray,
        dpi,
        font,
        font_annot,
        plot_width,
        legend_text,
        region = None,
        plot_cities=None,
        plot_faults=False,
        contours=None,
):

    pygmt.config(FONT_LABEL=font, FONT_ANNOT_PRIMARY=font_annot)
    # pygmt.config()

    projection = f'M{plot_width}c'
    if not region:
        region = "165/180/-48/-34"

    fig = pygmt.Figure()

    if grid is None:
        fig.coast(shorelines = True, water="white", frame = "a", projection=projection, region=region)
        faults, backarc, hikurangi, puysegur = load_polygons()
        fig.plot(data=hikurangi,fill="220/220/220",transparency=30,pen="black")
        fig.plot(data=puysegur,fill="220/220/220",transparency=30,pen="black")
        fig.plot(data=faults, pen="red")
        fig.basemap(frame=["a"])

        if plot_cities:
            names = [location_by_id(city)['name'] for city in plot_cities] 
            lats = [location_by_id(city)['latitude'] for city in plot_cities] 
            lons = [location_by_id(city)['longitude'] for city in plot_cities] 
            lats_txt = [lat + 0.15 for lat in lats]
            lons_txt = [lon + 0.2 for lon in lons]
            fig.plot(x=lons, y=lats, style="c0.2c", fill="white", pen="black")
            fig.text(text=names, x=lons_txt, y=lats_txt, justify="BL", fill="211", font="8p", clearance="20%/20%+tO")

        fig.show()
        return fig
            
    fig.grdimage(grid=grid, region=region, projection=projection, cmap = '/tmp/tmp.cpt', dpi = dpi, frame = "a")
    if contours:
        fig.grdcontour(grid=grid, annotation=contours['annotation'], interval=contours['interval'], label_placement=contours['label_placement'])
    # fig.coast(shorelines = True, water="white", region=region, projection=projection, frame = "a")
    fig.coast(shorelines = True, water="white")
    # fig.basemap(frame=["a", f"+t{vs30}m/s {imt} {poe*100:.0f}% in 50 yrs"])
    fig.basemap(frame=["a"])

    if plot_faults:
        faults, backarc, hikurangi, puysegur = load_polygons()
        fig.plot(data=hikurangi,fill="220/220/220",transparency=60,pen="black")
        fig.plot(data=puysegur,fill="220/220/220",transparency=60,pen="black")
        fig.plot(data=faults)
        # fig.plot(data=backarc, pen="1p,red")
        # filepath = Path(full_dir,f'{hazard_model["id"]}-{vs30}-{imt}-{poe}_faults.{filetype}')
        # filepath = Path(full_dir,f'{hazard_model["id"]}-{vs30}-{imt}-{poe}.{filetype}')
    
    if plot_cities:
        names = [location_by_id(city)['name'] for city in plot_cities] 
        lats = [location_by_id(city)['latitude'] for city in plot_cities] 
        lons = [location_by_id(city)['longitude'] for city in plot_cities] 
        lats_txt = [lat + 0.15 for lat in lats]
        lons_txt = [lon + 0.2 for lon in lons]
        fig.plot(x=lons, y=lats, style="c0.2c", fill="white", pen="black")
        fig.text(text=names, x=lons_txt, y=lats_txt, justify="BL", fill="211", font="8p", clearance="20%/20%+tO")
            
    # fig.colorbar(xshift='40c', yshift='10c', position='+w27c/3c+h', frame=f'af+l"{imt} ({poe*100:.0f}% PoE in 50)"')#,position='+ef')
    # fig.colorbar(frame=f'af+l"{legend_text}"')
    font = f'{int(int(font[:-1])*0.8)}p'
    font_annot = font
    pygmt.config(FONT_LABEL=font, FONT_ANNOT_PRIMARY=font_annot)
    fig.colorbar(frame=f'af+l"{legend_text}"', projection=projection, region=region, position="n0.5/0.07+w4.5c/6%+h+ml")
            
    # fig.savefig(filepath)
    fig.show()

    return fig


def plot_hazard_map(
        grid: DataArray,
        colormap,
        dpi,
        climits: List[float],
        font,
        font_annot,
        plot_width,
        legend_text,
        region=None,
        plot_cities=None,
        plot_faults=False
):

    clear_cpt()
    if grid is not None:
        pygmt.makecpt(cmap = colormap, log=True, series=[log10(climits[0]), log10(climits[1]), 0.1], output=str(CPT_FILEPATH))
    return plot_map(grid, dpi, font, font_annot, plot_width, legend_text, region, plot_cities, plot_faults)


def plot_hazard_diff_map(
        grid1: DataArray,
        grid2: DataArray,
        diff_type,
        dpi,
        climits: List[float],
        font,
        font_annot,
        plot_width,
        legend_text,
        region=None,
        plot_faults=False,
        contours=None,
):


    if diff_type == 'sub':
        dgrid = grid2 - grid1
        if not climits:
            max_diff = max(abs(float(dgrid.min())), abs(float(dgrid.max())))
            climits = (-max_diff, max_diff)
        pygmt.makecpt(cmap = "blue,white,red", series=f"{climits[0]},0.0,{climits[1]}", continuous=True, output=str(CPT_FILEPATH))
    elif diff_type == 'ratio':
        if not climits:
            raise Exception('color bar limits must be set when plotting ratio map')
        dgrid = grid2/grid1
        pygmt.makecpt(cmap = "blue,white,red", series=f"{climits[0]},1.0,{climits[1]}", continuous=True, output=str(CPT_FILEPATH))
    else:
        raise Exception('diff type %s not recognized' % diff_type)

    return plot_map(dgrid, dpi, font, font_annot, plot_width, legend_text, region, plot_faults, contours=contours)  
    