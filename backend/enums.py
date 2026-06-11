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

class WaterSource(str, enum.Enum):
    WELL = "well"
    CANAL = "canal"
    SURFACE = "surface"

class Locale(str, enum.Enum):
    EN = "en"
    ES = "es"

class Tier(str, enum.Enum):
    FREE = "free"
    PAID = "paid"

class IrrigationSource(str, enum.Enum):
    USER_LOG = "user_log"
    ESTIMATED = "estimated"

class JobStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class AlertChannel(str, enum.Enum):
    SMS = "sms"

class AlertFeedback(str, enum.Enum):
    """Farmer's reply to "does the crop look stressed?" — ground truth for
    alert precision metrics and Phase 9 model labels."""
    YES = "yes"
    NO = "no"