"""Strategy contract. Cartridges propose signals; only PaperEngine executes trades."""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Cartridge:
    id:str
    name:str
    description:str
    module:str
    parameters:tuple
    long:Callable
    short:Callable
    warmup:Callable
    reason:Callable
    version:str="1.0.0"
    requires_volume:bool=False
    protocol_only:bool=False
    fixed:tuple=()

    def describe(self):
        return {"id":self.id,"name":self.name,"description":self.description,"version":self.version,
                "parameters":list(self.parameters),"requires_volume":self.requires_volume,
                "protocol_only":self.protocol_only,"fixed":dict(self.fixed),
                "directions":["long","short","both"],"status":"Onderzoek; geen bewezen winstgevendheid"}
