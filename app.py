import os
from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from services.github_service import GitHubService
from services.claude_service import ClaudeService
from utils.pr_parser import parse_pr_url
import json

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "pr_review_assistant_secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reviews.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Initialize services
github_service = GitHubService(os.environ.get("GITHUB_TOKEN"))
claude_service = ClaudeService(os.environ.get("CLAUDE_API_KEY"))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review():
    pr_url = request.form.get('pr_url')
    
    try:
        # Parse PR URL
        pr_details = parse_pr_url(pr_url)
        if not pr_details:
            flash('Invalid PR URL format', 'error')
            return redirect(url_for('index'))

        # Fetch PR data
        pr_data = github_service.fetch_pr_data(pr_details)
        
        # Analyze with Claude
        context = {
            'pr_data': pr_data,
            'files': github_service.fetch_pr_files(pr_details),
            'comments': github_service.fetch_pr_comments(pr_details)
        }
        
        review = claude_service.analyze_pr(context)
        
        return render_template('review.html', review=review, pr_url=pr_url)
        
    except Exception as e:
        flash(f'Error processing PR: {str(e)}', 'error')
        return redirect(url_for('index'))

with app.app_context():
    db.create_all()
