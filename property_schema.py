from dataclasses import dataclass, field, fields
from typing import Optional, List, TypeVar
from abc import ABC
from pandas import DataFrame


class PropertyData(ABC):
    """Methods shared by Property objects and their component classes, e.g., LocationDetails. Currently, data validation."""
    def missing_fields(self) -> List[str]:
        return [field.name for field in fields(self) if getattr(self, field.name) is None]
    
    def is_complete(self) -> bool:
        return len(self.missing_fields()) == 0
    
    # TODO: cols_to_fields that takes a DF and defines relevant fields appropriately, checking subfields where needed (as in, for Property)
    def convert_cols_to_fields(self: "property_data_type", df: DataFrame) -> "property_data_type":
        # TODO: this will work for all PropertyData EXCEPT Property, which has PropertyData for fields, which won't match columns
        # for property specifically, go one layer deeper (fields(self) returns a tuple so work with that)
        for fld in fields(self):
            if fld.name in df.columns:
                # TODO: this grabs the first, but what I really want is to populate a LIST of Property objects, not Property objs themselves!
                new_value = df[fld.name].iloc[0]
                print(new_value)
                current_value = getattr(self, fld.name)
                print(f"Current Value for {fld.name}: {current_value}")
                if current_value is not None and current_value != new_value:
                    print(f"Warning: {self.__class__.__name__}.{fld.name}: '{current_value}' vs '{new_value}' - keeping first")
                elif current_value is None:
                    setattr(self, fld.name, new_value)
                    print(f"Should be successfully set! It's now {getattr(self, fld.name)}")
        return self

property_data_type = TypeVar("property_data_type", bound=PropertyData)

@dataclass
class LocationDetails(PropertyData):
    """Subset of Property data relevant to location."""
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[int] = None
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class FeatureDetails(PropertyData):
    """Property features, such as number of beds/baths."""
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None


@dataclass
class AttributeDetails(PropertyData):
    """Property facts not included in features, such as year built."""
    year_built: Optional[int] = None
    assessor_ID: Optional[int] = None
    legal_description: Optional[str] = None
    owner_occupied: Optional[bool] = None


@dataclass
class ValueDetails(PropertyData):
    """Values pertaining to expected revenue and costs."""
    value_est: Optional[int] = None
    property_tax: Optional[float] = None
    mean_rent_est: Optional[int] = None
    median_rent_est: Optional[int] = None
    min_rent: Optional[int] = None
    max_rent: Optional[int] = None
    mortgage_est: Optional[float] = None
    insurance_est: Optional[float] = None
    monthly_tax_est: Optional[float] = None
    capex_est: Optional[float] = None
    mgmt_est: Optional[float] = None
    sum_est_costs: Optional[float] = None


@dataclass    
class Metadata(PropertyData):
    filename: Optional[str] = None
    rentometer_url: Optional[str] = None
    rentcast_url: Optional[str] = None


@dataclass
class Property(PropertyData):
    """Domain model containing subsets of property data."""
    location: Optional[LocationDetails] = field(default_factory=LocationDetails)
    features: Optional[FeatureDetails] = field(default_factory=FeatureDetails)
    attributes: Optional[AttributeDetails] = field(default_factory=AttributeDetails)
    values: Optional[ValueDetails] = field(default_factory=ValueDetails)
    metadata: Optional[Metadata] = field(default_factory=Metadata)