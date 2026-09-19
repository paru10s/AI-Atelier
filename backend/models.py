from sqlalchemy import Column, Integer, String
from database import Base


class Design(Base):
    __tablename__ = "designs"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String)
    room_type = Column(String)
    style = Column(String)
    prompt = Column(String)