from english_main import Ui_MainWindow
from PyQt5 import QtWidgets
import sys
import csv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os
import threading, queue


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.folder_path = None
        self.detail = None
        self.input_list = []
        self.ui.finish.setHidden(True)
        self.ui.error.setHidden(True)
        self.count = 0

        self.ui.choose_file.clicked.connect(self.pick_folder)
        self.ui.start.clicked.connect(self.new_thread)
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

    def pick_folder(self):
        try:
            directory = QtWidgets.QFileDialog.getOpenFileName(self, "Select CSV", "C:/", "CSV data files (*.csv)")
            self.ui.file_text.setText(directory[0])
            self.folder_path = directory[0]
        except:
            print("close")

    def pos_change(self, input):
        pos_list = {}
        pos_list['verb'] = 'v.'
        pos_list['noun'] = 'n.'
        pos_list['adjective'] = 'adj.'
        pos_list['preposition'] = 'prep.'
        pos_list['adverb'] = 'adv.'
        pos_list['conjunction'] = 'conj.'

        for key, value in pos_list.items():
            if key == input:
                input = value
                break

        return input

    def cambridge(self, driver, input):
        try:
            driver.get('https://dictionary.cambridge.org/zht/')
            WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable((By.XPATH, '//input['
                                                                                                   '@id="searchword"]')))
            search = driver.find_element_by_xpath('//input[@id="searchword"]')
            search.send_keys(input)
            search.send_keys(Keys.RETURN)
            output = {}
            english_ex = []

            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.pr .entry-body__el')))
            entry = driver.find_elements_by_css_selector('.pr .entry-body__el')

            for en in entry:
                item = en.find_elements_by_css_selector('.pr .dsense')
                pos = en.find_element_by_css_selector("span.pos.dpos").text
                pos = self.pos_change(pos)

                for i in item:
                    try:
                        grid = i.find_elements_by_css_selector('div.sense-body.dsense_b > div.def-block.ddef_block')
                        explains = {"ph": {"yes": "False"}}
                        for g in grid:
                            chi = g.find_element_by_css_selector('div.def-body.ddef_b')
                            eng = g.find_element_by_css_selector('div.def.ddef_d.db').text
                            english_ex.append(eng)
                            explain = chi.find_element_by_css_selector('span.trans.dtrans.dtrans-se').text
                            examples = chi.find_elements_by_css_selector('div.examp.dexamp')
                            sentense = []
                            for e in examples:
                                eng_sen = e.find_elements_by_css_selector('span.eg.deg')
                                chi_sen = e.find_elements_by_css_selector('span.dtrans.hdb')
                                for w in range(len(eng_sen)):
                                    sentense.append(eng_sen[w].text)
                                    sentense.append(chi_sen[w].text)
                            explains[explain] = sentense
                        if pos in output:
                            output[pos].append(explains)
                        else:
                            output[pos] = [explains]
                    except:
                        print("no")

                    try:
                        grid = i.find_elements_by_css_selector('div.pr.phrase-block.dphrase-block')
                        explains = {"ph": {"yes": "True", "mean": {}}}
                        for g in grid:
                            phrase = g.find_element_by_css_selector('span.phrase-title.dphrase-title').text
                            mean = g.find_elements_by_css_selector('div.def-block.ddef_block')
                            ph_explains = {}
                            explains["ph"]["mean"][phrase] = []
                            for m in mean:
                                chi = m.find_element_by_css_selector('div.def-body.ddef_b')
                                eng = m.find_element_by_css_selector('div.def.ddef_d.db').text
                                english_ex.append(eng)
                                explain = chi.find_element_by_css_selector('span.trans.dtrans.dtrans-se').text
                                examples = chi.find_elements_by_css_selector('div.examp.dexamp')
                                sentense = []
                                for e in examples:
                                    eng_sen = e.find_elements_by_css_selector('span.eg.deg')
                                    chi_sen = e.find_elements_by_css_selector('span.dtrans.hdb')
                                    for w in range(len(eng_sen)):
                                        sentense.append(eng_sen[w].text)
                                        sentense.append(chi_sen[w].text)
                                ph_explains[explain] = sentense
                            explains["ph"]["mean"][phrase].append(ph_explains)
                        if pos in output:
                            output[pos].append(explains)
                        else:
                            output[pos] = [explains]
                    except:
                        print("no")


        except Exception as e:
            output = None
            english_ex = None
        finally:
            return [output, english_ex]

    def merriam(self, driver, input):
        try:
            driver.get('https://www.merriam-webster.com')
            WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//input[@aria-label="Search"]')))
            search = driver.find_element_by_xpath('//input[@aria-label="Search"]')
            search.send_keys(input)
            search.send_keys(Keys.RETURN)

            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '.entry-attr>div>.prs>.play-pron')))
            item = driver.find_elements_by_css_selector(".entry-attr>div>.prs>.play-pron")[0]
            dir = item.get_attribute("data-dir")
            file = item.get_attribute("data-file")
            audio_url = "http://media.merriam-webster.com/audio/prons/en/us/mp3/" + dir + "/" + file + ".mp3"
        except Exception as e:
            audio_url = None

        return audio_url

    def change_text(self, output, eng):
        mean_text = ""
        text = ""
        count = 0

        if output is not None:
            for pos in output:
                for explains in output[pos]:
                    if explains["ph"]["yes"] == "False":
                        for explain in explains:
                            if explain != "ph":
                                text += pos + " " + explain + "<br>"
                                mean_text += pos + " " + explain + "<br>"
                                text += eng[count] + "<br>"
                                count += 1
                                for sentense in explains[explain]:
                                    text += sentense + "<br>"
                                text += "---" + "<br>"
                    else:
                        for word in explains["ph"]["mean"]:
                            text += "@" + word + "<br>"
                            for mean_arr in explains["ph"]["mean"][word]:
                                for mean in mean_arr:
                                    text += pos + " " + mean + "<br>"
                                    mean_text += pos + " " + mean + "<br>"
                                    text += eng[count] + "<br>"
                                    count += 1
                                    for sentense in mean_arr[mean]:
                                        text += sentense + "<br>"
                                    text += "---" + "<br>"

            text = text.replace('"', '\\"')

        return [text, mean_text]

    def start_c(self, word, queue):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument('blink-settings=imagesEnabled=false')
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"
        prefs = {'profile.default_content_setting_values': {'images': 2}}
        chrome_options.add_experimental_option('prefs', prefs)
        PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) + '/chromedriver.exe'

        driver2 = webdriver.Chrome(desired_capabilities=caps, executable_path=PATH, options=chrome_options)

        tem_count = 0
        for w in word:
            output = self.cambridge(driver2, w)
            [text, mean_text] = self.change_text(output[0], output[1])

            self.input_list[tem_count][3] = mean_text
            self.input_list[tem_count][4] = text
            tem_count += 1
            self.count += 1
            self.ui.cur_num.setText(str(self.count / 2))

        queue.put("finishB")
        driver2.quit()

    def start_m(self, word, queue):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument('blink-settings=imagesEnabled=false')
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"
        prefs = {'profile.default_content_setting_values': {'images': 2}}
        chrome_options.add_experimental_option('prefs', prefs)
        PATH = os.path.join(os.path.dirname(os.path.abspath(__file__))) + '/chromedriver.exe'
        driver1 = webdriver.Chrome(desired_capabilities=caps,executable_path=PATH, options=chrome_options)

        tem_count = 0
        for w in word:
            output = self.merriam(driver1, w)
            self.input_list[tem_count][2] = output
            tem_count += 1
            self.count += 1
            self.ui.cur_num.setText(str(self.count / 2))

        queue.put("finishA")
        driver1.quit()

    def new_thread(self):
        t = threading.Thread(target=self.find)
        t.start()

    def find(self):
        self.ui.finish.setHidden(True)
        self.ui.error.setHidden(True)
        self.ui.choose_file.setDisabled(True)
        self.ui.start.setDisabled(True)
        self.ui.cur_num.setText(str(0))
        self.ui.all_num.setText(str(0))

        word_list = []

        try:
            with open(self.folder_path, newline='', encoding='utf-8-sig') as csvfile:
                rows = csv.reader(csvfile)
                all_num = sum(1 for row in rows)
                self.ui.all_num.setText(str(all_num))
                csvfile.seek(0)
                count_rows = csv.reader(csvfile)
                for row in count_rows:
                    self.input_list.append([row[0], "", "", "", ""])
                    word_list.append(row[0])

            q = queue.Queue()
            threads = [None] * 2
            threads[0] = threading.Thread(target=self.start_c, args=(word_list, q))
            threads[1] = threading.Thread(target=self.start_m, args=(word_list, q))
            threads[0].start()
            threads[1].start()

            q.join()
            q.get()
            q.get()

            with open(self.folder_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                for tem in self.input_list:
                    writer.writerow(tem)

            self.ui.finish.setHidden(False)
        except Exception as e:
            print(e)
            self.ui.error.setHidden(False)
        finally:
            self.count = 0
            self.ui.choose_file.setDisabled(False)
            self.ui.start.setDisabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
