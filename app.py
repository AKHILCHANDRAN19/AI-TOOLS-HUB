import os
import uuid
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from rembg import remove
from PIL import Image
from g4f.client import Client

app = Flask(__name__)
client = Client()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB limit

# Create uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Home Page Template
home_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tools Hub</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        
        body {
            margin: 0;
            padding: 0;
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(120deg, #1E1E2F, #292A40, #2E314F);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            text-align: center;
            animation: fadeIn 1.5s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        .container {
            max-width: 800px;
            width: 100%;
            padding: 20px;
            box-sizing: border-box;
        }
        h1 {
            font-size: min(2.5rem, 6vw);
            font-weight: 700;
            text-shadow: 2px 2px 10px rgba(255, 255, 255, 0.3);
            margin: 0 0 30px 0;
        }
        .tools {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            padding: 0 20px;
        }
        .tool-box {
            width: 180px;
            height: 200px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.4s ease-in-out;
            flex-shrink: 0;
        }
        .tool-box:hover {
            box-shadow: 0 0 20px #ff6a95;
            transform: scale(1.1);
        }
        .tool-box img {
            width: min(70px, 20vw);
            margin-bottom: 10px;
        }
        .tool-box p {
            font-size: min(1rem, 3.5vw);
            font-weight: 500;
            padding: 0 10px;
        }

        @media (max-width: 600px) {
            .tools {
                gap: 15px;
                padding: 0 10px;
            }
            .tool-box {
                width: calc(50% - 20px);
                height: 180px;
            }
        }

        @media (max-width: 400px) {
            .tool-box {
                width: 100%;
                max-width: 260px;
                height: 160px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to AI Tools Hub</h1>
        <div class="tools">
            <div class="tool-box" onclick="redirectTo('/ai-image')">
                <img src="https://img.icons8.com/ios/100/000000/artificial-intelligence.png" alt="AI Image">
                <p>AI Image Generator</p>
            </div>
            <div class="tool-box" onclick="redirectTo('/remove-background')">
                <img src="https://img.icons8.com/clouds/100/000000/background-remover.png" alt="AI bg remover">
                <p>AI Bg Remover</p>
            </div>
            <div class="tool-box" onclick="redirectTo('/pencil_sketch')>
                <img src="https://img.icons8.com/clouds/100/000000/brain.png" alt="AI Analysis">
                <p>AI Drawing Generator</p>
            </div>
        </div>
    </div>

    <script>
        function redirectTo(url) {
            window.location.href = url;
        }
    </script>
</body>
</html>
"""
            

# AI Image Generator Page Template
ai_image_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Image Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(120deg, #292A40, #2E314F, #3C3F60);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        h1 {
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 700;
            text-align: center;
            margin-bottom: 20px;
        }

        .input-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-width: 800px;
            margin: 0 auto;
        }

        .input-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        input, select {
            padding: 12px;
            border-radius: 8px;
            border: none;
            font-size: 1rem;
            flex: 1;
            min-width: 200px;
        }

        select {
            background: white;
            cursor: pointer;
        }

        .btn {
            background: #ff6a95;
            color: white;
            border: none;
            padding: 12px 25px;
            font-size: 1rem;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s ease;
            text-decoration: none;
            text-align: center;
            min-width: 120px;
        }

        .btn:hover {
            background: #ff4f7e;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 106, 149, 0.3);
        }

        .progress-container {
            margin: 20px auto;
            max-width: 600px;
        }

        .progress-bar {
            width: 100%;
            height: 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            overflow: hidden;
        }

        .progress {
            width: 0%;
            height: 100%;
            background: #ff6a95;
            border-radius: 6px;
            transition: width 0.5s ease-in-out;
        }

        .image-grid {
            display: grid;
            gap: 20px;
            margin-top: 30px;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }

        .image-card {
            position: relative;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s ease;
        }

        .image-card:hover {
            transform: translateY(-5px);
        }

        .image-wrapper {
            position: relative;
            padding-top: 100%;
        }

        .ratio-16-9 .image-wrapper {
            padding-top: 56.25%;
        }

        .ratio-9-16 .image-wrapper {
            padding-top: 177.78%;
        }

        .ratio-4-3 .image-wrapper {
            padding-top: 75%;
        }

        .ratio-3-2 .image-wrapper {
            padding-top: 66.67%;
        }

        .image-card img {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .card-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .image-card:hover .card-overlay {
            opacity: 1;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.9);
            z-index: 1000;
            padding: 20px;
        }

        .modal-content {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .modal img {
            max-width: 100%;
            max-height: 90vh;
            object-fit: contain;
        }

        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            font-size: 30px;
            cursor: pointer;
            z-index: 1001;
        }

        .loading-spinner {
            display: none;
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #ff6a95;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            .input-row {
                flex-direction: column;
            }

            .btn {
                width: 100%;
            }

            .image-grid {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
            }
        }

        @media (max-width: 480px) {
            .image-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Image Generator</h1>
        <div class="input-container">
            <div class="input-row">
                <input type="text" id="prompt" placeholder="Enter your AI image prompt...">
                <select id="aspectRatio">
                    <option value="1:1">Square (1:1)</option>
                    <option value="16:9">Landscape (16:9)</option>
                    <option value="9:16">Portrait (9:16)</option>
                    <option value="4:3">Standard (4:3)</option>
                    <option value="3:2">Photo (3:2)</option>
                </select>
            </div>
            <button class="btn" onclick="startGeneration()">Generate Images</button>
        </div>

        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress" id="progress"></div>
            </div>
        </div>

        <div class="loading-spinner" id="spinner"></div>
        <div class="image-grid" id="imageGrid"></div>
    </div>

    <div class="modal" id="imageModal" onclick="closeModal(event)">
        <span class="modal-close">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="" alt="Enlarged Image">
        </div>
    </div>

    <script>
        let currentRatio = '1:1';

        function startGeneration() {
            const prompt = document.getElementById("prompt").value;
            currentRatio = document.getElementById("aspectRatio").value;
            
            if (!prompt) {
                alert("Please enter a prompt!");
                return;
            }
            
            document.getElementById("progress").style.width = "0%";
            document.getElementById("spinner").style.display = "block";
            document.getElementById("imageGrid").innerHTML = '';
            
            let width = 0;
            let interval = setInterval(() => {
                if (width >= 90) {
                    clearInterval(interval);
                } else {
                    width += 1;
                    document.getElementById("progress").style.width = width + "%";
                }
            }, 50);

            fetch(`/generate-image?prompt=${encodeURIComponent(prompt)}&aspect_ratio=${encodeURIComponent(currentRatio)}`)
                .then(response => response.json())
                .then(data => {
                    clearInterval(interval);
                    document.getElementById("progress").style.width = "100%";
                    document.getElementById("spinner").style.display = "none";
                    
                    if (data.success) {
                        displayImages(data.image_urls);
                    } else {
                        alert("Failed to generate images: " + data.message);
                    }
                })
                .catch(error => {
                    clearInterval(interval);
                    document.getElementById("spinner").style.display = "none";
                    console.error("Error:", error);
                    alert("Error generating images. Please try again.");
                });
        }

        function displayImages(imageUrls) {
            const grid = document.getElementById("imageGrid");
            grid.innerHTML = '';
            
            imageUrls.forEach((url, index) => {
                const card = document.createElement('div');
                card.className = `image-card ratio-${currentRatio.replace(':', '-')}`;
                
                const wrapper = document.createElement('div');
                wrapper.className = 'image-wrapper';
                
                const img = document.createElement('img');
                img.src = url;
                img.alt = `Generated Image ${index + 1}`;
                img.loading = 'lazy';
                
                const overlay = document.createElement('div');
                overlay.className = 'card-overlay';
                
                const downloadBtn = document.createElement('a');
                downloadBtn.className = 'btn';
                downloadBtn.href = url;
                downloadBtn.download = `ai-image-${index + 1}.png`;
                downloadBtn.textContent = 'Download';
                downloadBtn.onclick = (e) => e.stopPropagation();
                
                wrapper.appendChild(img);
                overlay.appendChild(downloadBtn);
                card.appendChild(wrapper);
                card.appendChild(overlay);
                
                card.onclick = () => openModal(url);
                grid.appendChild(card);
            });
        }

        function openModal(imageUrl) {
            const modal = document.getElementById("imageModal");
            const modalImg = document.getElementById("modalImage");
            modal.style.display = "flex";
            modalImg.src = imageUrl;
        }

        function closeModal(event) {
            if (event.target.id === "imageModal" || event.target.className === "modal-close") {
                document.getElementById("imageModal").style.display = "none";
            }
        }
    </script>
</body>
</html>
"""

# HTML Template
BGREMOVER_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Background Remover</title>
    <style>
        /* CSS Styles */
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(120deg, #292A40, #2E314F, #3C3F60);
            min-height: 100vh;
            color: white;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
        }

        .welcome-section {
            text-align: center;
            margin-bottom: 40px;
        }

        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .feature-card h3 {
            color: #ff6a95;
            margin-bottom: 10px;
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
        }

        form {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }

        input[type="file"] {
            padding: 10px;
            border-radius: 5px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }

        .btn {
            background: #ff6a95;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn:hover {
            background: #ff4f7e;
            transform: translateY(-2px);
        }

        .download-btn {
            background: #4CAF50;
        }

        .download-btn:hover {
            background: #45a049;
        }

        .delete-btn {
            background: #f44336;
        }

        .delete-btn:hover {
            background: #da190b;
        }

        .error {
            color: #ff4444;
            text-align: center;
            margin: 10px 0;
        }

        .progress-container {
            margin: 20px auto;
            max-width: 600px;
        }

        .progress-bar {
            width: 100%;
            height: 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress {
            width: 0%;
            height: 100%;
            background: #ff6a95;
            border-radius: 6px;
            transition: width 0.5s ease-in-out;
        }

        .progress-text {
            text-align: center;
            color: white;
        }

        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255, 255, 255, 0.1);
            border-top: 5px solid #ff6a95;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .images {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 30px;
        }

        .image-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .image-card img {
            max-width: 300px;
            max-height: 300px;
            border-radius: 5px;
            margin: 10px 0;
        }

        .button-group {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 10px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
                margin: 10px;
            }
            
            .image-card img {
                max-width: 100%;
                height: auto;
            }
            
            form {
                flex-direction: column;
                align-items: center;
            }
            
            input[type="file"] {
                width: 100%;
                max-width: 300px;
            }
            
            .button-group {
                flex-direction: column;
                gap: 15px;
            }
            
            .btn {
                width: 100%;
                text-align: center;
            }
        }

        @media (min-width: 769px) and (max-width: 1024px) {
            .container {
                max-width: 90%;
            }
            
            .image-card img {
                max-width: 250px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="welcome-section">
            <h1>BG REMOVER TOOL</h1>
            <p>Upload your image and remove the background instantly!</p>
        </div>

        <div class="features">
            <div class="feature-card">
                <h3>Easy to Use</h3>
                <p>Simply upload your image and let our AI do the work</p>
            </div>
            <div class="feature-card">
                <h3>Fast Processing</h3>
                <p>Get your background-free image in seconds</p>
            </div>
            <div class="feature-card">
                <h3>High Quality</h3>
                <p>Maintain original image quality after processing</p>
            </div>
        </div>

        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".png,.jpg,.jpeg" required>
            <button type="submit" class="btn">Remove Background</button>
        </form>
        
        <div id="error" class="error"></div>

        <div class="progress-container" style="display: none;">
            <div class="progress-bar">
                <div class="progress" id="progress"></div>
            </div>
            <div class="progress-text">Processing your image...</div>
        </div>

        <div class="loading-spinner" id="spinner" style="display: none;"></div>

        <div id="imageContainer" class="images" style="display: none;">
            <div class="image-card">
                <h3>Original Image</h3>
                <img id="inputImage" src="" alt="Original">
            </div>
            <div class="image-card">
                <h3>Processed Image</h3>
                <img id="outputImage" src="" alt="Processed">
                <div class="button-group">
                    <a id="downloadBtn" href="#" class="btn download-btn" download>Download</a>
                    <button id="deleteBtn" class="btn delete-btn">Delete</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // JavaScript
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                showError('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show progress bar and spinner
            document.querySelector('.progress-container').style.display = 'block';
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('error').textContent = '';
            
            // Simulate progress
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 90) {
                    clearInterval(interval);
                } else {
                    width += 1;
                    document.getElementById('progress').style.width = width + '%';
                }
            }, 50);
            
            fetch('/bg-remove', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(interval);
                document.getElementById('progress').style.width = '100%';
                document.getElementById('spinner').style.display = 'none';
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                // Display images
                document.getElementById('imageContainer').style.display = 'flex';
                document.getElementById('inputImage').src = `/uploads/${data.input_image}`;
                document.getElementById('outputImage').src = `/uploads/${data.output_image}`;
                
                // Setup download button
                const downloadBtn = document.getElementById('downloadBtn');
                downloadBtn.href = `/uploads/${data.output_image}`;
                downloadBtn.download = 'processed_image.png';
                
                // Setup delete button
                document.getElementById('deleteBtn').onclick = () => deleteImage(data.output_image);
            })
            .catch(error => {
                clearInterval(interval);
                document.getElementById('spinner').style.display = 'none';
                showError('Error processing image. Please try again.');
                console.error('Error:', error);
            });
        });

        function showError(message) {
            document.getElementById('error').textContent = message;
            document.querySelector('.progress-container').style.display = 'none';
        }

        function deleteImage(filename) {
            fetch(`/delete/${filename}`, {
                method: 'POST'
            })
            .then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    showError('Error deleting image');
                }
            })
            .catch(error => {
                showError('Error deleting image');
                console.error('Error:', error);
            });
        }
    </script>
</body>
</html>
'''

PENCIL_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pencil Sketch Generator</title>
    <style>
        /* Base styling */
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(120deg, #292A40, #2E314F, #3C3F60);
            min-height: 100vh;
            color: white;
            margin: 0;
            padding: 20px;
            opacity: 0;
            animation: fadeIn 1s forwards;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            animation: slideIn 0.8s ease-out;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        form {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }
        input[type="file"] {
            padding: 10px;
            border-radius: 5px;
            border: 2px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: white;
        }
        .btn {
            background: #ff6a95;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #ff4f7e;
            transform: translateY(-2px);
        }
        .download-btn {
            background: #4CAF50;
        }
        .download-btn:hover {
            background: #45a049;
        }
        .error {
            color: #ff4444;
            text-align: center;
            margin: 10px 0;
        }
        .progress-container {
            margin: 20px auto;
            max-width: 600px;
        }
        .progress-bar {
            width: 100%;
            height: 12px;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress {
            width: 0%;
            height: 100%;
            background: #ff6a95;
            border-radius: 6px;
            transition: width 0.5s ease-in-out;
        }
        .progress-text {
            text-align: center;
        }
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 5px solid rgba(255,255,255,0.1);
            border-top: 5px solid #ff6a95;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        .images {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 30px;
            margin-top: 30px;
            opacity: 0;
            animation: fadeIn 1s forwards;
            animation-delay: 0.5s;
        }
        .image-card {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transform: translateY(20px);
            animation: slideUp 0.6s forwards;
        }
        .image-card img {
            max-width: 100%;
            border-radius: 5px;
            margin: 10px 0;
        }
        .button-group {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 10px;
        }
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from { transform: translateX(-100px); }
            to { transform: translateX(0); }
        }
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        /* Responsive Design */
        /* Mobile */
        @media (max-width: 767px) {
            form {
                flex-direction: column;
                align-items: center;
            }
            input[type="file"] {
                width: 100%;
                max-width: 300px;
            }
            .button-group {
                flex-direction: column;
                gap: 15px;
            }
            .btn {
                width: 100%;
                text-align: center;
            }
        }
        /* Tablet */
        @media (min-width: 768px) and (max-width: 1024px) {
            .container {
                max-width: 90%;
            }
            .image-card img {
                max-width: 250px;
            }
        }
        /* Desktop */
        @media (min-width: 1025px) {
            .container {
                max-width: 1000px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="welcome-section">
            <h1>Pencil Sketch Generator</h1>
        </div>
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="file" id="fileInput" accept=".png,.jpg,.jpeg" required>
            <button type="submit" class="btn">Generate Sketches</button>
        </form>
        <div id="error" class="error"></div>
        <div class="progress-container" style="display: none;">
            <div class="progress-bar">
                <div class="progress" id="progress"></div>
            </div>
            <div class="progress-text">Processing your image...</div>
        </div>
        <div class="loading-spinner" id="spinner" style="display: none;"></div>
        <div id="imageContainer" class="images" style="display: none;">
            <div class="image-card">
                <h3>Original Image</h3>
                <img id="inputImage" src="" alt="Original">
            </div>
            <div class="image-card">
                <h3>MODEL 1</h3>
                <img id="cv2Image" src="" alt="CV2 Sketch">
                <div class="button-group">
                    <a id="downloadCv2" href="#" class="btn download-btn" download>Download</a>
                </div>
            </div>
            <div class="image-card">
                <h3>MODEL 2</h3>
                <img id="scikitImage" src="" alt="Enhanced Sketch">
                <div class="button-group">
                    <a id="downloadScikit" href="#" class="btn download-btn" download>Download</a>
                </div>
            </div>
        </div>
    </div>
    <script>
        // Handle form submission and show progress animations
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            if (!file) {
                showError('Please select a file');
                return;
            }
            const formData = new FormData();
            formData.append('file', file);
            document.querySelector('.progress-container').style.display = 'block';
            document.getElementById('spinner').style.display = 'block';
            document.getElementById('error').textContent = '';
            
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 90) {
                    clearInterval(interval);
                } else {
                    width += 1;
                    document.getElementById('progress').style.width = width + '%';
                }
            }, 50);
            
            fetch('/', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(interval);
                document.getElementById('progress').style.width = '100%';
                document.getElementById('spinner').style.display = 'none';
                if (data.error) {
                    showError(data.error);
                    return;
                }
                document.getElementById('imageContainer').style.display = 'grid';
                document.getElementById('inputImage').src = `/uploads/${data.input_image}`;
                document.getElementById('cv2Image').src = `/uploads/${data.cv2_image}`;
                document.getElementById('scikitImage').src = `/uploads/${data.scikit_image}`;
                document.getElementById('downloadCv2').href = `/download/${data.cv2_image}`;
                document.getElementById('downloadScikit').href = `/download/${data.scikit_image}`;
            })
            .catch(error => {
                clearInterval(interval);
                document.getElementById('spinner').style.display = 'none';
                showError('Error processing image. Please try again.');
                console.error('Error:', error);
            });
        });
        
        function showError(message) {
            document.getElementById('error').textContent = message;
            document.querySelector('.progress-container').style.display = 'none';
        }
    </script>
</body>
</html>
'''

@app.route("/")
def home():
    return render_template_string(home_html)

@app.route("/ai-image")
def ai_image():
    return render_template_string(ai_image_html)

@app.route("/remove-background")
def remove_background():
    return render_template_string(BGREMOVER_HTML_TEMPLATE)

@app.route("/pencil_sketch")
def pencil_sketch():
    return render_template_string(PENCIL_HTML_TEMPLATE)

@app.route('/generate-image')
def generate_image():
    prompt = request.args.get('prompt', '')
    aspect_ratio = request.args.get('aspect_ratio', '1:1')
    
    if not prompt:
        return jsonify({'success': False, 'message': 'No prompt provided'})

    try:
        ratio_map = {
            '1:1': (1024, 1024),
            '16:9': (1280, 720),
            '9:16': (720, 1280),
            '4:3': (1024, 768),
            '3:2': (1200, 800)
        }
        width, height = ratio_map.get(aspect_ratio, (1024, 1024))
        
        image_urls = []
        for _ in range(4):
            response = client.images.generate(
                model="flux",
                prompt=prompt,
                response_format="url",
                width=width,
                height=height
            )
            image_urls.append(response.data[0].url)
        
        return jsonify({'success': True, 'image_urls': image_urls})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/bg-remove', methods=['GET', 'POST'])
def bg_remove():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})

        if file and allowed_file(file.filename):
            try:
                # Generate unique filenames
                uid = str(uuid.uuid4())
                input_filename = f"input_{uid}.png"
                output_filename = f"output_{uid}.png"

                # Save input file
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
                file.save(input_path)

                # Process image
                input_image = Image.open(input_path)
                output_image = remove(input_image)

                # Save output image
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
                output_image.save(output_path)

                return jsonify({
                    'input_image': input_filename,
                    'output_image': output_filename
                })
            except Exception as e:
                return jsonify({'error': f'Error processing image: {str(e)}'})

        return jsonify({'error': 'Invalid file type'})

    return render_template_string(HTML_TEMPLATE)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        return '', 204
    except Exception as e:
        return jsonify({'error': f'Error deleting file: {str(e)}'}), 500
        
if __name__ == '__main__':
    app.run(debug=True)
