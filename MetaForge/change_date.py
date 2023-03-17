import argparse

from MetaForge.paper import Paper
from MetaForge.misc import Date

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
        paper = Paper.set_date(paper, Date.from_DMY(args.publish_date))
        f.write(paper)
        f.close()
