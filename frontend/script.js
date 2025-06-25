// Global state
let currentSessionId = null;
let currentApp = null;

// API Base URL
const API_BASE = 'http://35.172.183.78:8000/api/v1';


// Tab Management
function switchTab(tabName) {
    // Handle app name mismatches
    const tabMap = {
        'vibe_studio': 'vibe-studio',
        'vibe-studio': 'vibe-studio'
    };
    
    const actualTabName = tabMap[tabName] || tabName;
    
    // Tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    const targetTab = document.getElementById(`tab-${actualTabName}`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // Tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    const targetPane = document.getElementById(`pane-${actualTabName}`);
    if (targetPane) {
        targetPane.classList.add('active');
    }
    
    // Updating current app
    currentApp = actualTabName === 'overview' ? null : actualTabName;
    
    // Sending context to chat
    if (actualTabName !== 'overview') {
        addMessage(`Opened ${actualTabName} app directly. You can work independently here or ask me for help!`, 'steve');
    }
}

// Chat functionality part
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    const loadingDiv = addMessage('Jarvis is thinking...', 'steve');
    loadingDiv.classList.add('loading');

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
                user_id: 'demo_user'
            })
        });

        const data = await response.json();
        loadingDiv.remove();
        addMessage(data.response, 'steve');
        currentSessionId = data.session_id;

        // Handling app opening
        if (data.action === 'open_app' && data.app_to_open && data.app_to_open !== 'chat') {
            setTimeout(() => switchTab(data.app_to_open), 1000);
        }

    } catch (error) {
        loadingDiv.remove();
        addMessage('Sorry, I encountered an error. Please try again.', 'steve');
        console.error('Chat error:', error);
    }
}

function addMessage(text, sender) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageDiv;
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// App generation functions
async function generateAppDirect() {
    const quickIdea = document.getElementById('quickAppIdea').value;
    const requirements = document.getElementById('codeRequirements').value;

    if (!quickIdea.trim()) {
        alert('Please describe your app idea first');
        return;
    }

    const resultDiv = document.getElementById('codeResult');
    resultDiv.innerHTML = '<div class="loading">Generating your simple Streamlit app...</div>';

    try {
        const response = await fetch(`${API_BASE}/vibe-studio/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                app_name: 'vibe_studio',
                action: 'generate',
                session_id: currentSessionId || 'direct_' + Date.now(),
                data: { 
                    requirements: requirements + ' App idea: ' + quickIdea
                }
            })
        });

        const result = await response.json();
        
        if (result.status === 'success') {
            const appData = result.result;
            resultDiv.innerHTML = `
                <div class="success">Simple app generated successfully!</div>
                <div><strong style="margin-bottom: 15px">App Name:</strong> ${appData.app_name}</div>
                <div><strong style="margin-bottom: 15px">Files Generated:</strong> ${appData.app_structure.total_files}</div>
                <div><strong style="margin-bottom: 15px">App Type:</strong> Simple, focused functionality</div>
                <div><strong style="margin-bottom: 15px">Run Command:</strong> <code>${appData.run_command}</code></div>
                
                <div style="margin: 15px 0;">
                    <button class="btn" onclick="downloadProjectFiles('${appData.app_name}')">Download Complete Project ZIP</button>
                </div>
                
                <!-- Individual File Downloads -->
                <div class="file-downloads">
                    <h4>Individual Files:</h4>
                    ${generateFileDownloadButtons(appData.project_files)}
                </div>
            `;
            
            window.currentProjectFiles = appData.project_files;
            window.currentAppName = appData.app_name;
        } else {
            resultDiv.innerHTML = `<div class="error">Failed to generate app: ${result.result?.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error">Error generating app: ${error.message}</div>`;
        console.error('Code generation error:', error);
    }
}

function generateFileDownloadButtons(projectFiles) {
    let buttonsHTML = '';
    
    Object.entries(projectFiles).forEach(([fileName, fileContent]) => {
        const fileSize = new Blob([fileContent]).size;
        const fileSizeFormatted = formatFileSize(fileSize);
        
        buttonsHTML += `
            <div class="file-item">
                <div>
                    <span class="file-name">${fileName}</span>
                    <span class="file-size">(${fileSizeFormatted})</span>
                </div>
                <button class="btn-secondary" onclick="downloadIndividualFile('${fileName}')">
                     Download
                </button>
            </div>
        `;
    });
    
    return buttonsHTML;
}

function downloadIndividualFile(fileName) {
    if (!window.currentProjectFiles || !window.currentProjectFiles[fileName]) {
        alert('File not found');
        return;
    }

    const fileContent = window.currentProjectFiles[fileName];
    const blob = new Blob([fileContent], { type: 'text/plain' });
    
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(blob);
    downloadLink.download = fileName;
    
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    URL.revokeObjectURL(downloadLink.href);
    addMessage(`Downloaded ${fileName} successfully!`, 'steve');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

async function generateImageDirect() {
    const context = document.getElementById('designContext').value;
    const imageType = document.getElementById('imageType').value;
    const prompt = document.getElementById('imagePrompt').value;

    const finalPrompt = prompt || `Create a ${imageType} for ${context || 'a mobile application'}`;

    const resultDiv = document.getElementById('imageResult');
    resultDiv.innerHTML = '<div class="loading">Generating your image...</div>';

    try {
        const response = await fetch(`${API_BASE}/design/generate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                app_name: 'design',
                action: 'generate_image',
                session_id: currentSessionId || 'direct_' + Date.now(),
                data: { 
                    image_type: imageType, 
                    prompt: finalPrompt 
                }
            })
        });

        const result = await response.json();
        
        if (result.status === 'success' && result.result.success) {
            const imageData = result.result;
            resultDiv.innerHTML = `
                <div class="success">Image generated successfully!</div>
                <div><strong style="margin-bottom: 15px">Type:</strong> ${imageData.image_type}</div>
                <div><strong style="margin-bottom: 15px">Prompt :</strong> ${imageData.prompt_used}</div>
                <img src="data:image/jpeg;base64,${imageData.image_data}" style="max-width: 100%; border-radius: 8px; margin-top: 10px;" alt="Generated image">
            `;
        } else {
            resultDiv.innerHTML = `<div class="error">Failed to generate image</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error">Error generating image</div>`;
        console.error('Image generation error:', error);
    }
}

// UPDATED: Email generation with send functionality (NO CTA BUTTON)
async function generateEmailDirect() {
    const context = document.getElementById('emailContext').value;
    const emailType = document.getElementById('emailType').value;
    const targetAudience = document.getElementById('targetAudience').value;

    if (!context.trim()) {
        alert('Please describe what you\'re launching');
        return;
    }

    const resultDiv = document.getElementById('emailResult');
    resultDiv.innerHTML = '<div class="loading">Drafting your email...</div>';

    try {
        const response = await fetch(`${API_BASE}/gmail/draft-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                app_name: 'gmail',
                action: 'draft_email',
                session_id: currentSessionId || 'direct_' + Date.now(),
                data: { 
                    email_type: emailType, 
                    target_audience: targetAudience,
                    context: context
                }
            })
        });

        const result = await response.json();
        
        if (result.status === 'success' && result.result.success) {
            const emailData = result.result;
            
            // Store email data globally for sending
            window.currentEmailData = {
                subject: emailData.subject_line,
                body: emailData.complete_email,
                session_id: currentSessionId || 'direct_' + Date.now()
            };
            
            resultDiv.innerHTML = `
                <div class="success">Email drafted successfully!</div>
                <div><strong style="margin-bottom: 15px">Subject:</strong> ${emailData.subject_line}</div>
                <div><strong style="margin-bottom: 15px">Type:</strong> ${emailData.email_type}</div>
                
                <!-- EMAIL SEND SECTION (NO CTA BUTTON) -->
                <div class="email-send-section" style="margin-top: 20px; padding: 16px; background: rgba(255, 255, 255, 0.04); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.08);">
                    <h4 style="margin-bottom: 12px; color: #ffffff;">Would you like to send this email?</h4>
                    
                    <div class="form-group" style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 8px; color: #ffffff; font-weight: 500;">Recipient Email Address:</label>
                        <input type="email" id="recipientEmail" placeholder="Enter recipient's email address..." 
                               style="width: 100%; padding: 12px 16px; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; color: #ffffff; font-size: 14px; outline: none;">
                    </div>
                    
                    <button class="btn" onclick="sendGeneratedEmail()" style="width: 100%; margin-bottom: 10px;">
                        Send Email Now
                    </button>
                    
                    <div id="emailSendStatus"></div>
                </div>
                
                <details style="margin-top: 15px;">
                    <summary style="cursor: pointer; padding: 8px; background: rgba(255, 255, 255, 0.05); border-radius: 6px;">Preview Email Content</summary>
                    <div style="border: 1px solid rgba(255, 255, 255, 0.08); padding: 15px; margin-top: 10px; border-radius: 8px; background: rgba(255, 255, 255, 0.04); max-height: 400px; overflow-y: auto;">
                        ${emailData.complete_email}
                    </div>
                </details>
            `;
        } else {
            resultDiv.innerHTML = `<div class="error">Failed to generate email</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="error">Error generating email</div>`;
        console.error('Email generation error:', error);
    }
}

// Send generated email function
async function sendGeneratedEmail() {
    const recipientEmail = document.getElementById('recipientEmail').value.trim();
    const statusDiv = document.getElementById('emailSendStatus');
    
    // Validation
    if (!recipientEmail) {
        statusDiv.innerHTML = '<div class="error">Please enter a recipient email address</div>';
        return;
    }
    
    if (!isValidEmail(recipientEmail)) {
        statusDiv.innerHTML = '<div class="error">Please enter a valid email address</div>';
        return;
    }
    
    if (!window.currentEmailData) {
        statusDiv.innerHTML = '<div class="error">No email data found. Please generate an email first.</div>';
        return;
    }
    
    // Show loading state
    statusDiv.innerHTML = '<div class="loading">Sending email...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/gmail/send-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                app_name: 'gmail',
                action: 'send_email',
                session_id: window.currentEmailData.session_id,
                data: {
                    recipient_email: recipientEmail,
                    subject: window.currentEmailData.subject,
                    email_body: window.currentEmailData.body,
                    sender_name: 'Steve Connect'
                }
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.innerHTML = `
                <div class="success">
                    Email sent successfully to ${recipientEmail}!
                    <br><small>Message ID: ${result.result.message_id || 'N/A'}</small>
                    <br><small>Method: ${result.result.method || 'MCP Gmail'}</small>
                </div>
            `;
            
            // Add chat message
            addMessage(`Email sent successfully to ${recipientEmail}!`, 'steve');
            
            // Clear the recipient field
            document.getElementById('recipientEmail').value = '';
            
        } else {
            statusDiv.innerHTML = `
                <div class="error">
                    Failed to send email: ${result.result?.error || result.message || 'Unknown error'}
                </div>
            `;
        }
        
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="error">
                Error sending email: ${error.message}
            </div>
        `;
        console.error('Email sending error:', error);
    }
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Workflow functions (original)
async function submitIdeation() {
    const appName = document.getElementById('appName').value;
    const appDescription = document.getElementById('appDescription').value;
    const appCategory = document.getElementById('appCategory').value;
    
    if (!appName || !appDescription || !appCategory) {
        alert('Please fill in all fields');
        return;
    }

    const data = {
        name: appName,
        description: appDescription,
        category: appCategory
    };

    try {
        const response = await fetch(`${API_BASE}/ideation/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                app_name: 'ideation',
                action: 'submit_data',
                session_id: currentSessionId || 'workflow_' + Date.now(),
                data: data
            })
        });

        const result = await response.json();
        
        if (result.status === 'success') {
            addMessage(result.next_suggestion, 'steve');
            document.getElementById('ideationResult').innerHTML = `
                <div class="success">Ideation completed successfully!</div>
                <div><strong>App Name:</strong> ${appName}</div>
                <div><strong>Category:</strong> ${appCategory}</div>
                <div><strong>Description:</strong> ${appDescription}</div>
                <p>Ready to continue the workflow? Check the chat for next steps!</p>
            `;
            
            // Auto-suggest next step
            setTimeout(() => {
                addMessage("Ready to build your app? Say 'yes' and I'll open Vibe Studio!", 'steve');
            }, 2000);
        }
    } catch (error) {
        console.error('Ideation error:', error);
        addMessage('Failed to save ideation data. Please try again.', 'steve');
    }
}

// Download functionality
async function downloadProjectFiles(appName) {
    if (!window.currentProjectFiles) {
        alert('No project files available for download');
        return;
    }

    try {
        if (!window.JSZip) {
            await loadJSZip();
        }

        const zip = new JSZip();
        
        Object.entries(window.currentProjectFiles).forEach(([filePath, fileContent]) => {
            zip.file(filePath, fileContent);
        });

        const zipBlob = await zip.generateAsync({type: "blob"});
        
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(zipBlob);
        downloadLink.download = `${appName || 'streamlit-app'}-project.zip`;
        
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        URL.revokeObjectURL(downloadLink.href);
        addMessage(`Downloaded ${appName} project files successfully!`, 'steve');
        
    } catch (error) {
        console.error('Download error:', error);
        alert('Failed to download project files. Please try again.');
    }
}

function loadJSZip() {
    return new Promise((resolve, reject) => {
        if (window.JSZip) {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js';
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load JSZip library'));
        document.head.appendChild(script);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    addMessage('Welcome! You can either follow the guided workflow or jump directly to any app using the tabs above. What would you like to work on?', 'steve');
});