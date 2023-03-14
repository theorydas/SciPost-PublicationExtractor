import re

from MetaForge.misc import Date, Abstract, format_line_spacing

class Paper():
    """ A class to represent a publication. """
    
    def get_title(paper: str) -> str:
        """ Finds the title of the paper. """
        
        title = re.findall('TODO: TITLE Paste title here\n(.*?)\n% multiline titles: end', paper, re.DOTALL)[0]
        title = format_line_spacing(title)
        
        return title
    
    def get_abstract(paper: str) -> Abstract:
        """ Finds the abstract of the paper. """
        
        abstract = re.findall('TODO: ABSTRACT Paste abstract here\n(.*?)\n%%%%%%%%%% END TODO: ABSTRACT', paper, re.DOTALL)[0]
        abstract = format_line_spacing(abstract)
        
        return Abstract(abstract)
    
    def get_dates(paper: str) -> list:
        """ Finds the received and accepted dates of the paper. """
        
        date_section = re.findall('TODO: DATES\n(.*?)\n%%%%%%%%%% END TODO: DATES', paper, re.DOTALL)[0]
        
        # We find these in DD-MM-YYYY format.
        received = re.findall('Received (.*?) \\\\newline', date_section, re.DOTALL)[0]
        accepted = re.findall('Accepted (.*?) \\\\newline', date_section, re.DOTALL)[0]
        
        # Date format should be in YYYY-MM-DD
        return Date.from_DMY(received), Date.from_DMY(accepted)
    
    def get_affiliations(paper: str) -> dict:
        # First we find the section where the affiliations exist.
        section = re.findall('TODO: AFFILIATIONS\n(.*?)\n%%%%%%%%%% END', paper, re.DOTALL)[0] + "%" # We add a % to the end to make sure the regex works.

        # Our goal is to create a dictionary where the keys are the affiliation ids from author profiles, and the values are the affiliation text.
        affids = re.findall(r"\{\\bf (\d+)\}", section) # We look for affiliations based on the {\bf k} format.
        if affids:
            affids = [int(i) for i in affids] # We count the number of affiliations.
            
            if affids != list(range(1, len(affids)+1)):
                raise ValueError("Affiliation ids are not in order. Are there missing affiliations?")
            
            affiliations = {}
            for k in affids: # Extract the affiliation text for each affiliation id.
                aff = re.findall(fr"bf {k}}} (.*?)({{|\%)", section, re.DOTALL)[0][0]
                
                # Format the line spacing.
                aff = format_line_spacing(aff)
                
                # Create a dictionary entry for that affiliation.
                affiliations[k] = aff
            
            return affiliations
        else: # There is only one affiliation OR something went wrong. We return all as is.
            return {1: section[:-1]} # We remove the % at the end (which was put for the other case to work).
    
    def get_emails(paper: str) -> dict:
        # First we find the section which contains the mails.
        section = re.findall('\% TODO: EMAIL(.*?)\% END TODO: EMAIL', paper, re.DOTALL)[0]

        # We want to extract the email addresses.
        mailkeys = re.findall(r"\$(.*?)\$", section)
        mails = re.findall(r"mailto:(.*?)\}", section)

        mails = {mailsymbol: mail for mailsymbol, mail in zip(mailkeys, mails)}
        
        return mails
    
    def format_publication_format(paper: str, doi: str, date: Date) -> str:
        # Firt, we need to begin a minipage environment.
        original_section = "\\begin{minipage}{0.4\\textwidth}\n%%%%%%%%%% TODO: DATES"
        target_section = "\\begin{minipage}{0.4\\textwidth}\n\\noindent\\begin{minipage}{0.68\\textwidth}\n%%%%%%%%%% TODO: DATES"
        
        paper = paper.replace(original_section, target_section)
        
        # Add the publication date
        paper = paper.replace("Published ??-??-20??", f"Published {date.DMY()}")
        
        
        # Add the doi on every page.
        paper = paper.replace("\\rhead{\small \href{https://scipost.org/SciPostPhys.?.?.???}", f"\\rhead{{\small \href{{https://scipost.org/{doi}}}")
        
        # We need to recognise which journal the paper is published at, and search for the appropriate template.
        journal = doi.split(".")[0]
        if journal == "SciPostPhys" or journal == "SciPostPhysCore":
            #SciPost Phys. ?, ??? (20??)
            #SciPost Phys. Core ?, ??? (20??)
            paper = paper.replace(" ?, ??? (20??)", f" {doi.split('.')[1]}, {doi.split('.')[3]} ({date.year})")
        elif journal == "SciPostPhysLectNotes":
            #SciPost Phys. Lect. Notes ??? (20??)
            paper = paper.replace(" ??? (20??)", f" {doi.split('.')[1]} ({date.year})")
        else:
            print("No known journal found. Please incorporate in the code.")
        
        
        
        # Find what exists between two DOI tags, and replace it with the new section.
        original_doi_section = re.findall(r'%%%%%%%%%% TODO: DOI\n(.*?)\n%%%%%%%%%% END TODO: DOI', paper, re.DOTALL)[0]
        new_doi_section = f"""}}
    \\end{{minipage}}
    \\begin{{minipage}}{{0.25\\textwidth}}
    \\begin{{center}}
    \\href{{https://crossmark.crossref.org/dialog/?doi=10.21468/{doi}&amp;domain=pdf&amp;date_stamp={date.YMD()}}}{{\includegraphics[width=7mm]{{CROSSMARK_BW_square_no_text.png}}}}\\\\
    \\tiny{{Check for}}\\\\
    \\tiny{{updates}}
    \\end{{center}}
    \\end{{minipage}}
    \\\\\\\\
    \small{{\doi{{10.21468/{doi}}}"""
        
        paper = paper.replace(original_doi_section, new_doi_section)
        
        return paper