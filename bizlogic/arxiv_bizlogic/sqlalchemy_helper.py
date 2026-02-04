import typing
import datetime
from calendar import timegm

from sqlalchemy import Integer, String, Text, func, cast, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import update
from pydantic import BaseModel
from .database import is_column_latin1

Base = declarative_base()

def update_model_fields(session: Session, model: Base,
                        data: dict,
                        updating_fields: typing.Set[str] = {},
                        handlers: typing.Dict[str, typing.Callable] = {},
                        primary_key_field: str = None,
                        primary_key_value: typing.Any = None,
                        on_update: typing.Callable = None,
                        ) -> bool:
    """
    Update model fields with type-aware data conversion and MySQL latin1 charset handling.
    
    Args:
        session: SQLAlchemy session for database operations
        model: SQLAlchemy model instance to update
        data: Dictionary of field names and values to update
        updating_fields: Set of field names that are allowed to be updated
        handlers: Custom field handlers for special processing
        primary_key_field: Primary key field name (auto-detected if None)
        primary_key_value: Primary key value (extracted from model if None)
        on_update: Callback function called after each field update
    
    Type conversions:
    - Boolean to int: True->1, False->0 for integer columns
    - Date/datetime to epoch: Converts to Unix timestamp for integer columns
    - String to binary: UTF-8 encode for string columns with latin1 charset
    
    Only updates fields when old and new values differ.
    Uses direct SQL for latin1 string columns to avoid encoding issues.
    
    Returns:
        bool: True if any field was updated, False if no changes were made.
    """
    mysql_charset = 'latin1'  # Very unfortunate
    try:
        table_args = getattr(model, "__table_args__")
        meta = {}
        if isinstance(table_args, dict):
            meta = table_args
        elif isinstance(table_args, tuple):
            for arg in table_args:
                if isinstance(arg, dict):
                    meta = arg
                    break
        mysql_charset = meta.get("mysql_charset", "latin1")
    except AttributeError:
        pass

    charset = "latin1" if mysql_charset == "latin1" else "utf-8"

    # Auto-detect primary key if not provided
    if primary_key_field is None:
        primary_keys = [col.name for col in model.__table__.primary_key.columns]
        if primary_keys:
            primary_key_field = primary_keys[0]  # Use first primary key
        else:
            primary_key_field = 'id'  # Default fallback
    
    # Get primary key value if not provided
    if primary_key_value is None:
        primary_key_value = getattr(model, primary_key_field, None)

    any_changes = False
    
    for key, value in data.items():
        if key not in updating_fields:
            continue
        handler = handlers.get(key, None)
        if handler:
            value = handler(session, model, key, value)
            continue
        
        # Get column information
        if hasattr(model, key):
            column = getattr(model.__table__.columns, key, None)
            if column is not None:
                column_type = column.type
                direct_update = False
                
                # Convert based on column type and data type
                if isinstance(column_type, Integer):
                    # Boolean to int conversion for int columns
                    if isinstance(value, bool):
                        value = 1 if value else 0
                    # Date/datetime to epoch conversion for int columns
                    elif isinstance(value, (datetime.date, datetime.datetime)):
                        if isinstance(value, datetime.datetime):
                            value = int(timegm(value.utctimetuple()))
                        else:
                            # Convert date to datetime at midnight UTC
                            dt = datetime.datetime.combine(value, datetime.time.min)
                            value = int(timegm(dt.utctimetuple()))
                
                elif isinstance(column_type, (String, Text)):
                    # String column with latin1 charset - convert to binary
                    if charset == 'latin1':
                        if isinstance(value, str):
                            value = value.encode('utf-8')
                            direct_update = True
                        elif isinstance(value, bytes):
                            # The column value is fetched as bytes, or it is already encoded in utf-8
                            direct_update = True
                        else:
                            raise ValueError(f"Invalid value type for {key}: {type(value)}")

                direct_update = direct_update and is_column_latin1(session,
                                                                   model.__table__.name,
                                                                   column.name)

                # Only update if the value has changed
                if direct_update:
                    # Get current value as bytes using cast to LargeBinary
                    column = getattr(model.__table__.c, key)
                    result = session.execute(
                        session.query(cast(column, LargeBinary)).
                        filter(getattr(model.__table__.c, primary_key_field) == primary_key_value)
                    ).scalar()
                    current_value = result if result is not None else b''
                else:
                    current_value = getattr(model, key)

                if current_value != value:
                    any_changes = True
                    if direct_update:
                        session.execute(
                            update(model.__table__)
                            .where(getattr(model.__table__.c, primary_key_field) == primary_key_value)
                            .values({key: func.binary(value)})
                        )
                    else:
                        setattr(model, key, value)
                    if on_update:
                        on_update(session, model, key, current_value, value)
    
    return any_changes


def sa_model_to_pydandic_model(
        record,
        pyd_model: type[BaseModel],
        name_map: dict = None
        ) -> dict:
    """
    Convert SQLAlchemy model/row data to Pydantic model format with type conversions.
    
    Args:
        record: SQLAlchemy model instance or row object
        pyd_model: Pydantic model class to convert to
        name_map: Optional mapping of pydantic field names to SQLAlchemy column names
    
    Type conversions:
    - Bytes to string: UTF-8 decode for Pydantic string fields
    - Int to boolean: 1->True, 0->False for Pydantic bool fields  
    - Epoch to datetime: Unix timestamp to datetime for Pydantic datetime fields
    
    Returns:
        dict: Data dictionary compatible with the Pydantic model
    """
    if name_map is None:
        name_map = {}
    
    # Convert record to dict
    if hasattr(record, '__table__'):
        # SQLAlchemy model instance
        data = {col.name: getattr(record, col.name) for col in record.__table__.columns}
    else:
        # SQLAlchemy Row object - use _mapping for newer SQLAlchemy or iterate keys
        if hasattr(record, '_mapping'):
            data = dict(record._mapping)
        else:
            # Fallback for older Row objects
            data = {key: record[key] for key in record.keys()}
    
    result = {}
    for field_name, field_info in pyd_model.model_fields.items():
        column_name = name_map.get(field_name, field_name)
        value = data.get(column_name, None)
        
        if value is None:
            result[field_name] = None
            continue
            
        field_type = field_info.annotation
        
        # Handle bytes to string conversion for Pydantic string fields
        if field_type == str and isinstance(value, bytes):
            result[field_name] = value.decode('utf-8')
        # Handle int to boolean conversion for Pydantic bool fields
        elif field_type == bool and isinstance(value, int):
            result[field_name] = bool(value)
        # Handle epoch to datetime conversion for Pydantic datetime fields
        elif field_type == datetime.datetime and isinstance(value, int):
            result[field_name] = datetime.datetime.fromtimestamp(value)
        elif field_type == datetime.date and isinstance(value, int):
            result[field_name] = datetime.date.fromtimestamp(value)
        else:
            result[field_name] = value
    
    return result