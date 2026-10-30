from .database import Base,engine,SessionLocal
from .models import GameItem,Task
COLLECTIONS=["Cyber City","Космическая экспедиция","Неоновая лаборатория","Пиксельный мир","Древние артефакты","Роботы будущего","Подводное королевство","Мир кристаллов","Лес загадок","Галактическая коллекция"]
RARITIES=["Обычный","Необычный","Редкий","Эпический","Легендарный","Мифический","Уникальный"]
ICONS=["🐈‍⬛","🛹","💠","🦊","🧭","💎","🤖","🫧","🗝️","🌿","☀️","🧊","🛸","🔮","🛰️","🛡️","🍄","⚙️"]
TASKS=[("first-item","Первый сигнал","Получи свой первый предмет",80,25,"item"),("open-container","Открытие горизонта","Открой игровой контейнер",60,20,"open"),("collect-five","Начинающий коллекционер","Собери пять предметов",120,40,"collect"),("daily-visit","Ежедневный визит","Забери ежедневную награду",50,15,"daily"),("level-up","Новый уровень","Получи новый уровень",100,35,"level"),("favorite","Любимчик","Добавь предмет в избранное",40,10,"favorite")]
def seed():
    Base.metadata.create_all(bind=engine); db=SessionLocal()
    try:
        existing={x.slug for x in db.query(GameItem).all()}
        for i in range(60):
            collection=COLLECTIONS[i%len(COLLECTIONS)]; rarity=RARITIES[i%len(RARITIES)]; icon=ICONS[i%len(ICONS)]; name=f"{['Неоновый','Квантовый','Звёздный','Кибер','Древний','Лунный','Плазменный','Кристальный'][i%8]} {['ворон','дрон','артефакт','спутник','страж','осколок','гриб','модуль'][i%8]} {i+1:02d}"; slug=f"artifact-{i+1:02d}"
            if slug not in existing: db.add(GameItem(slug=slug,name=name,description=f"Оригинальный коллекционный предмет из серии «{collection}».",rarity=rarity,collection=collection,icon=icon,power=i%12+1))
        task_slugs={x.slug for x in db.query(Task).all()}
        for slug,title,description,coins,xp,kind in TASKS:
            if slug not in task_slugs: db.add(Task(slug=slug,title=title,description=description,reward_coins=coins,reward_xp=xp,kind=kind))
        db.commit()
    finally: db.close()
if __name__=="__main__": seed()
