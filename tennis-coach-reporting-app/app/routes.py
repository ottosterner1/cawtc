import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import User, TennisGroup, TeachingPeriod, Student, Report, UserRole, TennisClub, ProgrammePlayers
from app import db
from app.auth import oauth
from app.clubs.routes import club_management
import pandas as pd
from sqlalchemy.orm import joinedload
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import session, url_for
from sqlalchemy.exc import SQLAlchemyError
from botocore.exceptions import ClientError
import boto3
import secrets
from authlib.integrations.base_client.errors import MismatchingStateError
from app.utils.report_generator import create_single_report_pdf
from app.utils.auth import admin_required, club_access_required
from app.clubs.middleware import verify_club_access
from flask import send_file, make_response
from io import BytesIO
import zipfile
<<<<<<< HEAD
=======
from app.config.clubs import get_club_from_email, TENNIS_CLUBS
from flask_cors import CORS, cross_origin
<<<<<<< HEAD
from sqlalchemy import func
>>>>>>> 1d721ff (Getting a more complex dashboard working)
=======
from sqlalchemy import func, distinct, and_
>>>>>>> 091dcc2 (Finalising React dashboard component)

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
    logout_uri = url_for('main.index', _external=True) 
    
    logout_url = (
        f"https://{cognito_domain}/logout?"
        f"client_id={client_id}&"
        f"logout_uri={logout_uri}"
    )
    
    print(f"Redirecting to logout URL: {logout_url}")  # Debug print
    return redirect(logout_url)

def serialize_period(period):
    """Helper function to serialize teaching period"""
    return {
        'id': period.id,
        'name': period.name,
        'start_date': period.start_date.isoformat() if period.start_date else None,
        'end_date': period.end_date.isoformat() if period.end_date else None
    }

def serialize_programme_player(player):
    """Helper function to serialize programme player"""
    return {
        'id': player.id,
        'student_id': player.student_id,
        'student_name': player.student.name if player.student else None,
        'tennis_group': {
            'id': player.tennis_group.id,
            'name': player.tennis_group.name
        } if player.tennis_group else None,
        'coach_id': player.coach_id
    }

def serialize_report(report):
    """Helper function to serialize report"""
    return {
        'id': report.id,
        'student_id': report.student_id,
        'coach_id': report.coach_id,
        'submission_date': report.submission_date.isoformat() if report.submission_date else None,
        'group_id': report.group_id,
        'recommended_group': report.tennis_group.name if report.tennis_group else None
    }

def serialize_coach(coach):
    """Helper function to serialize coach"""
    return {
        'id': coach.id,
        'name': coach.name,
        'email': coach.email
    }


# Keep your existing dashboard route for the initial page load
@main.route('/dashboard')
@login_required
@verify_club_access()
def dashboard():
    return render_template('pages/dashboard.html')

# Current user endpoint
@main.route('/api/current-user')
@login_required
@verify_club_access()
def current_user_info():
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'is_admin': current_user.is_admin,
        'is_super_admin': current_user.is_super_admin
    })

@main.route('/api/dashboard/stats')
@login_required
@verify_club_access()
def dashboard_stats():
    try:
        tennis_club_id = current_user.tennis_club_id
        selected_period_id = request.args.get('period', type=int)
        
        # Base queries - filter by coach if not admin
        players_query = ProgrammePlayers.query.filter_by(tennis_club_id=tennis_club_id)
        if not (current_user.is_admin or current_user.is_super_admin):
            players_query = players_query.filter_by(coach_id=current_user.id)
            
        if selected_period_id:
            players_query = players_query.filter_by(teaching_period_id=selected_period_id)
            
        total_students = players_query.count()
        
        # Get reports - filter by coach if not admin
        reports_query = Report.query.join(ProgrammePlayers).filter(
            ProgrammePlayers.tennis_club_id == tennis_club_id
        )
        if not (current_user.is_admin or current_user.is_super_admin):
            reports_query = reports_query.filter(Report.coach_id == current_user.id)
            
        if selected_period_id:
            reports_query = reports_query.filter(Report.teaching_period_id == selected_period_id)
            
        total_reports = reports_query.count()
        completion_rate = round((total_reports / total_students * 100) if total_students > 0 else 0, 1)
        
        # Get all periods
        periods = TeachingPeriod.query.filter_by(
            tennis_club_id=tennis_club_id
        ).order_by(TeachingPeriod.start_date.desc()).all()
        
        # Get group stats
        group_stats_query = db.session.query(
            TennisGroup.name,
            func.count(distinct(ProgrammePlayers.id)).label('count'),
            func.count(distinct(Report.id)).label('reports_completed')
        ).join(
            ProgrammePlayers, TennisGroup.id == ProgrammePlayers.group_id
        ).outerjoin(
            Report, ProgrammePlayers.id == Report.programme_player_id
        ).filter(
            ProgrammePlayers.tennis_club_id == tennis_club_id
        )
        
        if selected_period_id:
            group_stats_query = group_stats_query.filter(
                ProgrammePlayers.teaching_period_id == selected_period_id
            )
            
        if not (current_user.is_admin or current_user.is_super_admin):
            group_stats_query = group_stats_query.filter(
                ProgrammePlayers.coach_id == current_user.id
            )
            
        group_stats = group_stats_query.group_by(TennisGroup.name).all()
        
        # Get coach summaries only for admin users
        coach_summaries = None
        if current_user.is_admin or current_user.is_super_admin:
            coach_summaries = []
            coaches = User.query.filter_by(
                tennis_club_id=tennis_club_id,
                role=UserRole.COACH
            ).all()
            
            for coach in coaches:
                coach_players = players_query.filter_by(coach_id=coach.id)
                coach_reports = reports_query.filter_by(coach_id=coach.id)
                
                coach_summaries.append({
                    'id': coach.id,
                    'name': coach.name,
                    'total_assigned': coach_players.count(),
                    'reports_completed': coach_reports.count()
                })
        
        response_data = {
            'periods': [{
                'id': p.id,
                'name': p.name
            } for p in periods],
            'stats': {
                'totalStudents': total_students,
                'totalReports': total_reports,
                'reportCompletion': completion_rate,
                'currentGroups': [{
                    'name': name,
                    'count': count,
                    'reports_completed': completed
                } for name, count, completed in group_stats],
                'coachSummaries': coach_summaries
            }
        }
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in dashboard stats: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': f"Server error: {str(e)}",
            'periods': [],
            'stats': {
                'totalStudents': 0,
                'totalReports': 0,
                'reportCompletion': 0,
                'currentGroups': [],
                'coachSummaries': None
            }
        }), 500

@main.route('/api/programme-players')
@login_required
@verify_club_access()
def programme_players():
    try:
        tennis_club_id = current_user.tennis_club_id
        selected_period_id = request.args.get('period', type=int)
        
        # Base query - get all programme players for the club
        query = ProgrammePlayers.query.filter_by(
            tennis_club_id=tennis_club_id
        )
        
        if selected_period_id:
            query = query.filter_by(teaching_period_id=selected_period_id)
        
        # For regular coaches, only show players they're assigned to
        if not (current_user.is_admin or current_user.is_super_admin):
            query = query.filter_by(coach_id=current_user.id)
            
        players = query.join(
            Student, ProgrammePlayers.student_id == Student.id
        ).join(
            TennisGroup, ProgrammePlayers.group_id == TennisGroup.id
        ).outerjoin(
            Report, and_(
                ProgrammePlayers.id == Report.programme_player_id,
                ProgrammePlayers.teaching_period_id == Report.teaching_period_id
            )
        ).with_entities(
            ProgrammePlayers.id,
            Student.name.label('student_name'),
            TennisGroup.name.label('group_name'),
            Report.id.label('report_id'),
            Report.coach_id,
            ProgrammePlayers.coach_id.label('assigned_coach_id')
        ).all()
        
        return jsonify([{
            'id': player.id,
            'student_name': player.student_name,
            'group_name': player.group_name,
            'report_submitted': player.report_id is not None,
            'report_id': player.report_id,
            'can_edit': current_user.is_admin or current_user.is_super_admin or 
                       player.coach_id == current_user.id or 
                       player.assigned_coach_id == current_user.id
        } for player in players])
        
    except Exception as e:
        print(f"Error fetching programme players: {str(e)}")
        print(traceback.format_exc())
        return jsonify([]), 500

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

@main.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    current_period = request.args.get('period')
    report = Report.query.get_or_404(report_id)
    if report.coach_id != current_user.id:
        flash('You do not have permission to view this report')
        return redirect(url_for('main.dashboard', period=current_period))
    
    return render_template('pages/report_detail.html', 
                         report=report,
                         current_period=current_period)

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

@main.route('/report/create/<int:player_id>', methods=['GET', 'POST'])
@login_required
def create_report(player_id):
    current_period = request.args.get('period')
    player = ProgrammePlayers.query.get_or_404(player_id)
    
    # Permission check
    if not (current_user.is_admin or current_user.is_super_admin) and player.coach_id != current_user.id:
        flash('You do not have permission to create a report for this player', 'error')
        return redirect(url_for('main.dashboard', period=current_period))

    # Check if report already exists
    existing_report = Report.query.filter_by(
        student_id=player.student_id,
        teaching_period_id=player.teaching_period_id
    ).first()
    
    if existing_report:
        flash('A report already exists for this student in this teaching period', 'error')
        return redirect(url_for('main.dashboard', period=current_period))
    
    # Get the groups for the current user's tennis club
    groups = TennisGroup.query.filter_by(
        tennis_club_id=current_user.tennis_club_id
    ).order_by(TennisGroup.name).all()
    
    if request.method == 'POST':
        try:
            # Create new report
            report = Report(
                student_id=player.student_id,
                coach_id=current_user.id,
                teaching_period_id=player.teaching_period_id,
                programme_player_id=player.id,
                group_id=int(request.form['next_group_recommendation']),
                forehand=request.form['forehand'],
                backhand=request.form['backhand'],
                movement=request.form['movement'],
                overall_rating=int(request.form['overall_rating']),
                next_group_recommendation=request.form['next_group_recommendation'],
                notes=request.form['notes'],
                date=datetime.utcnow()
            )
            
            db.session.add(report)
            player.report_submitted = True
            
            db.session.commit()
            flash('Report created successfully', 'success')
            return redirect(url_for('main.dashboard', period=current_period))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating report: {str(e)}', 'error')
            return render_template('pages/create_report.html', 
                               player=player, 
                               groups=groups,
                               current_period=current_period)
    
    # GET request
    return render_template('pages/create_report.html', 
                         player=player, 
                         groups=groups,
                         current_period=current_period)

@main.route('/report/<int:report_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    # Get the current period from query parameters
    current_period = request.args.get('period')
    # Get report with relationships
    report = Report.query.get_or_404(report_id)
    
    if report.coach_id != current_user.id:
        flash('You do not have permission to edit this report', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get the groups for the current user's tennis club
    groups = TennisGroup.query.filter_by(
        tennis_club_id=current_user.tennis_club_id
    ).order_by(TennisGroup.name).all()
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['forehand', 'backhand', 'movement', 'overall_rating', 
                             'next_group_recommendation', 'notes']
            
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'The {field.replace("_", " ")} field is required', 'error')
                    return render_template('pages/edit_report.html', 
                                        report=report, 
                                        groups=groups)
            
            # Validate overall rating
            try:
                overall_rating = int(request.form['overall_rating'])
                if not 1 <= overall_rating <= 5:
                    raise ValueError("Rating must be between 1 and 5")
            except ValueError as e:
                flash(f'Invalid overall rating: {str(e)}', 'error')
                return render_template('pages/edit_report.html', 
                                    report=report, 
                                    groups=groups)
            
            # Update report fields
            report.forehand = request.form['forehand']
            report.backhand = request.form['backhand']
            report.movement = request.form['movement']
            report.overall_rating = overall_rating
            report.next_group_recommendation = request.form['next_group_recommendation']
            report.notes = request.form['notes']
            
            try:
                db.session.commit()
                flash('Report updated successfully', 'success')
                # Redirect back to dashboard with the period parameter
                return redirect(url_for('main.dashboard', period=current_period))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f'Database error: {str(e)}', 'error')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating report: {str(e)}', 'error')
            print(f"Error updating report: {str(e)}")
    
    return render_template('pages/edit_report.html', 
                         report=report, 
                         groups=groups,
                         current_period=current_period)

@main.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    current_period = request.args.get('period')
    report = Report.query.get_or_404(report_id)
    
    if report.coach_id != current_user.id:
        flash('You do not have permission to delete this report', 'error')
        return redirect(url_for('main.dashboard', period=current_period))
    
    try:
        programme_player = report.programme_player
        programme_player.report_submitted = False
        
        db.session.delete(report)
        db.session.commit()
        flash('Report deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting report: {str(e)}', 'error')
        return redirect(url_for('main.edit_report', report_id=report_id, period=current_period))
    
    return redirect(url_for('main.dashboard', period=current_period))

@main.route('/reports/send/<int:period_id>', methods=['GET', 'POST'])
@login_required
@admin_required  # Only admins can send reports
def send_reports(period_id):
    period = TeachingPeriod.query.get_or_404(period_id)
    
    # Get all reports for this period
    reports = Report.query.filter_by(teaching_period_id=period_id).all()
    
    # Get students with and without email contacts
    students_with_emails = []
    students_missing_emails = []
    
    for report in reports:
        if report.student.contact_email:
            students_with_emails.append(report.student)
        else:
            students_missing_emails.append(report.student)
    
    if request.method == 'POST':
        try:
            # Initialize AWS SES client
            ses_client = boto3.client('ses',
                                    region_name=current_app.config['AWS_REGION'],
                                    aws_access_key_id=current_app.config['AWS_ACCESS_KEY'],
                                    aws_secret_access_key=current_app.config['AWS_SECRET_KEY'])
            
            subject = request.form['email_subject']
            message = request.form['email_message']
            sender = current_app.config['AWS_SES_SENDER']
            
            success_count = 0
            error_count = 0
            
            for report in reports:
                if not report.student.contact_email:
                    continue
                
                try:
                    # Generate PDF
                    pdf_buffer = BytesIO()
                    create_single_report_pdf(report, pdf_buffer)
                    pdf_buffer.seek(0)
                    
                    # Create raw email message
                    response = ses_client.send_raw_email(
                        Source=sender,
                        Destinations=[report.student.contact_email],
                        RawMessage={
                            'Data': create_multipart_email(
                                sender=sender,
                                recipient=report.student.contact_email,
                                subject=subject,
                                body=message,
                                attachment=pdf_buffer,
                                filename=f"{report.student.name}_tennis_report.pdf"
                            )
                        }
                    )
                    success_count += 1
                    
                except ClientError as e:
                    print(f"Error sending email to {report.student.name}: {str(e)}")
                    error_count += 1
            
            flash(f'Successfully sent {success_count} reports. {error_count} failed.', 
                  'success' if error_count == 0 else 'warning')
            return redirect(url_for('main.dashboard', period=period_id))
            
        except Exception as e:
            flash(f'Error sending reports: {str(e)}', 'error')
            return redirect(url_for('main.dashboard', period=period_id))
    
    return render_template('pages/send_reports.html',
                         period=period,
                         total_reports=len(reports),
                         students_with_email=len(students_with_emails),
                         students_missing_email=len(students_missing_emails),
                         missing_emails=students_missing_emails)

def create_multipart_email(sender, recipient, subject, body, attachment, filename):
    """Helper function to create multipart email with attachment"""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    
    msg.attach(MIMEText(body))
    
    part = MIMEApplication(attachment.read())
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)
    
    return msg.as_string()