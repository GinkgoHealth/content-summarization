import sys
sys.path.append(r"C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\src")
from db_session import *
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
import pandas as pd
# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

## This script calls upon functions and magic functions in db_session.py

Base = declarative_base()

class GPT_queue(Base):
    __tablename__ = 'gpt_queue'
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(255))
    body = mapped_column(Text)
    section = mapped_column(String(100))
    sent_to_sources = mapped_column(Boolean)
    publication = mapped_column(String(100))

class Sources(Base):
    __tablename__ = 'sources'
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(255))
    text = mapped_column(Text)
    abstract = mapped_column(Text)
    publication = mapped_column(String(100))
    authors = mapped_column(String(300))
    year = mapped_column(Integer)
    month = mapped_column(String(10))
    pub_volume = mapped_column(String(10))
    pub_issue = mapped_column(String(10))
    start_page = mapped_column(String(10))
    end_page = mapped_column(String(10))
    doi = mapped_column(String(50))
    section = mapped_column(String(100))
    mesh_headings = mapped_column(Text)
    summaries = relationship('Summaries', back_populates='sources')

class Prompts(Base):
    __tablename__ = 'prompts'
    id = mapped_column(Integer, primary_key=True)
    full_template = mapped_column(Text)
    system_role = mapped_column(String(300))
    prep_steps = mapped_column(Text)
    task = mapped_column(Text)
    edit_steps = mapped_column(Text)
    simplify_steps = mapped_column(Text)
    audience = mapped_column(String(200))
    format_steps = mapped_column(Text)

    summaries = relationship('Summaries', back_populates='prompts')
    
class Summaries(Base):
    __tablename__ = 'summaries'
    id = mapped_column(Integer, primary_key=True)
    timestamp = mapped_column(TIMESTAMP(timezone=True))
    original_summary = mapped_column(Text)
    rating_original_content = mapped_column(Integer) 
    simple_summary = mapped_column(Text)
    rating_simple_content = mapped_column(Integer) 
    original_headline = mapped_column(String(255))
    prompt_id = mapped_column(Integer, ForeignKey('prompts.id'), autoincrement=False)
    reference_id = mapped_column(Integer, ForeignKey('sources.id'), autoincrement=False)
    choice = mapped_column(Integer)
    model = mapped_column(String(70))
    temperature = mapped_column(Numeric)

    prompts = relationship('Prompts', back_populates='summaries')
    sources = relationship('Sources', back_populates='summaries')

@remote_sql_session
def get_from_queue(session, input_df, order_by='id', order='ASC'):
    """
    Return the matching records from the sources table as a pandas dataframe.

    Parameters:
    - input_df: A pandas DataFrame with the article records from the gpt_queue table or equivalent. Columns include 'title' and 'section'.
    - limit: The number of records to return.
    """
    def row_to_dict(row):
        result = session.query(Sources).filter_by(
            title=row['title'],
            section=row['section']
        ).limit(1).all()[0]
        
        sources_series = pd.Series({column.name: getattr(result, column.name) for column in result.__table__.columns})
        return sources_series

    sources_df = input_df.apply(row_to_dict, axis=1)
    ascending = True if order == 'ASC' else False
    sources_df.sort_values(order_by, ascending=ascending, inplace=True)
    return sources_df

@remote_sql_session
def get_table(
        session, query='SELECT *', table='publications', limit=None, order_by='id', order='ASC',
        filter_statement=None
        ):
    """
    Return a database table as a pandas dataframe.
    """
    query_statement = f'{query} from {table}'
    if filter_statement:
        query_statement += f' WHERE {filter_statement}'
    if order_by:
        query_statement += f' ORDER BY {order_by} {order}'
    if limit:
        query_statement += f' LIMIT {limit}'
    print(f'Query: {query_statement}')
    q = session.execute(text(query_statement))
    df = pd.DataFrame(q.fetchall())
    return df


def bulk_append(input_df, table='summaries'):
    """
    Add articles to the `sources` table in the database from a dataframe containing article text and metadata.
    
    Parameters:
    - references_df: pandas dataframe containing article text and metadata.

    Returns: None
    """
    @remote_sql_session
    def insert_rows(session):
        try:
            print(f'Adding {len(input_df)} rows to the database...')
            def insert_row(row):
                if table == 'sources':
                    with session.no_autoflush:
                        existing_record = session.query(Sources).filter_by(
                            title=row['title'],
                            doi=row['doi'],
                            section=row['section']
                        ).first()
                        if not existing_record:
                            data = Sources(
                                title=row['title'],
                                text=row['text'],
                                abstract=row['abstract'],
                                publication=row['journal'],
                                authors=row['authors'],
                                year=row['year'],
                                month=row['month'],
                                pub_volume=row['pub_volume'],
                                pub_issue=row['pub_issue'],
                                start_page=row['start_page'],
                                end_page=row['end_page'],
                                doi=row['doi'],
                                section=row['section'],
                                mesh_headings=row['mesh_headings']
                            )
                            session.add(data)
                            print(f'\t{row["title"]}')
                        else:
                            print(f'\t** Already exists in the database: {row["title"]}.')
                elif table == 'gpt_queue':
                    data = GPT_queue(
                        title=row['title'],
                        body=row['body'],
                        section=row['section'],
                        sent_to_sources=row['sent_to_sources'],
                        publication=row['publication']
                    )
                    session.add(data)
                    print(f'\t{row["title"]}')
                elif table == 'summaries':
                    prompt = session.query(Prompts).filter_by(
                        full_template=row['full_summarize_task'],
                        system_role=row['system_role'],
                    ).first()
                    if prompt:
                        prompt_id = prompt.id
                    else:
                        prompt = Prompts(
                            full_template=row['full_summarize_task'],
                            prep_steps=row['prep_step'],
                            task=row['summarize_task'],
                            edit_steps=row['edit_task'],
                            audience=row['simplify_audience'],
                            simplify_steps=row['simplify_task'],
                            format_steps=row['format_task'],
                            system_role=row['system_role']
                        )
                        session.add(prompt)
                        session.flush()
                        prompt_id = prompt.id

                    summary = Summaries(
                        timestamp=row['timestamp'],
                        original_summary=row['summary'],
                        simple_summary=row['simple_summary'],
                        original_headline=row['headline'],
                        prompt_id=prompt_id,
                        reference_id=row['reference_id'],
                        choice=row['choice'],
                        model=row['model'],
                        temperature=row['temperature']
                    )
                    session.add(summary)
                    print(f'\tReference #{row["reference_id"]}: {row["headline"]}')
                elif table == 'feed':
                    source = session.query(Feed).filter_by(
                        title=row['title'],
                        journal=row['journal'],
                        doi=row['doi']
                    ).first()
                    if source:
                        print(f'\tAlready exists in the database: {row["title"]}.')

            input_df.apply(insert_row, axis=1)

            session.commit()
            print("New records added successfully (if applicable)!")
        except Exception as e:
            session.rollback()
            print(f"Error adding data to the database: {str(e)}")
        finally:
            session.close()

    return insert_rows()

########## No longer needed
class Feed(Base):
    __tablename__ = 'feed'
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(255))
    abstract = mapped_column(Text)
    publication = mapped_column(String(100))
    url = mapped_column(String(255))
    authors = mapped_column(String(300))
    year = mapped_column(Integer)
    month = mapped_column(String(10))
    pub_volume = mapped_column(String(10))
    pub_issue = mapped_column(String(10))
    start_page = mapped_column(String(10))
    end_page = mapped_column(String(10))
    doi = mapped_column(String(50))