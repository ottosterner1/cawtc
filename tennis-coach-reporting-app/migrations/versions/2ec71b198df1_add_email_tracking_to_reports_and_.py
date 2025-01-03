"""add_email_tracking_to_reports and removing email template

Revision ID: 2ec71b198df1
Revises: 5be3e38355b6
Create Date: 2024-12-20 18:40:36.493608

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2ec71b198df1'
down_revision = '5be3e38355b6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_templates')
    with op.batch_alter_table('report', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_sent', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_email_status', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('email_attempts', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('report', schema=None) as batch_op:
        batch_op.drop_column('email_attempts')
        batch_op.drop_column('last_email_status')
        batch_op.drop_column('email_sent_at')
        batch_op.drop_column('email_sent')

    op.create_table('email_templates',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('tennis_club_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('subject_template', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('body_template', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('recipient_type', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('is_default', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['tennis_club_id'], ['tennis_club.id'], name='email_templates_tennis_club_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='email_templates_pkey'),
    sa.UniqueConstraint('tennis_club_id', 'recipient_type', 'is_default', name='unique_default_template_per_type_club')
    )
    # ### end Alembic commands ###
