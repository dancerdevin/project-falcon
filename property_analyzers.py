from property_schema import Property, PropertyData
from typing import Protocol, List
import pandas as pd
from numpy import float64
from amortization.amount import calculate_amortization_amount


"""Interface for all data processors that, e.g., perform pandas analysis. Turn Property to DataFrame and back again."""
class PropertyAnalyzer(Protocol):
  def analyze(prop_list: List[Property]) -> List[Property]: ...

class CompletePropertyAnalyzer:
  """Include analysis that requires, e.g., data from both Rentcast and Rentometer."""
  # TODO: def __init__() valid data sources dict so you can complete todo below
  def __init__(self):
    self.LOAN_TO_VALUE = .7
    self.APR = 0.07
    self.AMORT_MONTHS = 360
    self.EST_YEARLY_INSURANCE = 1000

    self.data_type_dict = { # NOTE: Defaulting to floats for now even if ints might suffice for some
        "value_est": float64,
        "mean_rent_est": float64,
        "median_rent_est": float64,
        "min_rent": float64,
        "max_rent": float64,
        "mortgage_est": float64,
        "insurance_est": float64,
        "monthly_tax_est": float64,
        "capex_est": float64,
        "mgmt_est": float64,
        "sum_est_costs": float64
    }

  def analyze_property(self, prop: Property) -> Property:
    if prop.metadata.rentcast_id is None or prop.metadata.rentometer_url is None:
       raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    
    LOAN_TO_VALUE, APR, AMORT_MONTHS, EST_YEARLY_INSURANCE = self.LOAN_TO_VALUE, self.APR, self.AMORT_MONTHS, self.EST_YEARLY_INSURANCE
    df = prop.as_dataframe

    df = df.astype(self.data_type_dict)

    df["mortgage_est"] = df["value_est"].apply(lambda x: calculate_amortization_amount((x * LOAN_TO_VALUE), APR, AMORT_MONTHS))
    
    df["insurance_est"] = pd.Series(EST_YEARLY_INSURANCE / 12, index=df.index)

    df["monthly_tax_est"] = df["property_tax"] / 12 # Rentcast data is by year

    # Estimated maintenance/capex: 1% of house value per year, divided by 12 for monthly
    df["capex_est"] = df["value_est"].apply(lambda x: (x * 0.01) / 12)

    # Estimated management costs: 10% of monthly rent (using median as more robust indicator)
    df["mgmt_est"] = df["median_rent_est"] * .1

    # Estimated monthly costs, summed
    df["sum_est_costs"] = df[["mortgage_est", "insurance_est", "capex_est", "mgmt_est"]].sum(axis=1)

    analyzed_prop = PropertyData.build_property_from_dataframe(df)
    return analyzed_prop
  

class CompletePropertiesAnalyzer:
  """Include analysis that requires, e.g., data from both Rentcast and Rentometer."""
  def analyze_properties(self, prop_list: List[Property]) -> List[Property]:
    # TODO: Implement locale_level_analysis functions in this context to work with different non-Zillow data sources.
    raise Exception("Error: analyze_properties() called before implementation.")
    # if not isinstance(prop_list, list):
    #   raise TypeError("CompletePropertyAnalyzer takes a list of Properties. Please input the result of at least one different PropertyProvider.")
    # # TODO: make it so partial data is just skipped rather than errors out (change in add_costs functionality / move here?). Also no rentcast_url, just rentcast_id
    # # if prop.metadata.rentcast_url is None or prop.metadata.rentometer_url is None:
    # #   raise Exception("Error: CompletePropertyAnalyzer expects both Rentcast and Rentometer data, but at least one URL is None.")
    # prop_big_df = PropertyData.prop_list_to_dataframe(prop_list)
    # analyzed_df = add_costs_to_parsed_rentcast_data(prop_big_df)
    # analyzed_prop_list = PropertyData.build_properties_from_dataframe(analyzed_df)
    # return analyzed_prop_list