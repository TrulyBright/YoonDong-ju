import re
from typing import Union
from datetime import date, timedelta
import azure.functions as func
from FastAPIApp import app, models, crud, auth
from FastAPIApp.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from FastAPIApp import schemas, push_message
import nest_asyncio

nest_asyncio.apply()


class RegisterForm(BaseModel):
    portal_id: str
    portal_pw: str
    username: str
    password: str


class FindIDForm(BaseModel):
    portal_id: str
    portal_pw: str


class FindPWForm(BaseModel):
    portal_id: str
    portal_pw: str
    new_pw: str


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return func.AsgiMiddleware(app).handle(req, context)


@app.get("/club-information", response_model=models.ClubInformation)
async def get_club_information(db: Session = Depends(get_db)):
    return crud.get_club_information(db=db)


@app.put("/club-information", response_model=models.ClubInformation)
async def update_club_information(
    info: models.ClubInformationCreate,
    db: Session = Depends(get_db),
    modifier: schemas.Member = Depends(auth.get_current_member_board_only),
):
    return crud.update_club_information(db=db, info=info)


@app.get("/about", response_model=models.Post)
async def get_about(db: Session = Depends(get_db)):
    if existing := crud.get_post(db=db, type=models.PostType.about):
        return existing
    raise HTTPException(404, "소개가 아직 없습니다.")


@app.put("/about", response_model=models.Post)
async def update_about(
    about: models.PostCreate,
    db: Session = Depends(get_db),
    modifier: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if crud.get_post(db=db, type=models.PostType.about):
        return crud.update_post(
            db=db, type=models.PostType.about, post=about, modifier=modifier
        )
    return crud.create_post(
        db=db, author=modifier, post=about, type=models.PostType.about
    )


@app.get("/rules", response_model=models.Post)
async def get_rules(db: Session = Depends(get_db)):
    if existing := crud.get_post(db=db, type=models.PostType.rules):
        return existing
    raise HTTPException(404, "회칙이 아직 없습니다.")


@app.put("/rules", response_model=models.Post)
async def update_rules(
    rules: models.PostCreate,
    db: Session = Depends(get_db),
    modifier: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if crud.get_post(db=db, type=models.PostType.rules):
        return crud.update_post(
            db=db, type=models.PostType.rules, post=rules, modifier=modifier
        )
    return crud.create_post(
        db=db, author=modifier, post=rules, type=models.PostType.rules
    )


@app.get("/notices", response_model=list[models.PostOutline])
async def get_notices(
    skip: int = 0, limit: Union[int, None] = None, db: Session = Depends(get_db)
):
    return crud.get_posts(db=db, type=models.PostType.notice, skip=skip, limit=limit)


@app.get("/notices/recent", response_model=list[models.PostOutline])
async def get_recent_notices(limit: int = 4, db: Session = Depends(get_db)):
    return crud.get_posts(db=db, type=models.PostType.notice, limit=limit)


@app.get("/notices/count", response_model=int)
async def get_notice_count(db: Session = Depends(get_db)):
    return crud.get_post_count(db=db, type=models.PostType.notice)


@app.get("/notices/{no:int}", response_model=models.Post)
async def get_notice(no: int, db: Session = Depends(get_db)):
    if notice := crud.get_post(db=db, type=models.PostType.notice, no=no):
        return notice
    raise HTTPException(404, f"{no}번 글이 없습니다.")


@app.post("/notices", response_model=models.Post)
async def create_notice(
    post: models.PostCreate,
    db: Session = Depends(get_db),
    author: schemas.Member = Depends(auth.get_current_member_board_only),
):
    return crud.create_post(
        db=db, post=post, author=author, type=models.PostType.notice
    )


@app.put("/notices/{no:int}", response_model=models.Post)
async def update_notice(
    no: int,
    post: models.PostCreate,
    db: Session = Depends(get_db),
    modifier: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if updated := crud.update_post(db=db, post=post, modifier=modifier, no=no):
        return updated
    raise HTTPException(404, f"{no}번 글이 없습니다.")


@app.delete("/notices/{no:int}")
async def delete_notice(
    no: int,
    db: Session = Depends(get_db),
    deleter: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if not crud.delete_post(db=db, type=models.PostType.notice, no=no):
        raise HTTPException(404, f"{no}번 글이 없습니다.")


@app.get("/members", response_model=list[models.Member])
async def get_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    accessor: schemas.Member = Depends(auth.get_current_member_board_only),
):
    return crud.get_members(db, skip, limit)


@app.get("/members/{student_id:str}", response_model=models.Member)
async def get_member(
    student_id: str,
    db: Session = Depends(get_db),
    accessing: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if db_member := crud.get_member(db, student_id):
        return db_member
    raise HTTPException(404, "가입되지 않은 학번입니다.")


@app.get("/me", response_model=models.Member)
async def get_myself(
    db: Session = Depends(get_db), me: schemas.Member = Depends(auth.get_current_member)
):
    return me


@app.put("/members/{student_id:str}", response_model=models.Member)
async def update_member(
    student_id: str,
    member: models.MemberModify,
    db: Session = Depends(get_db),
    author: schemas.Member = Depends(auth.get_current_member_board_only),
):
    return crud.update_member(db=db, student_id=student_id, member=member)


@app.delete("/members/{student_id:str}")
async def delete_member(
    student_id: str,
    db: Session = Depends(get_db),
    deleter: schemas.Member = Depends(auth.get_current_member),
):
    if deleter.student_id != student_id and deleter.role not in {
        models.Role.board,
        models.Role.president,
    }:
        raise HTTPException(403)
    if not crud.delete_member(db=db, student_id=student_id):
        raise HTTPException(404)


@app.get("/uploaded/{id}")
async def get_uploaded_file(id: int, db: Session = Depends(get_db)):
    if uploaded := crud.get_uploaded_file(db=db, id=id):
        return Response(content=uploaded.binary, media_type=uploaded.content_type)
    raise HTTPException(404)


@app.post("/uploaded", response_model=models.UploadedFile)
async def create_uploaded_file(
    uploaded: UploadFile,
    db: Session = Depends(get_db),
    uploader=Depends(auth.get_current_member_board_only),
):
    return await crud.create_uploaded_file(db=db, file=uploaded)


@app.delete("/uploaded/{id}")
async def delete_uploaded_file(
    id: int,
    db: Session = Depends(get_db),
    deleter=Depends(auth.get_current_member_board_only),
):
    if not await crud.delete_uploaded_file(db=db, id=id):
        raise HTTPException(404)


@app.get("/uploaded/{id}/info", response_model=models.UploadedFile)
async def get_uploaded_file_info(id: int, db: Session = Depends(get_db)):
    return crud.get_uploaded_file(db=db, id=id)


@app.get("/magazines", response_model=list[models.MagazineOutline])
async def get_magazines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_magazines(db=db, skip=skip, limit=limit)


@app.get("/magazines/recent", response_model=list[models.MagazineOutline])
async def get_recent_magazines(limit: int = 4, db: Session = Depends(get_db)):
    return crud.get_magazines(db=db, skip=0, limit=limit)


@app.get("/magazines/{published}", response_model=models.Magazine)
async def get_magazine(published: date, db: Session = Depends(get_db)):
    if volume := crud.get_magazine(db=db, published=published):
        return volume
    raise HTTPException(404, f"{published}에 발행된 문집이 없습니다.")


@app.post("/magazines", response_model=models.Magazine)
async def create_magazine(
    magazine: models.MagazineCreate,
    db: Session = Depends(get_db),
    publisher: schemas.Member = Depends(auth.get_current_member_board_only),
):
    return crud.create_magazine(db=db, magazine=magazine)


@app.put("/magazines/{published}", response_model=models.Magazine)
async def update_magazine(
    published: date,
    magazine: models.MagazineCreate,
    db: Session = Depends(get_db),
    publisher: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if updated := crud.update_magazine(db=db, published=published, magazine=magazine):
        return updated
    raise HTTPException(404, f"{published}에 발행된 문집이 없습니다.")


@app.delete("/magazines/{published}")
async def delete_magazine(
    published: date,
    db: Session = Depends(get_db),
    deleter: schemas.Member = Depends(auth.get_current_member_board_only),
):
    if not crud.delete_magazine(db=db, published=published):
        raise HTTPException(404, f"{published}에 발행된 문집이 없습니다.")


# @app.get("/classes", response_model=list[models.Class])
# async def get_classes(db: Session = Depends(get_db)):
#     # Depends() not working at startup.
#     return crud.get_classes(db=db) or crud.create_classes_with_default_values(db=db)


# @app.get("/classes/{class_name}", response_model=models.Class)
# async def get_class(class_name: models.ClassName, db: Session = Depends(get_db)):
#     return crud.get_class(db=db, name=class_name)


# @app.put("/classes/{class_name}", response_model=models.Class)
# async def update_class(
#     class_name: models.ClassName,
#     class_data: models.ClassCreate,
#     db: Session = Depends(get_db),
#     modifier: schemas.Member = Depends(auth.get_current_member_board_only),
# ):
#     return crud.update_class(db=db, name=class_name, class_data=class_data)


# @app.get(
#     "/classes/{class_name}/records", response_model=list[models.ClassRecordOutline]
# )
# async def get_class_records(
#     class_name: models.ClassName,
#     skip: int = 0,
#     limit: int = 100,
#     db: Session = Depends(get_db),
# ):
#     return crud.get_class_records(db=db, class_name=class_name, skip=skip, limit=limit)


# @app.get(
#     "/classes/{class_name}/records/{conducted}",
#     response_model=Union[models.ClassRecord, models.ClassRecord],
# )
# async def get_class_record(
#     class_name: models.ClassName,
#     conducted: date,
#     db: Session = Depends(get_db),
#     accessing: schemas.Member = Depends(auth.get_current_member),
# ):
#     if record := crud.get_class_record(
#         db=db, class_name=class_name, conducted=conducted
#     ):
#         return record
#     raise HTTPException(404, f"{conducted}에 진행한 활동이 없습니다.")


# @app.post("/classes/{class_name}/records", response_model=models.ClassRecord)
# async def create_class_record(
#     class_name: models.ClassName,
#     record: models.ClassRecordCreate,
#     db: Session = Depends(get_db),
#     recorder: schemas.Member = Depends(auth.get_current_member_board_only),
# ):
#     return crud.create_class_record(
#         db=db, class_name=class_name, moderator=recorder, record=record
#     )


# @app.put(
#     "/classes/{class_name}/records/{conducted}", response_model=models.ClassRecord
# )
# async def update_class_record(
#     class_name: models.ClassName,
#     conducted: date,
#     record: models.ClassRecordCreate,
#     db: Session = Depends(get_db),
#     recorder: schemas.Member = Depends(auth.get_current_member_board_only),
# ):
#     if updated := crud.update_class_record(
#         db=db, class_name=class_name, conducted=conducted, record=record
#     ):
#         return updated
#     raise HTTPException(404, f"{conducted}에 진행한 활동이 없습니다.")


# @app.delete("/classes/{class_name}/records/{conducted}")
# async def delete_class_record(
#     class_name: models.ClassName,
#     conducted: date,
#     recorder: schemas.Member = Depends(auth.get_current_member_board_only),
#     db: Session = Depends(get_db),
# ):
#     if not crud.delete_class_record(db=db, class_name=class_name, conducted=conducted):
#         raise HTTPException(404, f"{conducted}에 진행된 활동이 없습니다.")


@app.post("/register", response_model=models.Member)
async def register(form: RegisterForm, db: Session = Depends(get_db)):
    real_name = auth.get_student_information(
        id=form.portal_id, pw=form.portal_pw).name
    if crud.get_member(db=db, student_id=form.portal_id):
        raise HTTPException(status_code=409, detail="이미 이 학번으로 가입된 계정이 있습니다.")
    if crud.get_member_by_username(db=db, username=form.username):
        raise HTTPException(status_code=409, detail="이미 있는 ID입니다.")
    if not re.match(auth.password_pattern, form.password):
        raise HTTPException(status_code=422, detail="비밀번호가 안전하지 않습니다.")
    if not re.match(auth.id_pattern, form.username):
        raise HTTPException(status_code=422, detail="이런 ID는 쓸 수 없습니다.")
    return crud.create_member(
        db=db,
        student_id=form.portal_id,
        member=models.MemberCreate(
            real_name=real_name, username=form.username, password=form.password
        ),
    )


@app.post("/token")
async def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    member = auth.authenticate(
        db=db, username=form.username, password=form.password)
    if not member:
        raise HTTPException(
            status_code=401,
            detail="ID나 비밀번호가 틀렸습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=30)
    access_token, expires_at = auth.create_access_token(
        data={"sub": member.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_at": expires_at,
    }


@app.post("/find/id")
async def find_ID(form: FindIDForm, db: Session = Depends(get_db)):
    if auth.is_yonsei_member(form.portal_id, form.portal_pw):
        if member := crud.get_member(db=db, student_id=form.portal_id):
            return member.username
        raise HTTPException(404)


@app.post("/find/pw")
async def find_PW(form: FindPWForm, db: Session = Depends(get_db)):
    if not auth.is_yonsei_member(form.portal_id, form.portal_pw):
        raise HTTPException(401)
    if crud.update_member(db=db, student_id=form.portal_id, member=models.MemberModify(password=form.new_pw)) is None:
        raise HTTPException(404)


@app.post("/club-members")
async def handle_club_member_registration(
    model: models.ClubMemberCreate, db=Depends(get_db)
):
    if student_information := auth.is_yonsei_member(model.portal_id, model.portal_pw):
        push_message.send_new_club_member_message(
            student_information, db=db, tel=model.tel, invite_informal_chat=model.invite_informal_chat)
    else:
        raise HTTPException(
            status_code=403, detail="해당 ID와 비밀번호로 연세포탈에 로그인할 수 없습니다.")
