from dataclasses import dataclass, field, fields
from typing import Optional, List
from abc import ABC


class PropertyData(ABC):
    """Methods shared by Property objects and their component classes, e.g., LocationDetails. Currently, data validation."""
    def missing_fields(self) -> List[str]:
        return [field.name for field in fields(self) if getattr(self, field.name) is None]
    
    def is_complete(self) -> bool:
        return len(self.missing_fields()) == 0

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