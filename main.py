from property_store import PropertyStore
from property_publish import PropertyGsheetPublisher
from property_get_options import PropertyLocationType, PropertyGetOption

# () go over other updates and do minor stuff / leave TODOs if it'd be good to do later
# 	* probably leave street address normalization as a TODO or refer to easy techniques

if __name__ == "__main__":
    prop_obj = PropertyStore().get_property(PropertyLocationType.ADDRESS, "6478 S M St, Tacoma, WA 98408", PropertyGetOption.JSON_ONLY)
    PropertyGsheetPublisher().publish(prop_obj)