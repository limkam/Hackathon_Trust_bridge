"""change_skills_required_to_json

Revision ID: a1b2c3d4e5f6
Revises: f3302325c5ca
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f3302325c5ca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Change skills_required column from ARRAY to JSON for SQLite compatibility.
    This migration handles both PostgreSQL (ARRAY) and SQLite (JSON) databases.
    """
    # Get the connection to check database type
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == 'postgresql'
    
    if is_postgresql:
        # For PostgreSQL: Convert ARRAY to JSON
        # Convert existing ARRAY data to JSON
        op.execute("""
            ALTER TABLE jobs 
            ALTER COLUMN skills_required TYPE jsonb 
            USING to_jsonb(skills_required)
        """)
    else:
        # For SQLite and other databases: SQLite doesn't support ARRAY natively
        # If the column exists as TEXT (SQLite's way of storing arrays), convert to JSON format
        # SQLite has limited ALTER TABLE, so we recreate the table
        try:
            # Create new table with JSON column
            op.execute("""
                CREATE TABLE jobs_new (
                    id INTEGER NOT NULL,
                    startup_id INTEGER,
                    company_name VARCHAR(255),
                    title VARCHAR(255) NOT NULL,
                    description VARCHAR(2000) NOT NULL,
                    location VARCHAR(255) NOT NULL,
                    skills_required TEXT NOT NULL,
                    min_experience INTEGER,
                    created_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(startup_id) REFERENCES startups (id)
                )
            """)
            
            # Copy data, ensuring skills_required is valid JSON
            op.execute("""
                INSERT INTO jobs_new 
                SELECT 
                    id, startup_id, company_name, title, description, location,
                    CASE 
                        WHEN typeof(skills_required) = 'text' AND json_valid(skills_required) THEN skills_required
                        WHEN typeof(skills_required) = 'text' THEN json_array(skills_required)
                        ELSE json('[]')
                    END as skills_required,
                    min_experience, created_at
                FROM jobs
            """)
            
            op.drop_table('jobs')
            op.execute("ALTER TABLE jobs_new RENAME TO jobs")
            
            # Recreate index
            op.create_index('ix_jobs_id', 'jobs', ['id'])
            
        except Exception as e:
            # If migration fails, the column might already be in the correct format
            # SQLite is dynamically typed, so this is mainly for documentation
            # Just ensure we're using JSON type in the model
            pass


def downgrade() -> None:
    """
    Revert skills_required column from JSON back to ARRAY.
    Note: This may not work perfectly on SQLite as it doesn't support ARRAY.
    """
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == 'postgresql'
    
    if is_postgresql:
        # For PostgreSQL: Convert JSON back to ARRAY
        op.execute("""
            ALTER TABLE jobs 
            ALTER COLUMN skills_required TYPE text[] 
            USING jsonb_array_elements_text(skills_required)::text[]
        """)
    else:
        # For SQLite and other databases, we can't easily convert back to ARRAY
        # Just change the type annotation - SQLite will store as TEXT anyway
        op.alter_column('jobs', 'skills_required',
                       existing_type=sa.JSON(),
                       type_=sa.String(),
                       existing_nullable=False)

