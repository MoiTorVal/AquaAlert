import enum 

class SoilTexture(str, enum.Enum):
    Sandy         = "Sandy"
    LoamySand     = "LoamySand"
    SandyLoam     = "SandyLoam"
    Loam          = "Loam"
    SiltLoam      = "SiltLoam"
    Silt          = "Silt"
    SandyClayLoam = "SandyClayLoam"
    ClayLoam      = "ClayLoam"
    SiltyClayLoam = "SiltyClayLoam"
    SandyClay     = "SandyClay"
    SiltyClay     = "SiltyClay"
    Clay          = "Clay"

class StressSeverity(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"