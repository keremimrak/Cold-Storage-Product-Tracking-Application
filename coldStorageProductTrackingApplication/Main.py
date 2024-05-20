import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem
import sqlite3
from datetime import datetime
import qrcode
import cv2
from pyzbar.pyzbar import decode
import pandas as pd
from PyQt5.QtCore import QTimer
from UIForApp import Ui_Form

#----------------------UYGULAMA OLUŞTURMA----------------------#
#----------------------UYGULAMA OLUŞTURMA----------------------#
Uygulama = QtWidgets.QApplication(sys.argv)
penAna = QMainWindow()
ui = Ui_Form()
ui.setupUi(penAna)
penAna.show()

ui.MessageLabel.setText("")

global conn 
global curs
global _passingTime
conn = sqlite3.connect("Malzemeler.db")
curs = conn.cursor()

malzemeler = ("CREATE TABLE IF NOT EXISTS malzemeler(             \
                  ID INTEGER NOT NULL UNIQUE ,                  \
                  day INTEGER ,                         \
                  mounth INTEGER,     \
                  year INTEGER,   \
                  hour INTEGER, \
                  minute INTEGER,  \
                  situation INTEGER,  \
                  passingTime INTEGER)")

# situation 1 ise zaman akıyor, 0 ise durmuş
curs.execute(malzemeler)
conn.commit()



# Excel dosyasına aktarır bubnun için bi buton koyup nutona basınca bu fonksiyonu çalıştırabilirsin
def create_and_export_to_excel():
    try:
       
        conn = sqlite3.connect("malzemeler.db")  
        cursor = conn.cursor()

       
        query = "SELECT ID, situation, passingTime FROM malzemeler"  
        data = cursor.execute(query).fetchall()

       
        columns = [description[0] for description in cursor.description]
        df = pd.DataFrame(data, columns=columns)

      
        df.to_excel("Malzemeler.xlsx", index=False, engine="openpyxl")

        print("Veriler Excel dosyasına aktarıldı.")
        ui.MessageLabel_2.setText("Veriler, Malzemeler isimli excel dosyasına aktarıldı")

    except Exception as e:
        print("Hata: ", e)

    finally:
        
        if conn:
            conn.close()

def cameraControl():
    uyarı = QMessageBox()
    uyarı.setIcon(QMessageBox.Warning)
    uyarı.setText("Okeye bastıktan sonra 5 saniye içinde qr kodu kameraya tutunuz")
    uyarı.setWindowTitle("Qr Uyarı")
    uyarı.setStandardButtons(QMessageBox.Ok)               
    returnValue = uyarı.exec()
    if returnValue==QMessageBox.Ok:
        penAna.show()


def read_qr_code_from_camera():
    try:
        uyarı = QMessageBox()
        uyarı.setIcon(QMessageBox.Warning)
        uyarı.setText("Okeye bastıktan sonra 5 saniye içinde qr kodu kameraya tutunuz")
        uyarı.setWindowTitle("Qr Uyarı")
        uyarı.setStandardButtons(QMessageBox.Ok)               
        returnValue = uyarı.exec()
        if returnValue==QMessageBox.Ok:

            font = cv2.FONT_HERSHEY_PLAIN
            cap = cv2.VideoCapture(0)

            while True:
            
                ret, frame = cap.read()

                decoded_objects = decode(frame)

                if decoded_objects:
                    for obj in decoded_objects:
                        qr_code_value = obj.data.decode('utf-8')
                        print("QR kodun değeri:", qr_code_value)
                        cv2.putText(frame, str(qr_code_value)+ "numaralı ürün tarandı bu sayfayı kapatabilirsiniz", (50, 50), font, 2,
                            (255, 0, 0), 3)
                        return qr_code_value   

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            
    except Exception as e:
        print("Hata: ", e)
        return None
        

# bu fonksiyon yeni oluşturulacak qr kodun numarasını yani ID sini buluyor ve qr kodu oluşturuyor 1 no lu ID den sonsuza kadar sıralar
def crateQr():
    try: 
        connection = sqlite3.connect("Malzemeler.db")
        cursor = connection.cursor()

        # Tabloda hiç kayıt yoksa, QR kodunu 1 olarak oluştur
        cursor.execute("SELECT COUNT(*) FROM malzemeler")
        count = cursor.fetchone()[0]
        if count == 0:
            data = 1
            ID = data
        else:
            # Tabloda kayıt varsa, son ID değerinden bir fazla olan sayının içinde yazılı QR kodu oluştur
            cursor.execute("SELECT id FROM malzemeler ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            last_id = result[0] if result else 0
            data = str(last_id + 1)
            ID = data
        connection.close()

        filename = f"{data}.png"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(filename)

        print(f"QR Code oluşturuldu ve {filename} olarak kaydedildi.")
        ui.MessageLabel.setText(f"QR Code oluşturuldu ve {filename} olarak kaydedildi.")
        now = datetime.now()
        _day = now.day
        _mounth = now.month  
        _year = now.year
        _hour = now.hour
        _minute = now.minute
        _situation = 0
        _passingTime = 0

        curs.execute("INSERT INTO malzemeler \
                                (ID,day,mounth,year,hour,minute,situation,passingTime)\
                                VALUES (?,?,?,?,?,?,?,?)", 
                                (ID,_day,_mounth,_year,_hour,_minute,_situation,_passingTime))
        conn.commit()
        create_and_export_to_excel()
    except Exception as e:
        print("Hata: ", e)


# zaman arasındaki dakika farkını hesaplıyor, bununla bişey yapmana gerek yok sadece diğer fonksiyonların içinde kullandım
def dakika_farki_hesapla(gun2, ay2, yil2, saat2, dakika2, gun1, ay1, yil1, saat1, dakika1):
    try:
        tarih1 = datetime(year=yil1, month=ay1, day=gun1, hour=saat1, minute=dakika1)
        tarih2 = datetime(year=yil2, month=ay2, day=gun2, hour=saat2, minute=dakika2)

        fark = tarih2 - tarih1
        dakika_farki = fark.total_seconds() / 60
        

        return int(dakika_farki)
      
    except ValueError:
        return "Geçersiz tarih veya saat bilgisi!"


# qr kodu ilk defa okuttuğumuzda bu çalışacak; o anki yıl, ay, gün..... gibi değerlieri veritabanına kaydeder 
# ilk defa bi ürünü depodan çıkartırken kullanılacak
def veriTabaninaÜrünEkle():

    try:

        ID = read_qr_code_from_camera()
        print(ID)
        now = datetime.now()
        _day = now.day
        _mounth = now.month  
        _year = now.year
        _hour = now.hour
        _minute = now.minute
        _situation = 0
        _passingTime = 0

        curs.execute("INSERT INTO malzemeler \
                                (ID,day,mounth,year,hour,minute,situation,passingTime)\
                                VALUES (?,?,?,?,?,?,?,?)", 
                                (ID,_day,_mounth,_year,_hour,_minute,_situation,_passingTime))
        conn.commit()
        create_and_export_to_excel()

        #bu satıra  sayfada güzükecek ürün kaydedildi ve depodan çıkarıldı yazısı ekleyebilirsin 
    except Exception as e:
        print("Hata: ", e)
    

# Bu fonksiyon çalıştığında o anki yıl,ay,gün,saat.... gibi bilgiler ile ilk databaseye kaydedilen bilgiler arasındaki farka bakıp dakika farkını hesaplar 
# data_situation değerini değiştirir, eğer bu değer  1 ise zaman akıyordur eğer değilse zaman durmuştur yani ürün yeniden dolaba konmuş olur
# yani ilk maddede anlatıığım hesaplanan dakika bilgisini eğer qr okutulduğundan değeri 1 ise, _passingTime(Geçen zamanı) arttırır ve databaseye yeniden kaydeder
    #Ve data_situation değerini 0 yapar yani ürün dolaptadır
#arayüze geçen zaman olarak _passingTime değişkenini yazdırabilirsin qr okutulduğunda
#daha önce depodan çıkarılmış ve yeniden depoya konulan yada sonra yeniden depodan çıkarılırken vb. kullanılır

def TekaradanAyniQROkutma():
    
    try:
        ID = read_qr_code_from_camera()
        print(ID)
        
        curs.execute("SELECT * FROM malzemeler WHERE ID = ?",\
                    (ID))
        data = curs.fetchall()
        
        print(data[0])

        #İlk elemanı alıp virgüllerden ayırma
        data = data[0]
        data = ', '.join(map(str, data))
        data = list(map(int, data.split(', ')))
        


        print(type(data[1]))
        

        data_ID = data[0]
        data_day = data[1]
        print(data_day)
        data_mounth = data[2]
        data_year = data[3]
        data_hour = data[4]
        data_minute = data[5]
        data_situation = data[6]
        data_passingTime = data[7]
        conn.commit()

        

        now = datetime.now()
        _day = now.day
        _mounth = now.month  
        _year = now.year
        _hour = now.hour
        _minute = now.minute

        if(data_situation == 1):
            fark = dakika_farki_hesapla(_day,_mounth,_year,_hour,_minute, data_day,data_mounth, data_year,data_hour, data_minute)
            _passingTime = data_passingTime + fark
            data_situation = 0
            print(_passingTime)
            curs.execute("UPDATE malzemeler SET day=?,mounth=?,year=?,hour=?,minute=?,situation=?,passingTime=? WHERE ID=?",\
                    (_day,_mounth,_year,_hour,_minute,data_situation,_passingTime,data_ID))
            conn.commit()
            ui.MessageLabel.setText(f"{ID} Numaralı Ürün Durumu Depoda olarak Güncellendi.")
            LISTELE()
            create_and_export_to_excel()
            #bu satıra  sayfada güzükecek depodaya girdi yazısı ekleyebilirsin ve _passingTime değişkeni yani geçen süre yasssın
            #(geçen süre dakika cinsinden)

        else:
            data_situation = 1
        
            curs.execute("UPDATE malzemeler SET day=?,mounth=?,year=?,hour=?,minute=?,situation=?,passingTime=? WHERE ID=?",\
                    (_day,_mounth,_year,_hour,_minute,data_situation,data_passingTime,data_ID))
            conn.commit()
            ui.MessageLabel.setText(f"{ID} Numaralı Ürün Durumu Dışarıda olarak Güncellendi.")
            LISTELE()
            create_and_export_to_excel()
            #bu satıra  sayfada güzükecek depodan çıkarıldı yazısı ekleyebilirsin ve _passingTime değişkeni yani geçen süre yasssın
            #(geçen süre dakika cinsinden)  
    except Exception as e:
        print("Hata: ", e)

async def ListeleAsync():
    while True:
        LISTELE()
        await asyncio.sleep(60)

async def main():
    await ListeleAsync()

def LISTELE():
    try:
        conn = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        curs = conn.cursor()

        # Fetch all rows from the table
        curs.execute("SELECT * FROM malzemeler")
        all_data = curs.fetchall()

        now = datetime.now()
        _day = now.day
        _month = now.month
        _year = now.year
        _hour = now.hour
        _minute = now.minute

        for data in all_data:
            data_ID = data[0]
            data_day = data[1]
            data_month = data[2]
            data_year = data[3]
            data_hour = data[4]
            data_minute = data[5]
            data_situation = data[6]
            data_passingTime = data[7]

            if data_situation == 1:
                fark = dakika_farki_hesapla(_day, _month, _year, _hour, _minute, data_day, data_month, data_year, data_hour, data_minute)
                _passingTime = data_passingTime + fark
                curs.execute("UPDATE malzemeler SET day=?, mounth=?, year=?, hour=?, minute=?, situation=?, passingTime=? WHERE ID=?", \
                             (_day, _month, _year, _hour, _minute, data_situation, _passingTime, data_ID))
                conn.commit()
                print("YeniSüreHesaplandı")
            else:
                curs.execute("UPDATE malzemeler SET day=?, mounth=?, year=?, hour=?, minute=?, situation=?, passingTime=? WHERE ID=?", \
                             (_day, _month, _year, _hour, _minute, data_situation, data_passingTime, data_ID))
                conn.commit()

        conn.close()




        connection = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        cursor = connection.cursor()
        cursor.execute("SELECT ID, situation, passingTime FROM malzemeler")  # Tablo adını buraya yazın
        data = cursor.fetchall()
        connection.close()
        print("listelle çalıştı")
        headers = ["ID", "Ürün Durumu", "Geçen zaman"]
        ui.tableWidget.setHorizontalHeaderLabels(headers)
        ui.tableWidget.setRowCount(len(data))

        ui.tableWidget.setColumnWidth(0, 150)
        ui.tableWidget.setColumnWidth(1, 150)
        ui.tableWidget.setColumnWidth(2, 150)

        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_idx == 1:  # Check if we are at the "situation" column
                    if cell_data == 0:
                        item.setText("Depoda")
                    elif cell_data == 1:
                        item.setText("Dışarıda")
                    else:
                        item.setText(str(cell_data))  # Handle other values if needed
                else:
                    item.setText(str(cell_data))
                ui.tableWidget.setItem(row_idx, col_idx, item)

    except Exception as hata_Lıstele:
        ui.statusbar.showMessage("Hata_Lıstele: " + str(hata_Lıstele), 6000)

def show_items_with_situation_0():
    try:
        # ui.tableWidget.clear()

        connection = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        cursor = connection.cursor()
        cursor.execute("SELECT ID, situation, passingTime FROM malzemeler WHERE situation = 0")  # Tablo adını buraya yazın ve sadece situation=1 olanları seçin
        data = cursor.fetchall()
        connection.close()

        headers = ["ID", "Ürün Durumu", "Geçen zaman"]
        ui.tableWidget.setHorizontalHeaderLabels(headers)
        ui.tableWidget.setRowCount(len(data))
        ui.tableWidget.setColumnWidth(0, 150)
        ui.tableWidget.setColumnWidth(1, 150)
        ui.tableWidget.setColumnWidth(2, 150)
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_idx == 1:  # Check if we are at the "situation" column
                    if cell_data == 0:
                        item.setText("Depoda")
                    elif cell_data == 1:
                        item.setText("Dışarıda")
                    else:
                        item.setText(str(cell_data))  # Handle other values if needed
                else:
                    item.setText(str(cell_data))
                ui.tableWidget.setItem(row_idx, col_idx, item)

    except Exception as hata_Lıstele:
        ui.statusbar.showMessage("Hata_Lıstele: " + str(hata_Lıstele), 6000)

def show_items_with_situation_1():
    try:
        ui.tableWidget.clear()

        connection = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        cursor = connection.cursor()
        cursor.execute("SELECT ID, situation, passingTime FROM malzemeler WHERE situation = 1")  # Tablo adını buraya yazın ve sadece situation=1 olanları seçin
        data = cursor.fetchall()
        connection.close()

        headers = ["ID", "Ürün Durumu", "Geçen zaman"]
        ui.tableWidget.setHorizontalHeaderLabels(headers)
        ui.tableWidget.setRowCount(len(data))
        ui.tableWidget.setColumnWidth(0, 150)
        ui.tableWidget.setColumnWidth(1, 150)
        ui.tableWidget.setColumnWidth(2, 150)
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_idx == 1:  # Check if we are at the "situation" column
                    if cell_data == 0:
                        item.setText("Depoda")
                    elif cell_data == 1:
                        item.setText("Dışarıda")
                    else:
                        item.setText(str(cell_data))  # Handle other values if needed
                else:
                    item.setText(str(cell_data))
                ui.tableWidget.setItem(row_idx, col_idx, item)

    except Exception as hata_Lıstele:
        ui.statusbar.showMessage("Hata_Lıstele: " + str(hata_Lıstele), 6000)

def LISTELE_OVER_30000():
    try:
        ui.tableWidget.clear()

        connection = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        cursor = connection.cursor()
        cursor.execute("SELECT ID, situation, passingTime FROM malzemeler")  # Tablo adını buraya yazın
        data = cursor.fetchall()
        connection.close()

        headers = ["ID", "Ürün Durumu", "Geçen zaman"]
        ui.tableWidget.setHorizontalHeaderLabels(headers)
        ui.tableWidget.setColumnWidth(0, 150)
        ui.tableWidget.setColumnWidth(1, 150)
        ui.tableWidget.setColumnWidth(2, 150)
        # Filter the data to keep only rows with "passingTime" value of 30000 and above
        data_filtered = [row for row in data if row[2] >= 30000]
        
        ui.tableWidget.setRowCount(len(data_filtered))
        
        for row_idx, row_data in enumerate(data_filtered):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_idx == 1:  # Check if we are at the "situation" column
                    if cell_data == 0:
                        item.setText("Depoda")
                    elif cell_data == 1:
                        item.setText("Dışarıda")
                    else:
                        item.setText(str(cell_data))  # Handle other values if needed
                else:
                    item.setText(str(cell_data))
                ui.tableWidget.setItem(row_idx, col_idx, item)

    except Exception as hata_Lıstele:
        ui.statusbar.showMessage("Hata_Lıstele: " + str(hata_Lıstele), 6000)


def LISTELE_Under_30000():
    try:
        ui.tableWidget.clear()

        connection = sqlite3.connect("Malzemeler.db")  # Veritabanı dosyanızın adını buraya yazın
        cursor = connection.cursor()
        cursor.execute("SELECT ID, situation, passingTime FROM malzemeler")  # Tablo adını buraya yazın
        data = cursor.fetchall()
        connection.close()

        headers = ["ID", "Ürün Durumu", "Geçen zaman"]
        ui.tableWidget.setHorizontalHeaderLabels(headers)
        
        # Filter the data to keep only rows with "passingTime" value of 30000 and above
        data_filtered = [row for row in data if row[2] <= 30000]
        
        ui.tableWidget.setRowCount(len(data_filtered))
        ui.tableWidget.setColumnWidth(0, 150)
        ui.tableWidget.setColumnWidth(1, 150)
        ui.tableWidget.setColumnWidth(2, 150)
        for row_idx, row_data in enumerate(data_filtered):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem()
                if col_idx == 1:  # Check if we are at the "situation" column
                    if cell_data == 0:
                        item.setText("Depoda")
                    elif cell_data == 1:
                        item.setText("Dışarıda")
                    else:
                        item.setText(str(cell_data))  # Handle other values if needed
                else:
                    item.setText(str(cell_data))
                ui.tableWidget.setItem(row_idx, col_idx, item)

    except Exception as hata_Lıstele:
        ui.statusbar.showMessage("Hata_Lıstele: " + str(hata_Lıstele), 6000)


ui.QrOlustur.clicked.connect(crateQr)
ui.QrOkut.clicked.connect(TekaradanAyniQROkutma)
ui.ExceleAktar.clicked.connect(create_and_export_to_excel)
ui.SuresiBitenler.clicked.connect(LISTELE_OVER_30000)
ui.SuresiKalanlar.clicked.connect( LISTELE_Under_30000)
ui.Listele.clicked.connect(LISTELE)
ui.Depodakiler.clicked.connect(show_items_with_situation_0)
ui.disasardakiler.clicked.connect(show_items_with_situation_1)
LISTELE()
timer = QTimer()
timer.timeout.connect(LISTELE)
timer.start(1000 * 60)  # 1 dakika (1 saniye = 1000 ms)

sys.exit(Uygulama.exec_())
