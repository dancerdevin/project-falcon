from dataclasses import dataclass, field, fields
from typing import Optional, List, TypeVar, get_origin, get_args, Any, Dict, NamedTuple
from abc import ABC
from pandas import DataFrame, concat


class PropertyData(ABC):
    """Methods shared by Property objects and their component classes, e.g., LocationDetails. Currently, data validation."""
    def missing_fields(self) -> List[str]:
        missing_fields = [field.name for field in fields(self) if getattr(self, field.name) is None]
        # If self is Property, check missing_fields in contained dataclasses too.
        if isinstance(self, Property):
            for field in fields(self):
                field_value = getattr(self, field.name)
                missing_subfields = field_value.missing_fields()
                missing_fields += missing_subfields
        print(f"final missing_fields: {missing_fields}")
        return missing_fields
    
    def is_complete(self) -> bool:
        return len(self.missing_fields()) == 0
    
    @staticmethod
    def build_property_from_dataframe(df: DataFrame) -> "Property":
        """Generate Property from a DataFrame with a single row."""
        if df.empty: # Finding location matches may have found no matches and so passed an empty DataFrame.
            return Property()
        else:
            if len(df) > 1:
                raise Exception("Error: build_property_from_dataframe() expects a DataFrame with a single row.")
            row_tuple = next(df.itertuples(index=False)) # or df.iloc[0]
            return PropertyData._build_property_from_row(row_tuple)
    
    @staticmethod
    def build_properties_from_dataframe(df: DataFrame) -> List["Property"]:
        """Generate list of Properties, each one corresponding to a row in a DataFrame."""
        if df.empty: # Finding location matches may have found no matches and so passed an empty DataFrame.
            return []
        else:
            return [PropertyData._build_property_from_row(row) for row in df.itertuples(index=False)]
    
    @staticmethod
    def _build_property_from_row(row: NamedTuple, prop=None) -> "Property":
        if prop is None:
            prop = Property() # prop parameter allows for recursion in finding fields to match column names

        for fld in fields(prop):
            field_type = PropertyData._check_optional_typing(fld)

            # Now check if that actual type inherits from PropertyData and, if so, recurse
            if isinstance(field_type, type) and issubclass(field_type, PropertyData): 
                nested_instance = getattr(prop, fld.name)
                if nested_instance is None:
                    nested_instance = fld.type() # Instantiate, e.g., LocationDetails() if not yet instantiated
                updated_nested = PropertyData._build_property_from_row(row, nested_instance)
                setattr(prop, fld.name, updated_nested)

            elif hasattr(row, fld.name):
                row_value = getattr(row, fld.name)
                setattr(prop, fld.name, row_value)

        return prop
    
    @staticmethod
    def prop_list_to_dataframe(prop_list: List["Property"]) -> DataFrame:
        """Analyze as-complete-as-possible Property objects by populating a big DataFrame where each Property element becomes a row."""
        prop_dict_list = [prop.as_flat_dict for prop in prop_list]
        df = DataFrame.from_records(prop_dict_list) # Can also just write DataFrame(prop_dict_list) but this makes explicit row-wise concatenation
        return df
    
    @property
    def as_dataframe(self: "property_data_type") -> DataFrame:
        """Converts a single Property object to a DataFrame. No longer used in prop_list_to_dataframe()."""
        df = DataFrame()
        for field in fields(self):
            field_type = PropertyData._check_optional_typing(field)
            field_value = getattr(self, field.name)

            # If this PropertyData is a Property and contains PropertyData, find the fields of the nested PropertyData instead
            if isinstance(field_type, type) and issubclass(field_type, PropertyData): 
                # Recurse and add more columns
                nested_df = field_value.as_dataframe
                df = concat([df, nested_df], axis=1)
            else:
                # Add non-dataclass field as a column
                df[field.name] = [field_value] # wrap in list for single row DataFrame
        return df
    
    @property
    def as_flat_dict(self: "property_data_type") -> Dict:
        """Converts a single Property object to a flat dict. The built-in asdict() dataclass method would return nested dict."""
        prop_dict = {}
        for field in fields(self):
            field_type = PropertyData._check_optional_typing(field)
            field_value = getattr(self, field.name)

            # Recurse to nested fields of PropertyData if needed to find non-PropertyData fields
            if isinstance(field_type, type) and issubclass(field_type, PropertyData):
                # Recurse and add new key-values pairs
                nested_dict = field_value.as_flat_dict
                for nested_key, nested_value in nested_dict.items():
                    prop_dict[nested_key] = nested_value
            else:
                prop_dict[field.name] = field_value
        
        return prop_dict

    @staticmethod
    def combine_partial_prop_data(prop_list: List["Property"]) -> List["Property"]:
        """Take a list of partial Properties presumed to be from different data sources and return a list of complete Properties."""
        if not isinstance(prop_list, List):
            raise TypeError("combine_partial_prop_data expects a list of Properties.")
        
        combined_prop_list = []
        
        # First, turn the big list of partial Properties from different data sources into a list of dicts bundling partial Properties on address
        prop_dict_list = PropertyData._prop_list_to_prop_dict_list(prop_list)

        for prop_dict in prop_dict_list:
            # Assume at this stage that every prop_dict represents a unique Property.
            combined_prop = Property()
            # Initialize sub-dataclasses
            for field in fields(combined_prop):
                field_type = PropertyData._check_optional_typing(field)
                # Generate a new object of that actual type and assign it to the field in question
                setattr(combined_prop, field.name, field_type())

            # Define merge priority: rentcast first, then rentometer
            merge_order = ["rentcast_data", "rentometer_data"]
            
            for source_key in merge_order:
                if source_key not in prop_dict:
                    continue
                    
                value = prop_dict[source_key]
                for field in fields(value):
                    # LocationDetails, etc.
                    prop_field_value = getattr(value, field.name)
                    # Compare every field in prop_field_value and combined_prop_field_value and replace if latter is None
                    combined_prop_field_value = getattr(combined_prop, field.name)                  
                    for fld in fields(prop_field_value):
                        nested_prop_fld_value = getattr(prop_field_value, fld.name)
                        nested_cmbd_prop_fld_value = getattr(combined_prop_field_value, fld.name)
                        if nested_cmbd_prop_fld_value is None and nested_prop_fld_value is not None:
                            # Populate the still-None subfields within a given field, but only if the source has actual data
                            setattr(combined_prop_field_value, fld.name, nested_prop_fld_value)
                    # Now update this specific field on the big combined_prop object, without overwriting any not-None subfield values already on it
                    setattr(combined_prop, field.name, combined_prop_field_value)

            # Combined_prop should be finished for this dict, so append to combined_prop_list.
            combined_prop_list.append(combined_prop)

        return combined_prop_list

    @staticmethod
    def _prop_list_to_prop_dict_list(prop_list: List["Property"]) -> List[Dict[str, "Property"]]:
        """Takes partial Properties from different data sources, e.g., Rentcast and Rentometer, finds matches by street address,
        and returns those matches bundled together as dicts to be combined by merge priority into complete Properties in combine_prop_data()."""
        # TODO: Street address normalization to catch, e.g., variations in spelling between data sources (centralize here? in helper called on intake?)

        # For each Property, generate a dict with key-value pairs for the address (as unique ID) and data sources, distinguishable by Property _url fields.
        prop_dict_list = []
        for prop in prop_list:
            data_source = None

            if prop.metadata.rentcast_id is not None and prop.metadata.rentometer_url is not None:
                raise Exception("Error: Property data seems to have more than one source, preventing proper bundling.")
            elif prop.metadata.rentcast_id is not None:
                data_source = "rentcast"
            elif prop.metadata.rentometer_url is not None:
                data_source = "rentometer"
            elif data_source is None:
                raise Exception("Error: Property data does not have recognizable source.")
            
            prop_dict = {}

            if data_source == "rentcast":
                prop_dict = {"address": prop.location.street_address, "rentcast_data": prop}
            elif data_source == "rentometer":
                prop_dict = {"address": prop.location.street_address, "rentometer_data": prop}
            if prop_dict is None:
                raise Exception("Error: prop_dict was somehow never assigned a data source.")
            
            if not prop_dict_list:
                prop_dict_list.append(prop_dict)
            else:
                # Try to find an address match. If the address isn't already in prop_dict_list, append new prop_dict. If it is, add entry to dict.
                match_found = False
                for stored_dict in prop_dict_list:
                    if stored_dict["address"] == prop_dict["address"]:
                        # Match found. Replace missing data
                        match_found = True
                        if "rentcast_data" not in stored_dict and "rentcast_data" in prop_dict:
                            stored_dict["rentcast_data"] = prop_dict["rentcast_data"]
                        if "rentometer_data" not in stored_dict and "rentometer_data" in prop_dict:
                            stored_dict["rentometer_data"] = prop_dict["rentometer_data"]
                        if not ("rentcast_data" in prop_dict or "rentometer_data" in prop_dict):
                            print(f"Warning: match found on {stored_dict["address"]} but no missing data could be replaced.")
                        break  # Exit the loop once match is found
                
                # If no match was found, append this as a new dict
                if not match_found:
                    prop_dict_list.append(prop_dict)

        # Check for data completion before returning prop_dict_list.
        for prop_dict in prop_dict_list:
            data_sources = ["rentcast_data", "rentometer_data"]
            for data_source in data_sources:
                if data_source not in prop_dict:
                    print(f"Warning: address {prop_dict["address"]} is still missing {data_source}.")

            # Drop "address" to make iterating through prop_dict.values() easier: all dict values should be Property objects.
            del prop_dict["address"]

        return prop_dict_list
    
    @staticmethod
    def _check_optional_typing(fld: field) -> Any:
        """Checks for Optional typing in partial PropertyData objects and, where needed, finds the actual intended type. Returns field type.
        This is a staticmethod so that combine_prop_data, which must take arrays of PropertyData, has access to it."""
        field_type = fld.type

        # If called on Property, must recurse to match dataclass fields with columns. First, unwrap Optional types.
        if get_origin(field_type) is not None: # Then it is a "generic" type, like Optional
            args = get_args(field_type)
            if args:
                field_type = args[0] # Optional[T] is Union[T, None], so index 0 is actual type
        
        return field_type

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
    rentometer_url: Optional[str] = None
    rentcast_id: Optional[str] = None
    rentometer_filename: Optional[str] = None
    rentcast_filename: Optional[str] = None


@dataclass
class Property(PropertyData):
    """Domain model containing subsets of property data."""
    location: Optional[LocationDetails] = field(default_factory=LocationDetails)
    features: Optional[FeatureDetails] = field(default_factory=FeatureDetails)
    attributes: Optional[AttributeDetails] = field(default_factory=AttributeDetails)
    values: Optional[ValueDetails] = field(default_factory=ValueDetails)
    metadata: Optional[Metadata] = field(default_factory=Metadata)