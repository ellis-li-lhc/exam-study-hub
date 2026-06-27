# 招生目录相关的数据库表模型。第一版先建「专业」这一组。
from sqlalchemy import ForeignKey, String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Major(Base):
    """专业表。对应前端 mvp.js 里的 majorOptions。"""
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)   # 如 "business"
    name: Mapped[str] = mapped_column(String(128))                           # 如 "工商管理"
    category: Mapped[str] = mapped_column(String(64))                        # 如 "经济管理类"

    # 一个专业有多门统考科目（1:N）。删除专业时，连带删除其科目。
    subjects: Mapped[list["MajorSubject"]] = relationship(
        back_populates="major",
        cascade="all, delete-orphan",
    )


class MajorSubject(Base):
    """专业↔统考科目（一个专业对应多门科目）。"""
    __tablename__ = "major_subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    major_id: Mapped[int] = mapped_column(
        ForeignKey("majors.id", ondelete="CASCADE"), index=True
    )
    subject: Mapped[str] = mapped_column(String(64))   # 如 "政治" / "英语" / "高等数学（二）"

    major: Mapped["Major"] = relationship(back_populates="subjects")


class Province(Base):
    """报考省份。对应前端 mvp.js 里的 provinceOptions。"""
    __tablename__ = "provinces"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)   # 如 "henan"
    name: Mapped[str] = mapped_column(String(64))                            # 如 "河南"
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)     # 报名提示文案


class Institution(Base):
    """招生院校。基础信息来自考试院投档线数据；
    city/学制/学费/教学点/学位条件等暂为空，后续从各院校招生简章逐校补充。"""
    __tablename__ = "institutions"
    __table_args__ = (UniqueConstraint("province_id", "code", name="uq_institution_province_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), index=True)          # 院校代码（省内唯一）
    name: Mapped[str] = mapped_column(String(128))
    province_id: Mapped[int] = mapped_column(ForeignKey("provinces.id"), index=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tuition: Mapped[int | None] = mapped_column(Integer, nullable=True)
    teaching_site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)

    scores: Mapped[list["AdmissionScore"]] = relationship(
        back_populates="institution", cascade="all, delete-orphan"
    )


class AdmissionScore(Base):
    """院校录取分数线。当前粒度为「院校 × 科类 × 投档线」（成考不公布逐专业线）。"""
    __tablename__ = "admission_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"), index=True
    )
    year: Mapped[int] = mapped_column(Integer)
    category_code: Mapped[str | None] = mapped_column(String(16), nullable=True)   # 科类码，如 1140
    category_name: Mapped[str] = mapped_column(String(64))                          # 科类名，如 专升本经管类
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)               # 投档分
    line_type: Mapped[str] = mapped_column(String(32))                              # 院校投档线 / 省控线...
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)          # 数据来源

    institution: Mapped["Institution"] = relationship(back_populates="scores")
