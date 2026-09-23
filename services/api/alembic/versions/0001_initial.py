"""initial schema
Revision ID: 0001
"""
from alembic import op
revision="0001"; down_revision=None
def upgrade():
    from intentledger.models import Base
    bind=op.get_bind(); Base.metadata.create_all(bind)
def downgrade():
    from intentledger.models import Base
    Base.metadata.drop_all(op.get_bind())
