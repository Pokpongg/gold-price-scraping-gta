#!/usr/bin/env python
# coding: utf-8

# In[ ]:

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os

# ตั้งค่า Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # ทำงานแบบไม่มี GUI
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# เปิดเบราว์เซอร์
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# เข้าเว็บไซต์ราคาทองคำ
url = "https://www.goldtraders.or.th/AvgPriceList.aspx"
driver.get(url)

# รอให้หน้าเว็บโหลด
time.sleep(3)

# ดึงค่าปีทั้งหมดจาก dropdown
year_dropdown = Select(driver.find_element(By.ID, "DetailPlace_ddlYear"))
years = [option.text for option in year_dropdown.options]

# **เรียงปีจากเก่าสุดไปใหม่สุด**
years.sort()

# ลำดับเดือนที่ถูกต้อง
month_order = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4, "พฤษภาคม": 5, "มิถุนายน": 6,
    "กรกฎาคม": 7, "สิงหาคม": 8, "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12
}

# เก็บข้อมูลทั้งหมด
gold_data = []

for year in years:
    print(f"📅 กำลังดึงข้อมูลปี {year} ...")

    # เลือกปี
    year_dropdown = Select(driver.find_element(By.ID, "DetailPlace_ddlYear"))
    year_dropdown.select_by_visible_text(year)

    # รอให้ข้อมูลในตารางโหลดใหม่
    WebDriverWait(driver, 5).until(EC.staleness_of(driver.find_element(By.ID, "DetailPlace_MainGridView")))

    # ดึงข้อมูลตารางใหม่อีกครั้ง
    table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "DetailPlace_MainGridView"))
    )

    rows = table.find_elements(By.TAG_NAME, "tr")

    # ข้าม 2 แถวแรก (หัวข้อ)
    for row in rows[2:]:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) == 8:  # ตรวจสอบว่ามีข้อมูลครบ
            month = cols[0].text.strip()
            gold_price = {
                "ปี พ.ศ.": year,
                "เดือน": month,
                "ทองรูปพรรณ รับซื้อ (บาท)": cols[1].text.strip(),
                "ทองรูปพรรณ ค่าธรรมเนียม (บาท)": cols[2].text.strip(),
                "ทองรูปพรรณ ขายออก (บาท)": cols[3].text.strip(),
                "ทองแท่ง รับซื้อ (บาท)": cols[4].text.strip(),
                "ทองแท่ง ขายออก (บาท)": cols[5].text.strip(),
                "US$ ต่อออนซ์": cols[6].text.strip(),
                "Baht / US$": cols[7].text.strip(),
                "month_order": month_order.get(month, 99)  # เก็บค่าเดือนเป็นตัวเลขสำหรับ sorting
            }
            gold_data.append(gold_price)

# ปิดเบราว์เซอร์
driver.quit()

# แปลงเป็น DataFrame
df = pd.DataFrame(gold_data)

# **Sort ข้อมูลตาม ปี -> เดือน**
df.sort_values(by=["ปี พ.ศ.", "month_order"], ascending=[True, True], inplace=True)

# ลบ column ช่วยเรียงเดือน
df.drop(columns=["month_order"], inplace=True)

# แปลง "ปี พ.ศ." เป็น integer
df["ปี พ.ศ."] = df["ปี พ.ศ."].astype(int)

# แปลงคอลัมน์ตัวเลขจาก string เป็น float
numeric_columns = [
    "ทองรูปพรรณ รับซื้อ (บาท)", "ทองรูปพรรณ ค่าธรรมเนียม (บาท)", "ทองรูปพรรณ ขายออก (บาท)",
    "ทองแท่ง รับซื้อ (บาท)", "ทองแท่ง ขายออก (บาท)", "US$ ต่อออนซ์", "Baht / US$"
]

for col in numeric_columns:
    df[col] = df[col].str.replace(",", "").astype(float)  # เอา , ออกแล้วแปลงเป็น float

# บันทึกเป็นไฟล์ Excel
file_path = "gold_prices.xlsx"

# บันทึกข้อมูลลงชีต "web scrap" โดยไม่ลบชีตอื่น
if not os.path.exists(file_path):
    # ถ้าไฟล์ยังไม่เคยมี → สร้างใหม่เลย
    df.to_excel(file_path, sheet_name="web scrap", index=False)
else:
    # ถ้ามีแล้ว → append แบบไม่ลบชีตอื่น
    with pd.ExcelWriter(file_path, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name="web scrap", index=False)

# แสดงข้อมูลเป็นตาราง
import ace_tools_open as tools
tools.display_dataframe_to_user(name="ราคาทองคำย้อนหลัง", dataframe=df)

print(f"✅ บันทึกข้อมูลสำเร็จ 🎉: {file_path}")

