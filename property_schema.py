from dataclasses import dataclass
from typing import Protocol

# TODO: route data intake (from Rentcast and Rentometer) into Property objects
# Next time: review what data is coming from where, what sort of dict results, and refactor to parse into Details objects.
# A Property object will be instantiated from Details presumably instantiated at different stages, e.g., analysis -> ValueDetails.
# TODO: design Spreadsheet objects similarly to provide formatting information to API clients
# TODO: design API Client abstract base class to expect PropertyBundles and SpreadsheetBundles
# TODO: scour the details of the refactored Gsheet plug-in to, e.g., receive Property data bundled as dicts and not "address_dict"

# NOTE: Data provider interface: swap from JSON dumps to live API calls without losing past code (maybe I'll want JSON dumps later!)
# I'll need to study how to hook up both sender and recipient to an interface, but that's what I want to learn.

@dataclass
class LocationDetails:
    """Subset of Property data relevant to location."""
    street_address: str
    city: str
    state: str
    zip_code: int
    county: str
    latitude: float | None
    longitude: float | None


@dataclass
class FeatureDetails:
    """Property features, such as number of beds/baths."""
    property_type: str
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size: int


@dataclass
class AttributeDetails:
    """Property facts not included in features, such as year built."""
    year_built: int
    assessor_ID: int
    legal_description: str
    owner_occupied: bool


@dataclass
class ValueDetails:
    """Values pertaining to expected revenue and costs."""
    value_est: int
    property_tax: float
    mean_rent_est: int
    median_rent_est: int
    min_rent: int
    max_rent: int
    mortgage_est: float
    insurance_est: float
    monthly_tax_est: float
    capex_est: float
    mgmt_est: float
    sum_est_costs: float


@dataclass    
class Metadata:
    filename: str
    rentometer_url: str | None
    rentcast_url: str | None
    name: str = "Metadata"

@dataclass
class Property:
    """Domain model containing subsets of property data."""
    location: LocationDetails
    features: FeatureDetails
    attributes: AttributeDetails
    values: ValueDetails
    metadata: Metadata
    COL_NAMES = ("location", "features", "attributes", "values", "metadata") # Hardcoding as class constant for now

    def as_bundle(self, bundle):
        """Return only a subset of relevant Property data as a bundle."""
        return bundle.extract(self)
    

"""Protocol to enable API client manager to type-check that a bundle is being passed. Just one for now."""    
class NeedsBasicPropertyInfo(Protocol):
    def extract(self, prop: Property) -> dict: ...


"""Bundles, rather than inheriting from an abstract bundle class, will be structurally typed by what they extract()."""
class BasicPropertyBundle:
    def extract(self, prop: Property):
        return {
          "street_address": prop.location.street_address,
          "city": prop.location.city,
          "state": prop.location.state,
          "zip_code": prop.location.zip_code,
          "county": prop.location.county,
          "latitude": prop.location.latitude,
          "longitude": prop.location.longitude,
          "property_type": prop.features.property_type,
          "bedrooms": prop.features.bedrooms,
          "bathrooms": prop.features.bathrooms,
          "sqft": prop.features.sqft,
          "lot_size": prop.features.lot_size,
          "year_built": prop.attributes.year_built,
          "assessor_ID": prop.attributes.assessor_ID,
          "legal_description": prop.attributes.legal_description,
          "owner_occupied": prop.attributes.owner_occupied,
          "value_est": prop.values.value_est,
          "property_tax": prop.values.property_tax,
          "mean_rent_est": prop.values.mean_rent_est,
          "median_rent_est": prop.values.median_rent_est,
          "min_rent": prop.values.min_rent,
          "max_rent": prop.values.max_rent,
          "mortgage_est": prop.values.mortgage_est,
          "insurance_est": prop.values.insurance_est,
          "monthly_tax_est": prop.values.monthly_tax_est,
          "capex_est": prop.values.capex_est,
          "mgmt_est": prop.values.mgmt_est,
          "sum_est_costs": prop.values.sum_est_costs
        }