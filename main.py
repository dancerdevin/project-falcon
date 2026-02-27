from property_store import PropertyStore
from property_publish import PropertyGsheetPublisher

# 	* depreciate location_params() as a part of that distinguishing of functionality
# () go over other updates and do minor stuff / leave TODOs if it'd be good to do later
# 	* probably leave street address normalization as a TODO or refer to easy techniques

if __name__ == "__main__":
    prop_obj = PropertyStore().get_property("6478 S M St, Tacoma, WA 98408")
    PropertyGsheetPublisher().publish(prop_obj)