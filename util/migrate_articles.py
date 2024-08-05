import os
import shutil
from util.path_utils import get_output_dir
from pages_util.Settings import load_categories, save_categories


def migrate_existing_articles():
    # Get the root output directory
    root_output_dir = get_output_dir()

    # Get all categories
    categories = load_categories()

    # Create "Uncategorized" category if it doesn't exist
    if "Uncategorized" not in categories:
        categories.append("Uncategorized")
        save_categories(categories)

    # Iterate through all files in the root output directory
    for item in os.listdir(root_output_dir):
        item_path = os.path.join(root_output_dir, item)
        if os.path.isdir(item_path):
            # Check if this directory is a category
            if item not in categories:
                # Move this directory to the "Uncategorized" category
                uncategorized_dir = get_output_dir("Uncategorized")
                shutil.move(item_path, os.path.join(uncategorized_dir, item))

    print("Migration complete.")


if __name__ == "__main__":
    migrate_existing_articles()
