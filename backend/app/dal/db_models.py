from typing import Optional
import datetime

from sqlalchemy import ARRAY, BigInteger, CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, REAL, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
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
    pipeline_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'::text"))
    title: Mapped[Optional[str]] = mapped_column(Text)
    published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    language: Mapped[Optional[str]] = mapped_column(Text)
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    reading_time_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    detected_published_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    authors: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))

    article_metadata: Mapped[list['ArticleMetadata']] = relationship('ArticleMetadata', back_populates='article')
    article_summary: Mapped[list['ArticleSummary']] = relationship('ArticleSummary', back_populates='article')
    article_workflow_runs: Mapped[list['ArticleWorkflowRuns']] = relationship('ArticleWorkflowRuns', back_populates='article')
    entities: Mapped[list['Entities']] = relationship('Entities', back_populates='article')
    relationships: Mapped[list['Relationships']] = relationship('Relationships', back_populates='article')
    workflow_step_executions: Mapped[list['WorkflowStepExecutions']] = relationship('WorkflowStepExecutions', back_populates='article')


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


class ArticleWorkflowRuns(Base):
    __tablename__ = 'article_workflow_runs'
    __table_args__ = (
        CheckConstraint("status = ANY (ARRAY['pending'::text, 'running'::text, 'completed'::text, 'failed'::text])", name='article_workflow_runs_status_check'),
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='article_workflow_runs_article_id_fkey'),
        PrimaryKeyConstraint('run_id', name='article_workflow_runs_pkey'),
        Index('ix_workflow_runs_article', 'article_id'),
        {'schema': 'public'}
    )

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    workflow_name: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_version: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'::text"))
    triggered_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    article: Mapped['Articles'] = relationship('Articles', back_populates='article_workflow_runs')
    workflow_step_executions: Mapped[list['WorkflowStepExecutions']] = relationship('WorkflowStepExecutions', back_populates='run')


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


class WorkflowStepExecutions(Base):
    __tablename__ = 'workflow_step_executions'
    __table_args__ = (
        CheckConstraint("status = ANY (ARRAY['pending'::text, 'running'::text, 'completed'::text, 'failed'::text, 'skipped'::text])", name='workflow_step_executions_status_check'),
        ForeignKeyConstraint(['article_id'], ['public.articles.article_id'], ondelete='CASCADE', name='workflow_step_executions_article_id_fkey'),
        ForeignKeyConstraint(['run_id'], ['public.article_workflow_runs.run_id'], ondelete='CASCADE', name='workflow_step_executions_run_id_fkey'),
        PrimaryKeyConstraint('step_exec_id', name='workflow_step_executions_pkey'),
        Index('ix_step_exec_article', 'article_id'),
        Index('ix_step_exec_run', 'run_id'),
        {'schema': 'public'}
    )

    step_exec_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    article_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    step_name: Mapped[str] = mapped_column(Text, nullable=False)
    celery_task_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'::text"))
    celery_task_id: Mapped[Optional[str]] = mapped_column(Text)
    config_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    article: Mapped['Articles'] = relationship('Articles', back_populates='workflow_step_executions')
    run: Mapped['ArticleWorkflowRuns'] = relationship('ArticleWorkflowRuns', back_populates='workflow_step_executions')
