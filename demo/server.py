from flask import Flask, request, render_template_string, session, redirect, url_for, flash, send_from_directory
from pathlib import Path
import uuid
import logging
import traceback
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import with proper error handling
try:
    from rag_document_viewer import RAG_DV
except ImportError as e:
    print(f"Warning: Could not import RAG_DV: {e}")
    RAG_DV = None

app = Flask(__name__)
app.secret_key = 'a&VhLelkAo!dKXm9o5RRHQ@#BxoI3Q5378qwFP&aJKA#PLjO7TU*Aq5Kwg4OTdMI7N3%wFAmnwezlEbPUdEQKhGJD10E8@0gSrS'
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'odp', 'ods'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_flash_and_redirect(message, endpoint='index'):
    """Safely flash a message and redirect, handling any errors"""
    try:
        flash(message)
        return redirect(url_for(endpoint))
    except Exception as e:
        logger.error(f"Error in flash_and_redirect: {e}")
        # Fallback without flash if flash fails
        return redirect(url_for(endpoint))

# Error handler for file too large
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    logger.warning("File upload too large attempted")
    return safe_flash_and_redirect('File is too large. Maximum size is 16MB.')

# Error handler for internal server errors (500)
@app.errorhandler(500)
def handle_internal_error(error):
    logger.error(f"Internal server error: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return safe_flash_and_redirect('An internal server error occurred. Please try again.')

# Error handler for 404 errors
@app.errorhandler(404)
def handle_not_found(error):
    logger.warning(f"404 error: {error}")
    return safe_flash_and_redirect('Page not found.')

# Error handler for general exceptions
@app.errorhandler(Exception)
def handle_general_exception(error):
    logger.error(f"Unhandled exception: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Don't handle HTTP exceptions here (let Flask handle them)
    if hasattr(error, 'code'):
        return error
    
    return safe_flash_and_redirect('An unexpected error occurred. Please try again.')

@app.route('/')
def index():
    try:
        return render_template_string(HTML_TEMPLATE)
    except Exception as e:
        logger.error(f"Error rendering index template: {e}")
        return safe_flash_and_redirect('Error loading page. Please refresh.')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if RAG_DV is available
        if RAG_DV is None:
            return safe_flash_and_redirect('RAG Document Viewer is not available. Please check the installation.')
        
        # Validate request
        if 'file' not in request.files:
            return safe_flash_and_redirect('No file selected')
        
        file = request.files['file']
        if file.filename == '' or file.filename is None:
            return safe_flash_and_redirect('No file selected')
        
        if not allowed_file(file.filename):
            return safe_flash_and_redirect('Invalid file type. Please upload a supported document.')
        
        # Generate unique filename to avoid conflicts
        filename = secure_filename(file.filename)
        if not filename:
            return safe_flash_and_redirect('Invalid filename')
        
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create directory structure
        dir_name = Path(str(unique_filename).replace(Path(unique_filename).suffix, ""))
        dir_path = Path(app.config['UPLOAD_FOLDER']) / dir_name
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            return safe_flash_and_redirect('Failed to create upload directory')
        
        file_path = dir_path / unique_filename
        
        # Save file with error handling
        try:
            file.save(str(file_path))
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return safe_flash_and_redirect('Failed to save uploaded file')
        
        # Verify file was saved
        if not file_path.exists():
            return safe_flash_and_redirect('File upload failed - file not saved')
        
        # Process with RAG_DV
        rag_output_path = file_path.parent / "rag_dv"
        try:
            RAG_DV(file_path, rag_output_path)
        except Exception as e:
            logger.error(f"RAG_DV processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Clean up the uploaded file if processing fails
            try:
                file_path.unlink()
                if dir_path.exists() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup after RAG_DV error: {cleanup_error}")
            
            return safe_flash_and_redirect('Failed to process document. Please try again or use a different file.')
        
        # Verify RAG processing created the expected output
        index_file = rag_output_path / "index.html"
        if not index_file.exists():
            return safe_flash_and_redirect('Document processing incomplete. Please try again.')
        
        # Store in session
        session['uploaded_file'] = unique_filename
        session['original_filename'] = filename
        
        return safe_flash_and_redirect('File successfully uploaded.')
        
    except Exception as e:
        logger.error(f"Unexpected error in upload_file: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return safe_flash_and_redirect('Upload failed due to an unexpected error')

@app.route('/refresh')
def refresh():
    try:
        # Clear session data
        session.pop('uploaded_file', None)
        session.pop('original_filename', None)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in refresh: {e}")
        return safe_flash_and_redirect('Error refreshing session')

@app.route('/load/<filename>')
def load(filename):
    try:
        if not filename:
            return safe_flash_and_redirect('Invalid filename')
        
        # Sanitize filename
        filename = secure_filename(filename)
        file_path = Path(app.config['UPLOAD_FOLDER']) / Path(filename).stem / filename
        
        if not file_path.exists():
            logger.warning(f"Attempted to load non-existent file: {file_path}")
            return safe_flash_and_redirect('File not found')
        
        index_file = file_path.parent / "rag_dv" / "index.html"
        if not index_file.exists():
            logger.warning(f"RAG index file not found: {index_file}")
            return safe_flash_and_redirect('Document index not found. Please re-upload the file.')
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read index file {index_file}: {e}")
            return safe_flash_and_redirect('Failed to load document content')
        
        return render_template_string(content)
        
    except Exception as e:
        logger.error(f"Unexpected error in load: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return safe_flash_and_redirect('Error loading document')

@app.route('/load/assets/<asset_type>/<filename>')
def load_assets(asset_type, filename):
    try:
        if 'uploaded_file' not in session:
            return safe_flash_and_redirect('No active session')
        
        # Sanitize inputs
        asset_type = secure_filename(asset_type)
        filename = secure_filename(filename)
        
        if not asset_type or not filename:
            return safe_flash_and_redirect('Invalid asset path')
        
        file_path = (Path(app.config['UPLOAD_FOLDER']) / 
                    Path(session['uploaded_file']).stem / 
                    "rag_dv" / "assets" / asset_type / filename)
        
        if not file_path.exists():
            logger.warning(f"Asset not found: {file_path}")
            return safe_flash_and_redirect('Asset not found')
        
        # Security check - ensure file is within expected directory
        upload_base = Path(app.config['UPLOAD_FOLDER']).resolve()
        if not file_path.resolve().is_relative_to(upload_base):
            logger.warning(f"Attempted path traversal: {file_path}")
            return safe_flash_and_redirect('Invalid file path')
        
        return send_from_directory(str(file_path.parent), filename)
        
    except Exception as e:
        logger.error(f"Error loading asset: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return safe_flash_and_redirect('Error loading asset')

# Add new route for file size error
@app.route('/file_size_error')
def file_size_error():
    flash('File size too large. Please upload a file smaller than 16MB.')
    return redirect(url_for('index'))

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }

        body {
            background: -webkit-linear-gradient(135deg, hsla(0, 0%, 0%, 1) 0%, hsla(0, 0%, 11%, 1) 100%);
            background: linear-gradient(135deg, hsla(0, 0%, 0%, 1) 0%, hsla(0, 0%, 11%, 1) 100%);
            background-attachment: fixed;
            min-height: 100vh;
            position: relative;
            color: #f3f3f3;
            line-height: 1.6;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Upload Area Styles */
        .upload-container {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }

        .upload-area {
            width: 100%;
            max-width: 500px;
            height: 300px;
            border: 2px dashed #4a5568;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
            padding: 0 2rem;
            margin: 0 1rem;
        }

        .upload-area:hover {
            border-color: #6b7280;
            background: rgba(255, 255, 255, 0.08);
        }

        .upload-area.dragover {
            border-color: #9ca3af;
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(255, 255, 255, 0.1);
        }

        .upload-icon {
            font-size: 48px;
            color: #9ca3af;
            margin-bottom: 20px;
        }

        .upload-text {
            font-size: 18px;
            color: #f3f3f3;
            margin-bottom: 10px;
            font-weight: 500;
        }

        .upload-subtext {
            font-size: 14px;
            color: #9ca3af;
            text-align: center;
        }

        .file-input {
            display: none;
        }

        /* Content Area Styles */
        .content-container {
            min-height: 90vh;
            padding: 20px;
        }

        .content-area {
            width: 100%;
            height: calc(100vh - 80px);
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
            overflow: hidden;
            border: 1px solid #374151;
        }

        .content-iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: rgba(255, 255, 255, 0.05);
            display: block;
            box-sizing: border-box;
        }

        /* Refresh Button Styles */
        .refresh-btn {
            font-family: helvetica neue;
            font-weight: bold;
            position: fixed;
            top: 0.5rem;
            left: 0.5rem;
            background: #212529;
            color: #fff;
            border: 0px;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 14px;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: all 0.2s ease;
            opacity: 1;
            z-index: 1000;
            white-space: nowrap;
            width: auto;
            max-width: fit-content;
        }

        .refresh-btn:hover {
            background: #424649;
            border-color: #6b7280;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        /* Flash Messages */
        .flash-messages {
            position: fixed;
            top: 25px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1001;
        }

        .flash-message {
            background: rgba(0, 57, 150, 0.4);
            color: #fff;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2);
            font-weight: 500;
            backdrop-filter: blur(10px);
            text-align: center;
        }

        /* Loading Animation */
        .loading {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }

        .loading.active {
            display: block;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #4a5568;
            border-top: 3px solid #f3f3f3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .upload-area {
                height: 250px;
                margin: 0 1rem;
                padding: 0 1rem;
                max-width: calc(100vw - 2rem);
            }
            
            .upload-text {
                font-size: 16px;
                text-align: center;
            }
            
            .upload-subtext {
                font-size: 13px;
                text-align: center;
            }
            
            .upload-container {
                padding: 0 1rem;
            }
            
            .refresh-btn {
                top: 10px;
                left: 10px;
                padding: 8px 12px;
                font-size: 11px;
                white-space: nowrap;
                width: auto;
                max-width: fit-content;
            }
        }

        @media (max-width: 480px) {
            .upload-area {
                height: 220px;
                margin: 0 0.5rem;
                padding: 0 0.5rem;
                max-width: calc(100vw - 1rem);
            }
            
            .upload-text {
                font-size: 14px;
            }
            
            .upload-subtext {
                font-size: 12px;
            }
            
            .upload-icon {
                font-size: 36px;
                margin-bottom: 15px;
            }
            
            .upload-container {
                padding: 0 0.5rem;
            }
        }
    </style>
</head>
<body>
    <!-- Flash Messages -->
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <div class="flash-messages">
                {% for message in messages %}
                    <div class="flash-message">{{ message }}</div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    <!-- Refresh Button (only visible after upload) -->
    {% if session.uploaded_file %}
        <button class="refresh-btn" onclick="refreshSession()">
            Start over
        </button>
    {% endif %}

    {% if not session.uploaded_file %}
        <!-- Upload Interface -->
        <h2 style="text-align: center; margin-top: 0.25rem;">Rag Document Viewer Demo</h2>
        <div class="upload-container">
            <form id="uploadForm" method="POST" action="/upload" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📂</div>
                    <div class="upload-text">Drop your file here or click to browse</div>
                    <div class="upload-subtext">Supports: PDFs, Office Documents, OpenOffice Documents <br>(Max: 16MB)</div>
                    <input type="file" name="file" class="file-input" id="fileInput" accept=".txt,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.odt,.odp,.ods">
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                    </div>
                </div>
            </form>
        </div>
    {% else %}
        <!-- Content Interface -->
        <h2 style="text-align: center; margin-top: 0.25rem;">Rag Document Viewer Demo</h2>
        <div class="content-container">
            <div class="content-area">
                <div class="content-iframe">
                    <iframe src="{{ url_for('load', filename=session.uploaded_file) }}" 
                            style="width: 100%; height: 100%; border: none; display: block;">
                    </iframe>
                </div>
            </div>
        </div>
    {% endif %}

    <script>
        // File upload handling
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');

        if (uploadArea) {
            // Click to browse
            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });

            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const file = files[0];
                    const maxSize = 16 * 1024 * 1024; // 16MB
                    
                    if (file.size > maxSize) {
                        // Redirect to file size error route instead of alert
                        window.location.href = '/file_size_error';
                        return;
                    }
                    
                    fileInput.files = files;
                    submitForm();
                }
            });

            // File input change
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    const maxSize = 16 * 1024 * 1024; // 16MB
                    
                    if (file.size > maxSize) {
                        // Redirect to file size error route instead of alert
                        fileInput.value = ''; // Clear the file input
                        window.location.href = '/file_size_error';
                        return;
                    }
                    
                    submitForm();
                }
            });

            function submitForm() {
                loading.classList.add('active');
                uploadForm.submit();
            }
        }

        // Refresh session function
        function refreshSession() {
            window.location.href = '/refresh';
        }

        // Auto-hide flash messages after 3 seconds
        setTimeout(() => {
            const flashMessages = document.querySelector('.flash-messages');
            if (flashMessages) {
                flashMessages.style.opacity = '0';
                flashMessages.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    flashMessages.style.display = 'none';
                }, 500);
            }
        }, 5000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)