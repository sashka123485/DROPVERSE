from datetime import datetime,timezone
import random
from fastapi import FastAPI,Depends,Header,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session,joinedload
from sqlalchemy import desc,text
from .config import settings
from .database import Base,engine,get_db
from .models import User,GameItem,InventoryItem,Task,UserTask,Transaction
from .security import validate_telegram_init_data,dev_user
from .seed import seed
app=FastAPI(title="DROPVERSE API",version="0.1.0",description="API коллекционной Telegram-игры DROPVERSE")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_list or ["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
Base.metadata.create_all(bind=engine); seed()
class TelegramAuth(BaseModel): init_data:str=Field(min_length=1)
class NameInput(BaseModel): display_name:str=Field(min_length=2,max_length=40)
class PurchaseInput(BaseModel): item_id:int

def current_user(db:Session=Depends(get_db),authorization:str|None=Header(default=None),x_demo_user:str|None=Header(default=None)):
    if settings.environment!="production" and x_demo_user=="true": return dev_user(db)
    if not authorization or not authorization.lower().startswith("bearer "): raise HTTPException(401,"Нужна авторизация Telegram")
    tg=validate_telegram_init_data(authorization[7:]); user=db.query(User).filter_by(telegram_id=tg["id"]).first()
    if not user:
        name=" ".join(x for x in [tg.get("first_name",""),tg.get("last_name","")] if x).strip() or "Игрок"
        user=User(telegram_id=tg["id"],username=tg.get("username",""),display_name=name[:40],avatar_url=tg.get("photo_url","")); db.add(user); db.commit(); db.refresh(user)
    else:
        user.username=tg.get("username",user.username or ""); user.avatar_url=tg.get("photo_url",user.avatar_url or ""); db.commit()
    return user

def profile_data(user,db):
    return {"id":user.id,"telegram_id":user.telegram_id,"username":user.username,"display_name":user.display_name,"avatar_url":user.avatar_url,"level":user.level,"xp":user.xp,"xp_next":user.level*100,"coins":user.coins,"energy":user.energy,"item_count":db.query(InventoryItem).filter_by(user_id=user.id).count(),"created_at":user.created_at.isoformat(),"hide_rating":user.hide_rating}
def award_xp(user,amount):
    user.xp+=amount
    while user.xp>=user.level*100: user.xp-=user.level*100; user.level+=1
def transaction(db,user,amount,operation,source):
    before=user.coins
    if amount<0 and user.coins < -amount: raise HTTPException(400,"Недостаточно DROP COINS")
    user.coins+=amount; db.add(Transaction(user_id=user.id,amount=amount,balance_before=before,balance_after=user.coins,operation=operation,source=source))

@app.get("/api/health")
def health(db:Session=Depends(get_db)):
    db.execute(text("SELECT 1")); return {"status":"ok","service":"dropverse-api","version":"0.1.0","database":"connected"}
@app.post("/api/auth/telegram")
def auth(payload:TelegramAuth,db:Session=Depends(get_db)):
    tg=validate_telegram_init_data(payload.init_data); user=db.query(User).filter_by(telegram_id=tg["id"]).first()
    if not user:
        name=" ".join(x for x in [tg.get("first_name",""),tg.get("last_name","")] if x).strip() or "Игрок"; user=User(telegram_id=tg["id"],username=tg.get("username",""),display_name=name[:40],avatar_url=tg.get("photo_url","")); db.add(user); db.commit(); db.refresh(user)
    return {"ok":True,"profile":profile_data(user,db)}
@app.get("/api/profile")
def profile(user:User=Depends(current_user),db:Session=Depends(get_db)): return profile_data(user,db)
@app.patch("/api/profile")
def update_profile(payload:NameInput,user:User=Depends(current_user),db:Session=Depends(get_db)):
    user.display_name=payload.display_name.strip(); db.commit(); return profile_data(user,db)
@app.get("/api/collections")
def collections(user:User=Depends(current_user),db:Session=Depends(get_db)):
    names=db.query(GameItem.collection).distinct().all(); result=[]
    for (name,) in names:
        total=db.query(GameItem).filter_by(collection=name).count(); owned=db.query(InventoryItem).join(GameItem,InventoryItem.item_id==GameItem.id).filter(InventoryItem.user_id==user.id,GameItem.collection==name).count()
        result.append({"id":name.lower().replace(" ","-"),"name":name,"total":total,"owned":owned,"unlocked":True})
    return result
@app.get("/api/collections/{collection_id}")
def collection_detail(collection_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    name=next((n for (n,) in db.query(GameItem.collection).distinct().all() if n.lower().replace(" ","-")==collection_id),None)
    if not name: raise HTTPException(404,"Коллекция не найдена")
    owned={x.item_id for x in db.query(InventoryItem).filter_by(user_id=user.id).all()}
    return {"name":name,"items":[{"id":i.id,"name":i.name,"description":i.description,"rarity":i.rarity,"icon":i.icon,"owned":i.id in owned} for i in db.query(GameItem).filter_by(collection=name).all()]}
@app.get("/api/inventory")
def inventory(page:int=Query(1,ge=1),limit:int=Query(30,ge=1,le=100),user:User=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(InventoryItem).filter_by(user_id=user.id).order_by(desc(InventoryItem.obtained_at)); total=q.count(); rows=q.offset((page-1)*limit).limit(limit).all(); out=[]
    for r in rows:
        item=db.query(GameItem).filter_by(id=r.item_id).first(); out.append({"inventory_id":r.id,"id":item.id,"name":item.name,"description":item.description,"rarity":item.rarity,"collection":item.collection,"icon":item.icon,"level":r.level,"favorite":r.favorite,"obtained_at":r.obtained_at.isoformat()})
    return {"items":out,"page":page,"limit":limit,"total":total}
CONTAINERS=[{"id":"starter","name":"Стартовый сигнал","description":"Первое знакомство с коллекцией","cost":0,"probabilities":{"Обычный":55,"Необычный":25,"Редкий":12,"Эпический":6,"Легендарный":2}},{"id":"city","name":"Неоновый квартал","description":"Предметы городской коллекции","cost":75,"probabilities":{"Обычный":35,"Необычный":28,"Редкий":20,"Эпический":11,"Легендарный":5,"Мифический":1}},{"id":"cosmic","name":"Орбита мечты","description":"Находки космической экспедиции","cost":150,"probabilities":{"Обычный":20,"Необычный":25,"Редкий":25,"Эпический":18,"Легендарный":9,"Мифический":3}}]
@app.get("/api/containers")
def containers(user:User=Depends(current_user)): return CONTAINERS
@app.post("/api/containers/{container_id}/open")
def open_container(container_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    c=next((x for x in CONTAINERS if x["id"]==container_id),None)
    if not c: raise HTTPException(404,"Контейнер не найден")
    if user.coins<c["cost"]: raise HTTPException(400,"Недостаточно DROP COINS")
    if user.energy<5: raise HTTPException(400,"Недостаточно энергии")
    try:
        rarity=random.choices(list(c["probabilities"]),weights=list(c["probabilities"].values()),k=1)[0]
        choices=db.query(GameItem).filter_by(rarity=rarity).all() or db.query(GameItem).all(); item=random.choice(choices)
        before=user.coins; user.coins-=c["cost"]; user.energy-=5; award_xp(user,15)
        owned=InventoryItem(user_id=user.id,item_id=item.id,obtained_from=container_id); db.add(owned); db.add(Transaction(user_id=user.id,amount=-c["cost"],balance_before=before,balance_after=user.coins,operation="container_open",source=container_id)); db.commit(); db.refresh(owned)
        return {"ok":True,"item":{"inventory_id":owned.id,"id":item.id,"name":item.name,"rarity":item.rarity,"collection":item.collection,"icon":item.icon},"profile":profile_data(user,db)}
    except Exception: db.rollback(); raise
@app.get("/api/tasks")
def tasks(user:User=Depends(current_user),db:Session=Depends(get_db)):
    inv=db.query(InventoryItem).filter_by(user_id=user.id).count(); result=[]; today=datetime.now(timezone.utc).date().isoformat()
    for t in db.query(Task).all():
        state=db.query(UserTask).filter_by(user_id=user.id,task_id=t.id).first(); progress=int((t.kind=="item" and inv>0) or (t.kind=="collect" and inv>=5) or (t.kind=="level" and user.level>1) or (t.kind=="daily" and user.last_daily==today) or t.kind in ("open","favorite")); status="claimed" if state and state.claimed else ("complete" if progress else "active")
        result.append({"id":t.id,"slug":t.slug,"title":t.title,"description":t.description,"progress":progress,"target":1,"reward_coins":t.reward_coins,"reward_xp":t.reward_xp,"status":status})
    return result
@app.post("/api/tasks/{task_id}/claim")
def claim_task(task_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    t=db.query(Task).filter_by(id=task_id).first()
    if not t: raise HTTPException(404,"Задание не найдено")
    state=db.query(UserTask).filter_by(user_id=user.id,task_id=t.id).with_for_update().first()
    if state and state.claimed: raise HTTPException(409,"Награда уже получена")
    inv=db.query(InventoryItem).filter_by(user_id=user.id).count(); today=datetime.now(timezone.utc).date().isoformat(); done=(t.kind=="item" and inv>0) or (t.kind=="collect" and inv>=5) or (t.kind=="level" and user.level>1) or (t.kind=="daily" and user.last_daily==today) or t.kind in ("open","favorite")
    if not done: raise HTTPException(400,"Задание ещё не выполнено")
    if not state: db.add(UserTask(user_id=user.id,task_id=t.id,progress=1,claimed=True))
    else: state.claimed=True; state.progress=1
    before=user.coins; user.coins+=t.reward_coins; award_xp(user,t.reward_xp); db.add(Transaction(user_id=user.id,amount=t.reward_coins,balance_before=before,balance_after=user.coins,operation="task_reward",source=t.slug)); db.commit()
    return {"ok":True,"reward_coins":t.reward_coins,"reward_xp":t.reward_xp,"profile":profile_data(user,db)}
@app.get("/api/rewards/daily")
def daily_status(user:User=Depends(current_user)): return {"claimed":user.last_daily==datetime.now(timezone.utc).date().isoformat(),"reward_coins":50,"reward_xp":20}
@app.post("/api/rewards/daily/claim")
def daily_claim(user:User=Depends(current_user),db:Session=Depends(get_db)):
    today=datetime.now(timezone.utc).date().isoformat()
    if user.last_daily==today: raise HTTPException(409,"Ежедневная награда уже получена")
    before=user.coins; user.coins+=50; user.last_daily=today; award_xp(user,20); db.add(Transaction(user_id=user.id,amount=50,balance_before=before,balance_after=user.coins,operation="daily_reward",source=today)); db.commit()
    return {"ok":True,"reward_coins":50,"reward_xp":20,"profile":profile_data(user,db)}
SHOP=[{"id":1,"name":"Рамка «Неон»","description":"Неоновая рамка профиля","cost":120,"icon":"🟣"},{"id":2,"name":"Фон «Орбита»","description":"Космический фон профиля","cost":180,"icon":"🌌"},{"id":3,"name":"Значок «Пилот»","description":"Значок исследователя","cost":90,"icon":"🚀"}]
@app.get("/api/shop/items")
def shop_items(): return SHOP
@app.post("/api/shop/purchase")
def purchase(payload:PurchaseInput,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=next((x for x in SHOP if x["id"]==payload.item_id),None)
    if not item: raise HTTPException(404,"Товар не найден")
    if user.coins<item["cost"]: raise HTTPException(400,"Недостаточно DROP COINS")
    before=user.coins; user.coins-=item["cost"]; db.add(Transaction(user_id=user.id,amount=-item["cost"],balance_before=before,balance_after=user.coins,operation="shop_purchase",source=str(item["id"]))); db.commit()
    return {"ok":True,"message":"Получено: "+item["name"],"profile":profile_data(user,db)}
@app.get("/api/transactions")
def transactions(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{"id":x.id,"amount":x.amount,"balance_before":x.balance_before,"balance_after":x.balance_after,"operation":x.operation,"source":x.source,"created_at":x.created_at.isoformat()} for x in db.query(Transaction).filter_by(user_id=user.id).order_by(desc(Transaction.created_at)).limit(100).all()]
@app.get("/api/ratings")
def ratings(user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(User).filter_by(hide_rating=False).order_by(desc(User.level),desc(User.xp)).limit(50).all()
    return [{"rank":i+1,"display_name":u.display_name,"level":u.level,"xp":u.xp,"item_count":db.query(InventoryItem).filter_by(user_id=u.id).count(),"is_me":u.id==user.id} for i,u in enumerate(rows)]
@app.get("/api/admin/stats")
def admin_stats(user:User=Depends(current_user),db:Session=Depends(get_db)):
    if user.telegram_id not in settings.admin_ids: raise HTTPException(403,"Недостаточно прав")
    return {"users":db.query(User).count(),"items":db.query(GameItem).count(),"inventory_items":db.query(InventoryItem).count(),"transactions":db.query(Transaction).count()}
# Demo routes are intentionally disabled in production.
def demo_guard():
    if settings.environment=="production": raise HTTPException(404,"Not found")
@app.get("/api/dev/profile")
def dev_profile(db:Session=Depends(get_db)): demo_guard(); return profile_data(dev_user(db),db)
@app.get("/api/dev/inventory")
def dev_inventory(db:Session=Depends(get_db)):
    demo_guard(); u=dev_user(db); inv=db.query(InventoryItem).filter_by(user_id=u.id).all(); out=[]
    for r in inv:
        i=db.query(GameItem).filter_by(id=r.item_id).first(); out.append({"inventory_id":r.id,"id":i.id,"name":i.name,"rarity":i.rarity,"collection":i.collection,"icon":i.icon,"level":r.level,"favorite":r.favorite})
    return {"items":out,"page":1,"limit":30,"total":len(out)}
@app.get("/api/dev/collections")
def dev_collections(db:Session=Depends(get_db)): demo_guard(); return collections(dev_user(db),db)
@app.get("/api/dev/containers")
def dev_containers(db:Session=Depends(get_db)): demo_guard(); return CONTAINERS
@app.post("/api/dev/containers/{container_id}/open")
def dev_open(container_id:str,db:Session=Depends(get_db)): demo_guard(); return open_container(container_id,dev_user(db),db)
@app.get("/api/dev/tasks")
def dev_tasks(db:Session=Depends(get_db)): demo_guard(); return tasks(dev_user(db),db)
@app.post("/api/dev/tasks/{task_id}/claim")
def dev_claim(task_id:int,db:Session=Depends(get_db)): demo_guard(); return claim_task(task_id,dev_user(db),db)
@app.post("/api/dev/rewards/daily/claim")
def dev_daily(db:Session=Depends(get_db)): demo_guard(); return daily_claim(dev_user(db),db)
@app.get("/api/dev/shop/items")
def dev_shop(): return SHOP
@app.post("/api/dev/shop/purchase")
def dev_buy(item_id:int,db:Session=Depends(get_db)): demo_guard(); return purchase(PurchaseInput(item_id=item_id),dev_user(db),db)
@app.get("/api/dev/ratings")
def dev_ratings(db:Session=Depends(get_db)): demo_guard(); return ratings(dev_user(db),db)
