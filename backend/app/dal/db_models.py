from typing import Optional
import datetime

from sqlalchemy import ARRAY, BigInteger, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, REAL, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Articles(Base):
    __tablename__ = 'articles'
    __table_args__ = (
        PrimaryKeyConstraint('article_id', name='articles_pkey'),
        UniqueConstraint('url', name='articles_url_key'),
        {'schema': 'public'}
    )

    article_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ingested_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    title: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    language: Mapped[Optional[str]] = mapped_column(Text)
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    reading_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    detected_published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    authors: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))

    article_metadata: Mapped[list['ArticleMetadata']] = relationship('ArticleMetadata', back_populates='article')
    article_summary: Mapped[list['ArticleSummary']] = relationship('ArticleSummary', back_populates='article')
    entities: Mapped[list['Entities']] = relationship('Entities', back_populates='article')
    relationships: Mapped[list['Relationships']] = relationship('Relationships', back_populates='article')


class ArticleMetadata(Base):
    __tablename__ = 'article_metadata'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='article_metadata_article_id_fkey'),
        PrimaryKeyConstraint('metadata_id', name='article_metadata_pkey'),
        Index('ix_article_metadata_article', 'article_id'),
        Index('ix_article_metadata_prop', 'article_id', 'prop_name'),
        {'schema': 'public'}
    )

    metadata_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prop_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    prop_value: Mapped[Optional[str]] = mapped_column(Text)

    article: Mapped['Articles'] = relationship('Articles', back_populates='article_metadata')


class ArticleSummary(Base):
    __tablename__ = 'article_summary'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='article_summary_article_id_fkey'),
        PrimaryKeyConstraint('summary_id', name='article_summary_pkey'),
        UniqueConstraint('article_id', 'prop_name', name='article_summary_article_id_prop_name_key'),
        Index('ix_article_summary_article', 'article_id'),
        {'schema': 'public'}
    )

    summary_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prop_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    prop_value: Mapped[Optional[str]] = mapped_column(Text)

    article: Mapped['Articles'] = relationship('Articles', back_populates='article_summary')


class Entities(Base):
    __tablename__ = 'entities'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='entities_article_id_fkey'),
        PrimaryKeyConstraint('entity_id', name='entities_pkey'),
        UniqueConstraint('article_id', 'entity_name', 'entity_type', name='entities_article_id_entity_name_entity_type_key'),
        Index('ix_entities_article', 'article_id'),
        Index('ix_entities_canonical', 'canonical_id'),
        {'schema': 'public'}
    )

    entity_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entity_name: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    canonical_id: Mapped[Optional[str]] = mapped_column(Text)
    salience: Mapped[Optional[float]] = mapped_column(REAL)
    mentions: Mapped[Optional[str]] = mapped_column(Text)

    article: Mapped['Articles'] = relationship('Articles', back_populates='entities')
    relationships_object_entity: Mapped[list['Relationships']] = relationship('Relationships', foreign_keys='[Relationships.object_entity_id]', back_populates='object_entity')
    relationships_subject_entity: Mapped[list['Relationships']] = relationship('Relationships', foreign_keys='[Relationships.subject_entity_id]', back_populates='subject_entity')


class Relationships(Base):
    __tablename__ = 'relationships'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='relationships_article_id_fkey'),
        ForeignKeyConstraint(['object_entity_id'], ['public.entities.entity_id'], ondelete='CASCADE', name='relationships_object_entity_id_fkey'),
        ForeignKeyConstraint(['subject_entity_id'], ['public.entities.entity_id'], ondelete='CASCADE', name='relationships_subject_entity_id_fkey'),
        PrimaryKeyConstraint('relationship_id', name='relationships_pkey'),
        Index('ix_relationships_article', 'article_id'),
        Index('ix_relationships_object', 'object_entity_id'),
        Index('ix_relationships_subject', 'subject_entity_id'),
        {'schema': 'public'}
    )

    relationship_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    subject_entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    object_entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    predicate: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    confidence: Mapped[Optional[float]] = mapped_column(REAL)
    evidence_span: Mapped[Optional[str]] = mapped_column(Text)

    article: Mapped['Articles'] = relationship('Articles', back_populates='relationships')
    object_entity: Mapped['Entities'] = relationship('Entities', foreign_keys=[object_entity_id], back_populates='relationships_object_entity')
    subject_entity: Mapped['Entities'] = relationship('Entities', foreign_keys=[subject_entity_id], back_populates='relationships_subject_entity')
