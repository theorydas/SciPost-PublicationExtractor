import argparse

from MetaForge.misc import Abstract

def write_jats_abstract(abstract_path: str) -> None:
    with open(abstract_path, "r+") as f:
        abstract = f.read()
        
        abstractJats = Abstract(abstract).jats
        f.write("\n\n")
        
        # We want to know if there are any special characters in the abstract. If there are, we inform the user.
        special_chars = ["<", ">", "&", "%", "\\", "'", "`", "~", "--"]
        for char in special_chars:
            if char in abstract:
                f.write(f"The abstract contains the special character: {char}")
                f.write("\n")
        
        f.write("\n\n")
        f.write(abstractJats) # We remove the newlines that are inserted by the JATS format.
        f.close()
    
    pass

if __name__ == "__main__":
    print("Creating jats format...")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("txt_file")

    args = parser.parse_args()

    write_jats_abstract(args.txt_file)
