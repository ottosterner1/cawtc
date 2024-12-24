from flask_login import UserMixin
from app import db
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Enum as PGEnum
import pytz
import secrets
from flask_login import UserMixin
from app.extensions import db


uk_timezone = pytz.timezone('Europe/London')

class UserRole(Enum):
    COACH = 'coach'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'

class FieldType(Enum):
    TEXT = 'text'
    TEXTAREA = 'textarea'
    RATING = 'rating'
    SELECT = 'select'
    PROGRESS = 'progress'

    @classmethod
    def get_default_options(cls, field_type):
        defaults = {
            cls.TEXT: None,
            cls.TEXTAREA: None,
            cls.RATING: {
                'min': 1,
                'max': 5,
                'options': ['Needs Development', 'Developing', 'Competent', 'Proficient', 'Excellent']
            },
            cls.SELECT: {
                'options': []
            },
            cls.PROGRESS: {
                'options': ['Yes', 'Nearly', 'Not Yet']
            }
        }
        return defaults.get(field_type)

class CoachQualification(Enum):
    LEVEL_1 = 'Level 1'
    LEVEL_2 = 'Level 2'
    LEVEL_3 = 'Level 3'
    LEVEL_4 = 'Level 4'
    LEVEL_5 = 'Level 5'
    NONE = 'None'

class CoachRole(Enum):
    HEAD_COACH = 'Head Coach'
    SENIOR_COACH = 'Senior Coach'
    LEAD_COACH = 'Lead Coach'
    ASSISTANT_COACH = 'Assistant Coach'
    JUNIOR_COACH = 'Junior Coach'

class TennisClub(db.Model):
    __tablename__ = 'tennis_club'
    __table_args__ = (
        Index('idx_tennis_club_subdomain', 'subdomain', unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    users = db.relationship('User', back_populates='tennis_club', lazy='dynamic')
    groups = db.relationship('TennisGroup', back_populates='tennis_club', lazy='dynamic')
    teaching_periods = db.relationship('TeachingPeriod', back_populates='tennis_club', lazy='dynamic')
    students = db.relationship('Student', back_populates='tennis_club', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='tennis_club', lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = (
        Index('idx_user_email_lower', text('lower(email)'), unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True)
    name = db.Column(db.String(100))
    role = db.Column(PGEnum(UserRole, name='userrole'), nullable=False, default=UserRole.COACH)
    is_active = db.Column(db.Boolean, default=True)
    auth_provider = db.Column(db.String(20), default='email')
    auth_provider_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='users')
    reports = db.relationship('Report', back_populates='coach', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='coach', lazy='dynamic')

    @property
    def is_admin(self):
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

class TennisGroup(db.Model):
    __tablename__ = 'tennis_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='groups')
    reports = db.relationship('Report', foreign_keys='Report.group_id',back_populates='tennis_group')
    recommended_in_reports = db.relationship('Report',foreign_keys='Report.recommended_group_id',backref='recommended_group')
    programme_players = db.relationship('ProgrammePlayers', back_populates='tennis_group', lazy='dynamic')
    template_associations = db.relationship('GroupTemplate', back_populates='group', cascade='all, delete-orphan')
    templates = db.relationship('ReportTemplate', secondary='group_template', back_populates='groups', overlaps="template_associations,groups")

class TeachingPeriod(db.Model):
    __tablename__ = 'teaching_period'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='teaching_periods')
    reports = db.relationship('Report', back_populates='teaching_period', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='teaching_period', lazy='dynamic')

class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='students')
    reports = db.relationship('Report', back_populates='student', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='student', lazy='dynamic')

class ProgrammePlayers(db.Model):
    __tablename__ = 'programme_players'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=False)
    teaching_period_id = db.Column(db.Integer, db.ForeignKey('teaching_period.id'), nullable=False)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)
    report_submitted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    student = db.relationship('Student', back_populates='programme_players')
    coach = db.relationship('User', back_populates='programme_players')
    tennis_group = db.relationship('TennisGroup', back_populates='programme_players')
    teaching_period = db.relationship('TeachingPeriod', back_populates='programme_players')
    tennis_club = db.relationship('TennisClub', back_populates='programme_players')
    reports = db.relationship('Report', back_populates='programme_player', lazy='dynamic')

class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=False)
    recommended_group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=True)
    teaching_period_id = db.Column(db.Integer, db.ForeignKey('teaching_period.id'), nullable=False)
    programme_player_id = db.Column(db.Integer, db.ForeignKey('programme_players.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('report_template.id'), nullable=False)
    content = db.Column(JSONB, nullable=False)  # Structured report data
    date = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Email tracking fields
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime(timezone=True))
    last_email_status = db.Column(db.String(50))
    email_attempts = db.Column(db.Integer, default=0)

    # Relationships
    student = db.relationship('Student', back_populates='reports')
    coach = db.relationship('User', back_populates='reports')
    tennis_group = db.relationship('TennisGroup', 
                                 foreign_keys=[group_id],
                                 back_populates='reports')
    teaching_period = db.relationship('TeachingPeriod', back_populates='reports')
    programme_player = db.relationship('ProgrammePlayers', back_populates='reports')
    template = db.relationship('ReportTemplate', back_populates='reports')

    def mark_as_sent(self, status='Success'):
        self.email_sent = True
        self.email_sent_at = datetime.now(timezone.utc)
        self.last_email_status = status
        self.email_attempts += 1

    def is_student_under_18(self):
        """Check if the student is under 18"""
        if not self.student.date_of_birth:
            return True  # Default to safest option if no birth date
        
        today = datetime.now(timezone.utc).date()
        age = today.year - self.student.date_of_birth.year
        # Adjust age if birthday hasn't occurred this year
        if today.month < self.student.date_of_birth.month or \
           (today.month == self.student.date_of_birth.month and 
            today.day < self.student.date_of_birth.day):
            age -= 1
        return age < 18



class CoachDetails(db.Model):
    __tablename__ = 'coach_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Basic Information
    coach_number = db.Column(db.String(50), unique=True)
    qualification = db.Column(PGEnum(CoachQualification, name='coachqualification'), default=CoachQualification.NONE)
    date_of_birth = db.Column(db.Date)
    contact_number = db.Column(db.String(20))

    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_number = db.Column(db.String(20))

    # Address
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    postcode = db.Column(db.String(10))

    # Role and UTR
    coach_role = db.Column(PGEnum(CoachRole, name='coachrole'))
    utr_number = db.Column(db.String(20))

    # Accreditations
    accreditation_expiry = db.Column(db.DateTime(timezone=True))
    bcta_accreditation = db.Column(db.String(10), default='N/A')

    # DBS Information
    dbs_number = db.Column(db.String(50))
    dbs_issue_date = db.Column(db.DateTime(timezone=True))
    dbs_expiry = db.Column(db.DateTime(timezone=True))
    dbs_update_service_id = db.Column(db.String(50))

    # First Aid
    pediatric_first_aid = db.Column(db.Boolean, default=False)
    pediatric_first_aid_expiry = db.Column(db.DateTime(timezone=True))
    first_aid_expiry = db.Column(db.DateTime(timezone=True))

    # Safeguarding
    safeguarding_expiry = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=text('CURRENT_TIMESTAMP'))

    # Relationships
    user = db.relationship('User', backref=db.backref('coach_details', uselist=False))
    tennis_club = db.relationship('TennisClub', backref='coach_details')

    def get_expiry_status(self, expiry_date):
        if not expiry_date:
            return None

        current_time = datetime.now(uk_timezone)
        if expiry_date.tzinfo != uk_timezone:
            expiry_date = expiry_date.astimezone(uk_timezone)

        days_until_expiry = (expiry_date - current_time).days

        if days_until_expiry < 0:
            return ('expired', days_until_expiry)
        elif days_until_expiry <= 90:
            return ('warning', days_until_expiry)
        else:
            return ('valid', days_until_expiry)
        
class CoachInvitation(db.Model):
    __tablename__ = 'coach_invitation'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)
    invited_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used = db.Column(db.Boolean, default=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', backref='coach_invitations')
    invited_by = db.relationship('User', backref='sent_invitations')

    @staticmethod
    def create_invitation(email, tennis_club_id, invited_by_id, expiry_hours=48):
        token = secrets.token_urlsafe(32)
        # Create timezone-aware datetime objects
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expiry_hours)
        
        invitation = CoachInvitation(
            email=email,
            token=token,
            tennis_club_id=tennis_club_id,
            invited_by_id=invited_by_id,
            expires_at=expires_at
        )
        
        return invitation

    @property
    def is_expired(self):
        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
        return now > expires_at
    
class ReportTemplate(db.Model):
    __tablename__ = 'report_template'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tennis_club = db.relationship('TennisClub', backref='report_templates')
    created_by = db.relationship('User', backref='created_templates')
    sections = db.relationship('TemplateSection', back_populates='template', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='template')
    group_associations = db.relationship('GroupTemplate', 
                                      back_populates='template', 
                                      cascade='all, delete-orphan')
    groups = db.relationship('TennisGroup', 
                           secondary='group_template', 
                           back_populates='templates',
                           overlaps="group_associations,templates")

class TemplateSection(db.Model):
    __tablename__ = 'template_section'

    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('report_template.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    
    # Relationships
    template = db.relationship('ReportTemplate', back_populates='sections')
    fields = db.relationship('TemplateField', back_populates='section', cascade='all, delete-orphan')

class TemplateField(db.Model):
    __tablename__ = 'template_field'

    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('template_section.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    field_type = db.Column(db.Enum(FieldType), nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, nullable=False)
    options = db.Column(JSONB)  # For select/rating fields
    
    # Relationships
    section = db.relationship('TemplateSection', back_populates='fields')

class GroupTemplate(db.Model):
    __tablename__ = 'group_template'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('report_template.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    group = db.relationship('TennisGroup', 
                          back_populates='template_associations', 
                          overlaps="templates,groups")
    template = db.relationship('ReportTemplate', 
                             back_populates='group_associations',
                             overlaps="templates,groups")