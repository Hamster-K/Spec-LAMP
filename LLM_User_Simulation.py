# Taking KIMI as an example
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementNotInteractableException,
    TimeoutException
)

options = webdriver.ChromeOptions()
options.headless = False
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

driver.get("https://kimi.moonshot.cn/")
time.sleep(5)

EXPERIMENT_DURATION = 10 * 60
ANSWER_TIMEOUT = 90
STABLE_THRESHOLD = 3
CHECK_INTERVAL = 5

questions = ["Set up a list of questions here"]

def log(msg):
    print(time.strftime("[%H:%M:%S] "), msg)

def get_input_box():
    return wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//div[@contenteditable='true' and @role='textbox']")
        )
    )

def send_question(question):
    while True:
        try:
            box = get_input_box()
            driver.execute_script("arguments[0].focus();", box)
            box.click()
            time.sleep(0.3)
            box.send_keys(question)
            time.sleep(0.2)
            box.send_keys(Keys.ENTER)
            return
        except (StaleElementReferenceException, ElementNotInteractableException):
            log("retry...")
            time.sleep(1)

def get_last_answer_text():
    try:
        return driver.execute_script("""
            let nodes = document.querySelectorAll('.paragraph');
            if (nodes.length === 0) return '';
            return nodes[nodes.length - 1].innerText.trim();
        """)
    except Exception:
        return ""

def wait_answer_finish(timeout=ANSWER_TIMEOUT):
    start = time.time()
    last_len = 0
    stable_round = 0

    while time.time() - start < timeout:
        text = get_last_answer_text()
        curr_len = len(text)
        if curr_len == 0:
            time.sleep(CHECK_INTERVAL)
            continue
        if curr_len == last_len:
            stable_round += 1
            if stable_round >= STABLE_THRESHOLD:
                return text
        else:
            last_len = curr_len
            stable_round = 0
        time.sleep(CHECK_INTERVAL)

    log("return")
    return text

log("start")
experiment_start = time.time()
question_index = 0

while time.time() - experiment_start < EXPERIMENT_DURATION:
    question = questions[question_index % len(questions)]
    log(f"question：{question}")
    send_question(question)
    answer = wait_answer_finish()
    log(f"len={len(answer)}")

    # record_timestamp()
    # save_answer(question, answer)
    # stop_perf()

    question_index += 1
    time.sleep(1)

log("End")
driver.quit()