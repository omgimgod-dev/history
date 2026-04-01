from sqlalchemy import Column, Integer, String, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    is_admin = Column(Boolean, default=False)
    avatar = Column(String, default="/static/uploads/default_avatar.png")
    bio = Column(Text, default="")

    places = relationship("Place", back_populates="creator")  # creator of place
    reviews = relationship("Review", back_populates="user")
    forum_topics = relationship("ForumTopic", back_populates="creator")
    forum_posts = relationship("ForumPost", back_populates="creator")
    test_attempts = relationship("TestAttempt", back_populates="user")

class Place(Base):
    __tablename__ = "places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    coord_x = Column(Float)  # процент от ширины
    coord_y = Column(Float)  # процент от высоты
    map_image = Column(String, default="/static/uploads/city_map.jpg")  # основное фото города (одно для всех мест)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="places")
    reviews = relationship("Review", back_populates="place")
    image_pairs = relationship("ImagePair", back_populates="place", cascade="all, delete-orphan", order_by="ImagePair.pair_index")



class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    place = relationship("Place", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class ForumTopic(Base):
    __tablename__ = "forum_topics"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="forum_topics")
    posts = relationship("ForumPost", back_populates="topic")

class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("forum_topics.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("ForumTopic", back_populates="posts")
    creator = relationship("User", back_populates="forum_posts")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User")
    questions = relationship("Question", back_populates="test")
    attempts = relationship("TestAttempt", back_populates="test")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    question_text = Column(String)
    option1 = Column(String)
    option2 = Column(String)
    option3 = Column(String)
    option4 = Column(String)
    correct_option = Column(Integer)  # 1-4

    test = relationship("Test", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question")

class TestAttempt(Base):
    __tablename__ = "test_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    score = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="test_attempts")
    test = relationship("Test", back_populates="attempts")
    answers = relationship("UserAnswer", back_populates="attempt")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option = Column(Integer)
    is_correct = Column(Boolean)

    attempt = relationship("TestAttempt", back_populates="answers")
    question = relationship("Question", back_populates="user_answers")

class ImagePair(Base):
    __tablename__ = "image_pairs"
    id = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey("places.id"))
    modern_path = Column(String)   # путь к современному фото
    past_path = Column(String)     # путь к историческому фото
    pair_index = Column(Integer, default=0)  # для сортировки
    created_at = Column(DateTime, default=datetime.utcnow)

    place = relationship("Place", back_populates="image_pairs")