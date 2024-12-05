from flask import Blueprint, request, render_template, flash, redirect, url_for, session, make_response
from app import db
from app.models import TennisClub, User, TennisGroup, TeachingPeriod, UserRole, Student, PlayerAssignment
from datetime import datetime, timedelta
from flask_login import login_required, current_user, login_user
import traceback
import pandas as pd 
from werkzeug.utils import secure_filename 
from datetime import datetime 
from app.utils.auth import admin_required

club_management = Blueprint('club_management', __name__, url_prefix='/clubs') 

ALLOWED_EXTENSIONS = {'csv'}  # Since we only want CSV files for assignments

# Add this helper function
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@club_management.context_processor
def utility_processor():
   from app.models import UserRole
   return {'UserRole': UserRole}

def setup_default_groups(club_id):
   groups = [
       {"name": "Beginners", "description": "New players learning basics"},
       {"name": "Intermediate", "description": "Players developing core skills"},
       {"name": "Advanced", "description": "Competitive players"}
   ]
   for group in groups:
       db.session.add(TennisGroup(tennis_club_id=club_id, **group))

def setup_initial_teaching_period(club_id):
   start_date = datetime.now()
   db.session.add(TeachingPeriod(
       tennis_club_id=club_id,
       name=f"Teaching Period {start_date.strftime('%B %Y')}",
       start_date=start_date, 
       end_date=start_date + timedelta(weeks=12)
   ))

@club_management.route('/onboard', methods=['GET', 'POST'])
def onboard_club():
   if request.method == 'GET':
       return render_template('admin/club_onboarding.html')

   try:
       club = TennisClub(
           name=request.form['club_name'],
           subdomain=request.form['subdomain']
       )
       db.session.add(club)
       db.session.flush()

       admin = User(
           email=request.form['admin_email'],
           username=f"admin_{request.form['subdomain']}",
           name=request.form['admin_name'],
           role=UserRole.ADMIN,
           tennis_club_id=club.id,
           is_active=True
       )
       db.session.add(admin)
       
       setup_default_groups(club.id)
       setup_initial_teaching_period(club.id)
       
       db.session.commit()
       flash('Tennis club created successfully', 'success')
       return redirect(url_for('main.home'))
       
   except Exception as e:
       db.session.rollback()
       flash(f'Error creating club: {str(e)}', 'error')
       return redirect(url_for('club_management.onboard_club'))

@club_management.route('/manage/<int:club_id>', methods=['GET', 'POST'])
@login_required
def manage_club(club_id):
   print(f"Managing club {club_id} for user {current_user.id} with role {current_user.role}")
   
   club = TennisClub.query.get_or_404(club_id)
   
   if not current_user.is_admin() and not current_user.is_super_admin():
       print(f"Access denied: User {current_user.id} is not an admin")
       flash('You must be an admin to manage club settings', 'error')
       return redirect(url_for('main.home'))
       
   if current_user.tennis_club_id != club.id:
       print(f"Access denied: User's club {current_user.tennis_club_id} doesn't match requested club {club.id}")
       flash('You can only manage your own tennis club', 'error')
       return redirect(url_for('main.home'))
   
   if request.method == 'POST':
       club.name = request.form['name']
       club.subdomain = request.form['subdomain']
       
       try:
           db.session.commit()
           flash('Club details updated successfully', 'success')
           return redirect(url_for('main.home'))
       except Exception as e:
           db.session.rollback()
           flash(f'Error updating club: {str(e)}', 'error')
           
   return render_template('admin/manage_club.html', club=club)

@club_management.route('/manage/<int:club_id>/teaching-periods', methods=['GET', 'POST'])
@login_required
def manage_teaching_periods(club_id):
   print(f"Managing teaching periods for club {club_id}")
   
   club = TennisClub.query.get_or_404(club_id)
   
   if not current_user.is_admin() and not current_user.is_super_admin():
       flash('You must be an admin to manage teaching periods', 'error')
       return redirect(url_for('main.home'))
       
   if current_user.tennis_club_id != club.id:
       flash('You can only manage teaching periods for your own tennis club', 'error')
       return redirect(url_for('main.home'))
   
   if request.method == 'POST':
       try:
           name = request.form['name']
           start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
           end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
           
           if start_date > end_date:
               flash('Start date must be before end date', 'error')
           else:
               period = TeachingPeriod(
                   name=name,
                   start_date=start_date,
                   end_date=end_date,
                   tennis_club_id=club.id
               )
               db.session.add(period)
               db.session.commit()
               flash('Teaching period created successfully', 'success')
               return redirect(url_for('club_management.manage_teaching_periods', club_id=club.id))
               
       except Exception as e:
           db.session.rollback()
           print(f"Error creating teaching period: {str(e)}")
           print(traceback.format_exc())
           flash(f'Error creating teaching period: {str(e)}', 'error')
   
   teaching_periods = TeachingPeriod.query.filter_by(
       tennis_club_id=club.id
   ).order_by(TeachingPeriod.start_date.desc()).all()
   
   return render_template('admin/manage_teaching_periods.html', 
                        club=club, 
                        teaching_periods=teaching_periods)

@club_management.route('/manage/<int:club_id>/teaching-periods/<int:teaching_period_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_teaching_period(club_id, teaching_period_id):
   club = TennisClub.query.get_or_404(club_id)
   period = TeachingPeriod.query.get_or_404(teaching_period_id)
   
   if not current_user.is_admin() and not current_user.is_super_admin():
       flash('You must be an admin to edit teaching periods', 'error')
       return redirect(url_for('main.home'))
       
   if current_user.tennis_club_id != club.id:
       flash('You can only edit teaching periods for your own tennis club', 'error')
       return redirect(url_for('main.home'))
   
   if request.method == 'POST':
       try:
           period.name = request.form['name']
           period.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
           period.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
           
           if period.start_date > period.end_date:
               flash('Start date must be before end date', 'error')
           else:
               db.session.commit()
               flash('Teaching period updated successfully', 'success')
               return redirect(url_for('club_management.manage_teaching_periods', club_id=club.id))
               
       except Exception as e:
           db.session.rollback()
           flash(f'Error updating teaching period: {str(e)}', 'error')
   
   return render_template('admin/edit_teaching_period.html', club=club, period=period)

@club_management.route('/manage/<int:club_id>/teaching-periods/<int:teaching_period_id>/delete', methods=['POST'])
@login_required
def delete_teaching_period(club_id, teaching_period_id):
   club = TennisClub.query.get_or_404(club_id)
   period = TeachingPeriod.query.get_or_404(teaching_period_id)
   
   if not current_user.is_admin() and not current_user.is_super_admin():
       flash('You must be an admin to delete teaching periods', 'error')
       return redirect(url_for('main.home'))
       
   if current_user.tennis_club_id != club.id:
       flash('You can only delete teaching periods for your own tennis club', 'error')
       return redirect(url_for('main.home'))
   
   try:
       if period.reports:
           flash('Cannot delete teaching period with existing reports', 'error')
       else:
           db.session.delete(period)
           db.session.commit()
           flash('Teaching period deleted successfully', 'success')
   except Exception as e:
       db.session.rollback()
       flash(f'Error deleting teaching period: {str(e)}', 'error')
   
   return redirect(url_for('club_management.manage_teaching_periods', club_id=club.id))

@club_management.route('/onboard-coach', methods=['GET', 'POST'])
def onboard_coach():
   # Get temp user info from session
   temp_user_info = session.get('temp_user_info')
   
   if request.method == 'POST':
       club_id = request.form.get('club_id')
       
       if not club_id:
           flash('Please select a tennis club', 'error')
           return redirect(url_for('club_management.onboard_coach'))
           
       # Get the selected tennis club
       club = TennisClub.query.get(club_id)
       
       if not club:
           flash('Invalid tennis club selected', 'error')
           return redirect(url_for('club_management.onboard_coach'))
       
       try:
           if temp_user_info:
               # Create or update user
               user = User.query.filter_by(email=temp_user_info['email']).first()
               if not user:
                   username = f"coach_{temp_user_info['email'].split('@')[0]}"
                   user = User(
                       email=temp_user_info['email'],
                       username=username,
                       name=temp_user_info['name'],
                       role=UserRole.COACH,
                       auth_provider='google',
                       auth_provider_id=temp_user_info['provider_id'],
                       is_active=True,
                       tennis_club_id=club.id
                   )
                   db.session.add(user)
               else:
                   user.tennis_club_id = club.id
                   user.auth_provider = 'google'
                   user.auth_provider_id = temp_user_info['provider_id']
               
               db.session.commit()
               login_user(user)
               session.pop('temp_user_info', None)
               
               flash('Welcome to your tennis club!', 'success')
               return redirect(url_for('main.home'))
           else:
               flash('User information not found. Please try logging in again.', 'error')
               return redirect(url_for('main.login'))
               
       except Exception as e:
           db.session.rollback()
           print(f"Error in onboarding: {str(e)}")
           flash('An error occurred during onboarding', 'error')
           return redirect(url_for('club_management.onboard_coach'))
   
   # Get the list of onboarded tennis clubs
   clubs = TennisClub.query.all()
   return render_template('admin/coach_onboarding.html', clubs=clubs)

@club_management.route('/manage/<int:club_id>/assignments', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_assignments(club_id):
    # Verify club exists and user has access
    club = TennisClub.query.get_or_404(club_id)
    
    if not (current_user.is_admin() or current_user.is_super_admin()):
        flash('You must be an admin to manage player assignments', 'error')
        return redirect(url_for('main.dashboard'))
        
    if current_user.tennis_club_id != club.id:
        flash('You can only manage assignments for your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
            
        file = request.files['file']
        teaching_period_id = request.form.get('teaching_period_id')
        
        if not teaching_period_id:
            flash('Please select a teaching period')
            return redirect(request.url)
            
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                df = pd.read_csv(file)
                
                # Verify required columns
                required_columns = ['student_name', 'student_age', 'coach_email', 'group_name']
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    flash(f'Missing columns: {", ".join(missing_columns)}')
                    return redirect(request.url)
                
                # Verify the teaching period belongs to this admin's club
                teaching_period = TeachingPeriod.query.filter_by(
                    id=teaching_period_id,
                    tennis_club_id=club.id
                ).first()
                
                if not teaching_period:
                    flash('Invalid teaching period selected')
                    return redirect(request.url)
                
                students_created = 0
                assignments_created = 0
                
                for _, row in df.iterrows():
                    try:
                        # Get or create student
                        student = Student.query.filter_by(
                            name=row['student_name'].strip(),
                            tennis_club_id=club.id
                        ).first()
                        
                        if not student:
                            student = Student(
                                name=row['student_name'].strip(),
                                age=int(row['student_age']),
                                tennis_club_id=club.id
                            )
                            db.session.add(student)
                            students_created += 1
                            db.session.flush()
                        
                        # Get coach - ensure coach belongs to this admin's club
                        coach = User.query.filter_by(
                            email=row['coach_email'].strip(),
                            tennis_club_id=club.id,
                            role=UserRole.COACH
                        ).first()
                        
                        if not coach:
                            flash(f'Coach with email {row["coach_email"]} not found in your club')
                            continue
                        
                        # Get group - ensure group belongs to this admin's club
                        group = TennisGroup.query.filter_by(
                            name=row['group_name'].strip(),
                            tennis_club_id=club.id
                        ).first()
                        
                        if not group:
                            flash(f'Group {row["group_name"]} not found in your club')
                            continue
                        
                        # Check for existing assignment
                        existing_assignment = PlayerAssignment.query.filter_by(
                            student_id=student.id,
                            teaching_period_id=teaching_period_id,
                            tennis_club_id=club.id
                        ).first()
                        
                        if existing_assignment:
                            # Update existing assignment
                            existing_assignment.coach_id = coach.id
                            existing_assignment.group_id = group.id
                        else:
                            # Create new assignment
                            assignment = PlayerAssignment(
                                student_id=student.id,
                                coach_id=coach.id,
                                group_id=group.id,
                                teaching_period_id=teaching_period_id,
                                tennis_club_id=club.id
                            )
                            db.session.add(assignment)
                            assignments_created += 1
                        
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Error processing row: {str(e)}')
                        return redirect(request.url)
                
                db.session.commit()
                flash(f'Successfully added {students_created} new students and {assignments_created} assignments')
                return redirect(url_for('club_management.manage_assignments', club_id=club.id))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}')
                return redirect(request.url)
    
    # Get data for template - ensure we only get data for this admin's club
    periods = TeachingPeriod.query.filter_by(
        tennis_club_id=club.id
    ).order_by(TeachingPeriod.start_date.desc()).all()
    
    selected_period_id = request.args.get('period', type=int)
    if not selected_period_id and periods:
        selected_period_id = periods[0].id
    
    assignments = None
    if selected_period_id:
        assignments = PlayerAssignment.query.filter_by(
            tennis_club_id=club.id,
            teaching_period_id=selected_period_id
        ).order_by(PlayerAssignment.created_at.desc()).all()
    
    return render_template('admin/player_assignments.html',
                         club=club,
                         periods=periods,
                         selected_period_id=selected_period_id,
                         assignments=assignments)

@club_management.route('/manage/<int:club_id>/assignments/download-template')
@login_required
@admin_required
def download_assignment_template(club_id):
    """Download a CSV template for player assignments"""
    club = TennisClub.query.get_or_404(club_id)
    
    if not (current_user.is_admin() or current_user.is_super_admin()):
        flash('You must be an admin to download the assignment template', 'error')
        return redirect(url_for('main.dashboard'))
        
    if current_user.tennis_club_id != club.id:
        flash('You can only download templates for your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))
        
    csv_data = "student_name,student_age,coach_email,group_name\n"
    csv_data += "John Smith,10,coach@example.com,Beginners\n"  # Example row
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=player_assignments_template.csv'
    
    return response