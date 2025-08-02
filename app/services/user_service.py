# 프로필 조회·수정

from sqlalchemy.orm import Session, joinedload
from app.models import User, UserProfile, School

# def get_user_profile(db: Session, user_id: str):
#     return db.query(UserProfile).options(joinedload(UserProfile.school)).filter_by(user_id=user_id).first()

def get_user_profile(db: Session, user_id: str):
    return db.query(UserProfile)\
        .options(
            joinedload(UserProfile.school),  # 학교 이름/코드 접근용
            joinedload(UserProfile.user)     # 사용자 이름 접근용
        )\
        .filter_by(user_id=user_id)\
        .first()


def update_user_profile(db: Session, user_id: str, updates: dict):
    user = db.query(User).filter_by(id=user_id).first()
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    
    if "email" in updates:
        user.email = updates["email"]
    if "phone" in updates:
        user.phone = updates["phone"]
    if "name" in updates:
        profile.username = updates["name"]
    if "gender" in updates:
        profile.gender = updates["gender"]
    
    db.commit()
    return user, profile

def get_class_ranking(db: Session, profile: UserProfile):
    
    classmates = db.query(UserProfile)\
        .options(joinedload(UserProfile.user))\
        .filter_by(
            school_id=profile.school_id,
            grade=profile.grade,
            class_num=profile.class_num
        ).all()

    ranked = sorted(classmates, key=lambda x: x.score or 0, reverse=True)

    my_rank = None
    for idx, p in enumerate(ranked):
        if p.user_id == profile.user_id:
            my_rank = idx + 1
    return ranked, my_rank
