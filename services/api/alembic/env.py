from alembic import context
from sqlalchemy import engine_from_config, pool
from intentledger.models import Base
config=context.config
def run_migrations_online():
    with engine_from_config(config.get_section(config.config_ini_section),prefix="sqlalchemy.",poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection,target_metadata=Base.metadata); 
        with context.begin_transaction(): context.run_migrations()
run_migrations_online()
