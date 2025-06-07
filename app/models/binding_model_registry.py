from typing import Dict, Type

from CADETProcess.processModel import StericMassAction

BindingModel = Type

binding_models: Dict[str, BindingModel] = {
    "StericMassAction": StericMassAction
}
