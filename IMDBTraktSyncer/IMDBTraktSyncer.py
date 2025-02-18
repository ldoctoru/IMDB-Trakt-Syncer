import os
import json
import requests
import time
import sys
import argparse
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import SessionNotCreatedException
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from IMDBTraktSyncer import arguments

class PageLoadException(Exception):
    pass

def main():
    parser = argparse.ArgumentParser(description="IMDBTraktSyncer CLI")
    parser.add_argument("--clear-user-data", action="store_true", help="Clears user entered credentials.")
    parser.add_argument("--clear-cache", action="store_true", help="Clears cached browsers, drivers and error logs.")
    parser.add_argument("--uninstall", action="store_true", help="Clears cached browsers, drivers and error logs before uninstalling.")
    parser.add_argument("--clean-uninstall", action="store_true", help="Clears all cached data, inluding user credentials, cached browsers and drivers before uninstalling.")
    parser.add_argument("--directory", action="store_true", help="Prints the package install directory.")
    
    args = parser.parse_args()
    
    main_directory = os.path.dirname(os.path.realpath(__file__))

    if args.clear_user_data:
        arguments.clear_user_data(main_directory)
    
    if args.clear_cache:
        arguments.clear_cache(main_directory)
    
    if args.uninstall:
        arguments.uninstall(main_directory)
    
    if args.clean_uninstall:
        arguments.clean_uninstall(main_directory)
    
    if args.directory:
        arguments.print_directory(main_directory)
    
    # If no arguments are passed, run the main package logic
    if not any([args.clear_user_data, args.clear_cache, args.uninstall, args.clean_uninstall, args.directory]):
        
        # Run main package
        print("Starting IMDBTraktSyncer....")
        from IMDBTraktSyncer import checkVersion as CV
        from IMDBTraktSyncer import verifyCredentials as VC
        from IMDBTraktSyncer import checkChrome as CC
        from IMDBTraktSyncer import traktData
        from IMDBTraktSyncer import imdbData
        from IMDBTraktSyncer import errorHandling as EH
        from IMDBTraktSyncer import errorLogger as EL
        
        # Check if package is up to date
        CV.checkVersion()
        
        try:
            # Print credentials directory
            VC.print_directory(main_directory)
            
            # Get credentials
            _, _, _, _, imdb_username, imdb_password = VC.prompt_get_credentials()
            sync_watchlist_value = VC.prompt_sync_watchlist()
            sync_ratings_value = VC.prompt_sync_ratings()
            remove_watched_from_watchlists_value = VC.prompt_remove_watched_from_watchlists()
            sync_reviews_value = VC.prompt_sync_reviews()
            
            # Check if Chrome portable browser is downloaded and up to date
            CC.checkChrome()

            # Set up directory for downloads
            directory = os.path.dirname(os.path.realpath(__file__))

            # Start WebDriver
            print('Starting WebDriver...')
            
            chrome_binary_path  = CC.get_chrome_binary_path(directory)
            
            # Initialize Chrome options
            options = Options()
            options.binary_location = chrome_binary_path
            options.add_argument("--headless=new")
            options.add_argument("--clear-cache")
            options.add_argument("--clear-metadata")
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
            options.add_experimental_option("prefs", {
                "download.default_directory": directory,
                "download.directory_upgrade": True,
                "download.prompt_for_download": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            })
            options.add_argument('--start-maximized')
            options.add_argument("--disable-autofill-for-password-fields")
            options.add_argument('--disable-notifications')
            options.add_argument("--disable-third-party-cookies")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-extensions")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument('--log-level=3')
                    
            service = Service()

            try:
                # Initialize WebDriver with the given options and service
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(60)

            except Exception as e:
                error_message = (f"Error initializing WebDriver: {str(e)}")
                print(f"{error_message}")
                EL.logger.error(error_message)
                raise SystemExit

            # Example: Wait for an element and interact with it
            wait = WebDriverWait(driver, 10)
            
            # Load sign in page
            success, status_code, url = EH.get_page_with_retries('https://www.imdb.com/registration/signin', driver, wait)
            if not success:
                # Page failed to load, raise an exception
                raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")

            # wait for sign in link to appear and then click it
            sign_in_link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.list-group-item > .auth-provider-text')))
            if 'IMDb' in sign_in_link.text:
                sign_in_link.click()

            # wait for email input field and password input field to appear, then enter credentials and submit
            email_input = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='email']")))[0]
            password_input = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='password']")))[0]
            email_input.send_keys(imdb_username)
            password_input.send_keys(imdb_password)
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
            submit_button.click()

            time.sleep(2)

            # go to IMDB homepage
            success, status_code, url = EH.get_page_with_retries('https://www.imdb.com/', driver, wait)
            if not success:
                # Page failed to load, raise an exception
                raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")

            time.sleep(2)

            # Check if signed in
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".nav__userMenu.navbar__user")))
            if element.find_elements(By.CSS_SELECTOR, ".imdb-header__account-toggle--logged-in"):
                print("Successfully signed in to IMDB")
            else:
                print("\nError: Not signed in to IMDB")
                print("\nPossible Causes and Solutions:")
                print("- IMDB captcha check triggered or incorrect IMDB login.")
                
                print("\n1. IMDB Captcha Check:")
                print("   If your login is correct, the issue is likely due to an IMDB captcha check.")
                print("   To resolve this, follow these steps:")
                print("   - Log in to IMDB on your browser (preferably Chrome) and on the same computer.")
                print("   - If already logged in, log out and log back in.")
                print("   - Repeat this process until a captcha check is triggered.")
                print("   - Complete the captcha and finish logging in.")
                print("   - After successfully logging in, run the script again.")
                print("   - You may need to repeat these steps until the captcha check is no longer triggered.")
                
                print("\n2. Incorrect IMDB Login:")
                print("   If your IMDB login is incorrect, update your login credentials:")
                print("   - Edit the 'credentials.txt' file in your settings directory with the correct login information.")
                print("   - Alternatively, delete the 'credentials.txt' file and run the script again.")
                
                print("\nFor more details, see the following GitHub link:")
                print("https://github.com/RileyXX/IMDB-Trakt-Syncer/issues/2")
                
                print("\nStopping script...")
                
                EL.logger.error("Error: Not signed in to IMDB")
                driver.close()
                driver.quit()
                service.stop()
                raise SystemExit
            
            # Check IMDB Language for compatability
            # Get Current Language
            language_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id*='nav-language-selector-contents'] .selected"))).get_attribute("aria-label")
            original_language = language_element
            if (original_language != "English (United States)"):
                print("Temporarily changing IMDB Language to English for compatability")
                # Open Language Dropdown
                language_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for*='nav-language-selector']")))
                driver.execute_script("arguments[0].click();", language_dropdown)
                # Change Language to English
                english_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span[id*='nav-language-selector-contents'] li[aria-label*='English (United States)']")))
                driver.execute_script("arguments[0].click();", english_element)        
            
            trakt_watchlist, trakt_ratings, trakt_reviews, watched_content = traktData.getTraktData()
            imdb_watchlist, imdb_ratings, imdb_reviews, errors_found_getting_imdb_reviews = imdbData.getImdbData(imdb_username, imdb_password, driver, directory, wait)
            
            # Get trakt and imdb data and filter out items with missing imdb id
            trakt_ratings = [rating for rating in trakt_ratings if rating.get('IMDB_ID') is not None]
            imdb_ratings = [rating for rating in imdb_ratings if rating.get('IMDB_ID') is not None]
            trakt_reviews = [review for review in trakt_reviews if review.get('IMDB_ID') is not None]
            imdb_reviews = [review for review in imdb_reviews if review.get('IMDB_ID') is not None]
            trakt_watchlist = [item for item in trakt_watchlist if item.get('IMDB_ID') is not None]
            imdb_watchlist = [item for item in imdb_watchlist if item.get('IMDB_ID') is not None]
            # Filter out items already set
            imdb_ratings_to_set = [rating for rating in trakt_ratings if rating['IMDB_ID'] not in [imdb_rating['IMDB_ID'] for imdb_rating in imdb_ratings]]
            trakt_ratings_to_set = [rating for rating in imdb_ratings if rating['IMDB_ID'] not in [trakt_rating['IMDB_ID'] for trakt_rating in trakt_ratings]]
            imdb_reviews_to_set = [review for review in trakt_reviews if review['IMDB_ID'] not in [imdb_review['IMDB_ID'] for imdb_review in imdb_reviews]]
            trakt_reviews_to_set = [review for review in imdb_reviews if review['IMDB_ID'] not in [trakt_review['IMDB_ID'] for trakt_review in trakt_reviews]]
            imdb_watchlist_to_set = [item for item in trakt_watchlist if item['IMDB_ID'] not in [imdb_item['IMDB_ID'] for imdb_item in imdb_watchlist]]
            trakt_watchlist_to_set = [item for item in imdb_watchlist if item['IMDB_ID'] not in [trakt_item['IMDB_ID'] for trakt_item in trakt_watchlist]]
            
            # Filter ratings to update
            imdb_ratings_to_update = []
            trakt_ratings_to_update = []

            # Dictionary to store IMDB_IDs and their corresponding ratings for IMDB and Trakt
            imdb_ratings_dict = {rating['IMDB_ID']: rating for rating in imdb_ratings}
            trakt_ratings_dict = {rating['IMDB_ID']: rating for rating in trakt_ratings}

            # Include only items with the same IMDB_ID and different ratings and prefer the most recent rating
            for imdb_id, imdb_rating in imdb_ratings_dict.items():
                if imdb_id in trakt_ratings_dict:
                    trakt_rating = trakt_ratings_dict[imdb_id]
                    if imdb_rating['Rating'] != trakt_rating['Rating']:
                        imdb_date_added = datetime.fromisoformat(imdb_rating['Date_Added'].replace('Z', '')).replace(tzinfo=timezone.utc)
                        trakt_date_added = datetime.fromisoformat(trakt_rating['Date_Added'].replace('Z', '')).replace(tzinfo=timezone.utc)
                        
                        # Check if ratings were added on different days
                        if (imdb_date_added.year, imdb_date_added.month, imdb_date_added.day) != (trakt_date_added.year, trakt_date_added.month, trakt_date_added.day):
                            # If IMDB rating is more recent, add the Trakt rating to the update list, and vice versa
                            if imdb_date_added > trakt_date_added:
                                trakt_ratings_to_update.append(imdb_rating)
                            else:
                                imdb_ratings_to_update.append(trakt_rating)

            # Update ratings_to_set
            imdb_ratings_to_set.extend(imdb_ratings_to_update)
            trakt_ratings_to_set.extend(trakt_ratings_to_update)
            
            # Filter out review items where the comment length is less than 600 characters
            def filter_by_comment_length(lst, min_comment_length=None):
                result = []
                for item in lst:
                    if min_comment_length is None or ('Comment' in item and len(item['Comment']) >= min_comment_length):
                        result.append(item)
                return result
            imdb_reviews_to_set = filter_by_comment_length(imdb_reviews_to_set, 600)
            
            # If remove_watched_from_watchlists_value is true
            if remove_watched_from_watchlists_value:        
                # Get the IDs from watched_content
                watched_content_ids = set(item['IMDB_ID'] for item in watched_content if item['IMDB_ID'])
                        
                # Filter out watched content from trakt_watchlist_to_set
                trakt_watchlist_to_set = [item for item in trakt_watchlist_to_set if item['IMDB_ID'] not in watched_content_ids]
                # Filter out watched content from trakt_watchlist_to_set
                imdb_watchlist_to_set = [item for item in imdb_watchlist_to_set if item['IMDB_ID'] not in watched_content_ids]
                
                # Find items to remove from trakt_watchlist
                trakt_watchlist_items_to_remove = [item for item in trakt_watchlist if item['IMDB_ID'] in watched_content_ids]
                # Find items to remove from imdb_watchlist
                imdb_watchlist_items_to_remove = [item for item in imdb_watchlist if item['IMDB_ID'] in watched_content_ids]
            
            # If sync_watchlist_value is true
            if sync_watchlist_value:
                # Set Trakt Watchlist Items
                if trakt_watchlist_to_set:
                    print('Setting Trakt Watchlist Items')

                    # Count the total number of items
                    num_items = len(trakt_watchlist_to_set)
                    item_count = 0

                    for item in trakt_watchlist_to_set:
                        item_count += 1
                        print(f" - Adding item ({item_count} of {num_items}): {item['Title']} ({item['Year']}) to Trakt Watchlist ({item['IMDB_ID']})")
                        imdb_id = item['IMDB_ID']
                        media_type = item['Type']  # 'movie', 'show', or 'episode'

                        url = f"https://api.trakt.tv/sync/watchlist"

                        data = {
                            "movies": [],
                            "shows": [],
                            "episodes": []
                        }

                        if media_type == 'movie':
                            data['movies'].append({
                                "ids": {
                                    "imdb": imdb_id
                                }
                            })
                        elif media_type == 'show':
                            data['shows'].append({
                                "ids": {
                                    "imdb": imdb_id
                                }
                            })
                        elif media_type == 'episode':
                            data['episodes'].append({
                                "ids": {
                                    "imdb": imdb_id
                                }
                            })
                        else:
                            data = None

                        if data:
                            response = EH.make_trakt_request(url, payload=data)
                            
                            if response is None:
                                error_message = f"Failed to add item ({item_count} of {num_items}): {item['Title']} ({item['Year']}) to Trakt Watchlist ({item['IMDB_ID']})"
                                print(f"   - {error_message}")
                                EL.logger.error(error_message)

                    print('Setting Trakt Watchlist Items Complete')
                else:
                    print('No Trakt Watchlist Items To Set')

                # Set IMDB Watchlist Items
                if imdb_watchlist_to_set:
                    print('Setting IMDB Watchlist Items')
                    
                    # Count the total number of items
                    num_items = len(imdb_watchlist_to_set)
                    item_count = 0
                                    
                    for item in imdb_watchlist_to_set:
                        try:
                            item_count += 1
                            year_str = f' ({item["Year"]})' if item["Year"] is not None else '' # sometimes year is None for episodes from trakt so remove it from the print string
                            print(f" - Adding item ({item_count} of {num_items}): {item['Title']}{year_str} to IMDB Watchlist ({item['IMDB_ID']})")
                            
                            # Load page
                            success, status_code, url = EH.get_page_with_retries(f'https://www.imdb.com/title/{item["IMDB_ID"]}/', driver, wait)
                            if not success:
                                # Page failed to load, raise an exception
                                raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")
                            
                            current_url = driver.current_url
                            
                            # Check if the URL doesn't contain "/reference"
                            if "/reference" not in current_url:
                                # Wait until the loader has disappeared, indicating the watchlist button has loaded
                                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="tm-box-wl-loader"]')))
                                
                                # Scroll the page to bring the element into view
                                watchlist_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"]')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", watchlist_button)
                                
                                # Wait for the element to be clickable
                                watchlist_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"]')))
                                
                                # Check if item is already in watchlist otherwise skip it
                                if 'ipc-icon--done' not in watchlist_button.get_attribute('innerHTML'):
                                    retry_count = 0
                                    while retry_count < 2:
                                        driver.execute_script("arguments[0].click();", watchlist_button)
                                        try:
                                            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"] .ipc-icon--done')))
                                            break  # Break the loop if successful
                                        except TimeoutException:
                                            retry_count += 1

                                    if retry_count == 2:
                                        error_message = f"Failed to add item ({item_count} of {num_items}): {item['Title']}{year_str} to IMDB Watchlist ({item['IMDB_ID']})"
                                        print(f"   - {error_message}")
                                        EL.logger.error(error_message)
                            else:
                                # Handle the case when the URL contains "/reference"
                                
                                # Scroll the page to bring the element into view
                                watchlist_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.titlereference-watch-ribbon > .wl-ribbon')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", watchlist_button)
                                
                                # Check if watchlist_button has class .not-inWL before clicking
                                if 'not-inWL' in watchlist_button.get_attribute('class'):
                                    driver.execute_script("arguments[0].click();", watchlist_button)
                            
                        except (NoSuchElementException, TimeoutException, PageLoadException):
                            error_message = f"Failed to add item ({item_count} of {num_items}): {item['Title']}{year_str} to IMDB Watchlist ({item['IMDB_ID']})"
                            print(f"   - {error_message}")
                            EL.logger.error(error_message, exc_info=True)
                            pass

                    
                    print('Setting IMDB Watchlist Items Complete')
                else:
                    print('No IMDB Watchlist Items To Set')
             
            # If sync_ratings_value is true
            if sync_ratings_value:
                
                #Set Trakt Ratings
                if trakt_ratings_to_set:
                    print('Setting Trakt Ratings')

                    # Set the API endpoints
                    rate_url = "https://api.trakt.tv/sync/ratings"
                    
                    # Count the total number of items
                    num_items = len(trakt_ratings_to_set)
                    item_count = 0
                            
                    # Loop through your data table and rate each item on Trakt
                    for item in trakt_ratings_to_set:
                        item_count += 1
                        if item["Type"] == "show":
                            # This is a TV show
                            data = {
                                "shows": [{
                                    "ids": {
                                        "imdb": item["IMDB_ID"]
                                    },
                                    "rating": item["Rating"]
                                }]
                            }
                            print(f" - Rating TV show ({item_count} of {num_items}): {item['Title']} ({item['Year']}): {item['Rating']}/10 on Trakt ({item['IMDB_ID']})")
                        elif item["Type"] == "movie":
                            # This is a movie
                            data = {
                                "movies": [{
                                    "ids": {
                                        "imdb": item["IMDB_ID"]
                                    },
                                    "rating": item["Rating"]
                                }]
                            }
                            print(f" - Rating movie ({item_count} of {num_items}): {item['Title']} ({item['Year']}): {item['Rating']}/10 on Trakt ({item['IMDB_ID']})")
                        elif item["Type"] == "episode":
                            # This is an episode
                            data = {
                                "episodes": [{
                                    "ids": {
                                        "imdb": item["IMDB_ID"]
                                    },
                                    "rating": item["Rating"]
                                }]
                            }
                            print(f" - Rating episode ({item_count} of {num_items}): {item['Title']} ({item['Year']}): {item['Rating']}/10 on Trakt ({item['IMDB_ID']})")
                        else:
                            data = None
                        
                        if data:
                            # Make the API call to rate the item
                            response = EH.make_trakt_request(rate_url, payload=data)

                            if response is None:
                                error_message = f"Failed rating {item['Type']} ({item_count} of {num_items}): {item['Title']} ({item['Year']}): {item['Rating']}/10 on Trakt ({item['IMDB_ID']})"
                                print(f"   - {error_message}")
                                EL.logger.error(error_message)

                    print('Setting Trakt Ratings Complete')
                else:
                    print('No Trakt Ratings To Set')

                # Set IMDB Ratings
                if imdb_ratings_to_set:
                    print('Setting IMDB Ratings')

                    # loop through each movie and TV show rating and submit rating on IMDB website
                    for i, item in enumerate(imdb_ratings_to_set, 1):

                        year_str = f' ({item["Year"]})' if item["Year"] is not None else '' # sometimes year is None for episodes from trakt so remove it from the print string
                        print(f' - Rating {item["Type"]}: ({i} of {len(imdb_ratings_to_set)}) {item["Title"]}{year_str}: {item["Rating"]}/10 on IMDB ({item["IMDB_ID"]})')
                        
                        try:
                            # Load page
                            success, status_code, url = EH.get_page_with_retries(f'https://www.imdb.com/title/{item["IMDB_ID"]}/', driver, wait)
                            if not success:
                                # Page failed to load, raise an exception
                                raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")
                            
                            current_url = driver.current_url
                            
                            # Check if the URL doesn't contain "/reference"
                            if "/reference" not in current_url:
                                # Wait until the rating bar has loaded
                                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="hero-rating-bar__loading"]')))
                                
                                # Wait until rate button is located and scroll to it
                                button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="hero-rating-bar__user-rating"] button.ipc-btn')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)

                                # click on "Rate" button and select rating option, then submit rating
                                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="hero-rating-bar__user-rating"] button.ipc-btn')))
                                element_rating_bar = button.find_element(By.CSS_SELECTOR, '[data-testid*="hero-rating-bar__user-rating__"]')
                                if element_rating_bar:
                                    driver.execute_script("arguments[0].click();", button)
                                    rating_option_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[aria-label="Rate {item["Rating"]}"]')))
                                    driver.execute_script("arguments[0].click();", rating_option_element)
                                    submit_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ipc-rating-prompt__rate-button')))
                                    submit_element.click()
                                    time.sleep(1)
                            else:
                                # Handle the case when the URL contains "/reference"
                                
                                # Wait until rate button is located and scroll to it
                                button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ipl-rating-interactive__star-container')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", button)

                                # click on "Rate" button and select rating option, then submit rating
                                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.ipl-rating-interactive__star-container')))
                                driver.execute_script("arguments[0].click();", button)
                                
                                # Find the rating option element based on the data-value attribute
                                rating_option_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'.ipl-rating-selector__star-link[data-value="{item["Rating"]}"]')))
                                driver.execute_script("arguments[0].click();", rating_option_element)
                                
                                time.sleep(1)
                                
                        except (NoSuchElementException, TimeoutException, PageLoadException):
                            error_message = f'Failed to rate {item["Type"]}: ({i} of {len(imdb_ratings_to_set)}) {item["Title"]}{year_str}: {item["Rating"]}/10 on IMDB ({item["IMDB_ID"]})'
                            print(f"   - {error_message}")
                            EL.logger.error(error_message, exc_info=True)
                            pass

                    print('Setting IMDB Ratings Complete')
                else:
                    print('No IMDB Ratings To Set')

            # If sync_reviews_value is true
            if sync_reviews_value:
                
                # Check if there was an error getting IMDB reviews
                if not errors_found_getting_imdb_reviews:
                    
                    # Set Trakt Reviews
                    if trakt_reviews_to_set:
                        print('Setting Trakt Reviews')

                        # Count the total number of items
                        num_items = len(trakt_reviews_to_set)
                        item_count = 0

                        for review in trakt_reviews_to_set:
                            item_count += 1
                            print(f" - Submitting comment ({item_count} of {num_items}): {review['Title']} ({review['Year']}) on Trakt ({item['IMDB_ID']})")
                            imdb_id = review['IMDB_ID']
                            comment = review['Comment']
                            media_type = review['Type']  # 'movie', 'show', or 'episode'

                            url = f"https://api.trakt.tv/comments"

                            data = {
                                "comment": comment
                            }

                            if media_type == 'movie':
                                data['movie'] = {
                                    "ids": {
                                        "imdb": imdb_id
                                    }
                                }
                            elif media_type == 'show':
                                data['show'] = {
                                    "ids": {
                                        "imdb": imdb_id
                                    }
                                }
                            elif media_type == 'episode':
                                data['episode'] = {
                                    "ids": {
                                        "imdb": episode_id
                                    }
                                }
                            else:
                                data = None
                            
                            if data:
                                response = EH.make_trakt_request(url, payload=data)
                                
                                if response is None:
                                    error_message = f"Failed to submit comment ({item_count} of {num_items}): {review['Title']} ({review['Year']}) on Trakt ({item['IMDB_ID']})"
                                    print(f"   - {error_message}")
                                    EL.logger.error(error_message)

                        print('Trakt Reviews Set Successfully')
                    else:
                        print('No Trakt Reviews To Set')

                    # Set IMDB Reviews
                    if imdb_reviews_to_set:
                        # Call the check_last_run() function
                        if check_imdb_reviews_last_submitted():
                            print('Setting IMDB Reviews')
                            
                            # Count the total number of items
                            num_items = len(imdb_reviews_to_set)
                            item_count = 0
                            
                            for review in imdb_reviews_to_set:
                                item_count += 1
                                try:
                                    print(f" - Submitting review ({item_count} of {num_items}): {review['Title']} ({review['Year']}) on IMDB ({item['IMDB_ID']})")
                                    
                                    # Load page
                                    success, status_code, url = EH.get_page_with_retries(f'https://contribute.imdb.com/review/{review["IMDB_ID"]}/add?bus=imdb', driver, wait)
                                    if not success:
                                        # Page failed to load, raise an exception
                                        raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")
                                    
                                    review_title_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.klondike-input")))
                                    review_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.klondike-textarea")))
                                    
                                    review_title_input.send_keys("My Review")
                                    review_input.send_keys(review["Comment"])
                                    
                                    no_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.klondike-userreview-spoiler li:nth-child(2)")))
                                    yes_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.klondike-userreview-spoiler li:nth-child(1)")))
                                    
                                    if review["Spoiler"]:
                                        yes_element.click()                        
                                    else:
                                        no_element.click()
                                                            
                                    submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.a-button-input[type='submit']")))

                                    submit_button.click()
                                    
                                    time.sleep(3) # wait for rating to submit
                                except (NoSuchElementException, TimeoutException, PageLoadException):
                                    error_message = f"Failed to submit review ({item_count} of {num_items}): {review['Title']} ({review['Year']}) on IMDB ({item['IMDB_ID']})"
                                    print(f"   - {error_message}")
                                    EL.logger.error(error_message, exc_info=True)
                                    pass
                            
                            print('Setting IMDB Reviews Complete')
                        else:
                            print('IMDB reviews were submitted within the last 10 days. Skipping IMDB review submission.')
                    else:
                        print('No IMDB Reviews To Set')
                else:
                    print('There was an error getting IMDB reviews. See exception. Skipping reviews submissions.')

            # If remove_watched_from_watchlists_value is true
            if remove_watched_from_watchlists_value:
                
                # Remove Watched Items Trakt Watchlist
                if trakt_watchlist_items_to_remove:
                    print('Removing Watched Items From Trakt Watchlist')

                    # Set the API endpoint
                    remove_url = "https://api.trakt.tv/sync/watchlist/remove"

                    # Count the total number of items
                    num_items = len(trakt_watchlist_items_to_remove)
                    item_count = 0

                    # Loop through the items to remove from the watchlist
                    for item in trakt_watchlist_items_to_remove:
                        item_count += 1
                        if item["Type"] == "show":
                            # This is a TV show
                            data = {
                                "shows": [{
                                    "ids": {
                                        "trakt": item["TraktID"]
                                    }
                                }]
                            }
                            print(f" - Removing TV show ({item_count} of {num_items}): {item['Title']} ({item['Year']}) from Trakt Watchlist ({item['IMDB_ID']})")
                        elif item["Type"] == "movie":
                            # This is a movie
                            data = {
                                "movies": [{
                                    "ids": {
                                        "trakt": item["TraktID"]
                                    }
                                }]
                            }
                            print(f" - Removing movie ({item_count} of {num_items}): {item['Title']} ({item['Year']}) from Trakt Watchlist ({item['IMDB_ID']})")
                        elif item["Type"] == "episode":
                            # This is an episode
                            data = {
                                "episodes": [{
                                    "ids": {
                                        "trakt": item["TraktID"]
                                    }
                                }]
                            }
                            print(f" - Removing episode ({item_count} of {num_items}): {item['Title']} ({item['Year']}) from Trakt Watchlist ({item['IMDB_ID']})")
                        else:
                            data = None

                        if data:
                            # Make the API call to remove the item from the watchlist
                            response = EH.make_trakt_request(remove_url, payload=data)

                            if response is None:
                                error_message = f"Failed removing {item['Type']} ({item_count} of {num_items}): {item['Title']} ({item['Year']}) from Trakt Watchlist ({item['IMDB_ID']})"
                                print(f"   - {error_message}")
                                EL.logger.error(error_message)

                    print('Removing Watched Items From Trakt Watchlist Complete')
                else:
                    print('No Watched Items To Remove From Trakt Watchlist')

                # Remove Watched Items IMDB Watchlist
                if imdb_watchlist_items_to_remove:
                    print('Removing Watched Items From IMDB Watchlist')
                    
                    # Count the total number of items
                    num_items = len(imdb_watchlist_items_to_remove)
                    item_count = 0
                                    
                    for item in imdb_watchlist_items_to_remove:
                        try:
                            item_count += 1
                            year_str = f' ({item["Year"]})' if item["Year"] is not None else '' # sometimes year is None for episodes from trakt so remove it from the print string
                            print(f" - Removing item ({item_count} of {num_items}): {item['Title']}{year_str} from IMDB Watchlist ({item['IMDB_ID']})")
                            
                            # Load page
                            success, status_code, url = EH.get_page_with_retries(f'https://www.imdb.com/title/{item["IMDB_ID"]}/', driver, wait)
                            if not success:
                                # Page failed to load, raise an exception
                                raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")
                            
                            current_url = driver.current_url
                            
                            # Check if the URL doesn't contain "/reference"
                            if "/reference" not in current_url:
                                # Wait until the loader has disappeared, indicating the watchlist button has loaded
                                wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-testid="tm-box-wl-loader"]')))
                                
                                # Scroll the page to bring the element into view
                                watchlist_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"]')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", watchlist_button)
                                
                                # Wait for the element to be clickable
                                watchlist_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"]')))
                                
                                # Check if item is not in watchlist otherwise skip it
                                if 'ipc-icon--add' not in watchlist_button.get_attribute('innerHTML'):
                                    retry_count = 0
                                    while retry_count < 2:
                                        driver.execute_script("arguments[0].click();", watchlist_button)
                                        try:
                                            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tm-box-wl-button"] .ipc-icon--add')))
                                            break  # Break the loop if successful
                                        except TimeoutException:
                                            retry_count += 1

                                    if retry_count == 2:
                                        error_message = f"Failed to remove item ({item_count} of {num_items}): {item['Title']}{year_str} from IMDB Watchlist ({item['IMDB_ID']})"
                                        print(f"   - {error_message}")
                                        EL.logger.error(error_message)
                        
                            else:
                                # Handle the case when the URL contains "/reference"
                                
                                # Scroll the page to bring the element into view
                                watchlist_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.titlereference-watch-ribbon > .wl-ribbon')))
                                driver.execute_script("arguments[0].scrollIntoView(true);", watchlist_button)
                                
                                # Check if watchlist_button doesn't have the class .not-inWL before clicking
                                if 'not-inWL' not in watchlist_button.get_attribute('class'):
                                    driver.execute_script("arguments[0].click();", watchlist_button)

                        except (NoSuchElementException, TimeoutException, PageLoadException):
                            error_message = f"Failed to remove item ({item_count} of {num_items}): {item['Title']}{year_str} from IMDB Watchlist ({item['IMDB_ID']})"
                            print(f"   - {error_message}")
                            EL.logger.error(error_message, exc_info=True)
                            pass

                    
                    print('Removing Watched Items From IMDB Watchlist Complete')
                else:
                    print('No Watched Items To Remove From IMDB Watchlist')
            
            if (original_language != "English (United States)"):
                print("Changing IMDB Language Back to Original")
                # go to IMDB homepage
                success, status_code, url = EH.get_page_with_retries('https://www.imdb.com/', driver, wait)
                if not success:
                    # Page failed to load, raise an exception
                    raise PageLoadException(f"Failed to load page. Status code: {status_code}. URL: {url}")
                
                # Change Language Back to Original
                # Open Language Dropdown
                language_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for*='nav-language-selector']")))
                driver.execute_script("arguments[0].click();", language_dropdown)
                # Change Language to Original
                original_language_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"span[id*='nav-language-selector-contents'] li[aria-label*='{original_language}']")))
                driver.execute_script("arguments[0].click();", original_language_element)
            
            #Close web driver
            print("Closing webdriver...")
            driver.close()
            driver.quit()
            service.stop()
            print("IMDBTraktSyncer Complete")
        
        except Exception as e:
            error_message = "An error occurred while running the script."
            EH.report_error(error_message)
            EL.logger.error(error_message, exc_info=True)
            
            # Close the driver and stop the service if they were initialized
            if 'driver' in locals() and driver is not None:
                driver.close()
                driver.quit()
            if 'service' in locals() and service is not None:
                service.stop()

if __name__ == '__main__':
    main()