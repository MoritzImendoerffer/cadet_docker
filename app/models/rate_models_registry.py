from typing import Dict, Type
from CADETProcess.processModel import GeneralRateModel

RateModel = Type

rate_models: Dict[str, RateModel] = {
    "GeneralRateModel": GeneralRateModel,
    # "SomeOtherModel":  SomeOtherModel,
}