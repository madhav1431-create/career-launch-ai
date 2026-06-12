import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from core.orchestrator import Orchestrator
from engine import extract_text_from_pdf

app = Flask(__name__)
CORS(app)

def validate_jd_content(text):
    if not text or len(text.strip()) < 50:
        return {
            'valid': False,
            'message': 'The uploaded file appears to be empty or too short to be a Job Description.'
        }

    text_lower = text.lower()

    jd_keywords = [
        'responsibilities', 'requirements', 'qualifications', 'experience',
        'skills', 'job', 'role', 'position', 'candidate', 'apply',
        'team', 'work', 'develop', 'engineer', 'analyst', 'manager',
        'salary', 'benefits', 'full-time', 'part-time', 'remote',
        'bachelor', 'degree', 'years of experience', 'preferred',
        'required', 'looking for', 'we are', 'you will', 'must have'
    ]

    resume_keywords = [
        'education', 'objective', 'summary', 'projects', 'internship',
        'cgpa', 'gpa', 'college', 'university', 'institute',
        'trained', 'coursework', 'extracurricular', 'hobbies',
        'declaration', 'date of birth', 'languages known',
        'personal details', 'contact', 'linkedin', 'github'
    ]

    jd_score = sum(1 for kw in jd_keywords if kw in text_lower)
    resume_score = sum(1 for kw in resume_keywords if kw in text_lower)

    if resume_score >= 4 and resume_score > jd_score:
        return {
            'valid': False,
            'message': 'This file looks like a Resume, not a Job Description. Please upload the correct JD file.'
        }

    if jd_score < 2:
        return {
            'valid': False,
            'message': 'This file does not appear to be a Job Description. Please upload a valid JD PDF or paste the job description text.'
        }

    return {'valid': True, 'message': 'OK'}


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        resume_file = request.files.get('resume')
        jd_text = request.form.get('jd_text', '').strip()
        target_role = request.form.get('target_role', 'Data Scientist')
        jd_file = request.files.get('jd_file')

        if not resume_file:
            return jsonify({'error': 'No resume uploaded'}), 400

        # Save resume temporarily
        resume_path = 'temp_resume.pdf'
        resume_file.save(resume_path)

        # Validate JD file is not the same as resume
        if jd_file and jd_file.filename != '':
            resume_file.seek(0, 2)
            jd_file.seek(0, 2)
            resume_size = resume_file.tell()
            jd_size = jd_file.tell()
            resume_file.seek(0)
            jd_file.seek(0)

            if resume_size == jd_size:
                return jsonify({
                    'error': 'The Job Description file appears to be the same as your Resume. Please upload a different PDF.'
                }), 400

        # Handle JD
        if jd_file and jd_file.filename != '':
            jd_path = 'temp_jd.pdf'
            jd_file.save(jd_path)
            jd_text = extract_text_from_pdf(jd_path)
            if os.path.exists(jd_path):
                os.remove(jd_path)

            jd_validation = validate_jd_content(jd_text)
            if not jd_validation['valid']:
                return jsonify({'error': jd_validation['message']}), 400

        if jd_text and jd_text.strip() and not (jd_file and jd_file.filename != ''):
            jd_validation = validate_jd_content(jd_text)
            if not jd_validation['valid']:
                return jsonify({'error': jd_validation['message']}), 400

        # Run orchestrator
        orchestrator = Orchestrator()
        state = orchestrator.run(resume_path, jd_text, target_role)

        if os.path.exists(resume_path):
            os.remove(resume_path)

        return jsonify({
            'success': True,
            'target_role': state['target_role'],
            'resume_skills': state['resume_skills'],
            'jd_skills': state['jd_skills'],
            'jd_source': state['jd_source'],
            'match_score': state['match_score'],
            'level': state['level'],
            'overview': state['overview'],
            'missing_skills': state['missing_skills'],
            'roadmap': state['roadmap'],
            'project_recommendations': state['project_recommendations'],
            'certifications': state['certifications'],
            'career_strategy': state['career_strategy'],
            'interview_questions': state['interview_questions'],
            'career_readiness_score': state['career_readiness_score'],
            'agent_logs': state['agent_logs'],
            'hiring_simulation': state['hiring_simulation'],
            'risk_assessment': state['risk_assessment'],
            'shortlisting_probability': state['shortlisting_probability']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'CareerLaunch AI is running'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)