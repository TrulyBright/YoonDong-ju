import re
from functools import lru_cache
from datetime import date, datetime, timedelta
from typing import Union
from uuid import UUID
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from sqlalchemy.orm import Session
from pydantic import UUID5, BaseModel, BaseSettings
import models
import crud
import auth
import schemas
from database import SessionLocal, engine, get_db

schemas.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.0.4"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
Path("uploaded").mkdir(exist_ok=True)


class RegisterForm(BaseModel):
    portal_id: str
    portal_pw: str
    real_name: str
    username: str
    password: str


@app.get("/club-information", response_model=models.ClubInformation)
async def get_club_information(db: Session = Depends(get_db)):
    return crud.get_club_information(db=db)


@app.put("/club-information", response_model=models.ClubInformation)
async def update_club_information(info: models.ClubInformationCreate, db: Session = Depends(get_db), modifier: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.update_club_information(db=db, info=info)


@app.get("/recent-notices", response_model=list[models.PostOutline])
async def get_recent_notices(limit: int = 4, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, type=models.PostType.notice, limit=limit)


@app.get("/recent-magazines", response_model=list[models.MagazineOutline])
async def get_recent_magazines(limit: int = 4, db: Session = Depends(get_db)):
    return crud.get_magazines(db=db, skip=0, limit=limit)


@app.get("/about", response_model=models.Post)
async def get_about(db: Session = Depends(get_db)):
    if existing := crud.get_post(db=db, type=models.PostType.about):
        return existing
    raise HTTPException(404, "????????? ?????? ????????????.")


@app.put("/about", response_model=models.Post)
async def update_about(about: models.PostCreate, db: Session = Depends(get_db), modifier: schemas.Member = Depends(auth.get_current_member_board_only)):
    if crud.get_post(db=db, type=models.PostType.about):
        return crud.update_post(db=db, type=models.PostType.about, post=about, modifier=modifier)
    return crud.create_post(db=db, author=modifier, post=about, type=models.PostType.about)


@app.get("/rules", response_model=models.Post)
async def get_rules(db: Session = Depends(get_db)):
    if existing := crud.get_post(db=db, type=models.PostType.rules):
        return existing
    raise HTTPException(404, "????????? ?????? ????????????.")


@app.put("/rules", response_model=models.Post)
async def update_rules(rules: models.PostCreate, db: Session = Depends(get_db), modifier: schemas.Member = Depends(auth.get_current_member_board_only)):
    if crud.get_post(db=db, type=models.PostType.rules):
        return crud.update_post(db=db, type=models.PostType.rules, post=rules, modifier=modifier)
    return crud.create_post(db=db, author=modifier, post=rules, type=models.PostType.rules)


@app.get("/notices", response_model=list[models.PostOutline])
async def get_notices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, type=models.PostType.notice, skip=skip, limit=limit)


@app.get("/notices/{no:int}", response_model=models.Post)
async def get_notice(no: int, db: Session = Depends(get_db)):
    if notice := crud.get_post(db=db, type=models.PostType.notice, no=no):
        return notice
    raise HTTPException(404, f"{no}??? ?????? ????????????.")


@app.post("/notices", response_model=models.Post)
async def create_notice(post: models.PostCreate, db: Session = Depends(get_db), author: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.create_post(db=db, post=post, author=author, type=models.PostType.notice)


@app.patch("/notices/{no:int}", response_model=models.Post)
async def update_notice(no: int, post: models.PostCreate, db: Session = Depends(get_db), modifier: schemas.Member = Depends(auth.get_current_member_board_only)):
    if updated := crud.update_post(db=db, post=post, modifier=modifier, no=no):
        return updated
    raise HTTPException(404, f"{no}??? ?????? ????????????.")


@app.delete("/notices/{no:int}")
async def delete_notice(no: int, db: Session = Depends(get_db), deleter: schemas.Member = Depends(auth.get_current_member_board_only)):
    if not crud.delete_post(db=db, type=models.PostType.notice, no=no):
        raise HTTPException(404, f"{no}??? ?????? ????????????.")


@app.get("/members", response_model=list[models.Member])
async def get_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), accessor: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.get_members(db, skip, limit)


@app.get("/members/{student_id:int}", response_model=models.Member)
async def get_member(student_id: int, db: Session = Depends(get_db), accessing: schemas.Member = Depends(auth.get_current_member_board_only)):
    if db_member := crud.get_member(db, student_id):
        return db_member
    raise HTTPException(404, "???????????? ?????? ???????????????.")


@app.get("/me", response_model=models.Member)
async def get_myself(db: Session = Depends(get_db), me: schemas.Member = Depends(auth.get_current_member)):
    return me


@app.patch("/members/{student_id:int}", response_model=models.Member)
async def update_member(student_id: int, member: models.MemberModify, db: Session = Depends(get_db), author: schemas.Member = Depends(auth.get_current_member)):
    if author.role not in {
        models.Role.board,
        models.Role.president
    } and member.role is not None:
        raise HTTPException(403)
    try:
        return crud.update_member(db=db, student_id=student_id, member=member)
    except ValueError:
        raise HTTPException(422, "??????????????? ????????? ?????? ????????????.")


@app.delete("/members/{student_id:int}")
async def delete_member(student_id: int, db: Session = Depends(get_db), deleter: schemas.Member = Depends(auth.get_current_member)):
    if deleter.student_id != student_id and deleter.role not in {models.Role.board, models.Role.president}:
        raise HTTPException(403)
    if not crud.delete_member(db=db, student_id=student_id):
        raise HTTPException(404)


@app.get("/uploaded/{uuid}")
async def get_uploaded_file(uuid: UUID, db: Session = Depends(get_db)):
    if uploaded := crud.get_uploaded_file(db=db, uuid=uuid):
        return FileResponse("uploaded/"+str(uuid), filename=uploaded.name, media_type=uploaded.content_type)
    raise HTTPException(404)


@app.post("/uploaded", response_model=models.UploadedFile)
async def create_uploaded_file(uploaded: UploadFile, db: Session = Depends(get_db), uploader=Depends(auth.get_current_member_board_only)):
    return await crud.create_uploaded_file(db=db, file=uploaded)


@app.delete("/uploaded/{uuid}")
async def delete_uploaded_file(uuid: UUID, db: Session = Depends(get_db), deleter=Depends(auth.get_current_member_board_only)):
    if not await crud.delete_uploaded_file(db=db, uuid=uuid):
        raise HTTPException(404)


@app.get("/uploaded-info/{uuid}", response_model=models.UploadedFile)
async def get_uploaded_file_info(uuid: UUID, db: Session = Depends(get_db)):
    return crud.get_uploaded_file(db=db, uuid=uuid)


@app.get("/magazines", response_model=list[models.MagazineOutline])
async def get_magazines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_magazines(db=db, skip=skip, limit=limit)


@app.get("/magazines/{published}", response_model=models.Magazine)
async def get_magazine(published: date, db: Session = Depends(get_db)):
    if volume := crud.get_magazine(db=db, published=published):
        return volume
    raise HTTPException(404, f"{published}??? ????????? ????????? ????????????.")


@app.post("/magazines", response_model=models.Magazine)
async def create_magazine(magazine: models.MagazineCreate, db: Session = Depends(get_db), publisher: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.create_magazine(db=db, magazine=magazine)


@app.patch("/magazines/{published}", response_model=models.Magazine)
async def update_magazine(published: date, magazine: models.MagazineCreate, db: Session = Depends(get_db), publisher: schemas.Member = Depends(auth.get_current_member_board_only)):
    if updated := crud.update_magazine(db=db, published=published, magazine=magazine):
        return updated
    raise HTTPException(404, f"{published}??? ????????? ????????? ????????????.")


@app.delete("/magazines/{published}")
async def delete_magazine(published: date, db: Session = Depends(get_db), deleter: schemas.Member = Depends(auth.get_current_member_board_only)):
    if not crud.delete_magazine(db=db, published=published):
        raise HTTPException(404, f"{published}??? ????????? ????????? ????????????.")


@app.get("/classes", response_model=list[models.Class])
async def get_classes(db: Session = Depends(get_db)):
    # Depends() not working at startup.
    return crud.get_classes(db=db) or crud.create_classes_with_default_values(db=db)


@app.get("/classes/{class_name}", response_model=models.Class)
async def get_class(class_name: models.ClassName, db: Session = Depends(get_db)):
    return crud.get_class(db=db, name=class_name)


@app.patch("/classes/{class_name}", response_model=models.Class)
async def update_class(class_name: models.ClassName, class_data: models.ClassCreate, db: Session = Depends(get_db), modifier: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.update_class(db=db, name=class_name, class_data=class_data)


@app.get("/classes/{class_name}/records", response_model=list[models.ClassRecordOutline])
async def get_class_records(class_name: models.ClassName, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_class_records(db=db, class_name=class_name, skip=skip, limit=limit)


@app.get("/classes/{class_name}/records/{conducted}", response_model=Union[models.ClassRecord, models.ClassRecord])
async def get_class_record(class_name: models.ClassName, conducted: date, db: Session = Depends(get_db), accessing: schemas.Member = Depends(auth.get_current_member)):
    if record := crud.get_class_record(db=db, class_name=class_name, conducted=conducted):
        return record
    raise HTTPException(404, f"{conducted}??? ????????? ????????? ????????????.")


@app.post("/classes/{class_name}/records", response_model=models.ClassRecord)
async def create_class_record(class_name: models.ClassName, record: models.ClassRecordCreate, db: Session = Depends(get_db), recorder: schemas.Member = Depends(auth.get_current_member_board_only)):
    return crud.create_class_record(db=db, class_name=class_name, moderator=recorder, record=record)


@app.patch("/classes/{class_name}/records/{conducted}", response_model=models.ClassRecord)
async def update_class_record(class_name: models.ClassName, conducted: date, record: models.ClassRecordCreate, db: Session = Depends(get_db), recorder: schemas.Member = Depends(auth.get_current_member_board_only)):
    if updated := crud.update_class_record(db=db, class_name=class_name, conducted=conducted, record=record):
        return updated
    raise HTTPException(404, f"{conducted}??? ????????? ????????? ????????????.")


@app.delete("/classes/{class_name}/records/{conducted}")
async def delete_class_record(class_name: models.ClassName, conducted: date, recorder: schemas.Member = Depends(auth.get_current_member_board_only), db: Session = Depends(get_db)):
    if not crud.delete_class_record(db=db, class_name=class_name, conducted=conducted):
        raise HTTPException(404, f"{conducted}??? ????????? ????????? ????????????.")


@app.post("/register", response_model=models.Member)
async def register(form: RegisterForm, db: Session = Depends(get_db)):
    if str(form.portal_id)[4] == "2":
        raise HTTPException(
            status_code=403,
            detail="???????????? ????????? ??? ????????????."
        )
    if not auth.is_yonsei_member(form.portal_id, form.portal_pw):
        raise HTTPException(
            status_code=403,
            detail="?????? ID??? ??????????????? ??????????????? ???????????? ??? ????????????."
        )
    if crud.get_member(db=db, student_id=form.portal_id):
        raise HTTPException(
            status_code=409,
            detail="?????? ??? ???????????? ????????? ????????? ????????????."
        )
    if crud.get_member_by_username(db=db, username=form.username):
        raise HTTPException(
            status_code=409,
            detail="?????? ?????? ID?????????."
        )
    if not re.match(auth.password_pattern, form.password):
        raise HTTPException(
            status_code=422,
            detail="??????????????? ???????????? ????????????."
        )
    if not re.match(auth.id_pattern, form.username):
        raise HTTPException(
            status_code=422,
            detail="?????? ID??? ??? ??? ????????????."
        )
    return crud.create_member(
        db=db,
        student_id=form.portal_id,
        member=models.MemberCreate(
            real_name=form.real_name,
            username=form.username,
            password=form.password
        )
    )


@app.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    member = auth.authenticate(
        db=db, username=form.username, password=form.password)
    if not member:
        raise HTTPException(
            status_code=401,
            detail="ID??? ??????????????? ???????????????.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = Authorize.create_access_token(member.username, expires_time=access_token_expires)
    refresh_token = Authorize.create_refresh_token(subject=member.username)
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "refresh_token": refresh_token,
        "expires_at": (datetime.now()+access_token_expires).timestamp()
    }


@app.post("/refresh")
def refresh(Authorize: AuthJWT = Depends()):
    """For accessing /refresh endpoint,
    remember to change access_token
    with refresh_token in the header
    Authorization: Bearer <refresh_token>
    """
    Authorize.jwt_refresh_token_required(auth_from="headers")

    current_user = Authorize.get_jwt_subject()
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = Authorize.create_access_token(current_user, expires_time=access_token_expires)
    return {
        "access_token": new_access_token,
        "expires_at": (datetime.now()+access_token_expires).timestamp()
    }
