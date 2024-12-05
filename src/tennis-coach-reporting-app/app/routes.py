import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, TennisGroup, TeachingPeriod, Student, Report, UserRole, TennisClub, PlayerAssignment
from app import db
from app.auth import oauth
from app.clubs.routes import club_management
import pandas as pd
from datetime import datetime
import csv
from werkzeug.utils import secure_filename
from flask import session, url_for
import os
import random
import string
import secrets
from authlib.integrations.base_client.errors import MismatchingStateError
from app.utils.report_generator import create_single_report_pdf
from app.utils.auth import admin_required, club_access_required
from app.clubs.middleware import verify_club_access
from flask import send_file, make_response
from io import BytesIO
import zipfile
from app.config.clubs import get_club_from_email, TENNIS_CLUBS

main = Blueprint('main', __name__)

@main.context_processor
def utility_processor():
    return {'UserRole': UserRole}

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
REQUIRED_COLUMNS = ['student_name', 'age', 'performance', 'recommendations']

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('pages/index.html')

@main.route('/login')
def login():
    try:
        # Generate secure tokens for both state and nonce
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        
        # Store both in session
        session['oauth_state'] = state
        session['oauth_nonce'] = nonce
        
        redirect_uri = url_for('main.auth_callback', _external=True)
        print(f"Login attempted with redirect URI: {redirect_uri}")
        print(f"State token generated: {state}")
        
        provider = request.args.get('provider')
        
        authorize_params = {
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'nonce': nonce,  # Add nonce to the authorization request
            'scope': 'openid email profile'
        }
        
        if provider == 'Google':
            authorize_params['identity_provider'] = 'Google'
        
        return oauth.cognito.authorize_redirect(**authorize_params)
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        return f"Login error: {str(e)}", 500

@main.route('/auth/callback')
def auth_callback():
    print("Callback reached")
    try:
        # Validate state
        state = session.pop('oauth_state', None)
        nonce = session.pop('oauth_nonce', None)
        state_in_request = request.args.get('state')
        code = request.args.get('code')
        
        print(f"State validation: Session state: {state}, Request state: {state_in_request}")
        
        if not state or state != state_in_request:
            print("State mismatch or missing")
            flash('Invalid state parameter')
            return redirect(url_for('main.login'))

        try:
            # Exchange the authorization code for tokens
            cognito = oauth.create_client('cognito')
            if not cognito:
                raise Exception("Failed to create Cognito client")

            token = cognito.authorize_access_token()
            
            # Verify token and get user info
            try:
                userinfo = cognito.userinfo(token=token)
                print("User info received:", {k: v for k, v in userinfo.items() if k != 'sub'})
            except Exception as e:
                print(f"Error getting user info: {str(e)}")
                raise Exception("Failed to get user info")
            
            # Extract user information
            email = userinfo.get('email')
            name = userinfo.get('name')
            provider_id = userinfo.get('sub')

            if not email:
                print("No email provided in user info")
                flash('Email not provided')
                return redirect(url_for('main.login'))

            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            # If user exists and has a tennis club, proceed with normal login
            if user and user.tennis_club_id:
                user.auth_provider = 'google'
                user.auth_provider_id = provider_id
                if name:
                    user.name = name
                db.session.commit()
                login_user(user)
                flash('Successfully logged in!')
                return redirect(url_for('main.home'))
            
            # For new users or users without a tennis club, store their info in session
            # and redirect to onboarding
            session['temp_user_info'] = {
                'email': email,
                'name': name,
                'provider_id': provider_id,
                'auth_provider': 'google'
            }
            
            return redirect(url_for('club_management.onboard_coach'))

        except Exception as e:
            print(f"OAuth exchange error: {str(e)}")
            print(traceback.format_exc())
            flash('Authentication failed')
            return redirect(url_for('main.login'))

    except Exception as e:
        print(f"Auth callback error: {str(e)}")
        print(traceback.format_exc())
        flash('Authentication error')
        return redirect(url_for('main.login'))


@main.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    
    cognito_domain = current_app.config['COGNITO_DOMAIN']
    client_id = current_app.config['AWS_COGNITO_CLIENT_ID']
    # Get the absolute URL for the home page
    logout_uri = url_for('main.index', _external=True)  # This will create the full URL including http://localhost:3000
    
    logout_url = (
        f"https://{cognito_domain}/logout?"
        f"client_id={client_id}&"
        f"logout_uri={logout_uri}"
    )
    
    print(f"Redirecting to logout URL: {logout_url}")  # Debug print
    return redirect(logout_url)

@main.route('/dashboard')
@login_required
@verify_club_access()
def dashboard():
    try:
        selected_period_id = request.args.get('period', type=int)
        
        # Get periods for this club only
        periods = TeachingPeriod.query.filter_by(
            tennis_club_id=current_user.tennis_club_id
        ).order_by(TeachingPeriod.start_date.desc()).all()
        
        if not selected_period_id and periods:
            selected_period_id = periods[0].id
        
        # Get groups for this club only
        groups = TennisGroup.query.filter_by(
            tennis_club_id=current_user.tennis_club_id
        ).all()
        
        # Start with base Report query
        reports_query = Report.query
        
        # Add filters
        if not current_user.is_admin():
            reports_query = reports_query.filter(Report.coach_id == current_user.id)
        
        # Join with Student and filter by tennis club
        reports_query = (reports_query
            .join(Student)
            .filter(Student.tennis_club_id == current_user.tennis_club_id))
            
        if selected_period_id:
            reports_query = reports_query.filter(Report.teaching_period_id == selected_period_id)
        
        # Get recent reports
        recent_reports = (reports_query
            .order_by(Report.date.desc())
            .limit(10)
            .all())
        
        # Count reports for each group
        group_reports = {}
        for group in groups:
            count_query = Report.query.filter(
                Report.coach_id == current_user.id,
                Report.group_id == group.id
            )
            if selected_period_id:
                count_query = count_query.filter(Report.teaching_period_id == selected_period_id)
            group_reports[group.id] = count_query.count()
        
        return render_template('pages/dashboard.html',
                             periods=periods,
                             selected_period_id=selected_period_id,
                             groups=groups,
                             group_reports=group_reports,
                             recent_reports=recent_reports)
                             
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        flash("Error loading dashboard")
        return redirect(url_for('main.home'))

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # Get groups and periods specific to the user's tennis club
    groups = TennisGroup.query.filter_by(tennis_club_id=current_user.tennis_club_id).all()
    periods = TeachingPeriod.query.filter_by(tennis_club_id=current_user.tennis_club_id).order_by(TeachingPeriod.start_date.desc()).all()

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
            
        file = request.files['file']
        group_id = request.form.get('group_id')
        teaching_period_id = request.form.get('teaching_period_id')
        
        if not group_id or not teaching_period_id:
            flash('Please select both group and term')
            return redirect(request.url)
            
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                df = pd.read_csv(file)
                
                # Simplified expected columns
                expected_columns = [
                    'student_name',
                    'age',
                    'forehand',
                    'backhand',
                    'movement',
                    'overall_rating',
                    'next_group_recommendation',
                    'notes'
                ]
                
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    flash(f'Missing columns: {", ".join(missing_columns)}')
                    return redirect(request.url)
                
                students_created = 0
                reports_created = 0
                
                # Verify group and term belong to user's tennis club
                group = TennisGroup.query.filter_by(id=group_id, tennis_club_id=current_user.tennis_club_id).first()
                term = TeachingPeriod.query.filter_by(id=teaching_period_id, tennis_club_id=current_user.tennis_club_id).first()
                
                if not group or not term:
                    flash('Invalid group or term selected')
                    return redirect(request.url)
                
                for _, row in df.iterrows():
                    try:
                        # Get or create student
                        student_name = row['student_name'].strip()
                        student = Student.query.filter_by(
                            name=student_name,
                            tennis_club_id=current_user.tennis_club_id
                        ).first()
                        
                        if not student:
                            student = Student(
                                name=student_name,
                                age=int(row['age']),
                                tennis_club_id=current_user.tennis_club_id
                            )
                            db.session.add(student)
                            students_created += 1
                        
                        # Create simplified report
                        report = Report(
                            student=student,
                            coach_id=current_user.id,
                            group_id=group_id,
                            teaching_period_id=teaching_period_id,
                            forehand=row['forehand'],
                            backhand=row['backhand'],
                            movement=row['movement'],
                            overall_rating=int(row['overall_rating']),
                            next_group_recommendation=row['next_group_recommendation'],
                            notes=row.get('notes', '')  # Optional field
                        )
                        db.session.add(report)
                        reports_created += 1
                        
                    except Exception as e:
                        db.session.rollback()
                        print(f"Error processing student: {str(e)}")  # Add logging
                        flash(f'Error processing student {student_name}: {str(e)}')
                        return redirect(request.url)
                
                db.session.commit()
                flash(f'Successfully added {students_created} new students and {reports_created} reports')
                return redirect(url_for('main.dashboard'))
                
            except Exception as e:
                db.session.rollback()
                print(f"Error processing file: {str(e)}")  # Add logging
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
                
        else:
            flash('Invalid file type. Please upload a CSV or Excel file')
            return redirect(request.url)
            
    return render_template('pages/upload.html', groups=groups, periods=periods)

@main.route('/home')
@login_required
def home():
    try:
        # Get basic counts without group/term relations for now
        reports = Report.query.filter_by(coach_id=current_user.id).order_by(Report.date.desc()).all()
        students = Student.query.join(Report).filter(Report.coach_id == current_user.id).distinct().all()
        
        return render_template('pages/home.html', 
                            reports=reports,
                            students=students)
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        flash("Error loading dashboard data", "error")
        return redirect(url_for('main.index'))
    
@main.route('/reports/<int:group_id>')
@login_required
def view_group_reports(group_id):
    group = TennisGroup.query.get_or_404(group_id)
    selected_period_id = request.args.get('teaching_period_id', type=int)
    
    # Get all periods
    periods = TeachingPeriod.query.order_by(TeachingPeriod.start_date.desc()).all()
    if not selected_period_id and periods:
        selected_period_id = periods[0].id

    # Get reports for this group and term
    reports = Report.query.filter_by(
        coach_id=current_user.id,
        group_id=group_id,
        teaching_period_id=selected_period_id
    ).order_by(Report.date.desc()).all()

    return render_template('pages/group_reports.html',
                         group=group,
                         reports=reports,
                         periods=periods,
                         selected_period_id=selected_period_id)

@main.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.coach_id != current_user.id:
        flash('You do not have permission to view this report')
        return redirect(url_for('main.dashboard'))
    
    return render_template('pages/report_detail.html', report=report)

@main.route('/report/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.coach_id != current_user.id:
        flash('You do not have permission to edit this report')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            report.forehand = request.form['forehand']
            report.backhand = request.form['backhand']
            report.movement = request.form['movement']
            report.overall_rating = int(request.form['overall_rating'])
            report.next_group_recommendation = request.form['next_group_recommendation']
            report.notes = request.form['notes']
            
            db.session.commit()
            flash('Report updated successfully')
            return redirect(url_for('main.view_report', report_id=report.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating report: {str(e)}')
    
    return render_template('pages/edit_report.html', report=report)

@main.route('/download_reports')
@login_required
def download_reports():
    """Download all reports for the current term as a ZIP file"""
    selected_period_id = request.args.get('teaching_period_id', type=int)
    selected_group_id = request.args.get('group_id', type=int)
    
    # Query reports based on filters
    query = Report.query.filter_by(coach_id=current_user.id)
    if selected_period_id:
        query = query.filter_by(teaching_period_id=selected_period_id)
    if selected_group_id:
        query = query.filter_by(group_id=selected_group_id)
    
    reports = query.all()
    
    if not reports:
        flash('No reports found for the selected criteria')
        return redirect(url_for('main.dashboard'))
    
    # Create a ZIP file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for report in reports:
            # Create PDF for each report
            pdf_buffer = BytesIO()
            create_single_report_pdf(report, pdf_buffer)
            
            # Add PDF to ZIP with a meaningful filename
            filename = f"{report.student.name}_{report.teaching_period.name}_{report.tennis_group.name}.pdf".replace(' ', '_')
            zf.writestr(filename, pdf_buffer.getvalue())
    
    memory_file.seek(0)
    
    # Generate timestamp for the zip filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    response = make_response(memory_file.getvalue())
    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = f'attachment; filename=tennis_reports_{timestamp}.zip'
    
    return response

@main.route('/download_single_report/<int:report_id>')
@login_required
def download_single_report(report_id):
    """Download a single report as PDF"""
    report = Report.query.get_or_404(report_id)
    
    if report.coach_id != current_user.id:
        flash('You do not have permission to download this report')
        return redirect(url_for('main.dashboard'))
    
    # Create PDF in memory
    pdf_buffer = BytesIO()
    create_single_report_pdf(report, pdf_buffer)
    
    # Generate filename
    filename = f"{report.student.name}_{report.teaching_period.name}_{report.tennis_group.name}.pdf".replace(' ', '_')
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@main.route('/admin/coaches', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_coaches():
    """Admin route for managing coaches in their tennis club"""
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        
        # Create new coach user
        coach = User(
            email=email,
            username=f"coach_{email.split('@')[0]}",
            name=name,
            role=UserRole.COACH,
            tennis_club_id=current_user.tennis_club_id
        )
        db.session.add(coach)
        db.session.commit()
        
        flash('Coach added successfully')
        return redirect(url_for('main.manage_coaches'))
        
    coaches = User.query.filter_by(
        tennis_club_id=current_user.tennis_club_id,
        role=UserRole.COACH
    ).all()
    
    return render_template('admin/coaches.html', coaches=coaches)

