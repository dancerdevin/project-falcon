from property_store import PropertyStore
from property_publish import PropertyGsheetPublisher

# [] pipeline update: get_property() vs get_properties(), just do Property not List[Property] in former, latter is stub
# 	* don't worry about breaking up build_properties() but note it's doing a lot of work or whatever
# 	* encapsulate property -> DataFrame -> property stuff as class helper methods just for clarity
# 	* note that when you eventually return to locale analysis type stuff, you'll hook it up to get_properties()
# 	* depreciate location_params() as a part of that distinguishing of functionality
# () go over other updates and do minor stuff / leave TODOs if it'd be good to do later
# 	* probably leave street address normalization as a TODO or refer to easy techniques

if __name__ == "__main__":
    prop_obj = PropertyStore().get_property("6478 S M St, Tacoma, WA 98408")
    PropertyGsheetPublisher().publish(prop_obj)