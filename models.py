from database import Base
from sqlalchemy import Column, Integer, String, Boolean

class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    describe = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)