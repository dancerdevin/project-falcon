from property_schema import Property
from typing import Protocol

"""Store and retrieve Property objects, calling intake APIs when needed data is not already stored."""

"""When requesting data on a Property, first check storage."""
class PropertyStore:
  def get(location) -> Property:
    # NOTE: This can initially fail by default, then, e.g., scan all JSON dumps saved in the root directory, then get more refined.
    # When it fails, instantiate CompletePropertyProvider and get the Property to return that way
    pass

"""Interface that sets expectations for all data providers, e.g., RentcastPropertyProvider."""
class PropertyProvider(Protocol):
  # NOTE: how do I want to make this return a partial property object? at this stage, it won't have enough to instantiate a Property
  def request(location) -> Property: ...

class CompletePropertyProvider:
  # List distinct PropertyProviders and go through them as needed. THIS will return a completely initialized Property object
  def request(location) -> Property:
    pass

class RentcastPropertyProvider:
  # This follows the PropertyProvider Protocol and def request() outputs a partial property object. Put in CompletePropertyProvider
  def request(location) -> Property:
    pass

# TODO: Should I make a PropertyBuilder that is like a Property but with Optional fields, which PropertyProvider returns in a patchwork
# fashion and which CompletePropertyProvider assembles an actual Property out of?
# Or should I use Pydantic and upgrade my Property dataclass? Or just use a dict to hold my data in CompletePropertyProvider?