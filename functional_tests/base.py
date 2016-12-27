import os
import sys
from unittest import skip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

class FunctionalTest(StaticLiveServerTestCase):

    @classmethod
    def setChromedriverPath(cls):
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        DIR = os.path.join(BASE_DIR, 'chromedriver')
        cls.chromedriver_path = DIR
        return DIR

    @classmethod
    def setUpClass(cls):
        cls.setChromedriverPath()
        for arg in sys.argv:
            if 'liveserver' in arg:
                cls.server_url = 'http://' + arg.split('=')[1]
                cls.live_server_url = ''
                return
        super().setUpClass()
        cls.server_url = cls.live_server_url

    @classmethod
    def tearDownClass(cls):
        if cls.server_url == cls.live_server_url:
            super().tearDownClass()

    def setUp(self):
        self.browser = webdriver.Chrome(executable_path=self.chromedriver_path)
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def check_for_row_in_list_table(self, row_text):
        table = self.browser.find_element_by_id('id_list_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(row_text, [row.text for row in rows])
