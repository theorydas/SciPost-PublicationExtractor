import argparse

from MetaForge.paper import Paper
from MetaForge.misc import Date

from datetime import date
from datetime import timedelta

if __name__ == "__main__":
    print("Changing date...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("latex_file")
    parser.add_argument("publish_date") # DD-MM-YYYY

    args = parser.parse_args()

    # We read the file first
    with open(args.latex_file, "r") as f:
        paper = f.read()
        f.close()
    
    # We now open it with write permissions to clean it first.
    with open(args.latex_file, "w") as f:
        if args.publish_date.isdigit():
            # We want to publish with a delay.
            publication_date = (date.today() + timedelta(days = int(args.publish_date))).strftime("%d-%m-%Y")
        else:
            # We want to publish on a specific date.
            publication_date = args.publish_date
        
        paper = Paper.set_date(paper, Date.from_DMY(publication_date))
        f.write(paper)
        f.close()
