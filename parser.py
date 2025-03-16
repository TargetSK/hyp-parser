from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import datetime
import time
import json 
import re
from unidecode import unidecode

class Parser():
    def __init__(self, url: str) -> None:
        self.url:str = url
        self.old_url:str = "hypermarkte"
        self.shops: list = []
        self.shop_names_parsed: list = []
        self.shop_names_unparsed: list= []
        self.flyer_elements: list
        self.output: list = []

        self.driver:webdriver = webdriver.Chrome()
        
        self.flyer_grid: WebElement       
        self.flyer_grid: WebElement
        self.agree_button: WebElement
        self.list_of_shops: WebElement

    #click agree on popup
    def agree_popup(self) -> None:        
        self.agree_button = self.driver.find_element(By.ID,"didomi-notice-agree-button")
        self.agree_button.click()

    #go to different site
    def change_url(self, new_url:str) -> None:
        self.url = self.url.replace(self.old_url,new_url)
        self.old_url = new_url
        self.driver.get(self.url)

    #returns list of <a> tags with all the shops
    def get_shops(self):
        self.list_of_shops = self.driver.find_element(By.ID,'left-category-shops')
        return self.list_of_shops.find_elements(By.TAG_NAME, "a")

    #changes shop names for usage (lowercase, no ä, ö and such, ...)
    def parse_shop_names(self,shop_name:str) -> str:
        shop_name = unidecode(shop_name)
        shop_name = shop_name.lower()
        shop_name = re.sub(r'\s+', '-', shop_name)
        shop_name = re.sub(r'[^a-z-]', '', shop_name)
        shop_name = re.sub(r'-+', '-', shop_name)
        shop_name = shop_name.strip('-')
        return shop_name
    
    #scroll to the bottom of the page so that all elements load
    def scroll_down(self) -> None:
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    #set flyer_elements to list of flyer webelements
    def get_flyers(self) -> None:
        self.flyer_grid = self.driver.find_element(By.XPATH, "//div[contains(@class, 'letaky-grid')]")
        self.flyer_elements = self.flyer_grid.find_elements(By.XPATH, ".//div[contains(@class, 'grid-item box blue  ')]")


    #return parsed dates (dd.mm.yyyy -> YYYY-mm-dd)
    def parse_date_range(self,flyer) -> tuple[str, str]:
        text = flyer.find_element(By.XPATH,".//small[contains(@class, 'visible-sm')]").text
        text = text.replace(".", "-")

        #fiew are like "from Monday 13. 3." for example
        if "von" in text:
            end_date = "0"
            text = text.split(" ")
            start_date = text[-1].split("-")
            start_date = "-".join(start_date[::-1])

        else:
            start_date = text[0:5]
            end_date = text[9:]

            end_date = end_date.split("-")
            start_date = start_date.split("-")
            start_date.append(end_date[-1])

            end_date = "-".join(end_date[::-1])
            start_date = "-".join(start_date[::-1])

        return [start_date,end_date]
    
    #add to output variable
    def add_to_output(self) -> None:
        self.output.append({
            "title":self.title,
            "thumbnail":self.thumbnail,
            "shop_name":self.shop_name,
            "valid_from":self.valid_from,
            "valid_to":self.valid_to,
            "parsed_time":self.parsed_time
        })

    # remove accents from words
    def normalize_title(self,title:str) -> str:
        return unidecode(title)

    #validate if flyer is current, if yes call add_to_output
    def validate_dates(self) -> None:
        today_datetime:datetime.datetime = datetime.datetime.today().strftime('%Y-%m-%d')
        today_datetime:datetime.datetime = datetime.datetime.strptime(today_datetime,'%Y-%m-%d')
        valid_from_daytime:datetime.datetime = datetime.datetime.strptime(self.valid_from, "%Y-%m-%d")

        if self.valid_to == "0": pass
        else: valid_to_daytime = datetime.datetime.strptime(self.valid_to, "%Y-%m-%d") 

        if valid_from_daytime <= today_datetime:
            if self.valid_to == "0":
                self.add_to_output()
            elif valid_to_daytime >= today_datetime:
                self.add_to_output()

    #get the main info from the flyer webelement 
    def parse_flyers(self,shop_name_parsed:str) -> None:
        for flyer in self.flyer_elements:
            self.title: str = self.normalize_title(flyer.find_element(By.TAG_NAME,"strong").text)

            self.thumbnail: str = flyer.find_element(By.XPATH, ".//img").get_attribute("src")

            self.shop_name: str = unidecode(self.shop_names_unparsed[self.shop_names_parsed.index(shop_name_parsed)]) #if parsed is for example aldi then it picks the unparsed version (Aldi)

            self.valid_from: str = self.parse_date_range(flyer)[0]

            self.valid_to: str = self.parse_date_range(flyer)[1]

            self.parsed_time: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.validate_dates()
            
    #create .json file with all the data
    def dump_to_json(self) -> None:
        with open("output.json", "w") as file:
            json.dump(self.output,file,indent=4)

    #main method of the parser
    def parse(self) -> str:
        self.driver.get(self.url)
        self.agree_popup()
        self.shops: list = self.get_shops()

        for shop in self.shops:
            self.shop_names_unparsed.append(shop.text)
            self.shop_names_parsed.append(self.parse_shop_names(shop.text))
        
        for shop_name_parsed in self.shop_names_parsed:
            self.change_url(shop_name_parsed)
            self.scroll_down()
            self.get_flyers()
            self.parse_flyers(shop_name_parsed)
        
        self.dump_to_json()


def main() -> None:
    parser = Parser("https://www.prospektmaschine.de/hypermarkte/")
    parser.parse()

if __name__ == "__main__":
    main()