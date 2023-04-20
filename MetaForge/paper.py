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

    def set_doi(paper: str, doi: str) -> str:
        """ Set the DOI of the paper on all related fields. """
        
        return paper.replace("TODO: DOI", doi)
    
    def set_date(paper: str, date: Date) -> str:
        """ Set the date of the paper on all related fields. """
        
        DMY = date.DMY()
        YMD = date.YMD()

        # Change the publication date in titlepage.
        published_section = re.findall("Published (.*?)\n%%%%%%%%%% END TODO: DATES", paper)[0]
        paper = paper.replace(f"Published {published_section}", f"Published {DMY}")
        
        # Change in the URL section.
        url_section = re.findall("&amp;date_stamp=(.*?)}", paper)[0]
        paper = paper.replace(f"&amp;date_stamp={url_section}", f"&amp;date_stamp={YMD}")
        
        # Change at the top of every page.
        top_section = re.findall(r"\\rhead{\\small \\href{https://scipost.org(.*?)\}\}", paper)[0]
        paper = paper.replace(top_section, f"{top_section[:-5]}{date.year})")

        return paper
    
    def format_publication_format(paper: str, doi: str, date: Date) -> str:
        """ Format the paper for publication. """
        
        # Remove linenumbers
        paper = paper.replace("\n\\linenumbers\n", "\n%\\linenumbers\n" )
        
        # Match \url links with \doi and \hrefs
        paper = paper.replace("\n\\urlstyle{sf}\n", "\n\\urlstyle{same}\n" )
        
        # Remove \usepackage[bottom]{footmisc} which breaks footnotes in some compilers. TODO: Check in summer if still needed or is removed from template.
        paper = paper.replace("\n\\usepackage[bottom]{footmisc}\n", "\n%\\usepackage[bottom]{footmisc}\n" )
        
        # We need to begin a minipage environment. But first we need to find the right textwidth dimensions according to journal.
        dimension = re.findall(r'\\begin{minipage}{(.*?)\\textwidth}\n%%%%%%%%%% TODO: DATES', paper)[0]
        
        original_section = f"\\begin{{minipage}}{{{dimension}\\textwidth}}\n%%%%%%%%%% TODO: DATES"
        target_section = f"\\begin{{minipage}}{{{dimension}\\textwidth}}\n\\noindent\\begin{{minipage}}{{0.68\\textwidth}}\n%%%%%%%%%% TODO: DATES"
        
        paper = paper.replace(original_section, target_section)
        
        # Add the doi on every page.
        original = re.findall("scipost.org/(.*?)\}\{SciPost", paper)[0]
        paper = paper.replace(f"\\rhead{{\small \href{{https://scipost.org/{original}}}", f"\\rhead{{\small \href{{https://scipost.org/{doi}}}")
        
        # We need to recognise which journal the paper is published at, and search for the appropriate template.
        journal = doi.split(".")[0]
        if journal == "SciPostPhys" or journal == "SciPostPhysCore" or journal == "SciPostChem":
            #SciPost Phys. ?, ??? (20??), SciPost Phys. Core ?, ??? (20??), SciPost Chem. ?, ??? (20??)
            paper = paper.replace(" ?, ??? (20??)", f" {doi.split('.')[1]}, {doi.split('.')[3]} (20??)")
        elif journal == "SciPostPhysLectNotes":
            #SciPost Phys. Lect. Notes ??? (20??)
            paper = paper.replace(" ??? (20??)", f" {doi.split('.')[1]} (20??)")
        elif journal == "SciPostPhysCodeb":
            #SciPost Phys. Codebases ?, ??? (20??) ->
            #SciPost Phys. Codebases ?? (20??)
            paper = paper.replace(" ?, ??? (20??)", f" {doi.split('.')[1]} (20??)")
        else:
            print("No known journal found. Please incorporate in the code.")
        
        # Find what exists between two DOI tags, and replace it with the new section.
        original_doi_section = re.findall(r'%%%%%%%%%% TODO: DOI\n(.*?)\n%%%%%%%%%% END TODO: DOI', paper, re.DOTALL)[0]
        new_doi_section = f"""}}
    \\end{{minipage}}
    \\begin{{minipage}}{{0.25\\textwidth}}
    \\begin{{center}}
    \\href{{https://crossmark.crossref.org/dialog/?doi=10.21468/{doi}&amp;domain=pdf&amp;date_stamp=YYYY-MM-DD}}{{\includegraphics[width=7mm]{{CROSSMARK_BW_square_no_text.png}}}}\\\\
    \\tiny{{Check for}}\\\\
    \\tiny{{updates}}
    \\end{{center}}
    \\end{{minipage}}
    \\\\\\\\
    \small{{\doi{{10.21468/{doi}}}"""
        
        paper = paper.replace(original_doi_section, new_doi_section)
        
        # Add a publication date to the paper.
        paper = Paper.set_date(paper, date)
        return paper