import pandas as pd
# import numpy as np
from scipy.stats import iqr

# List of ZIP codes in which we are currently interested:
zip_codes = [98403, 98404, 98405, 98406, 98407, 98408, 98409, 98418, 98422, 98465, 98424, 98466, 98467, 98332, 98335]
# Result 9-12-25: 98408, center-south Tacoma, is where annual *growth* is above county average but *rent* is below median.

def aggregate_rent_analysis(df):
    # Core functionality for Project Falcon #1: based on aggregate rental market index, identify
    # 1) Annualized % growth (average and median) aggregated for 1a) county and 1b) state,
    # 2) Absolute index value IQR today by county, and
    # 3) Zip codes where the annual growth has been above county average since 1/2024 but where the absolute
    # index value is below the median for the county.

    if not df.columns.to_list() == ["Zip", "County", "State", "Date", "Rent"]:
        return print("Error: dataframe should contain only the five columns Zip, County, State, Date, and Rent.")

    df["Date"] = pd.to_datetime(df["Date"]) # Ensuring that the date column is converted to datetime objects

    clean_df = df.dropna()
    df = clean_df # Comment this out to not drop NaN values from the dataset.

    # Index dataframe to date, thereby dropping "Date" column and helping to analyze over time.
    df = df.set_index("Date")

    df = annualized_growth_by_locale(df)

    current_rent_iqr_by_county(df)

    compare_rent_and_growth(df)    


def annualized_growth_by_locale(df):
    # Aggregate annualized growth in rent by county, state, and zip, adding columns and printing mean/medians.
    df["Annual_Growth_By_County"] = (df.groupby("County")["Rent"].pct_change(periods=12) * 100)
    grouped_growth_by_county = df.groupby("County")["Annual_Growth_By_County"]
    mean_growth_by_county = grouped_growth_by_county.mean()
    median_growth_by_county = df.groupby("County")["Annual_Growth_By_County"].median()
    print(f"Mean annualized percent growth by county: \n{mean_growth_by_county}")
    print(f"Median annualized percent growth by county: \n{median_growth_by_county}")

    df["Annual_Growth_By_State"] = (df.groupby("State")["Rent"].pct_change(periods=12) * 100)
    mean_growth_by_state = df.groupby("State")["Annual_Growth_By_State"].mean()
    median_growth_by_state = df.groupby("State")["Annual_Growth_By_State"].median()
    print(f"Mean annualized percent growth by state: \n{mean_growth_by_state}")
    print(f"Median annualized percent growth by state: \n{median_growth_by_state}")

    df["Annual_Growth_By_Zip"] = (df.groupby("Zip")["Rent"].pct_change(periods=12) * 100)
    mean_growth_by_zip = df.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    median_growth_by_zip = df.groupby("Zip")["Annual_Growth_By_Zip"].median()
    print(f"Mean annualized percent growth by Zip:\n {mean_growth_by_zip}")
    print(f"Median annualized percent growth by Zip:\n {median_growth_by_zip}")
    return df


def current_rent_iqr_by_county(df):
    # First, filter the dataframe, indexed to date, by most recent date using max().
    most_recent_df = df[df.index == df.index.max()]

    # Next, print the IQR of the rent in this subset, grouped by county.
    rent_quartiles_by_county = most_recent_df.groupby("County")["Rent"].quantile([0.25, 0.75])
    print(f"Rent 1st and 3rd Quartiles for most recent date by county: \n {rent_quartiles_by_county}")

    # Scipy's iqr() behavior is peculiar here: I need to transform(iqr) and then sum() the quartiles, grouping each time.
    rent_iqr_by_county = rent_quartiles_by_county.groupby("County").transform(iqr)
    rent_iqr_by_county = rent_iqr_by_county.groupby("County").sum()
    print(f"Rent IQR for most recent date by county: \n{rent_iqr_by_county}")


def compare_rent_and_growth(df):
    # Filter out before 1/2024 and find above-average rent-growth and below-median rent. First, filter the dates.
    target_date = pd.to_datetime("2024-01-01")
    after_2024_df = df[df.index >= target_date]

    # Next, identify ZIP codes where growth is above county average.
    # If annualized_growth_by_locale has been called, the "Annual_Growth_By_Zip" column will exist. If not, define it.
    try:
        avg_growth_df = after_2024_df.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    except:
        df["Annual_Growth_By_Zip"] = (df.groupby("Zip")["Rent"].pct_change(periods=12) * 100)
        avg_growth_df = after_2024_df.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    above_avg_growth_df = avg_growth_df > avg_growth_df.mean()
    above_avg_growth_zips = above_avg_growth_df[above_avg_growth_df].index.to_list()
    print(f"ZIP codes in which rent growth is above average: {above_avg_growth_zips}")

    # Now, identify a separate list of zips where the most recent month of rent is below-median.
    most_recent_rent = after_2024_df.groupby("Zip")["Rent"].last() # series of most recent rents by zip
    most_recent_median_rent = most_recent_rent.median()
    below_median_rent_df = most_recent_rent < most_recent_median_rent
    below_median_rent_zips = below_median_rent_df[below_median_rent_df].index.to_list()
    print(f"ZIP codes in which most recent rent is below median: {below_median_rent_zips}")
    # store series/dict indexed to zip containing median rent growth ranked by furthest below median (?)

    # Lastly, find common elements of both lists using set intersection.
    intersecting_zips = list(set(above_avg_growth_zips).intersection(below_median_rent_zips))
    print(f"ZIP codes in which rent growth is above average and rent is below median: {intersecting_zips}")

    # Percentile ranking of ZIP codes in terms of higher rent growth and lower recent rent.
    avg_growth_pct_rank = avg_growth_df.rank(pct=True)
    recent_rent_pct_rank = most_recent_rent.rank(pct=True, ascending=False)
    rank_comparison_df = pd.concat([avg_growth_pct_rank, recent_rent_pct_rank], axis=1)
    rank_comparison_df["Combined_Rank"] = (rank_comparison_df["Annual_Growth_By_Zip"] + rank_comparison_df["Rent"]) / 2
    sorted_rank_comparison_df = rank_comparison_df.sort_values(by="Combined_Rank", ascending=False).dropna(subset="Combined_Rank")
    print(f"ZIP codes ranked in order of higher rent growth averaged with lower recent rent: \n{sorted_rank_comparison_df}")


def zillow_data_parser(data):
    # A wrapper function specifically to parse our Zillow housing data and feed it into aggregate_rents_by_zip().
    df = pd.read_csv(data, delimiter=",")

    # Zillow data is wide: there's a column for each month of data. I'll convert it to long format for analysis.
    # First, I'll select for the ZIP codes we're currently interested in.
    zip_df = df[df["RegionName"].isin(zip_codes)].reset_index(drop=True)

    # Next, I'll drop the columns that don't concern us.
    dropped_df = zip_df.drop(columns=["RegionID", "SizeRank", "RegionType", "StateName", "City", "Metro"])

    # I'll rename the columns so that aggregate_rents_by_zip() can expect consistent column names.
    renamed_df = dropped_df.rename(columns={"RegionName": "Zip", "CountyName": "County"})

    # Finally, I'll pivot the data so that dates are stored long rather than wide, in a single Date column.
    # Given how many date columns there are (might change, too), I'll slice the columns by index in value_vars.
    long_df = pd.melt(renamed_df,
                      id_vars=["Zip", "County", "State"],
                      value_vars=renamed_df.iloc[:, 3:-1],
                      var_name="Date",
                      value_name="Rent")
    return long_df


long_df = zillow_data_parser("zillow_data.csv")
aggregate_rent_analysis(long_df)