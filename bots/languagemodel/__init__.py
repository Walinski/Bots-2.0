import logging

GREY_FADED = "\033[2;37m"
YELLOW_FADED = "\033[2;33m"
RED_FADED = "\033[2;31m"
BRIGHT_BLUE = "\033[1;34m"
RESET = "\033[0m"

class CustomColorFormatter(logging.Formatter):
    def __init__(self, fmt=None, color=GREY_FADED):
        super().__init__(fmt)
        self.color = color
    
    def format(self, record):
        log_msg = super().format(record)
        if record.message:  
            log_msg = log_msg.replace(record.message, f"{self.color}{record.message}{RESET}")
        
        return log_msg
    
    def set_color(self, color):
        """Method to change the color dynamically."""
        self.color = color

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
LoggerFormatting = CustomColorFormatter('%(asctime)s: %(message)s')
handler.setFormatter(LoggerFormatting)
logger.addHandler(handler)
