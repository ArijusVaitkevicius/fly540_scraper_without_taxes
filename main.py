import os
import re
from datetime import date, timedelta, datetime, timezone
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from multiprocessing import Pool, cpu_count
import pandas as pd
import logging as logs

# Chrome driver and chrome settings.
CHROME_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe'  # Specify the path to chrome.exe.
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("start-maximized")
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.binary_location = CHROME_PATH

# If you're using a proxy server comment these two lines
s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s, options=chrome_options)

# If you're using a proxy server uncomment these two lines
# DRIVER_PATH = '/path/to/chromedriver'
# driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=chrome_options)

driver.implicitly_wait(10)


def log(level, message):
    """
    This function configures logging settings.

    :param str level: log level
    :param str message: log message
    :return: None
    """
    logs.basicConfig(level=logs.INFO, filename='fly540.log', filemode="a",
                     format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y %m %d %H:%M:%S', force=True)
    if level == 'INFO':
        logs.info(f'{message}')
    if level == 'WARNING':
        logs.warning(f'{message}')
    if level == 'ERROR':
        logs.error(f'{message}')


def flights_scraper(dep_iata, arr_iata, cur, dep_date, ret_date):
    """
    This function generates URL by giving arguments.
    Gets page html source code and counts all possible flight combinations and returns required data from page.

    :param str dep_iata: Departure flight IATA airport code
    :param str arr_iata: Arrival flight IATA airport code
    :param str cur: Currency
    :param datetime.date dep_date: Departing date
    :param datetime.date ret_date: Returning date
    :return: list of url and flights indexes
    """

    # List to return.
    data = []

    # Generates URL by variables.
    url = f"https://www.fly540.com/flights/nairobi-to-mombasa?isoneway=0&depairportcode={dep_iata}" \
          f"&arrvairportcode={arr_iata}&date_from={dep_date.strftime('%a')}%2C+{str(int(dep_date.strftime('%d')))}" \
          f"+{dep_date.strftime('%b')}+{dep_date.strftime('%Y')}&date_to={ret_date.strftime('%a')}%2C+" \
          f"{str(int(ret_date.strftime('%d')))}+{ret_date.strftime('%b')}+{ret_date.strftime('%Y')}" \
          f"&adult_no=1&children_no=0&infant_no=0&currency={cur}&searchFlight="

    # Gets to url and gives HTML to BeautifulSoup parser.
    driver.get(url)
    sleep(2)
    source = driver.find_element(By.XPATH, "//section").get_attribute('outerHTML')
    soup = BeautifulSoup(source, 'html.parser')

    # Gets selected date from page and extracts year.
    dates = soup.find('div', class_='fly5-query').find('div', class_='col-md-4 cl-2').find_all('div', class_='col-5')
    depart_year = re.search(r'\d{4}', dates[0].text)[0]
    return_year = re.search(r'\d{4}', dates[1].text)[0]

    # Counts depart and return flights options.
    all_outbounds = soup.find('div', class_='fly5-flights fly5-depart th').find('div', class_='fly5-results').find_all(
        'div', class_='fly5-result')
    all_inbounds = soup.find('div', class_='fly5-flights fly5-return th').find('div', class_='fly5-results').find_all(
        'div', class_='fly5-result')

    # These loops combine all round trip flights.
    for out_index in range(len(all_outbounds)):
        for in_index in range(len(all_inbounds)):
            outbound_card = all_outbounds[out_index]
            outbound_departs_column = outbound_card.find('td', {'data-title': 'Departs'})
            outbound_arrives_column = outbound_card.find('td', {'data-title': 'Arrives'})

            # Outbound details (outbound departure and arrival airports codes, price, dates and times).
            out_from_lst = outbound_departs_column.select('.flfrom')
            out_from = re.search(r'[A-Z]{3}', out_from_lst[0].text)[0]
            out_to_lst = outbound_arrives_column.select('.flfrom')
            out_to = re.search(r'[A-Z]{3}', out_to_lst[0].text)[0]
            out_dep_date_lst = outbound_departs_column.select('.fldate')
            out_dep_date = out_dep_date_lst[0].text.strip()
            out_dep_time_lst = outbound_departs_column.select('.fltime.ftop')
            out_dep_time = out_dep_time_lst[0].text.strip()
            out_arr_date_lst = outbound_arrives_column.select('.fldate')
            out_arr_date = out_arr_date_lst[0].text.strip()
            out_arr_time_lst = outbound_arrives_column.select('.fltime.ftop')
            out_arr_time = out_arr_time_lst[0].text.strip()
            out_price_card = outbound_card.find('td', {"id": "fdflight"})
            out_price_lst = out_price_card.select('.flprice')
            out_price = out_price_lst[0].text.strip()

            inbound_card = all_inbounds[in_index]
            inbound_departs_column = inbound_card.find('td', {'data-title': 'Departs'})
            inbound_arrives_column = inbound_card.find('td', {'data-title': 'Arrives'})

            # Inbound details (inbound departure and arrival airports codes, price, dates and times).
            in_from_lst = inbound_departs_column.select('.flfrom')
            in_from = re.search(r'[A-Z]{3}', in_from_lst[0].text)[0]
            in_to_lst = inbound_arrives_column.select('.flfrom')
            in_to = re.search(r'[A-Z]{3}', in_to_lst[0].text)[0]
            in_dep_date_lst = inbound_departs_column.select('.fldate')
            in_dep_date = in_dep_date_lst[0].text.strip()
            in_dep_time_lst = inbound_departs_column.select('.fltime.ftop')
            in_dep_time = in_dep_time_lst[0].text.strip()
            in_arr_date_lst = inbound_arrives_column.select('.fldate')
            in_arr_date = in_arr_date_lst[0].text.strip()
            in_arr_time_lst = inbound_arrives_column.select('.fltime.ftop')
            in_arr_time = in_arr_time_lst[0].text.strip()
            in_price_card = inbound_card.find('td', {"id": "fdflight"})
            in_price_lst = in_price_card.select('.flprice')
            in_price = in_price_lst[0].text.strip()

            # Gets total price.
            total_price = f"{float(out_price) + float(in_price):,{'.2f'}}"

            def time_formatter(part_of_date, time, year):
                """
                This inner function formats and returns time as required.

                :param str part_of_date: Scraped date without year and time
                :param str time: Scraped time
                :param str year: Scraped year
                :return: Formatted full date as in example
                """
                full_date = f'{part_of_date} {time} {year}'  # Date is merged.
                date_datetime = datetime.strptime(full_date, "%a %d, %b %I:%M%p %Y").replace(
                    tzinfo=timezone.utc)  # String converted to date format and changed time zone.
                date_str = date_datetime.strftime(
                    "%a %b %d %I:%M:%S GMT %Y")  # Date converted back to string and formatted.

                return date_str

            # Calls time_formatter function and add formatted dates to variables.
            outbound_departure_time = time_formatter(out_dep_date, out_dep_time, depart_year)
            outbound_arrival_time = time_formatter(out_arr_date, out_arr_time, depart_year)
            inbound_departure_time = time_formatter(in_dep_date, in_dep_time, return_year)
            inbound_arrival_time = time_formatter(in_arr_date, in_arr_time, return_year)

            # Appends collected data to data list outside this loop.
            data.append([out_from, out_to, outbound_departure_time, outbound_arrival_time, in_from, in_to,
                         inbound_departure_time, inbound_arrival_time, total_price])

    driver.quit()

    return data


def main():
    """
    This function is main and execute when the program is being run.

    Requirements:
    Collect required data from www.fly540.com for ALL round trip flight combinations from NBO (Nairobi) to MBA (Mombasa)
    departing 10 and 20 days from the current date and returning 7 days after the departure date.

    Required data:
    departure airport, arrival airport, departure time, arrival time, cheapest fare price, taxes.
    """

    # Defines variables according to requirements.
    depart_date_1 = date.today() + timedelta(days=10)
    return_date_1 = depart_date_1 + timedelta(days=7)
    depart_date_2 = date.today() + timedelta(days=20)
    return_date_2 = depart_date_2 + timedelta(days=7)

    departure_iata = 'NBO'
    arrival_iata = 'MBA'
    currency = 'USD'
    dates_list = [[depart_date_1, return_date_1], [depart_date_2, return_date_2]]

    # This part calls flights_scraper function twice with different arguments and executes it in parallel.
    flights_scraper_return = []

    try:
        # Sets max 'workers' number depending on the amount of arguments and CPU capability.
        workers = len(dates_list) if len(dates_list) < cpu_count() - 1 else cpu_count() - 1
        pool = Pool(workers)

        # This loop calls function twice and appends returned data to flights_scraper_return list.
        for dates in dates_list:
            flights_scraper_return.append(
                pool.apply_async(flights_scraper, args=(departure_iata, arrival_iata, currency, dates[0], dates[1],))
            )
        pool.close()
        pool.join()

        log('INFO', 'Page was successfully scraped.')
    except:
        log('Error', 'Failed to scrape page.')

    data = []

    for r in flights_scraper_return:  # Gets data from returned objects.
        data.extend(r.get())

    # Saves collected data to result.csv.
    data_frame = pd.DataFrame(data, columns=['outbound_departure_airport',
                                             'outbound_arrival_airport',
                                             'outbound_departure_time',
                                             'outbound_arrival_time',
                                             'inbound_departure_airport',
                                             'inbound_arrival_airport',
                                             'inbound_departure_time',
                                             'inbound_arrival_time',
                                             'total_price'])

    file_exists = os.path.isfile('result.csv')  # Checks or such file exist. If not, set header=True.
    header = False
    if not file_exists:
        header = True

    try:
        # noinspection PyTypeChecker
        data_frame.to_csv('result.csv', mode='a', sep=';', index=False, header=header)
        log('INFO', f'Data successfully wrote to result.csv')
    except:
        log('Error', f'Failed to write data to csv.')


if __name__ == "__main__":
    main()
