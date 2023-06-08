import argparse

from MetaForge.misc import Date, print_error
from MetaForge.paper import Paper
from MetaForge.write_jats_abstract import write_jats_abstract

from pathlib import Path
from datetime import date, timedelta

def make_publication_format(paper_path: str, doi: str, date: str) -> None:
    with open(paper_path, "r") as f:
        # Given the paper_path we want to find its parent folder if possible.
        folder = paper_path.split("/")[0] # For this to work, publications should be in folders in a directory where this is called.
        
        target_name = doi.replace(".", "_")
        with open(f"{folder}/{target_name}.tex", "w") as f2:
            formatted = Paper.format_publication_format(f.read(), doi, Date.from_DMY(date))
            f2.write(formatted)
            f2.close()
        
        # We also want a JATS version of the abstract in the folder.
        try:
            abstract = Paper.get_abstract(formatted)
            abstractJats = abstract.jats
            
            if abstractJats == "" or abstractJats == None:
                raise Exception("No abstract found.")
            
            with open(f"{folder}/Abstract.txt", "w") as f2:
                f2.write(abstract.text)
                f2.close()
            
            write_jats_abstract(f"{folder}/Abstract.txt")
            
        except:
            print_error("No abstract found.")
        
        f.close()
        
    # We copy the crossmark image to the folder.
    imagepath = "CROSSMARK_BW_square_no_text.png"
    
    source = Path(f"../MetaForge/{imagepath}")
    newpath = Path(f"{folder}/{imagepath}")
    newpath.write_bytes(source.read_bytes())
    
    # We also copy the most up-to-date SciPost.cls file.
    imagepath = "SciPost.cls"
    
    source = Path(f"../MetaForge/{imagepath}")
    newpath = Path(f"{folder}/{imagepath}")
    newpath.write_bytes(source.read_bytes())
    
    # And the .gitignore file.    
    source = Path(f"../MetaForge/gitignore.txt")
    newpath = Path(f"{folder}/.gitignore")
    newpath.write_bytes(source.read_bytes())
    
    pass

if __name__ == "__main__":
    print("Creating publishable documents...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("latex_file")
    parser.add_argument("target_doi") # Journal.??.?.???
    parser.add_argument("publish_date") # DD-MM-YYYY or blank for today or int (for days from today).

    args = parser.parse_args()
    publication_date = args.publish_date
    if args.publish_date.isdigit():
        # We want to publish with a delay.
        publication_date = (date.today() + timedelta(days = int(args.publish_date))).strftime("%d-%m-%Y")
    
    print("Publication date:", publication_date)
    make_publication_format(args.latex_file, args.target_doi, publication_date)
