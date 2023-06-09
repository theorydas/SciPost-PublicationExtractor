import re
import requests
from tqdm import tqdm
from multiprocessing import Pool

from MetaForge.misc import Date, Abstract, format_line_spacing, print_error, print_warning

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

        try: # Change the publication date in titlepage.
            published_section = re.findall("Published (.*?)\n%%%%%%%%%% END TODO: DATES", paper)[0]
            if paper == (paper := paper.replace(f"Published {published_section}", f"Published {DMY}")):
                raise ValueError
        except:
            print_error("Could not find the publication date.")
        
        try: # Change in the URL section.
            url_section = re.findall("&amp;date_stamp=(.*?)}", paper)[0]
            if paper == (paper := paper.replace(f"&amp;date_stamp={url_section}", f"&amp;date_stamp={YMD}")):
                raise ValueError
        except:
            print_error("Could not find the URL section.")
        
        # Change at the top of every page.
        try:
            top_section = re.findall(r"\\rhead{\\small \\href{https://scipost.org(.*?)\}\}", paper)[0]
            if paper == (paper := paper.replace(top_section, f"{top_section[:-5]}{date.year})")):
                raise ValueError
        except:
            print_error("Could not find the top section.")
        
        return paper
    
    def find_wrong_dois(paper: str) -> list:
        """ Find the wrong DOIs in the paper. """
        
        
        # We only look for DOIs in the references section, i.e. below '\begin{thebibliography}'
        reference_section = re.findall(r"\\begin{thebibliography}{(.*?)\\end{thebibliography}", paper, re.DOTALL)[0]
        
        # First we replace everything that is commented out, i.e., anything following % in a line.
        uncommented_reference_section = re.sub(r"%.*", "", reference_section)
        
        # We find the DOIs in the paper.
        dois = re.findall(r"\\doi{(.*?)\}", uncommented_reference_section)
        
        # For each doi we ping the DOI foundation (https://doi.org/doi) and check if it is OK (200 code)
        # wrong_dois = [ doi for doi in tqdm(dois) if requests.get(f"https://doi.org/{doi}").status_code != 200 ]
        
        # We want to run this in parallel
        with Pool(10) as pool:
            statuses = list(tqdm(
                pool.imap(Paper.doi_status_code, dois), total = len(dois)
            ))
        
        wrong_dois = [ doi for doi, status in zip(dois, statuses) if status != 200 ]
        
        for doi in wrong_dois:
            status = statuses[dois.index(doi)]
            reference_id = dois.index(doi) +1
            link = f"https://doi.org/{doi}"
            
            string = f" [{reference_id}]: ({status}) - {link}"
            if status == 404:
                print_error(string)
            elif status != 302:
                print_warning(string) # Sometimes we find forbidden (403) due to bot protection.
        
        return wrong_dois
    
    def is_doi_wrong(doi: str) -> bool:
        return Paper.doi_status_code(doi) != 200
    
    def doi_status_code(doi: str) -> int:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            response = requests.get(f"https://doi.org/{doi}", headers = headers, allow_redirects = False)
            status_code = response.status_code
            
            return status_code
        except:
            return 500 # Server error (probably)
    
    def format_publication_format(paper: str, doi: str, date: Date) -> str:
        """ Format the paper for publication. """
        
        # Remove linenumbers
        if paper == (paper := paper.replace("\n\\linenumbers\n", "\n%\\linenumbers\n" )):
            print_error("Could not find linenumbers.")
        
        # Match \url links with \doi and \hrefs
        if paper == (paper := paper.replace("\n\\urlstyle{sf}\n", "\n\\urlstyle{same}\n" )):
            print_error("Could not find urlstyle.")
        
        if paper != (paper := paper.replace("\n\\usepackage[bottom]{footmisc}\n", "\n%\\usepackage[bottom]{footmisc}\n" )):
            print_warning("Removed (problematic) footmisc package.")
        
        # # Add the doi on every page.
        try:
            original = re.findall("scipost.org/(.*?)\}\{SciPost", paper)[0]
            if paper == (paper := paper.replace(f"\\rhead{{\small \href{{https://scipost.org/{original}}}", f"\\rhead{{\small \href{{https://scipost.org/{doi}}}")):
                raise ValueError
        except:
            print_error("Could not find the doi section.")
        
        # We need to recognise which journal the paper is published at, and search for the appropriate template.
        journal = doi.split(".")[0]
        
        if journal != "SciPostPhysProc":
            # We need to begin a minipage environment. But first we need to find the right textwidth dimensions according to journal.
            dimension = re.findall(r'\\begin{minipage}{(.*?)\\textwidth}\n%%%%%%%%%% TODO: DATES', paper)[0]
            
            original_section = f"\\begin{{minipage}}{{{dimension}\\textwidth}}\n%%%%%%%%%% TODO: DATES"
            target_section = f"\\begin{{minipage}}{{{dimension}\\textwidth}}\n\\noindent\\begin{{minipage}}{{0.68\\textwidth}}\n%%%%%%%%%% TODO: DATES"
            
            paper = paper.replace(original_section, target_section)
            
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
        else:
            issue = doi.split(".")[1]
            page = doi.split(".")[2]
            
            #SciPost Phys. Proc. ?, ?? (202?)
            # We remove the extra 2 from the year.
            if paper == (paper := paper.replace(" ?, ?? (202?)", f" {issue}, {page} (20??)")):
                print_error("Could not find the year.")
            
            # Proceedings also carry the issue number on their page numbers.
            if paper == (paper := paper.replace(r"??.\thepage", rf"{page}.\thepage")):
                print_error("Could not find the page numbers at the end of each page.")
            
            if paper.find(r"\noindent\begin{minipage}{0.68\textwidth}") == -1:
                print_warning("Had to add a minipage to fix the central banner.")
                paper = paper.replace("%%%%%%%%%% TODO: DATES", "\\noindent\\begin{minipage}{0.68\\textwidth}\n%%%%%%%%%% TODO: DATES")
            
            # Find the central DOI section near the dates.
            # doi_section = re.findall(r'%%%%%%%%%% TODO: DOI\n(.*?)\n%%%%%%%%%% END TODO: DOI', paper, re.DOTALL)[0]

            # if paper == (paper := paper.replace(doi_section, rf"\newline \doi{{10.21468/SciPostPhysProc.{issue}.{page}}}")):
            #     print_error("Could not find the central DOI near the dates.")
            
            if paper == (paper := paper.replace("\doi{10.21468/SciPostPhysProc.?", f"\doi{{10.21468/SciPostPhysProc.{issue}")):
                print_error("Could not find the DOI.")
            
            # if paper == (paper := paper.replace("SciPostPhysProc.?.??", f"SciPostPhysProc.{issue}.{page}")):
            #     print_error("Could not find DOI links at the top and center.")
            
            # Find what exists between two DOI tags, and replace it with the new section.
            try:
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
            
                if paper == (paper := paper.replace(original_doi_section, new_doi_section)):
                    raise ValueError
            except:
                print_warning("Could not find the old DOI section at the center.")
        # Add a publication date to the paper.
        paper = Paper.set_date(paper, date)
        return paper