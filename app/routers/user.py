# /users/me 라우터 (프로필)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.dependencies import get_db, get_current_user
from app.models import User, UserProfile, QuizScore, School
from app.schemas.user import MyInfoResponse, UpdateMyInfoRequest, UpdateResponse, RankInfo, ClassRankingResponse
from app.services.auth_service import get_password_hash

router = APIRouter(prefix="/users/me", tags=["mypage"])


@router.get("", response_model=MyInfoResponse)
def get_my_info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile)\
        .options(joinedload(UserProfile.school))\
        .filter_by(user_id=user.id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="프로필 정보를 찾을 수 없습니다.")

    school_code = ""
    if profile.school:
        school_code = f"{profile.school.name}{profile.grade:02d}{profile.class_num:02d}"

    return MyInfoResponse(
        userId=str(user.id),
        loginId=user.email,
        name=profile.nickname,
        gender=profile.gender,
        schoolCode=school_code,
        phone=user.phone,
        email=user.email
    )


@router.put("", response_model=UpdateResponse)
def update_my_info(data: UpdateMyInfoRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.password and data.password != data.passwordConfirm:
        raise HTTPException(status_code=422, detail="비밀번호와 비밀번호 확인이 일치하지 않습니다")

    if data.loginId and data.loginId != user.email:
        if db.query(User).filter(User.email == data.loginId).first():
            raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다")
        user.email = data.loginId

    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=409, detail="이미 사용 중인 이메일입니다")
        user.email = data.email

    if data.password:
        user.password_hash = get_password_hash(data.password)

    if data.phone:
        user.phone = data.phone

    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="프로필 정보가 없습니다.")

    if data.name:
        profile.nickname = data.name
    if data.gender:
        profile.gender = data.gender

    db.commit()
    return UpdateResponse(message="사용자 정보가 성공적으로 수정되었습니다.")


@router.get("/classRank", response_model=ClassRankingResponse)
def get_class_ranking(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    if not profile:
        raise HTTPException(status_code=500, detail="프로필 정보를 찾을 수 없습니다.")

    same_class_profiles = db.query(UserProfile).filter(
        UserProfile.school_id == profile.school_id,
        UserProfile.grade == profile.grade,
        UserProfile.class_num == profile.class_num
    ).all()

    sorted_profiles = sorted(
        same_class_profiles,
        key=lambda p: p.score or 0,
        reverse=True
    )

    ranking_data = []
    my_rank_info = None

    for idx, p in enumerate(sorted_profiles, start=1):
        entry = RankInfo(
            userId=str(p.user_id),
            username=p.nickname,
            score=p.score or 0,
            rank=idx
        )
        ranking_data.append(entry)
        if p.user_id == user.id:
            my_rank_info = entry

    school = db.query(School).filter(School.id == profile.school_id).first()
    if not school:
        raise HTTPException(status_code=500, detail="학교 정보를 찾을 수 없습니다.")

    return ClassRankingResponse(
        classInfo={
            "schoolName": school.name,
            "grade": profile.grade,
            "classNumber": profile.class_num
        },
        myRank=my_rank_info,
        ranking=ranking_data
    )
