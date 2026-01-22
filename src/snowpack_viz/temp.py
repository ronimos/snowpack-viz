
import pandas as pd
from io import StringIO
from pathlib import Path

units = '- W/m2 W/m2 W/m2 K W/m2 W/m2 kJ/m2 kJ/m2 MJ/m2 W/m2 W/m2 W/m2 W/m2 W/m2 W/m2 - - W/m2 W/m2 W/m2 K K K K - m/s m/s °  kg/m2/h m m m m m m m m m m m kg/m2 kg/m2 kg/m2 kg/m2 kg/m2/h kg/m2/h kg/m2 kg/m2 kg/m2 kg/m2 kg/m2 - - m - m - m - m - m - '.split()
plot_description = 'timestamp  sensible_heat  latent_heat  ground_heat  ground_temperature  ground_heat_at_soil_interface  rain_energy  snow_internal_energy_change  snow_melt_freeze_energy  snow_cold_content outgoing_long_wave_radiation  incoming_long_wave_radiation  net_long_wave_radiation reflected_short_wave_radiation  incoming_short_wave_radiation  net_short_wave_radiation  parametrized_albedo  measured_albedo  incoming_short_wave_on_horizontal  direct_incoming_short_wave  diffuse_incoming_short_wave air_temperature  surface_temperature(mod)  surface_temperature(meas)  bottom_temperature  relative_humidity  wind_velocity  wind_velocity_drift  wind_direction  solid_precipitation_rate  snow_height(mod)  snow_height(meas) hoar_size  24h_wind_drift 3h_height_of_new_snow 6h_height_of_new_snow 12h_height_of_new_snow 24h_height_of_new_snow 3d_sum_of_daily_height_of_new_snow 24h_percipitation skier_penetration_depth snow_water_equivalent  total_amount_of_water  total_amount_of_water_soil  total_amount_of_ice_soil  erosion_mass_loss  rain_rate  virtual_lysimeter_surface_snow_only surface_mass_flux  virtual_lysimeter_under_the_soil  sublimation_mass  evaporated_mass profile_type  stability_class  z_Sdef  deformation_rate_stability_index  z_Sn38  natural_stability_index  z_Sk38  Sk38_skier_stability_index  z_SSI  structural_stability_index  z_S5 stability_index_5'.split()
fields           = 'timestamp Qs Ql Qg TSG Qg0 Qr dIntEnergySnow meltFreezeEnergySnow ColdContentSnow OLWR ILWR LWR_net RSWR ISWR Qw pAlbedo mAlbedo ISWR_h ISWR_dir ISWR_diff TA TSS_mod TSS_meas T_bottom RH VW VW_drift DW MS_Snow HS_mod HS_meas hoar_size wind_trans24 HN3 HN6 HN12 HN24 HN72_24 HNW24 ski_pen SWE MS_Water MS_Water_Soil MS_Ice_Soil MS_Wind MS_Rain MS_SN_Runoff MS_Surface_Mass_Flux MS_Soil_Runoff MS_Sublimation MS_Evap Sclass1 Sclass2 zSd Sd zSn Sn zSs Ss zS4 S4 zS5 S5'.split() 

for u, d, f in zip(units, plot_description, fields):
    print([d.strip(), u.strip(), f.strip()])




from read_smet import parse_smet

root_path = Path(__file__).parent.parent.parent
file_path = root_path / "data" / "hdd1" / "snowpack" / "output.caw.2025" / "27240" / "27240_res.smet"
if file_path.exists():
    metadata, df = parse_smet(file_path)
    print('\n')#df.columns)
    df = df[['MS_Rain', 'SWE', 'MS_Water', 'HS_mod']]
    print(df.max(axis=0))
    print(df[df['MS_Rain']>0])
    print(df.head(50))
