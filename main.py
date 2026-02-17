from property_store import PropertyStore
from property_publish import PropertyGsheetPublisher

if __name__ == "__main__":
    prop_list = PropertyStore().get("6478 S M St, Tacoma, WA 98408")
    prop_obj = prop_list[0]
    PropertyGsheetPublisher().publish(prop_obj)