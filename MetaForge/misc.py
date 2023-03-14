import subprocess
import re

class Author():
    """ A class to represent an author. """
    
    def __init__(self, name, email = None, affiliation = None):
        self.name = name
        self.email = email
        self.affiliation = affiliation

class Abstract():
    """ A class to represent an abstract. """
    
    def __init__(self, text):
        self.text = text
        self.jats = self.get_Jats()
    
    def get_Jats(self):
        """ Returns the JATS XML for the abstract. """
        # First we create a temporary file with the original abstract.
        
        with open("abstract.txt", "w") as f:
            f.write(self.text)
        
        # Then we use pandoc to convert it to JATS.
        subprocess.run(["pandoc", "-t", "jats", "abstract.txt", "-o", "abstract.xml"])
        
        # We read the JATS XML, and delete the temporary files.
        abstract_jats = open("abstract.xml", "r").read()        
        subprocess.run(["rm", "abstract.txt"])
        subprocess.run(["rm", "abstract.xml"])
        
        # Finally we have to format the JATS XML.
        tags_to_change = ["p", "inline-formula", "alternatives", "tex-math"]
        for tag in tags_to_change:
            abstract_jats = abstract_jats.replace(f"<{tag}>", f"<jats:{tag}>")
            abstract_jats = abstract_jats.replace(f"</{tag}>", f"</jats:{tag}>")
        
        return abstract_jats
    
    def __repr__(self):
        return self.text

class Date():
    """ A class to represent a date. """
    
    def __init__(self, year: int, month: int, day: int):
        self.year = year
        self.month = month
        self.day = day
    
    @classmethod
    def from_DMY(cls, date_string: str):
        """ Creates a Date object from a string in the format DD-MM-YYYY. """
        
        day = int(re.findall('(\d{2})', date_string)[0])
        month = int(re.findall('(\d{2})', date_string)[1])
        year = int(re.findall('(\d{4})', date_string)[0])
        
        return cls(year, month, day)
    
    @classmethod
    def from_YMD(cls, date_string: str):
        """ Creates a Date object from a string in the format YYYY-MM-DD. """
        
        year = int(re.findall('(\d{4})', date_string)[0])
        month = int(re.findall('(\d{2})', date_string)[0])
        day = int(re.findall('(\d{2})', date_string)[1])
        
        return cls(year, month, day)
    
    def DMY(self) -> str:
        """ Returns the date in the format DD-MM-YYYY. """
        return f"{self.day}-{self.month:02d}-{self.year:02d}"
    
    def YMD(self) -> str:
        """" Returns the date in the format YYYY-MM-DD. """
        return f"{self.year}-{self.month:02d}-{self.day:02d}"
    
    def __repr__(self):
        return self.YMD()


# ============================================================

def format_line_spacing(text: str) -> str:
    """ Formats the line spacing of a string. """
    
    # We remove any newlines, and backslashes.
    text = text.replace("\n", " ")
    text = text.replace(r"\\", " ")
    
    # We remove any extra whitespace.
    text = re.sub(r"\s+", " ", text)
    
    # If the final character is a space, we remove it.
    text = text.strip()
    
    return text