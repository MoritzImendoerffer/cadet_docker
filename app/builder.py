from CADETProcess.processModel import (
    ComponentSystem, StericMassAction,
    Inlet, Outlet, GeneralRateModel,
    FlowSheet, Process
)

# Register supported models
binding_models = {
    "SMA": StericMassAction
}

rate_models = {
    "GeneralRateModel": GeneralRateModel
}

unit_classes = {
    "Inlet": Inlet,
    "Outlet": Outlet
}

def build_process(parsed: dict) -> Process:
    # Build component system
    cs = ComponentSystem()
    for comp in parsed["ComponentSystemParams"]["components"]:
        cs.add_component(comp)

    # Build binding model
    bp = parsed["BindingParams"]
    binding_cls = binding_models.get(bp["type"])
    if not binding_cls:
        raise NotImplementedError(f"Unsupported binding model: {bp['type']}")
    binding = binding_cls(cs, name=bp["name"])
    binding.parameters = {k: bp[k] for k in binding.required_parameters}

    # Build rate model (column)
    rp = parsed["RateModelParams"]
    column_name = rp["name"]
    rate_cls = rate_models.get(column_name)
    if not rate_cls:
        raise NotImplementedError(f"Unsupported rate model: {column_name}")
    column = rate_cls(cs, name=column_name)
    column.parameters = {k: rp[k] for k in column.required_parameters}
    column.binding = binding

    # Build other units
    inlet = Inlet(cs, **parsed["InletParams"])
    outlet = Outlet(cs, **parsed["OutletParams"])

    # Build flowsheet
    fs = FlowSheet(cs)
    unit_instances = {
        inlet.name: inlet,
        outlet.name: outlet,
        column.name: column
    }

    for unit_def in parsed["FlowSheetParams"]["units"]:
        unit = unit_instances[unit_def["name"]]
        is_product = unit.name == parsed["FlowSheetParams"]["product_outlet"]
        fs.add_unit(unit, product_outlet=is_product)

    for conn in parsed["FlowSheetParams"]["connections"]:
        fs.add_connection(
            unit_instances[conn["from_unit"]],
            unit_instances[conn["to_unit"]]
        )

    # Build and return full process
    return Process(
        system=cs,
        flowSheet=fs,
        **parsed["ProcessParams"]
    )
