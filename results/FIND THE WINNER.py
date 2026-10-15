import pandas as pd

results = pd.read_csv("C:/Group Project/model_comparison_by_segment.csv")

winner = results.loc[results.groupby("segment")["rmse"].idxmin()]

print("Best model by segment")

print(winner[["segment", "model_name", "with_radiation", "rmse", "mae", "mape_pct", "r2"]])

winner.to_csv("C:/Group Project/best_model_by_segment.csv", index=False)




#compare radiation within models

with_rad = results[results["with_radiation"] == True]
without_rad = results[results["with_radiation"] == False]

rad_compare = pd.merge( with_rad, without_rad, on=["model_name", "segment"], suffixes=("_rad", "_no_rad"))

rad_compare["rmse_diff"] = (rad_compare["rmse_rad"]-rad_compare["rmse_no_rad"])

rad_compare["mae_diff"] = (rad_compare["mae_rad"]-rad_compare["mae_no_rad"])

rad_compare["mape_diff"] = (rad_compare["mape_pct_rad"]-rad_compare["mape_pct_no_rad"])

rad_compare["r2_diff"] = (rad_compare["r2_rad"]-rad_compare["r2_no_rad"])

print("Compare Radiation on and off")

print(rad_compare[["model_name", "segment", "rmse_rad", "rmse_no_rad", "rmse_diff", "r2_rad", "r2_no_rad", "r2_diff"]])

#what am i even doing? 

# winner with the radiation on

with_rad = results[results["with_radiation"] == True]

winner_with_rad = with_rad.loc[ with_rad.groupby("segment")["rmse"].idxmin()]

#winner with no radiation

not_rad = results[results["with_radiation"] == False]

winner_not_rad = not_rad.loc[ not_rad.groupby("segment")["rmse"].idxmin()]

print("Radiation Winners")

print(winner_with_rad[[ "segment", "model_name", "rmse", "mae", "mape_pct", "r2"]])

#winner winner chicken dinner --- is solar radiation worth using as a feature? 

legend_status = pd.merge( winner_with_rad, winner_not_rad, on="segment", suffixes=("_rad", "_no_rad"))

legend_status["rmse_diff"] = (legend_status["rmse_rad"] - legend_status["rmse_no_rad"])

print("Best rad vs best no rad")

print(legend_status[["segment", "model_name_rad", "rmse_rad", "model_name_no_rad", "rmse_no_rad", "rmse_diff"]])

legend_status.to_csv("C:/Group Project/rad_no_rad_winner_comparison.csv", index=False)



# does it look the same by r2? 

# winner with the radiation on

with_rad_r2 = results[results["with_radiation"] == True]

winner_with_rad_r2 = with_rad.loc[ with_rad_r2.groupby("segment")["r2"].idxmax()]

#winner with no radiation

not_rad_r2 = results[results["with_radiation"] == False]

winner_not_rad_r2 = not_rad_r2.loc[ not_rad_r2.groupby("segment")["r2"].idxmax()]

print("Radiation Winners")

print(winner_with_rad_r2[[ "segment", "model_name", "rmse", "mae", "mape_pct", "r2"]])

#lets check i didnt break anything... r2 and rmse should give the same models... ... should... 

legend_status_r2 = pd.merge( winner_with_rad_r2, winner_not_rad_r2, on="segment", suffixes=("_rad", "_no_rad"))

legend_status_r2["r2_diff"] = (legend_status_r2["r2_rad"] - legend_status_r2["r2_no_rad"])

print("Best rad vs best no rad by r2")

print(legend_status_r2[["segment", "model_name_rad", "r2_rad", "model_name_no_rad", "r2_no_rad", "r2_diff"]])

legend_status_r2.to_csv("C:/Group Project/rad_no_rad_winner_r2_comparison.csv", index=False)

