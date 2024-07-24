import os
import json
import base64
import datetime
import pytz
from .shared_utils import parse


class DemoFileIOHelper:
    @staticmethod
    def read_structure_to_dict(articles_root_path):
        """
        Reads the directory structure of articles stored in the given root path and
        returns a nested dictionary. The outer dictionary has article names as keys,
        and each value is another dictionary mapping file names to their absolute paths.

        Args:
            articles_root_path (str): The root directory path containing article subdirectories.

        Returns:
            dict: A dictionary where each key is an article name, and each value is a dictionary
                of file names and their absolute paths within that article's directory.
        """
        articles_dict = {}
        for topic_name in os.listdir(articles_root_path):
            topic_path = os.path.join(articles_root_path, topic_name)
            if os.path.isdir(topic_path):
                articles_dict[topic_name] = {}
                for file_name in os.listdir(topic_path):
                    file_path = os.path.join(topic_path, file_name)
                    articles_dict[topic_name][file_name] = os.path.abspath(
                        file_path)
        return articles_dict

    @staticmethod
    def read_txt_file(file_path):
        """
        Reads the contents of a text file and returns it as a string.

        Args:
            file_path (str): The path to the text file to be read.

        Returns:
            str: The content of the file as a single string.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def read_json_file(file_path):
        """
        Reads a JSON file and returns its content as a Python dictionary or list,
        depending on the JSON structure.

        Args:
            file_path (str): The path to the JSON file to be read.

        Returns:
            dict or list: The content of the JSON file. The type depends on the
                        structure of the JSON file (object or array at the root).
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def read_image_as_base64(image_path):
        """
        Reads an image file and returns its content encoded as a base64 string,
        suitable for embedding in HTML or transferring over networks where binary
        data cannot be easily sent.

        Args:
            image_path (str): The path to the image file to be encoded.

        Returns:
            str: The base64 encoded string of the image, prefixed with the necessary
                data URI scheme for images.
        """
        with open(image_path, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data)
        data = "data:image/png;base64," + encoded.decode("utf-8")
        return data

    @staticmethod
    def set_file_modification_time(file_path, modification_time_string):
        """
        Sets the modification time of a file based on a given time string in the California time zone.

        Args:
            file_path (str): The path to the file.
            modification_time_string (str): The desired modification time in 'YYYY-MM-DD HH:MM:SS' format.
        """
        california_tz = pytz.timezone("America/Los_Angeles")
        modification_time = datetime.datetime.strptime(
            modification_time_string, "%Y-%m-%d %H:%M:%S"
        )
        modification_time = california_tz.localize(modification_time)
        modification_time_utc = modification_time.astimezone(
            datetime.timezone.utc)
        modification_timestamp = modification_time_utc.timestamp()
        os.utime(file_path, (modification_timestamp, modification_timestamp))

    @staticmethod
    def get_latest_modification_time(path):
        """
        Returns the latest modification time of all files in a directory in the California time zone as a string.

        Args:
            path (str): The path to the directory or file.

        Returns:
            str: The latest file's modification time in 'YYYY-MM-DD HH:MM:SS' format.
        """
        california_tz = pytz.timezone("America/Los_Angeles")
        latest_mod_time = None

        file_paths = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
        else:
            file_paths = [path]

        for file_path in file_paths:
            modification_timestamp = os.path.getmtime(file_path)
            modification_time_utc = datetime.datetime.utcfromtimestamp(
                modification_timestamp
            )
            modification_time_utc = modification_time_utc.replace(
                tzinfo=datetime.timezone.utc
            )
            modification_time_california = modification_time_utc.astimezone(
                california_tz
            )

            if (
                latest_mod_time is None
                or modification_time_california > latest_mod_time
            ):
                latest_mod_time = modification_time_california

        if latest_mod_time is not None:
            return latest_mod_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return datetime.datetime.now(
                california_tz).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def assemble_article_data(article_file_path_dict):
        if (
            "storm_gen_article.md" in article_file_path_dict
            or "storm_gen_article_polished.md" in article_file_path_dict
        ):
            full_article_name = (
                "storm_gen_article_polished.md"
                if "storm_gen_article_polished.md" in article_file_path_dict
                else "storm_gen_article.md"
            )
            # Read the article content
            article_content = DemoFileIOHelper.read_txt_file(
                article_file_path_dict[full_article_name]
            )

            # Add the current date at the beginning of the article
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            article_content = f"{current_date}\n\n{article_content}"

            # Parse the article content
            parsed_article_content = parse(article_content)

            article_data = {"article": parsed_article_content}
            if "url_to_info.json" in article_file_path_dict:
                article_data["citations"] = (
                    DemoFileIOHelper._construct_citation_dict_from_search_result(
                        DemoFileIOHelper.read_json_file(
                            article_file_path_dict["url_to_info.json"])))
            if "conversation_log.json" in article_file_path_dict:
                article_data["conversation_log"] = DemoFileIOHelper.read_json_file(
                    article_file_path_dict["conversation_log.json"])
            return article_data
        return None

    @staticmethod
    def _construct_citation_dict_from_search_result(search_results):
        """
        Constructs a citation dictionary from search results.

        Args:
            search_results (dict): A dictionary containing search results.

        Returns:
            dict or None: A dictionary of citations, or None if search_results is None.
        """
        if search_results is None:
            return None
        citation_dict = {}
        for url, index in search_results["url_to_unified_index"].items():
            citation_dict[index] = {
                "url": url,
                "title": search_results["url_to_info"][url]["title"],
                "snippets": search_results["url_to_info"][url]["snippets"],
            }
        return citation_dict

    @staticmethod
    def write_txt_file(file_path, content):
        """
        Writes content to a text file.

        Args:
            file_path (str): The path to the text file to be written.
            content (str): The content to write to the file.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def write_json_file(file_path, data):
        """
        Writes data to a JSON file.

        Args:
            file_path (str): The path to the JSON file to be written.
            data (dict or list): The data to write to the file.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create_directory(directory_path):
        """
        Creates a directory if it doesn't exist.

        Args:
            directory_path (str): The path of the directory to create.
        """
        os.makedirs(directory_path, exist_ok=True)

    @staticmethod
    def delete_file(file_path):
        """
        Deletes a file if it exists.

        Args:
            file_path (str): The path of the file to delete.
        """
        if os.path.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def copy_file(source_path, destination_path):
        """
        Copies a file from source to destination.

        Args:
            source_path (str): The path of the source file.
            destination_path (str): The path where the file should be copied to.
        """
        import shutil

        shutil.copy2(source_path, destination_path)

    @staticmethod
    def move_file(source_path, destination_path):
        """
        Moves a file from source to destination.

        Args:
            source_path (str): The path of the source file.
            destination_path (str): The path where the file should be moved to.
        """
        import shutil

        shutil.move(source_path, destination_path)
