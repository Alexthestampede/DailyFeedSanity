import os
import requests
import xml.etree.ElementTree as ET
import re
import argparse
import html

def download_comic_from_rss(comic_name, rss_url, output_dir):
    """
    Downloads the latest comic from an RSS feed.

    Args:
        comic_name: The name of the comic.
        rss_url: The URL of the RSS feed.
        output_dir: The directory to save the image.
    """
    print(f"Processing {comic_name}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # Find the latest item
        latest_item = root.find('.//item')
        if latest_item is None:
            print(f"Could not find any items in the RSS feed for {comic_name}")
            return

        # Find the image URL within the description or content
        content_encoded = latest_item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
        if content_encoded is not None and content_encoded.text:
            description = html.unescape(content_encoded.text)
        else:
            description = html.unescape(latest_item.find('description').text)
        if description is None:
            print(f"Could not find description in the RSS feed for {comic_name}")
            return

        # This regex will look for an img tag and extract the src
        if comic_name == "Savestate":
            match = re.search(r'<p><a href.*?<img.*?src="(.*?)"', description)
        elif comic_name == "Wondermark":
            match = re.search(r'<div class="widget.*?<img.*?src="(.*?)"', description)
        elif comic_name == "exocomics":
            match = re.search(r'<img class="image-style-main-comic".*?src="(.*?)"', description)
        else:
            match = re.search(r'<img src="(.*?)"', description)

        if match:
            image_url = match.group(1)
            if comic_name == "Savestate":
                image_url = re.sub(r'-\d+x\d+', '', image_url)
            print(f"Found image URL: {image_url}")

            # Handle relative URLs
            if not image_url.startswith('http'):
                base_url = "/" .join(rss_url.split('/')[:3])
                image_url = base_url + image_url

            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()

            filename = os.path.join(output_dir, f"{comic_name}.jpg")

            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"Saved comic to {filename}")
        else:
            print(f"Could not find comic image in the RSS feed for {comic_name}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {rss_url}: {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML for {comic_name}: {e}")

def download_penny_arcade(rss_url, output_dir):
    """
    Downloads the latest Penny Arcade comic.

    Args:
        rss_url: The URL of the RSS feed.
        output_dir: The directory to save the image.
    """
    print("Processing Penny Arcade")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        # Find the latest comic item
        latest_comic_item = None
        for item in root.findall('.//item'):
            if '/comic/' in item.find('link').text:
                latest_comic_item = item
                break

        if latest_comic_item is None:
            print("Could not find any comic items in the RSS feed for Penny Arcade")
            return

        comic_page_url = latest_comic_item.find('link').text

        # Fetch the comic page
        page_response = requests.get(comic_page_url, headers=headers)
        page_response.raise_for_status()
        html_content = page_response.text

        # Find the image URL
        match = re.search(r'src="(https://assets.penny-arcade.com/comics/.*?p1.*?)"', html_content)
        if match:
            panel1_url = match.group(1)
            print(f"Found panel 1 URL: {panel1_url}")

            # Download panel 1
            image_response = requests.get(panel1_url, headers=headers)
            image_response.raise_for_status()
            filename = os.path.join(output_dir, "Penny Arcade-p1.jpg")
            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"Saved comic to {filename}")

            # Download other panels
            for i in range(2, 4):
                panel_url = panel1_url.replace("p1", f"p{i}")
                print(f"Found panel {i} URL: {panel_url}")
                image_response = requests.get(panel_url, headers=headers)
                image_response.raise_for_status()
                filename = os.path.join(output_dir, f"Penny Arcade-p{i}.jpg")
                with open(filename, "wb") as f:
                    f.write(image_response.content)
                print(f"Saved comic to {filename}")
        else:
            print("Could not find comic image on the Penny Arcade comic page")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {rss_url}: {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML for Penny Arcade: {e}")

def download_widdershins(rss_url, output_dir):
    """
    Downloads the latest Widdershins comic.

    Args:
        rss_url: The URL of the RSS feed.
        output_dir: The directory to save the image.
    """
    print("Processing Widdershins")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        latest_item = root.find('.//item')
        if latest_item is None:
            print("Could not find any items in the RSS feed for Widdershins")
            return

        description = latest_item.find('description').text
        if description is None:
            print("Could not find description in the RSS feed for Widdershins")
            return

        match = re.search(r'<a href="(.*?)">', description)
        if match:
            comic_page_url = match.group(1)
            print(f"Found comic page URL: {comic_page_url}")

            page_response = requests.get(comic_page_url, headers=headers)
            page_response.raise_for_status()
            html_content = page_response.text

            img_match = re.search(r'<img id="cc-comic".*?src="(.*?)"', html_content)
            if img_match:
                image_url = img_match.group(1)
                print(f"Found image URL: {image_url}")

                if not image_url.startswith('http'):
                    base_url = "/" .join(rss_url.split('/')[:3])
                    image_url = base_url + image_url

                image_response = requests.get(image_url, headers=headers)
                image_response.raise_for_status()

                filename = os.path.join(output_dir, "Widdershins.jpg")

                with open(filename, "wb") as f:
                    f.write(image_response.content)
                print(f"Saved comic to {filename}")
            else:
                print("Could not find comic image on the Widdershins comic page")
        else:
            print("Could not find comic page link in the RSS feed for Widdershins")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {rss_url}: {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML for Widdershins: {e}")

def download_gunnerkrigg(rss_url, output_dir):
    """
    Downloads the latest Gunnerkrigg Court comic.

    Args:
        rss_url: The URL of the RSS feed.
        output_dir: The directory to save the image.
    """
    print("Processing Gunnerkrigg Court")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        latest_item = root.find('.//item')
        if latest_item is None:
            print("Could not find any items in the RSS feed for Gunnerkrigg Court")
            return

        comic_page_url = latest_item.find('link').text
        if comic_page_url is None:
            print("Could not find link in the RSS feed for Gunnerkrigg Court")
            return
        
        print(f"Found comic page URL: {comic_page_url}")

        page_response = requests.get(comic_page_url, headers=headers)
        page_response.raise_for_status()
        html_content = page_response.text

        img_match = re.search(r'<img class="comic_image".*?src="(.*?)"', html_content)
        if img_match:
            image_url = img_match.group(1)
            print(f"Found image URL: {image_url}")

            if not image_url.startswith('http'):
                image_url = "http://www.gunnerkrigg.com" + image_url

            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()

            filename = os.path.join(output_dir, "Gunnerkrigg Court.jpg")

            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"Saved comic to {filename}")
        else:
            print("Could not find comic image on the Gunnerkrigg Court comic page")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {rss_url}: {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML for Gunnerkrigg Court: {e}")

def download_oglaf(output_dir):
    """
    Downloads the latest Oglaf comic.

    Args:
        output_dir: The directory to save the image.
    """
    print("Processing Oglaf")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        
        main_page_url = "https://www.oglaf.com/"
        main_page_response = requests.get(main_page_url, headers=headers)
        main_page_response.raise_for_status()
        main_html = main_page_response.text

        img_match = re.search(r'<img id="strip".*?src="(.*?)"', main_html)
        if img_match:
            image_url = img_match.group(1)
            print(f"Found image URL: {image_url}")

            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()

            filename = os.path.join(output_dir, "Oglaf.jpg")

            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"Saved comic to {filename}")
        else:
            print("Could not find comic image on the Oglaf main page")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Oglaf: {e}")

def download_girlgenius(output_dir):
    """
    Downloads the latest Girl Genius comic.

    Args:
        output_dir: The directory to save the image.
    """
    print("Processing girlgeniusonline")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        
        comic_page_url = "https://www.girlgeniusonline.com/comic.php"
        page_response = requests.get(comic_page_url, headers=headers)
        page_response.raise_for_status()
        html_content = page_response.text

        img_match = re.search(r"<IMG ALT='Comic'.*?SRC='(.*?)'", html_content)
        if img_match:
            image_url = img_match.group(1)
            print(f"Found image URL: {image_url}")

            image_response = requests.get(image_url, headers=headers)
            image_response.raise_for_status()

            filename = os.path.join(output_dir, "girlgeniusonline.jpg")

            with open(filename, "wb") as f:
                f.write(image_response.content)
            print(f"Saved comic to {filename}")
        else:
            print("Could not find comic image on the Girl Genius comic page")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Girl Genius: {e}")

def main():
    parser = argparse.ArgumentParser(description='Download the latest webcomics from RSS feeds.')
    parser.add_argument('output_dir', help='The directory to save the comics.')
    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found at {args.output_dir}")
        return

    rss_feeds = {
        "Questionable Content": "https://www.questionablecontent.net/QCRSS.xml",
        "Penny Arcade": "https://www.penny-arcade.com/feed",
        "Savestate": "http://www.savestatecomic.com/rss/",
        "Wondermark": "http://wondermark.com/feed/",
        "Xkcd": "https://xkcd.com/rss.xml",
        "Widdershins": "https://www.widdershinscomic.com/comic/rss",
        "Gunnerkrigg Court": "https://www.gunnerkrigg.com/rss.xml",
        "Oglaf": "",
        "exocomics": "https://www.exocomics.com/index.xml",
        "girlgeniusonline": ""
    }

    for comic_name, rss_url in rss_feeds.items():
        if comic_name == "Penny Arcade":
            download_penny_arcade(rss_url, args.output_dir)
        elif comic_name == "Widdershins":
            download_widdershins(rss_url, args.output_dir)
        elif comic_name == "Gunnerkrigg Court":
            download_gunnerkrigg(rss_url, args.output_dir)
        elif comic_name == "Oglaf":
            download_oglaf(args.output_dir)
        elif comic_name == "girlgeniusonline":
            download_girlgenius(args.output_dir)
        else:
            download_comic_from_rss(comic_name, rss_url, args.output_dir)

if __name__ == "__main__":
    main()
