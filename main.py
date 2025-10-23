import pandas as pd
from enum import StrEnum
from json_to_df import json_to_df
from property_data import rentometer_api
from datetime import datetime

# List of ZIP codes in which we are currently interested:
zip_codes = [98403, 98404, 98405, 98406, 98407, 98408, 98409, 98418, 98422, 98465, 98424, 98466, 98467, 98332, 98335]
# Result 9-12-25: 98408, center-south Tacoma, is where annual *growth* is above county average but *rent* is below median.

class ExpectedColumns(StrEnum):
    ZIP = "Zip"
    COUNTY = "County"
    STATE = "State"
    DATE = "Date"
    RENT = "Rent"
    VALUE = "Value"
    ANNUAL_GROWTH_BY_ZIP = "Annual_Growth_By_Zip"
    PROPERTY_TAX = "property_tax"

def aggregate_analysis(df, metric):
    """Core functionality for Project Falcon #1: based on aggregate rental market index, identify
    1) Annualized % growth (average and median) aggregated for 1a) county and 1b) state,
    2) Absolute index value IQR today by county, and
    3) Zip codes where the annual growth has been above county average since 1/2024 but where the absolute
    index value is below the median for the county."""
    
    if metric != metric.title():
        metric = metric.title()
    if metric not in [ExpectedColumns.RENT, ExpectedColumns.VALUE]:
        raise ValueError("Please specify how to aggregate: in terms of 'rent' or home 'value'.")
    
    if not df.columns.to_list() == [ExpectedColumns.ZIP, ExpectedColumns.COUNTY, ExpectedColumns.STATE, ExpectedColumns.DATE, metric]:
        raise ValueError("Error: dataframe should contain only the five columns Zip, County, State, Date, and either Rent or Value.")

    df["Date"] = pd.to_datetime(df["Date"]) # Ensuring that the date column is converted to datetime objects

    clean_df = df.dropna()
    df = clean_df # Comment this out to not drop NaN values from the dataset.

    # Index dataframe to date, thereby dropping "Date" column and helping to analyze over time.
    df = df.set_index("Date")

    df = annualized_growth_by_locale(df, metric)

    print_current_iqr(df, metric)

    compare_metric_and_growth(df, metric)    


def annualized_growth_by_locale(df, metric):
    # Aggregate annualized growth in rent by county, state, and zip, adding columns and printing mean/medians.
    df["Annual_Growth_By_County"] = (df.groupby("County")[metric].pct_change(periods=12) * 100)
    grouped_growth_by_county = df.groupby("County")["Annual_Growth_By_County"]
    mean_growth_by_county = grouped_growth_by_county.mean()
    median_growth_by_county = df.groupby("County")["Annual_Growth_By_County"].median()
    print(f"Mean annualized percent growth by county: \n{mean_growth_by_county}")
    print(f"Median annualized percent growth by county: \n{median_growth_by_county}")

    df["Annual_Growth_By_State"] = (df.groupby("State")[metric].pct_change(periods=12) * 100)
    mean_growth_by_state = df.groupby("State")["Annual_Growth_By_State"].mean()
    median_growth_by_state = df.groupby("State")["Annual_Growth_By_State"].median()
    print(f"Mean annualized percent growth by state: \n{mean_growth_by_state}")
    print(f"Median annualized percent growth by state: \n{median_growth_by_state}")

    df["Annual_Growth_By_Zip"] = (df.groupby("Zip")[metric].pct_change(periods=12) * 100)
    mean_growth_by_zip = df.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    median_growth_by_zip = df.groupby("Zip")["Annual_Growth_By_Zip"].median()
    print(f"Mean annualized percent growth by Zip:\n {mean_growth_by_zip}")
    print(f"Median annualized percent growth by Zip:\n {median_growth_by_zip}")
    return df


def print_current_iqr(df, metric, group="County"):
    # Prints Q1, Q3, and IQR of rent/value. Defaults to grouping by county.
    def q1(group):
        return group.quantile(0.25)
    
    def q3(group):
        return group.quantile(0.75)
    
    def iqr(group):
        return group.quantile(0.75) - group.quantile(0.25)
    
    f = {metric: [q1, q3, iqr]}
    
    # Filter the dataframe, indexed to date, by most recent date using max().
    most_recent_df = df[df.index == df.index.max()]

    # Apply aggregate functions to filtered dataframe to assign multi-index columns.
    quartiles_df = most_recent_df.groupby(group).agg(f)

    # Flatten multi-index columns back into a 2-dimensional dataframe for ease of reference.
    quartiles_df.columns = list(map('_'.join, quartiles_df.columns.values))

    # Next, print the IQR of the rent in this subset, grouped by county.
    print(f"{metric} Quartiles and IQR for most recent date by {group}: \n {quartiles_df}")


def check_for_growth_by_zip(df):
    # Multiple functions rely on annualized_growth_by_locale generating the "Annual_Growth_by_Zip" column, so check for it.
    if ExpectedColumns.ANNUAL_GROWTH_BY_ZIP not in df.columns.to_list():
        raise ValueError("Function expects Annual_Growth_by_Zip column. Call annualized_growth_by_locale first.")
    

def compare_metric_and_growth(df, metric, above_median=False):
    # Filter out before 1/2024 and find above-average rent-growth and below-median rent. First, filter the dates.
    target_date = pd.to_datetime("2024-01-01")
    after_2024_df = df[df.index >= target_date]
    metric_lower = metric.lower()

    # Next, identify ZIP codes where growth is above county average.
    check_for_growth_by_zip(df)
    avg_growth_df = after_2024_df.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    above_avg_growth_df = avg_growth_df > avg_growth_df.mean()
    above_avg_growth_zips = above_avg_growth_df[above_avg_growth_df].index.to_list()
    print(f"ZIP codes in which {metric_lower} growth is above average: {above_avg_growth_zips}")

    # Identify a separate list of zips where the most recent month's value is below-median, or above if specified.
    most_recent_value = after_2024_df.groupby("Zip")[metric].last()
    median_comparison_string, median_value_comparison_df = _check_above_or_below_median(most_recent_value, above_median)
    median_value_zips = median_value_comparison_df[median_value_comparison_df].index.to_list()
    print(f"ZIP codes in which most recent {metric_lower} is {median_comparison_string} median: {median_value_zips}")

    # Lastly, find common elements of both lists using set intersection.
    intersecting_zips = list(set(above_avg_growth_zips).intersection(median_value_zips))
    print(f"ZIP codes in which {metric_lower} growth is above average and {metric_lower} is {median_comparison_string} median: {intersecting_zips}")

    # Percentile ranking of ZIP codes in terms of higher rent growth and lower recent rent.
    avg_growth_pct_rank = avg_growth_df.rank(pct=True)
    recent_value_pct_rank = most_recent_value.rank(pct=True, ascending=False)
    rank_comparison_df = pd.concat([avg_growth_pct_rank, recent_value_pct_rank], axis=1)
    rank_comparison_df["Combined_Rank"] = (rank_comparison_df["Annual_Growth_By_Zip"] + rank_comparison_df[metric]) / 2
    sorted_rank_comparison_df = rank_comparison_df.sort_values(by="Combined_Rank", ascending=False).dropna(subset="Combined_Rank")
    print(f"ZIP codes ranked in order of higher {metric_lower} growth averaged with lower recent {metric_lower}: \n{sorted_rank_comparison_df}")


def _check_above_or_below_median(recent_values, above_median):
    most_recent_median_values = recent_values.median()
    if above_median:
        median_comparison_string = "above"
        median_value_comparison_df = recent_values > most_recent_median_values
    else:
        median_comparison_string = "below"
        median_value_comparison_df = recent_values < most_recent_median_values
    return median_comparison_string, median_value_comparison_df


def compare_price_to_rent(price_data, rent_data):
    # Ranking of ZIP codes' price-to-rent ratio and percentile ranking of price-to-rent ratio and higher rent growth.
    if "Date" not in price_data.columns.to_list() or "Date" not in rent_data.columns.to_list():
        return print("Error: datasets should be parsed to contain a 'Date' column and be pivoted long.")
    
    avg_home_value_by_zip = price_data.groupby("Zip")["Value"].mean()
    avg_rent_by_zip = rent_data.groupby("Zip")["Rent"].mean()
    price_to_rent_by_zip = avg_home_value_by_zip / avg_rent_by_zip
    sorted_price_to_rent_by_zip = price_to_rent_by_zip.sort_values(ascending=True)
    print(f"ZIP codes ranked in ascending order of price-to-rent ratio: \n{sorted_price_to_rent_by_zip}")

    check_for_growth_by_zip(rent_data)
    avg_rent_growth_df = rent_data.groupby("Zip")["Annual_Growth_By_Zip"].mean()
    
    # Percentile ranking of ZIP codes in terms of higher rent growth and lower price-to-rent ratio.
    avg_growth_pct_rank = avg_rent_growth_df.rank(pct=True)
    price_to_rent_pct_rank = price_to_rent_by_zip.rank(pct=True, ascending=False)
    rank_comparison_df = pd.concat([avg_growth_pct_rank, price_to_rent_pct_rank], axis=1)
    rank_comparison_df.rename(columns={rank_comparison_df.columns[0]: "Avg_Growth_Pct_Rank", rank_comparison_df.columns[1]: "Price_to_Rent_Pct_Rank"}, inplace=True)
    rank_comparison_df["Combined_Rank"] = (rank_comparison_df["Avg_Growth_Pct_Rank"] + rank_comparison_df["Price_to_Rent_Pct_Rank"]) / 2
    sorted_rank_comparison_df = rank_comparison_df.sort_values(by="Combined_Rank", ascending=False).dropna(subset="Combined_Rank")
    print(f"ZIP codes ranked in order of higher rent growth averaged with lower price-to-rent ratio: \n{sorted_rank_comparison_df}")


def zillow_data_parser(data, metric):
    # A wrapper function specifically to parse our Zillow housing data and feed it into an aggregation function.
    if metric != metric.title():
        metric = metric.title()
    if metric not in ["Rent", "Value"]:
        return print("Please specify if this Zillow dataset concerns 'rent' or home 'value'.")
    
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
                      value_name=metric.title())
    return long_df


def rentcast_data_parser(datetime=None):
    # Use json_to_df to parse rentcast data for initial desired inputs. Returns dict subset.
    df = json_to_df("rentcast", datetime)
    max_value = 550000
    min_bedrooms = 3
    min_bathrooms = 1.5
    property_type = "Single Family"

    # Extract most recent home value from nested dictionary.
    value_df = pd.json_normalize(df["taxAssessments"])
    df["value"] = value_df["2025.value"]

    # Extract most recent property tax assessment.
    tax_df = pd.json_normalize(df["propertyTaxes"])
    df["property_tax"] = tax_df["2025.total"]

    # Extract relevant features.
    features_df = pd.json_normalize(df["features"])
    df["garage"] = features_df["garage"]
    df["heatingType"] = features_df["heatingType"]

    # Parse dataframe by specified constants and return.
    subset_df = df[(df["value"] <= max_value) & (df["bedrooms"] >= min_bedrooms) & (df["bathrooms"] >= min_bathrooms) & (df["propertyType"] == property_type)].reset_index(drop=True)
    return subset_df


def add_rent_to_parsed_rentcast_data(parsed_data, datetime_string=None):
    # For each address in parsed rentcast data, find rent data, add as expected income, and return dataframe.
    if ExpectedColumns.PROPERTY_TAX not in parsed_data.columns.to_list():
        raise Exception("Error: property tax column missing. First call rentcast_data_parser on dataframe input.")
    
    # If I've specified a datetime, the JSON dumps already exist on disk. If not, make necessary API calls.
    # For each address in the parsed_data, apply rentometer_api function in property_data.
    if datetime_string is None:
        datetime_string = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        parsed_data["formattedAddress"].apply(rentometer_api)

    # Load JSON dumps saved to disk from relevant datetime (right before making API calls) and concatenate into dataframe.
    rent_data = json_to_df("rentometer", datetime_string)

    # Match addresses between parsed_data and new Rentometer JSON dumps, add Rentometer data, and return.
    parsed_data = parsed_data.rename(columns={"formattedAddress": "address"})
    joined_data = pd.merge(parsed_data, rent_data, on="address", how="inner") # Presumes exact same address string
    return joined_data


# rent_df = zillow_data_parser("zillow_rent_data.csv", "rent")
# price_df = zillow_data_parser("zillow_sfh_value_data.csv", "value")
# compare_price_to_rent(price_df, rent_df)
# aggregate_analysis(rent_df, "rent")
# aggregate_analysis(price_df, "value")
property_df = rentcast_data_parser("2025-10-10_12-42-27")
# property_df.to_csv("rentcast_test.csv")
joined_data = add_rent_to_parsed_rentcast_data(property_df, "2025-10-22_13-42")
joined_data.to_csv("join_test.csv")