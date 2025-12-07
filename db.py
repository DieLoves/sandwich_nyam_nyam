import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import random
from constants import PIPELINE_COORDS

@st.cache_resource
def init_db():
    conn = sqlite3.connect('integrityos.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS Pipelines (pipeline_id TEXT PRIMARY KEY, name TEXT)''')
    c.executemany("INSERT OR IGNORE INTO Pipelines VALUES (?, ?)", 
                  [('MT-01', 'Main Trunk 01'), ('MT-02', 'Main Trunk 02'), 
                   ('MT-03', 'Main Trunk 03'), ('MT-04', 'Main Trunk 04')])

    c.execute('''CREATE TABLE IF NOT EXISTS Objects
                 (object_id INTEGER PRIMARY KEY, object_name TEXT, object_type TEXT,
                  pipeline_id TEXT, lat REAL, lon REAL, year INTEGER, material TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS Inspections
                 (diag_id INTEGER PRIMARY KEY, object_id INTEGER, method TEXT, date DATE,
                  temperature REAL, humidity REAL, illumination REAL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS Defects
                 (defect_id INTEGER PRIMARY KEY AUTOINCREMENT, diag_id INTEGER,
                  defect_found BOOLEAN, defect_description TEXT, quality_grade TEXT,
                  param1 REAL, param2 REAL, param3 REAL, ml_label TEXT)''')

    if c.execute("SELECT COUNT(*) FROM Objects").fetchone()[0] == 0:
        st.sidebar.info("Генерация тестовых данных (30 объектов на 4 магистралях)...")

        def get_point_on_pipeline(pipeline_id):
            coords = PIPELINE_COORDS[pipeline_id]
            seg_idx = random.randint(0, len(coords)-2)
            p1, p2 = coords[seg_idx], coords[seg_idx+1]
            t = random.uniform(0, 1)
            lat = p1[0] + t * (p2[0] - p1[0])
            lon = p1[1] + t * (p2[1] - p1[1])
            return round(lat, 4), round(lon, 4)

        objects = []
        for i in range(1, 31):
            pipeline_id = f"MT-0{random.randint(1,4)}"
            lat, lon = get_point_on_pipeline(pipeline_id)
            name = random.choices(
                [f"Участок {random.choice(['Атырау','Тенгиз','Актау','Кульсары','Бейнеу','Жанаозен','Макат'])}-{random.randint(1,99)}",
                 f"Кран №{random.randint(100,999)}"],
                weights=[80,20])[0]
            obj_type = random.choices(["pipeline_section", "crane", "compressor_station"], weights=[78,18,4])[0]
            year = random.randint(2005, 2024)
            material = random.choice(["X70", "X80", "09Г2С", "17Г1С", "Сталь 20"])
            objects.append((i, name, obj_type, pipeline_id, lat, lon, year, material))

        c.executemany("INSERT INTO Objects VALUES (?,?,?,?,?,?,?,?)", objects)
        
        inspections_data = [
            (1,1,'MFL','2025-08-15',18,55,520),(2,1,'UZK','2025-11-20',2,80,280),(3,2,'VIK','2025-10-05',8,65,450),
            (4,3,'MFL','2025-09-12',22,48,580),(5,4,'UZK','2025-07-22',25,52,620),(6,5,'MFL','2025-06-30',28,45,680),
            (7,6,'VIK','2025-05-18',15,60,500),(8,7,'UZK','2025-04-10',12,70,420),(9,8,'MFL','2025-03-25',6,75,350),
            (10,9,'VIK','2025-02-14',-5,85,200),(11,10,'MFL','2025-01-08',0,90,180),(12,11,'UZK','2025-11-11',3,78,300),
            (13,12,'VIK','2025-10-30',10,62,480),(14,13,'MFL','2025-09-28',20,50,600),(15,14,'UZK','2025-08-20',24,47,650),
            (16,15,'MFL','2025-12-01',5,70,400),(17,16,'UZK','2025-11-15',1,82,250),(18,17,'VIK','2025-10-20',7,68,420),
            (19,18,'MFL','2025-09-15',19,53,570),(20,19,'UZK','2025-08-10',26,49,610),(21,20,'MFL','2025-07-25',29,44,670),
            (22,21,'VIK','2025-06-12',16,59,510),(23,22,'UZK','2025-05-05',13,69,430),(24,23,'MFL','2025-04-18',7,74,360),
            (25,24,'VIK','2025-03-10',-3,84,210),(26,25,'MFL','2025-02-28',1,89,190),(27,26,'UZK','2025-01-15',-1,91,170),
            (28,27,'VIK','2025-12-10',4,76,320),(29,28,'MFL','2025-11-25',9,64,460),(30,29,'UZK','2025-10-18',14,58,500),
            (31,30,'MFL','2025-09-30',21,51,590),(32,1,'VIK','2025-12-05',6,72,380),(33,3,'UZK','2025-11-28',4,79,290),
            (34,5,'MFL','2025-10-25',11,66,470),(35,7,'VIK','2025-09-20',23,48,580),(36,9,'UZK','2025-08-15',27,46,630),
            (37,11,'MFL','2025-07-30',30,43,690),(38,13,'VIK','2025-06-20',17,58,520),(39,15,'UZK','2025-05-10',14,67,440),
            (40,17,'MFL','2025-04-25',8,73,370),(41,19,'VIK','2025-03-15',0,83,220),(42,21,'UZK','2025-02-20',-2,88,200),
            (43,23,'MFL','2025-01-25',-4,92,160),(44,25,'VIK','2025-12-15',5,75,340),(45,27,'UZK','2025-11-18',8,71,390),
            (46,29,'MFL','2025-10-12',15,57,510),(47,2,'VIK','2025-09-08',24,49,600),(48,4,'UZK','2025-08-28',28,45,660),
            (49,6,'MFL','2025-07-18',31,42,700),(50,8,'VIK','2025-06-08',18,57,530),(51,10,'UZK','2025-05-22',15,66,450),
            (52,12,'MFL','2025-04-15',9,72,380),(53,14,'VIK','2025-03-28',2,81,240),(54,16,'UZK','2025-02-15',-3,87,210),
            (55,18,'MFL','2025-01-20',-5,93,150),(56,20,'VIK','2025-12-20',7,70,400),(57,22,'UZK','2025-11-10',10,65,450),
            (58,24,'MFL','2025-10-05',16,56,520),(59,26,'VIK','2025-09-18',25,47,590),(60,28,'UZK','2025-08-25',29,44,650),
            (61,30,'MFL','2025-07-15',32,41,710),(62,1,'VIK','2025-06-25',19,55,540),(63,3,'UZK','2025-05-30',16,64,460),
            (64,5,'MFL','2025-04-20',10,71,390),(65,7,'VIK','2025-03-12',3,80,250),(66,9,'UZK','2025-02-28',-1,86,220),
            (67,11,'MFL','2025-01-18',-6,94,140),(68,13,'VIK','2025-12-25',8,69,410),(69,15,'UZK','2025-11-20',11,63,460),
            (70,17,'MFL','2025-10-15',17,55,530),(71,19,'VIK','2025-09-25',26,46,600),(72,21,'UZK','2025-08-18',30,43,660),
            (73,23,'MFL','2025-07-28',33,40,720),(74,25,'VIK','2025-06-15',20,54,550),(75,27,'UZK','2025-05-25',17,63,470),
            (76,29,'MFL','2025-04-10',11,70,400),(77,2,'VIK','2025-03-20',4,79,260),(78,4,'UZK','2025-02-15',-2,85,230),
            (79,6,'MFL','2025-01-30',-4,91,170),(80,8,'VIK','2025-12-12',9,68,420),(81,10,'UZK','2025-11-22',12,62,470),
            (82,12,'MFL','2025-10-28',18,54,540),(83,14,'VIK','2025-09-20',27,45,610),(84,16,'UZK','2025-08-30',31,42,670),
            (85,18,'MFL','2025-07-20',34,39,730),(86,20,'VIK','2025-06-18',21,53,560),(87,22,'UZK','2025-05-28',18,62,480),
        ]
        c.executemany("INSERT INTO Inspections VALUES (?,?,?,?,?,?,?)", inspections_data)

        defects_data = [
            (1,True,'Металлосс 18%', 'недопустимо',17.8,145,7.2,'high'),
            (2,True,'Внешняя коррозия глубокая', 'недопустимо',19.3,160,7.8,'high'),
            (3,True,'Трещина продольная', 'недопустимо',15.6,210,6.9,'high'),
            (4,True,'Глубокий питтинг', 'недопустимо',21.2,185,8.5,'high'),
            (5,True,'Металлосс критический', 'недопустимо',23.7,220,9.1,'high'),
            (8,True,'Гофр + коррозия', 'недопустимо',18.9,155,7.5,'high'),
            (9,True,'Вмятина большая', 'недопустимо',20.4,195,8.3,'high'),
            (13,True,'Трещина у сварного шва', 'недопустимо',22.1,235,8.9,'high'),
            (14,True,'Коррозия внутренняя', 'недопустимо',16.8,135,6.8,'high'),
            (15,True,'Множественный питтинг', 'недопустимо',19.9,175,7.9,'high'),
            (19,True,'Глубокая коррозия', 'недопустимо',24.5,245,9.5,'high'),
            (35,True,'Критическая трещина', 'недопустимо',26.3,280,10.2,'high'),
            (48,True,'Развитая коррозия', 'недопустимо',25.1,260,9.8,'high'),
            (59,True,'Критический металлосс', 'недопустимо',27.8,295,10.8,'high'),
            (72,True,'Опасная вмятина', 'недопустимо',28.9,310,11.2,'high'),
            (6,False,'','удовлетворительно',0,0,0,'normal'),
            (7,True,'Локальная коррозия','допустимо',4.2,65,2.9,'medium'),
            (10,False,'','удовлетворительно',0,0,0,'normal'),
            (11,True,'Мелкий питтинг','допустимо',3.1,45,2.1,'medium'),
            (16,True,'Коррозионное пятно','допустимо',5.5,85,3.3,'medium'),
            (20,False,'','удовлетворительно',0,0,0,'normal'),
        ]
        for d in defects_data:
            c.execute("INSERT INTO Defects (diag_id, defect_found, defect_description, quality_grade, param1, param2, param3, ml_label) VALUES (?,?,?,?,?,?,?,?)", d)

        conn.commit()
        st.sidebar.success("Тестовые данные загружены — 30 объектов, 4 магистрали, 87 инспекций")

    conn.commit()
    return conn