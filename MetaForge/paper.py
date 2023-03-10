import re

from .misc import Date, format_line_spacing

class Paper():
    """ A class to represent a publication. """
    
    def get_title(paper: str) -> str:
        """ Finds the title of the paper. """
        
        title = re.findall('TODO: TITLE Paste title here\n(.*?)\n% multiline titles: end', paper, re.DOTALL)[0]
        title = format_line_spacing(title)
        
        return title
    
    def get_abstract(paper: str) -> str:
        """ Finds the abstract of the paper. """
        
        abstract = re.findall('TODO: ABSTRACT Paste abstract here\n(.*?)\n%%%%%%%%%% END TODO: ABSTRACT', paper, re.DOTALL)[0]
        abstract = format_line_spacing(abstract)
        
        return abstract
    
    def get_dates(paper: str) -> list:
        """ Finds the received and accepted dates of the paper. """
        
        date_section = re.findall('TODO: DATES\n(.*?)\n%%%%%%%%%% END TODO: DATES', paper, re.DOTALL)[0]
        
        # We find these in DD-MM-YYYY format.
        received = re.findall('Received (.*?) \\\\newline', date_section, re.DOTALL)[0]
        accepted = re.findall('Accepted (.*?) \\\\newline', date_section, re.DOTALL)[0]
        
        # Date format should be in YYYY-MM-DD
        return Date.from_DMY(received), Date.from_DMY(accepted)