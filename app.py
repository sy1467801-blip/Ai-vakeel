ai-vakeel/
├── package.json
├── .env.example
├── server.js
├── public/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
  {
  "name": "ai-vakeel",
  "version": "1.0.0",
  "description": "Your AI-Powered Indian Legal Assistant",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2",
    "multer": "^1.4.5-lts.1",
    "openai": "^4.56.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
  }
  PORT=3000
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const dotenv = require('dotenv');
const OpenAI = require('openai');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';

// In-memory upload handling for security (no files left on disk)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 } // 5MB limit
});

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// Initialize OpenAI client if key is present
const apiKey = process.env.OPENAI_API_KEY ? process.env.OPENAI_API_KEY.trim() : null;
let openai = null;
if (apiKey) {
  openai = new OpenAI({ apiKey });
}

// System prompt enforcing Indian Legal standards & ethics
const INDIAN_LEGAL_SYSTEM_PROMPT = `
You are "AI Vakeel", an expert Indian Legal AI Assistant.
Your mission is to help Indian citizens understand their legal rights, draft structured documents, research Indian statutory law, and analyze legal notices or case files.

CORE DIRECTIVES:
1. Always base advice on Indian Law (Constitutional Law, Criminal Law [Bharatiya Nyaya Sanhita 2023 / Bharatiya Nagarik Suraksha Sanhita 2023 / Bharatiya Sakshya Adhiniyam 2023 as well as relevant historical IPC/CrPC references where older cases apply], Civil Procedure Code, Property Law, Family & Personal Laws, Consumer Protection Act 2019, IT Act 2000, Motor Vehicles Act, RTI Act 2005, and Labour Codes).
2. Clarify that Indian laws may have State-specific amendments (e.g., Rent Control Acts, Stamp Duty, Police Regulations). Ask the user for their Indian State/UT if relevant to their situation.
3. LANGUAGE HANDLING:
   - If the user interacts in Hindi (Devanagari or Romanized/Hinglish) or requests Hindi, reply in clear, natural, respectful Hindi (or bilingual Hindi-English terminology where appropriate).
   - If the user selects English, reply in clean, accessible Indian Legal English.
4. ACCURACY & ANTI-HALLUCINATION:
   - Never invent legal sections, case laws, or citations.
   - Reference official sources: India Code (indiacode.nic.in), Supreme Court of India (sci.gov.in), eCourts (ecourts.gov.in), and NALSA (nalsa.gov.in).
   - Explicitly note if an issue is still unsettled in law or requires evidentiary verification.
5. LEGAL DRAFTING:
   - When generating drafts (RTI, Legal Notices, Police Complaints, Consumer Complaints, Affidavits, Rent Agreements), use professional legal formats with standard placeholders like [Name], [Address], [Date], [Police Station Jurisdiction], [Amount].
6. MANDATORY DISCLAIMER:
   - Always clarify that AI Vakeel provides general legal information and drafting assistance, not an advocate-client professional representation, and advise consultation with a licensed advocate before filing documents in court.
`;

// Helper function to call OpenAI safely
async function callOpenAI(messages, temperature = 0.3) {
  if (!openai) {
    throw new Error('OPENAI_API_KEY_MISSING');
  }
  const completion = await openai.chat.completions.create({
    model: OPENAI_MODEL,
    messages,
    temperature,
  });
  return completion.choices[0].message.content;
}

// 1. Health check & configuration check
app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    appName: 'AI Vakeel',
    aiConfigured: Boolean(openai),
    model: OPENAI_MODEL
  });
});

// 2. Chatbot Endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { message, conversationHistory = [], language = 'en', state = '' } = req.body;
    if (!message || !message.trim()) {
      return res.status(400).json({ error: 'Message cannot be empty.' });
    }

    if (!openai) {
      return res.status(503).json({
        error: 'OPENAI_API_KEY_MISSING',
        message: 'OpenAI API Key is not configured yet.',
        fallbackNotice: 'Please add your OPENAI_API_KEY in Replit Secrets or environment variables to enable live AI consultations.'
      });
    }

    const messages = [
      { role: 'system', content: `${INDIAN_LEGAL_SYSTEM_PROMPT}\nUser Preferred Language: ${language === 'hi' ? 'Hindi' : 'English'}.\nUser Indian State/Jurisdiction: ${state || 'Not specified'}.` },
      ...conversationHistory.slice(-6),
      { role: 'user', content: message }
    ];

    const reply = await callOpenAI(messages, 0.3);
    res.json({ reply });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({
      error: 'AI_ERROR',
      message: error.message || 'Error communicating with AI service.'
    });
  }
});

// 3. Document Generator Endpoint
app.post('/api/draft', async (req, res) => {
  try {
    const { docType, state, language = 'en', details } = req.body;
    if (!docType || !details) {
      return res.status(400).json({ error: 'Document type and key details are required.' });
    }

    if (!openai) {
      return res.status(503).json({
        error: 'OPENAI_API_KEY_MISSING',
        message: 'OpenAI API Key is missing. Add your key to generate dynamic drafts.'
      });
    }

    const prompt = `
Create a complete, properly structured draft for: "${docType}".
Jurisdiction / State: ${state || 'General Indian Jurisdiction'}
Language: ${language === 'hi' ? 'Hindi (Devanagari)' : 'English'}
User-provided details:
${JSON.stringify(details, null, 2)}

Requirements:
1. Include standard legal headers, subject line, jurisdiction, formal opening, factual statement paragraphs, grounds/violations, prayer/demand clause, and verification/signature blocks.
2. Use clear placeholders like [INSERT DATE], [INSERT OPPOSITE PARTY ADDRESS], [INSERT POLICE STATION NAME] wherever critical information must be filled in.
3. Include statutory references where applicable (e.g. Section 6(1) RTI Act 2005, Section 35 Consumer Protection Act 2019, Section 138 NI Act, or relevant provisions of BNS/BNSS 2023).
4. At the end, add an Advocate Review Checklist with 3-4 points the user must verify before signing or dispatching.
`;

    const messages = [
      { role: 'system', content: INDIAN_LEGAL_SYSTEM_PROMPT },
      { role: 'user', content: prompt }
    ];

    const draft = await callOpenAI(messages, 0.2);
    res.json({ draft });
  } catch (error) {
    console.error('Draft error:', error);
    res.status(500).json({ error: 'AI_ERROR', message: error.message });
  }
});

// 4. Legal Research Endpoint
app.post('/api/research', async (req, res) => {
  try {
    const { query, category, language = 'en' } = req.body;
    if (!query) {
      return res.status(400).json({ error: 'Research query is required.' });
    }

    if (!openai) {
      return res.status(503).json({
        error: 'OPENAI_API_KEY_MISSING',
        message: 'OpenAI API Key is missing. Add key to search Indian statutes and rulings.'
      });
    }

    const prompt = `
Conduct an Indian legal research review for this topic: "${query}".
Category: ${category || 'General Indian Law'}
Language: ${language === 'hi' ? 'Hindi' : 'English'}

Provide a structured briefing containing:
1. Relevant Statutory Provisions (Mention accurate Act name, Section number, and brief description. If transitioning between IPC/CrPC and BNS/BNSS 2023, note both).
2. Landmark Judgments & Precedents (Mention only real, established Supreme Court or High Court judgments; state ratio decidendi clearly. DO NOT invent citations).
3. Official Portals to check: Include clickable Markdown links to:
   - India Code: https://www.indiacode.nic.in/
   - Supreme Court of India: https://www.sci.gov.in/
   - eCourts Services: https://ecourts.gov.in/
   - NALSA: https://nalsa.gov.in/
4. Status of Law: Mention if any recent amendments or judicial benches have examined this issue.
`;

    const messages = [
      { role: 'system', content: INDIAN_LEGAL_SYSTEM_PROMPT },
      { role: 'user', content: prompt }
    ];

    const research = await callOpenAI(messages, 0.2);
    res.json({ research });
  } catch (error) {
    console.error('Research error:', error);
    res.status(500).json({ error: 'AI_ERROR', message: error.message });
  }
});

// 5. Case Document Analysis Endpoint (Text or File Upload)
app.post('/api/analyze', upload.single('documentFile'), async (req, res) => {
  try {
    let documentText = req.body.documentText || '';
    const language = req.body.language || 'en';

    if (req.file) {
      // Decode uploaded text or buffer
      documentText = req.file.buffer.toString('utf-8');
    }

    if (!documentText || documentText.trim().length < 20) {
      return res.status(400).json({
        error: 'Please paste or upload valid document text (at least 20 characters).'
      });
    }

    if (!openai) {
      return res.status(503).json({
        error: 'OPENAI_API_KEY_MISSING',
        message: 'OpenAI API Key is missing. Add key to perform AI document analysis.'
      });
    }

    // Truncate document text to avoid token limits
    const safeText = documentText.slice(0, 15000);

    const prompt = `
Analyze the following Indian legal document text:
"""
${safeText}
"""

Output language: ${language === 'hi' ? 'Hindi' : 'English'}.
Provide a clear, structured breakdown:
1. Document Type (e.g., Legal Notice, FIR, Bail Order, Rental Agreement, Sale Deed, Petition).
2. Plain-Language Summary (Explain in simple terms an ordinary citizen can understand).
3. Critical Dates, Deadlines & Financial Amounts (List chronologically).
4. Key Legal Rights, Liabilities, & Risks identified.
5. Next Actionable Steps.
6. 5 Precise Questions to Ask an Indian Advocate regarding this document.

Warn the user to redact Aadhaar, PAN, and bank credentials before uploading sensitive files.
`;

    const messages = [
      { role: 'system', content: INDIAN_LEGAL_SYSTEM_PROMPT },
      { role: 'user', content: prompt }
    ];

    const analysis = await callOpenAI(messages, 0.2);
    res.json({ analysis });
  } catch (error) {
    console.error('Analyze error:', error);
    res.status(500).json({ error: 'AI_ERROR', message: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`=========================================`);
  console.log(` AI Vakeel is running on port ${PORT}`);
  console.log(` Local access: http://localhost:${PORT}`);
  console.log(` OpenAI Configured: ${Boolean(openai) ? 'YES' : 'NO (Add OPENAI_API_KEY)'}`);
  console.log(`=========================================`);
});
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AI Vakeel - Your AI-Powered Indian Legal Assistant</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>

  <!-- Top Navigation Bar -->
  <header class="app-header">
    <div class="header-inner">
      <div class="brand">
        <div class="brand-emblem">⚖️</div>
        <div>
          <h1 class="brand-title">AI Vakeel</h1>
          <p class="brand-tagline" data-i18n="tagline">Your AI-Powered Indian Legal Assistant</p>
        </div>
      </div>
      <div class="header-controls">
        <select id="langSelect" class="lang-selector" aria-label="Select Language">
          <option value="en">English</option>
          <option value="hi">हिन्दी (Hindi)</option>
        </select>
      </div>
    </div>
  </header>

  <!-- Banner for Missing API Key Alert -->
  <div id="apiKeyBanner" class="api-banner hidden">
    <div class="banner-content">
      <span>⚠️ <strong>Setup Required:</strong> Add your <code>OPENAI_API_KEY</code> in Replit Secrets to activate full AI features.</span>
      <button id="dismissBannerBtn" class="dismiss-btn">&times;</button>
    </div>
  </div>

  <!-- Mandatory Legal Disclaimer Banner -->
  <aside class="disclaimer-banner">
    <div class="disclaimer-content">
      <strong data-i18n="disclaimerTitle">Legal Disclaimer:</strong>
      <span data-i18n="disclaimerText">AI Vakeel provides general legal information and drafting assistance, not professional legal advice. AI-generated answers may contain errors. Verify current laws and citations through official sources and consult a qualified Indian advocate before making important legal decisions or filing documents.</span>
    </div>
  </aside>

  <!-- Main Container -->
  <main class="main-content">

    <!-- Screen 1: Home Dashboard with 4 Large Action Cards -->
    <section id="homeScreen" class="screen active">
      <div class="welcome-box">
        <h2 data-i18n="welcomeTitle">Namaste! How can AI Vakeel assist you today?</h2>
        <p data-i18n="welcomeSub">Select a service below to get instant guidance on Indian Law, prepare legal drafts, or analyze court documents.</p>
      </div>

      <div class="action-grid">
        <!-- Card 1 -->
        <button class="action-card" onclick="navigateTo('chat')">
          <div class="card-icon">💬</div>
          <div class="card-text">
            <h3 data-i18n="card1Title">Ask a Legal Question</h3>
            <p data-i18n="card1Desc">Get simplified answers on Criminal, Civil, Property, Family, Consumer & Cyber Law.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- Card 2 -->
        <button class="action-card" onclick="navigateTo('draft')">
          <div class="card-icon">📝</div>
          <div class="card-text">
            <h3 data-i18n="card2Title">Draft a Legal Document</h3>
            <p data-i18n="card2Desc">Prepare ready-to-use RTI, Legal Notices, Complaints, Agreements & Affidavits.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- Card 3 -->
        <button class="action-card" onclick="navigateTo('research')">
          <div class="card-icon">🔍</div>
          <div class="card-text">
            <h3 data-i18n="card3Title">Research Indian Law</h3>
            <p data-i18n="card3Desc">Find authentic sections from India Code, BNS/BNSS, and Supreme Court rulings.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- Card 4 -->
        <button class="action-card" onclick="navigateTo('analyze')">
          <div class="card-icon">📑</div>
          <div class="card-text">
            <h3 data-i18n="card4Title">Analyse a Case Document</h3>
            <p data-i18n="card4Desc">Upload or paste legal notices or orders to extract key dates, risks, and next steps.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>
      </div>

      <!-- Quick Indian Legal Portals Bar -->
      <div class="official-links-card">
        <h4 data-i18n="officialLinksTitle">Official Indian Legal Portals:</h4>
        <div class="portal-badges">
          <a href="https://www.indiacode.nic.in/" target="_blank" rel="noopener">India Code</a>
          <a href="https://www.sci.gov.in/" target="_blank" rel="noopener">Supreme Court (SCI)</a>
          <a href="https://ecourts.gov.in/" target="_blank" rel="noopener">eCourts Services</a>
          <a href="https://nalsa.gov.in/" target="_blank" rel="noopener">NALSA (Free Legal Aid)</a>
        </div>
      </div>
    </section>

    <!-- Screen 2: Legal Chatbot -->
    <section id="chatScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="chatTitle">Legal AI Consultation</h2>
        <div class="state-picker">
          <label for="chatState" data-i18n="stateLabel">State:</label>
          <select id="chatState">
            <option value="">All India (Central)</option>
            <option value="Delhi">Delhi</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="West Bengal">West Bengal</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Rajasthan">Rajasthan</option>
            <option value="Bihar">Bihar</option>
            <option value="Madhya Pradesh">Madhya Pradesh</option>
            <option value="Punjab">Punjab</option>
            <option value="Haryana">Haryana</option>
            <option value="Kerala">Kerala</option>
            <option value="Telangana">Telangana</option>
            <option value="Andhra Pradesh">Andhra Pradesh</option>
            <option value="Other">Other State / UT</option>
          </select>
        </div>
      </div>

      <div class="chat-container">
        <div id="chatMessages" class="chat-messages">
          <div class="message ai-msg">
            <div class="msg-avatar">⚖️</div>
            <div class="msg-body">
              <p data-i18n="chatGreeting">Namaste! I am AI Vakeel. You can ask me any question about Indian law (e.g., criminal complaints, tenant rights, consumer disputes, divorce, cheque bounce, or traffic challans). Which issue can I help you understand?</p>
            </div>
          </div>
        </div>

        <div id="chatTyping" class="typing-indicator hidden">
          <span>AI Vakeel is analyzing Indian statutes...</span>
        </div>

        <form id="chatForm" class="chat-input-bar">
          <textarea id="chatInput" rows="2" placeholder="Ask your legal question in Hindi or English..." required></textarea>
          <button type="submit" id="chatSendBtn" class="primary-btn">
            <span>Send</span> ➔
          </button>
        </form>
      </div>
    </section>

    <!-- Screen 3: Legal Document Generator -->
    <section id="draftScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="draftTitle">Legal Document Generator</h2>
      </div>

      <div class="form-card">
        <form id="draftForm">
          <div class="form-group">
            <label for="draftDocType" data-i18n="docTypeLabel">Select Document Type *</label>
            <select id="draftDocType" required>
              <option value="RTI Application under Section 6(1) of RTI Act 2005">RTI Application (Right to Information)</option>
              <option value="Legal Notice for Recovery of Dues / Money Dispute">Legal Notice for Money Recovery</option>
              <option value="Police Complaint for Cyber Fraud / Cheating">Police Complaint (Cyber Crime / Cheating)</option>
              <option value="Consumer Complaint under Consumer Protection Act 2019">Consumer Court Complaint (Defective Product/Service)</option>
              <option value="Legal Notice for Tenant Eviction or Landlord Rent Default">Rental Legal Notice (Tenant / Landlord)</option>
              <option value="General Affidavit Format">General Sworn Affidavit</option>
              <option value="Standard Residential Rental Agreement">Residential Rent Agreement Draft</option>
              <option value="Formal Representation / Grievance to Municipal / Govt Authority">Government / Municipal Grievance Letter</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="draftState" data-i18n="stateLabel">Jurisdiction / State</label>
              <input type="text" id="draftState" placeholder="e.g., Delhi, Karnataka, UP">
            </div>
          </div>

          <div class="form-group">
            <label for="draftDetails" data-i18n="draftDetailsLabel">Document Facts & Specifics *</label>
            <textarea id="draftDetails" rows="5" placeholder="Provide details: Names of parties, dates, amounts, incident description, and what relief you are demanding." required></textarea>
            <small class="helper-text" data-i18n="draftHelper">Do not share sensitive passwords, OTPs, or biometric info.</small>
          </div>

          <button type="submit" id="draftSubmitBtn" class="primary-btn full-width">
            <span>Generate Legal Draft</span> 📜
          </button>
        </form>
      </div>

      <div id="draftResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="draftResultTitle">Generated Legal Draft</h3>
          <div class="result-actions">
            <button class="action-btn" onclick="copyToClipboard('draftContent')">📋 Copy</button>
            <button class="action-btn" onclick="printElement('draftContent')">🖨️ Print</button>
          </div>
        </div>
        <pre id="draftContent" class="code-view"></pre>
      </div>
    </section>

    <!-- Screen 4: Legal Research -->
    <section id="researchScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="researchTitle">Indian Legal Research</h2>
      </div>

      <div class="form-card">
        <form id="researchForm">
          <div class="form-group">
            <label for="researchCategory" data-i18n="categoryLabel">Legal Domain</label>
            <select id="researchCategory">
              <option value="Criminal Law (BNS, BNSS, BSA, IPC)">Criminal Law (BNS / IPC)</option>
              <option value="Constitutional & Fundamental Rights">Constitutional & Fundamental Rights</option>
              <option value="Property & Tenancy Disputes">Property & Land Disputes</option>
              <option value="Family, Marriage & Succession Law">Family Law (Hindu, Muslim, Special Marriage)</option>
              <option value="Consumer & Contract Law">Consumer Protection & Contracts</option>
              <option value="Cyber Law & Digital Personal Data">Cybercrime & IT Act</option>
              <option value="Labour & Industrial Relations">Labour & Employment</option>
            </select>
          </div>

          <div class="form-group">
            <label for="researchQuery" data-i18n="researchQueryLabel">Research Topic or Legal Section *</label>
            <input type="text" id="researchQuery" placeholder="e.g., Anticipatory bail grounds under BNSS, Cheque bounce Section 138" required>
          </div>

          <button type="submit" id="researchSubmitBtn" class="primary-btn full-width">
            <span>Find Legislation & Rulings</span> 🔍
          </button>
        </form>
      </div>

      <div id="researchResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="researchResultTitle">Research Findings</h3>
          <button class="action-btn" onclick="copyToClipboard('researchContent')">📋 Copy</button>
        </div>
        <div id="researchContent" class="formatted-view"></div>
      </div>
    </section>

    <!-- Screen 5: Case Document Analysis -->
    <section id="analyzeScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="analyzeTitle">Case Document Analysis</h2>
      </div>

      <div class="form-card">
        <div class="privacy-notice">
          🔒 <strong>Confidentiality Notice:</strong> Do not upload documents containing unredacted Aadhaar numbers, bank account passwords, or personal biometric records.
        </div>

        <form id="analyzeForm">
          <div class="form-group">
            <label for="documentFile" data-i18n="uploadLabel">Upload Legal File (.txt or text-based documents)</label>
            <input type="file" id="documentFile" accept=".txt,.doc,.docx,.pdf">
          </div>

          <div class="divider-text"><span>OR</span></div>

          <div class="form-group">
            <label for="documentText" data-i18n="pasteLabel">Paste Notice / Order Text Here</label>
            <textarea id="documentText" rows="6" placeholder="Paste the text of the legal notice, agreement, police complaint, or court order here..."></textarea>
          </div>

          <button type="submit" id="analyzeSubmitBtn" class="primary-btn full-width">
            <span>Analyze Legal Document</span> 📑
          </button>
        </form>
      </div>

      <div id="analyzeResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="analysisResultTitle">Analysis & Advocate Questions</h3>
          <button class="action-btn" onclick="copyToClipboard('analyzeContent')">📋 Copy</button>
        </div>
        <div id="analyzeContent" class="formatted-view"></div>
      </div>
    </section>

  </main>

  <script src="app.js"></script>
</body>
</html>
:root {
  --navy-primary: #0a1931;
  --navy-secondary: #152642;
  --navy-light: #1f3556;
  --gold-accent: #c5a059;
  --gold-hover: #dcb36d;
  --bg-page: #f4f6fa;
  --card-bg: #ffffff;
  --text-dark: #1e293b;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --shadow: 0 4px 14px rgba(10, 25, 49, 0.08);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  -webkit-tap-highlight-color: transparent;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-page);
  color: var(--text-dark);
  line-height: 1.5;
  padding-bottom: 40px;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, var(--navy-primary) 0%, var(--navy-secondary) 100%);
  color: #ffffff;
  border-bottom: 3px solid var(--gold-accent);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 12px 16px;
}

.header-inner {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-emblem {
  font-size: 26px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--gold-accent);
}

.brand-title {
  font-family: 'Cinzel', serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.brand-tagline {
  font-size: 0.72rem;
  color: var(--gold-accent);
}

.lang-selector {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 1px solid var(--gold-accent);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.lang-selector option {
  background: var(--navy-primary);
  color: #fff;
}

/* API Banner */
.api-banner {
  background: #fff3cd;
  color: #856404;
  border-bottom: 1px solid #ffeeba;
  padding: 10px 16px;
  font-size: 0.85rem;
}

.banner-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: #856404;
}

/* Disclaimer Banner */
.disclaimer-banner {
  background: #eef2f8;
  border-left: 4px solid var(--gold-accent);
  border-bottom: 1px solid var(--border-color);
  padding: 10px 16px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.disclaimer-content {
  max-width: 900px;
  margin: 0 auto;
}

/* Main Content */
.main-content {
  max-width: 900px;
  margin: 16px auto;
  padding: 0 16px;
}

.screen {
  display: none;
  animation: fadeIn 0.25s ease-in-out;
}

.screen.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Welcome Box */
.welcome-box {
  background: #ffffff;
  padding: 20px;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-color);
  text-align: center;
}

.welcome-box h2 {
  font-size: 1.25rem;
  color: var(--navy-primary);
  margin-bottom: 6px;
}

.welcome-box p {
  font-size: 0.88rem;
  color: var(--text-muted);
}

/* 4 Action Cards */
.action-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-bottom: 24px;
}

@media (min-width: 600px) {
  .action-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.action-card {
  display: flex;
  align-items: center;
  text-align: left;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 18px;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  width: 100%;
}

.action-card:hover, .action-card:active {
  border-color: var(--gold-accent);
  transform: translateY(-2px);
  background: #fdfdfd;
}

.card-icon {
  font-size: 2rem;
  background: #f0f4f9;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  margin-right: 14px;
  flex-shrink: 0;
}

.card-text {
  flex: 1;
}

.card-text h3 {
  font-size: 1.05rem;
  color: var(--navy-primary);
  margin-bottom: 4px;
}

.card-text p {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.35;
}

.card-arrow {
  color: var(--gold-accent);
  font-size: 1.4rem;
  font-weight: bold;
  padding-left: 8px;
}

/* Official Links Bar */
.official-links-card {
  background: #ffffff;
  padding: 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.official-links-card h4 {
  font-size: 0.85rem;
  color: var(--navy-primary);
  margin-bottom: 10px;
}

.portal-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.portal-badges a {
  background: #f1f5f9;
  color: var(--navy-light);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid #cbd5e1;
}

.portal-badges a:hover {
  background: var(--navy-light);
  color: #fff;
  border-color: var(--navy-light);
}

/* Screen Headers */
.screen-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 16px;
}

.screen-header h2 {
  font-size: 1.25rem;
  color: var(--navy-primary);
}

.back-btn {
  background: #e2e8f0;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  color: var(--navy-primary);
}

.state-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.state-picker select {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  font-size: 0.85rem;
}

/* Chat Screen */
.chat-container {
  background: #ffffff;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 230px);
  min-height: 480px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 90%;
}

.ai-msg {
  align-self: flex-start;
}

.user-msg {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--navy-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.user-msg .msg-avatar {
  background: var(--gold-accent);
}

.msg-body {
  background: #f1f5f9;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-line;
  word-break: break-word;
}

.user-msg .msg-body {
  background: var(--navy-primary);
  color: #ffffff;
}

.typing-indicator {
  padding: 8px 16px;
  font-size: 0.8rem;
  color: var(--gold-accent);
  font-style: italic;
}

.chat-input-bar {
  display: flex;
  padding: 10px;
  gap: 8px;
  border-top: 1px solid var(--border-color);
  background: #fafafa;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.chat-input-bar textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  resize: none;
  outline: none;
}

.chat-input-bar textarea:focus {
  border-color: var(--navy-light);
}

/* Forms & Cards */
.form-card {
  background: #ffffff;
  padding: 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--navy-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--navy-light);
  box-shadow: 0 0 0 2px rgba(10, 25, 49, 0.08);
}

.helper-text {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.primary-btn {
  background: linear-gradient(135deg, var(--navy-primary) 0%, var(--navy-secondary) 100%);
  color: #ffffff;
  border: 1px solid var(--gold-accent);
  padding: 12px 18px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.2s ease;
}

.primary-btn:hover {
  opacity: 0.95;
}

.full-width {
  width: 100%;
}

/* Results Display */
.result-card {
  background: #ffffff;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  padding: 18px;
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.result-header h3 {
  font-size: 1.1rem;
  color: var(--navy-primary);
}

.result-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 500;
}

.action-btn:hover {
  background: #e2e8f0;
}

.code-view {
  white-space: pre-wrap;
  word-break: break-word;
  background: #f8fafc;
  padding: 14px;
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--text-dark);
  border: 1px solid #e2e8f0;
  max-height: 500px;
  overflow-y: auto;
}

.formatted-view {
  font-size: 0.92rem;
  line-height: 1.6;
  white-space: pre-line;
  color: var(--text-dark);
}

/* Privacy & Alert Notice */
.privacy-notice {
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #1e40af;
  margin-bottom: 16px;
}

.divider-text {
  text-align: center;
  position: relative;
  margin: 16px 0;
}

.divider-text::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 1px solid var(--border-color);
  z-index: 1;
}

.divider-text span {
  position: relative;
  z-index: 2;
  background: #fff;
  padding: 0 10px;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.hidden {
  display: none !important;
}
// State Management
let currentLanguage = 'en';
const conversationHistory = [];

// Bilingual UI Text
const translations = {
  en: {
    tagline: "Your AI-Powered Indian Legal Assistant",
    disclaimerTitle: "Legal Disclaimer:",
    disclaimerText: "AI Vakeel provides general legal information and drafting assistance, not professional legal advice. AI-generated answers may contain errors. Verify current laws and citations through official sources and consult a qualified Indian advocate before making important legal decisions or filing documents.",
    welcomeTitle: "Namaste! How can AI Vakeel assist you today?",
    welcomeSub: "Select a service below to get instant guidance on Indian Law, prepare legal drafts, or analyze court documents.",
    card1Title: "Ask a Legal Question",
    card1Desc: "Get simplified answers on Criminal, Civil, Property, Family, Consumer & Cyber Law.",
    card2Title: "Draft a Legal Document",
    card2Desc: "Prepare ready-to-use RTI, Legal Notices, Complaints, Agreements & Affidavits.",
    card3Title: "Research Indian Law",
    card3Desc: "Find authentic sections from India Code, BNS/BNSS, and Supreme Court rulings.",
    card4Title: "Analyse a Case Document",
    card4Desc: "Upload or paste legal notices or orders to extract key dates, risks, and next steps.",
    backHome: "Home",
    chatTitle: "Legal AI Consultation",
    stateLabel: "Jurisdiction / State:",
    chatGreeting: "Namaste! I am AI Vakeel. You can ask me any question about Indian law (e.g., criminal complaints, tenant rights, consumer disputes, divorce, cheque bounce, or traffic challans). Which issue can I help you understand?",
    draftTitle: "Legal Document Generator",
    docTypeLabel: "Select Document Type *",
    draftDetailsLabel: "Document Facts & Specifics *",
    draftHelper: "Do not share sensitive passwords, OTPs, or biometric info.",
    draftResultTitle: "Generated Legal Draft",
    researchTitle: "Indian Legal Research",
    categoryLabel: "Legal Domain",
    researchQueryLabel: "Research Topic or Legal Section *",
    researchResultTitle: "Research Findings",
    analyzeTitle: "Case Document Analysis",
    uploadLabel: "Upload Legal File (.txt or text-based documents)",
    pasteLabel: "Paste Notice / Order Text Here",
    analysisResultTitle: "Analysis & Advocate Questions",
    officialLinksTitle: "Official Indian Legal Portals:"
  },
  hi: {
    tagline: "आपका एआई-संचालित भारतीय कानूनी सहायक",
    disclaimerTitle: "कानूनी अस्वीकरण (Disclaimer):",
    disclaimerText: "AI Vakeel केवल सामान्य कानूनी जानकारी और ड्राफ्टिंग सहायता प्रदान करता है, पेशेवर कानूनी सलाह नहीं। एआई द्वारा उत्पन्न उत्तरों में त्रुटियाँ हो सकती हैं। आधिकारिक स्रोतों के माध्यम से कानूनों और धाराओं की पुष्टि करें और किसी भी महत्वपूर्ण कानूनी निर्णय या कोर्ट में दस्तावेज़ दाखिल करने से पहले किसी योग्य भारतीय वकील (Advocate) से परामर्श लें।",
    welcomeTitle: "नमस्ते! AI Vakeel आज आपकी क्या सहायता कर सकता है?",
    welcomeSub: "भारतीय कानून समझने, कानूनी ड्राफ्ट तैयार करने या अदालती दस्तावेज़ों का विश्लेषण करने के लिए नीचे किसी सेवा का चयन करें।",
    card1Title: "कानूनी प्रश्न पूछें (Ask Legal AI)",
    card1Desc: "आपराधिक, दीवानी, संपत्ति, पारिवारिक, उपभोक्ता और साइबर कानून पर सरल उत्तर प्राप्त करें।",
    card2Title: "कानूनी दस्तावेज़ तैयार करें",
    card2Desc: "RTI, कानूनी नोटिस, पुलिस शिकायत, रेंट एग्रीमेंट और हलफनामा तैयार करें।",
    card3Title: "भारतीय कानून में रिसर्च करें",
    card3Desc: "इंडिया कोड (India Code), बीएनएस/बीएनएसएस और सुप्रीम कोर्ट के फैसलों की धाराएं खोजें।",
    card4Title: "केस दस्तावेज़ का विश्लेषण करें",
    card4Desc: "कानूनी नोटिस या अदालती आदेश की समीक्षा करें, तारीखें, जोखिम और आगे के कदम समझें।",
    backHome: "होम",
    chatTitle: "कानूनी एआई परामर्श (Chat)",
    stateLabel: "राज्य / अधिकार क्षेत्र:",
    chatGreeting: "नमस्ते! मैं AI Vakeel हूँ। आप मुझसे भारतीय कानून से जुड़ा कोई भी सवाल पूछ सकते हैं (जैसे- पुलिस शिकायत, किरायेदार विवाद, उपभोक्ता संरक्षण, चेक बाउंस, या साइबर फ्रॉड)। मैं आपकी क्या सहायता करूँ?",
    draftTitle: "कानूनी ड्राफ्ट जनरेटर",
    docTypeLabel: "दस्तावेज़ का प्रकार चुनें *",
    draftDetailsLabel: "मामले का विवरण और मुख्य तथ्य *",
    draftHelper: "कृपया आधार नंबर, पासवर्ड या संवेदनशील व्यक्तिगत जानकारी साझा न करें।",
    draftResultTitle: "तैयार किया गया कानूनी ड्राफ्ट",
    researchTitle: "भारतीय कानूनी अनुसंधान (Research)",
    categoryLabel: "कानूनी श्रेणी",
    researchQueryLabel: "रिसर्च विषय या कानूनी धारा *",
    researchResultTitle: "रिसर्च रिपोर्ट",
    analyzeTitle: "केस दस्तावेज़ विश्लेषण",
    uploadLabel: "दस्तावेज़ फाइल अपलोड करें (.txt या टेक्स्ट)",
    pasteLabel: "नोटिस या अदालती आदेश का टेक्स्ट यहाँ पेस्ट करें",
    analysisResultTitle: "विश्लेषण और वकील से पूछने योग्य सवाल",
    officialLinksTitle: "आधिकारिक भारतीय कानूनी पोर्टल:"
  }
};

// Navigation controller
function navigateTo(screenId) {
  const screens = ['home', 'chat', 'draft', 'research', 'analyze'];
  screens.forEach(s => {
    const el = document.getElementById(s + 'Screen');
    if (el) el.classList.remove('active');
  });
  const target = document.getElementById(screenId + 'Screen');
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// Language switch controller
function setLanguage(lang) {
  currentLanguage = lang;
  const dict = translations[lang] || translations.en;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  const chatInput = document.getElementById('chatInput');
  if (chatInput) {
    chatInput.placeholder = lang === 'hi' 
      ? "अपना कानूनी सवाल यहाँ हिन्दी या अंग्रेज़ी में लिखें..." 
      : "Ask your legal question in Hindi or English...";
  }
}

// Initial check on load
document.addEventListener('DOMContentLoaded', async () => {
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => setLanguage(e.target.value));
  }

  // Dismiss API banner
  const dismissBtn = document.getElementById('dismissBannerBtn');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      document.getElementById('apiKeyBanner').classList.add('hidden');
    });
  }

  // Verify Backend Status
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (!data.aiConfigured) {
      document.getElementById('apiKeyBanner').classList.remove('hidden');
    }
  } catch (err) {
    console.warn('Could not contact status endpoint:', err);
  }
});

// 1. Chatbot Logic
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const chatTyping = document.getElementById('chatTyping');

if (chatForm) {
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Append User Message
    appendMessage(query, 'user');
    chatInput.value = '';
    chatTyping.classList.remove('hidden');

    const state = document.getElementById('chatState').value;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          conversationHistory,
          language: currentLanguage,
          state
        })
      });

      const data = await response.json();
      chatTyping.classList.add('hidden');

      if (!response.ok) {
        if (data.error === 'OPENAI_API_KEY_MISSING') {
          appendMessage(`⚠️ **OpenAI API Key Missing**: ${data.fallbackNotice}\n\nTo resolve: Go to Replit "Secrets" (Tools > Secrets) and add Key: OPENAI_API_KEY with your key.`, 'ai');
          return;
        }
        appendMessage(`❌ Error: ${data.message || 'Something went wrong.'}`, 'ai');
        return;
      }

      appendMessage(data.reply, 'ai');
      conversationHistory.push({ role: 'user', content: query });
      conversationHistory.push({ role: 'assistant', content: data.reply });
    } catch (err) {
      chatTyping.classList.add('hidden');
      appendMessage(`❌ Network error: Could not reach AI Vakeel server.`, 'ai');
    }
  });
}

function appendMessage(text, sender) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = sender === 'user' ? '👤' : '⚖️';

  const body = document.createElement('div');
  body.className = 'msg-body';
  body.textContent = text;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(body);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 2. Document Generator Logic
const draftForm = document.getElementById('draftForm');
if (draftForm) {
  draftForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const docType = document.getElementById('draftDocType').value;
    const state = document.getElementById('draftState').value;
    const details = document.getElementById('draftDetails').value;
    const btn = document.getElementById('draftSubmitBtn');
    const resultArea = document.getElementById('draftResultArea');
    const contentBox = document.getElementById('draftContent');

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'ड्राफ्ट तैयार हो रहा है...' : 'Generating Draft...';

    try {
      const res = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ docType, state, details, language: currentLanguage })
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Generate Legal Draft</span> 📜`;

      if (!res.ok) {
        alert(data.message || 'Failed to generate document draft.');
        return;
      }

      contentBox.textContent = data.draft;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Generate Legal Draft</span> 📜`;
      alert('Network error connecting to draft engine.');
    }
  });
}

// 3. Legal Research Logic
const researchForm = document.getElementById('researchForm');
if (researchForm) {
  researchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('researchQuery').value;
    const category = document.getElementById('researchCategory').value;
    const btn = document.getElementById('researchSubmitBtn');
    const resultArea = document.getElementById('researchResultArea');
    const contentBox = document.getElementById('researchContent');

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'रिसर्च जारी है...' : 'Searching Statutes & Judgments...';

    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, category, language: currentLanguage })
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Find Legislation & Rulings</span> 🔍`;

      if (!res.ok) {
        alert(data.message || 'Error conducting research.');
        return;
      }

      contentBox.textContent = data.research;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Find Legislation & Rulings</span> 🔍`;
      alert('Network error executing legal research.');
    }
  });
}

// 4. Case Document Analysis Logic
const analyzeForm = document.getElementById('analyzeForm');
if (analyzeForm) {
  analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('documentFile');
    const textInput = document.getElementById('documentText');
    const btn = document.getElementById('analyzeSubmitBtn');
    const resultArea = document.getElementById('analyzeResultArea');
    const contentBox = document.getElementById('analyzeContent');

    const formData = new FormData();
    if (fileInput.files.length > 0) {
      formData.append('documentFile', fileInput.files[0]);
    }
    formData.append('documentText', textInput.value);
    formData.append('language', currentLanguage);

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'दस्तावेज़ का विश्लेषण हो रहा है...' : 'Analyzing Legal Document...';

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Analyze Legal Document</span> 📑`;

      if (!res.ok) {
        alert(data.message || data.error || 'Failed to analyze document.');
        return;
      }

      contentBox.textContent = data.analysis;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Analyze Legal Document</span> 📑`;
      alert('Network error analyzing document.');
    }
  });
}

// Utility: Copy to Clipboard
function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    alert(currentLanguage === 'hi' ? 'सफलतापूर्वक कॉपी किया गया!' : 'Copied to clipboard successfully!');
  }).catch(() => {
    alert('Copy failed. Please manually select and copy.');
  });
}

// Utility: Print Element
function printElement(elementId) {
  const content = document.getElementById(elementId).innerText;
  const printWindow = window.open('', '_blank');
  printWindow.document.write(`
    <html>
      <head>
        <title>AI Vakeel - Legal Document</title>
        <style>
          body { font-family: serif; padding: 40px; line-height: 1.6; color: #111; font-size: 14pt; }
          pre { white-space: pre-wrap; font-family: serif; }
        </style>
      </head>
      <body>
        <pre>${content}</pre>
      </body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}
# AI Vakeel ⚖️
**Your AI-Powered Indian Legal Assistant**

A mobile-friendly, secure web application designed for Indian citizens to explore Indian legal provisions, prepare formal draft applications (RTI, notices, complaints), and analyze legal documents.

---

## 📱 How to Run on an Android Phone (via Replit)

1. Open your browser on Android (Chrome/Brave) and log in to **[Replit](https://replit.com)**.
2. Tap **Create Repl** and select **Node.js** as the template. Name it `ai-vakeel`.
3. In Replit's file explorer on the left:
   - Create the `public` folder.
   - Paste each file matching the filenames provided (`package.json`, `server.js`, `public/index.html`, `public/style.css`, `public/app.js`).
4. **Configure your OpenAI Key**:
   - In Replit, tap the **Tools** icon (or sidebar) and select **Secrets** (the lock icon 🔒).
   - Add a Secret:
     - **Key**: `OPENAI_API_KEY`
     - **Value**: `sk-proj-...` (Your OpenAI API key)
   - Optional: Add `OPENAI_MODEL` with value `gpt-4o-mini`.
5. Tap the big green **Run** button at the top.
6. The app will install dependencies automatically and launch in the Replit Webview! You can bookmark the URL or add it to your Android home screen as a Web App.

---

## 💻 Running Locally (Optional)

```bash
npm install
node server.js
---

### What's Built In

1. **State-Aware Indian Law AI**: Pre-instructed on criminal law updates (Bharatiya Nyaya Sanhita 2023 / IPC), Consumer Protection Act 2019, IT Act 2000, and State jurisdiction awareness.
2. **Dynamic Legal Draft Engine**: Creates structured templates with placeholders and checklist items for RTI, Consumer Complaints, Police Complaints, and Affidavits.
3. **Official Links**: Instant verified references to **India Code**, **Supreme Court**, **eCourts**, and **NALSA**.
4. **Android-First Touch Design**: Custom Navy & Gold layout designed to fit handheld screens, with easy copy-to-clipboard, print formatting, and Hindi/English switching.
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>AI Vakeel - Your AI-Powered Indian Legal Assistant</title>
  <link rel="stylesheet" href="style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>

  <!-- Top App Bar -->
  <header class="app-header">
    <div class="header-inner">
      <div class="brand" onclick="navigateTo('home')" style="cursor: pointer;">
        <div class="brand-emblem">⚖️</div>
        <div>
          <h1 class="brand-title">AI Vakeel</h1>
          <p class="brand-tagline" data-i18n="tagline">Your AI-Powered Indian Legal Assistant</p>
        </div>
      </div>
      <div class="header-controls">
        <select id="langSelect" class="lang-selector" aria-label="Select Language">
          <option value="en">English</option>
          <option value="hi">हिन्दी (Hindi)</option>
        </select>
      </div>
    </div>
  </header>

  <!-- Missing API Key Alert Banner -->
  <div id="apiKeyBanner" class="api-banner hidden">
    <div class="banner-content">
      <span>⚠️ <strong>Setup Notice:</strong> Add your <code>OPENAI_API_KEY</code> in Secrets/Environment variables to enable AI responses.</span>
      <button id="dismissBannerBtn" class="dismiss-btn" aria-label="Dismiss">&times;</button>
    </div>
  </div>

  <!-- Mandatory Statutory Legal Disclaimer -->
  <aside class="disclaimer-banner">
    <div class="disclaimer-content">
      <strong data-i18n="disclaimerTitle">Legal Disclaimer:</strong>
      <span data-i18n="disclaimerText">AI Vakeel provides general legal information and drafting assistance, not professional legal advice. AI-generated answers may contain errors. Verify current laws and citations through official sources and consult a qualified Indian advocate before making important legal decisions or filing documents.</span>
    </div>
  </aside>

  <!-- Main Container -->
  <main class="main-content">

    <!-- Screen 1: Home Dashboard -->
    <section id="homeScreen" class="screen active">
      <div class="welcome-box">
        <h2 data-i18n="welcomeTitle">Namaste! How can AI Vakeel assist you today?</h2>
        <p data-i18n="welcomeSub">Select a service below to get instant guidance on Indian Law, prepare legal drafts, or analyze court documents.</p>
      </div>

      <div class="action-grid">
        <!-- 1. Ask a Legal Question -->
        <button class="action-card" onclick="navigateTo('chat')">
          <div class="card-icon">💬</div>
          <div class="card-text">
            <h3 data-i18n="card1Title">1. Ask a Legal Question</h3>
            <p data-i18n="card1Desc">Get simplified answers on Criminal, Civil, Property, Family, Consumer & Cyber Law.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- 2. Draft a Legal Document -->
        <button class="action-card" onclick="navigateTo('draft')">
          <div class="card-icon">📝</div>
          <div class="card-text">
            <h3 data-i18n="card2Title">2. Draft a Legal Document</h3>
            <p data-i18n="card2Desc">Prepare ready-to-use RTI, Legal Notices, Complaints, Agreements & Affidavits.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- 3. Research Indian Law -->
        <button class="action-card" onclick="navigateTo('research')">
          <div class="card-icon">🔍</div>
          <div class="card-text">
            <h3 data-i18n="card3Title">3. Research Indian Law</h3>
            <p data-i18n="card3Desc">Find authentic sections from India Code, BNS/BNSS, and Supreme Court rulings.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>

        <!-- 4. Analyse a Case -->
        <button class="action-card" onclick="navigateTo('analyze')">
          <div class="card-icon">📑</div>
          <div class="card-text">
            <h3 data-i18n="card4Title">4. Analyse a Case</h3>
            <p data-i18n="card4Desc">Upload or paste legal notices or orders to extract key dates, risks, and advocate questions.</p>
          </div>
          <div class="card-arrow">&rarr;</div>
        </button>
      </div>

      <!-- Official Indian Legal Portals Bar -->
      <div class="official-links-card">
        <h4 data-i18n="officialLinksTitle">Official Indian Legal Portals:</h4>
        <div class="portal-badges">
          <a href="https://www.indiacode.nic.in/" target="_blank" rel="noopener">India Code</a>
          <a href="https://www.sci.gov.in/" target="_blank" rel="noopener">Supreme Court of India (SCI)</a>
          <a href="https://ecourts.gov.in/" target="_blank" rel="noopener">eCourts Services</a>
          <a href="https://nalsa.gov.in/" target="_blank" rel="noopener">NALSA (Free Legal Aid)</a>
        </div>
      </div>
    </section>

    <!-- Screen 2: Legal AI Chatbot -->
    <section id="chatScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="chatTitle">Legal AI Consultation</h2>
        <div class="state-picker">
          <label for="chatState" data-i18n="stateLabel">State:</label>
          <select id="chatState">
            <option value="">All India (Central)</option>
            <option value="Delhi">Delhi</option>
            <option value="Maharashtra">Maharashtra</option>
            <option value="Uttar Pradesh">Uttar Pradesh</option>
            <option value="Karnataka">Karnataka</option>
            <option value="Tamil Nadu">Tamil Nadu</option>
            <option value="West Bengal">West Bengal</option>
            <option value="Gujarat">Gujarat</option>
            <option value="Rajasthan">Rajasthan</option>
            <option value="Bihar">Bihar</option>
            <option value="Madhya Pradesh">Madhya Pradesh</option>
            <option value="Punjab">Punjab</option>
            <option value="Haryana">Haryana</option>
            <option value="Kerala">Kerala</option>
            <option value="Telangana">Telangana</option>
            <option value="Andhra Pradesh">Andhra Pradesh</option>
            <option value="Other">Other State / UT</option>
          </select>
        </div>
      </div>

      <div class="chat-container">
        <div id="chatMessages" class="chat-messages">
          <div class="message ai-msg">
            <div class="msg-avatar">⚖️</div>
            <div class="msg-body">
              <p data-i18n="chatGreeting">Namaste! I am AI Vakeel. You can ask me any question about Indian law (e.g., criminal complaints, tenant rights, consumer disputes, divorce, cheque bounce, or traffic challans). Which issue can I help you understand?</p>
            </div>
          </div>
        </div>

        <div id="chatTyping" class="typing-indicator hidden">
          <span>AI Vakeel is analyzing Indian statutes...</span>
        </div>

        <form id="chatForm" class="chat-input-bar">
          <textarea id="chatInput" rows="2" placeholder="Ask your legal question in Hindi or English..." required></textarea>
          <button type="submit" id="chatSendBtn" class="primary-btn">
            <span>Send</span> ➔
          </button>
        </form>
      </div>
    </section>

    <!-- Screen 3: Legal Document Generator -->
    <section id="draftScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="draftTitle">Legal Document Generator</h2>
      </div>

      <div class="form-card">
        <form id="draftForm">
          <div class="form-group">
            <label for="draftDocType" data-i18n="docTypeLabel">Select Document Type *</label>
            <select id="draftDocType" required>
              <option value="RTI Application under Section 6(1) of RTI Act 2005">RTI Application (Right to Information)</option>
              <option value="Legal Notice for Recovery of Dues / Money Dispute">Legal Notice for Money Recovery</option>
              <option value="Police Complaint for Cyber Fraud / Cheating">Police Complaint (Cyber Crime / Cheating)</option>
              <option value="Consumer Complaint under Consumer Protection Act 2019">Consumer Court Complaint (Defective Product/Service)</option>
              <option value="Legal Notice for Tenant Eviction or Landlord Rent Default">Rental Legal Notice (Tenant / Landlord)</option>
              <option value="General Affidavit Format">General Sworn Affidavit</option>
              <option value="Standard Residential Rental Agreement">Residential Rent Agreement Draft</option>
              <option value="Formal Representation / Grievance to Municipal / Govt Authority">Government / Municipal Grievance Letter</option>
              <option value="Petition under Section 125 CrPC / BNSS Maintenance">Maintenance Representation Draft</option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="draftState" data-i18n="stateLabel">Jurisdiction / State</label>
              <input type="text" id="draftState" placeholder="e.g., Delhi, Maharashtra, UP">
            </div>
          </div>

          <div class="form-group">
            <label for="draftDetails" data-i18n="draftDetailsLabel">Document Facts & Specifics *</label>
            <textarea id="draftDetails" rows="5" placeholder="Provide details: Names of parties, dates, amounts, incident description, and what relief you are demanding." required></textarea>
            <small class="helper-text" data-i18n="draftHelper">Do not share sensitive passwords, OTPs, or biometric info.</small>
          </div>

          <button type="submit" id="draftSubmitBtn" class="primary-btn full-width">
            <span>Generate Legal Draft</span> 📜
          </button>
        </form>
      </div>

      <div id="draftResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="draftResultTitle">Generated Legal Draft</h3>
          <div class="result-actions">
            <button class="action-btn" onclick="copyToClipboard('draftContent')">📋 Copy Draft</button>
            <button class="action-btn" onclick="printElement('draftContent')">🖨️ Print</button>
          </div>
        </div>
        <pre id="draftContent" class="code-view"></pre>
      </div>
    </section>

    <!-- Screen 4: Legal Research -->
    <section id="researchScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="researchTitle">Indian Legal Research</h2>
      </div>

      <div class="form-card">
        <form id="researchForm">
          <div class="form-group">
            <label for="researchCategory" data-i18n="categoryLabel">Legal Domain</label>
            <select id="researchCategory">
              <option value="Criminal Law (BNS, BNSS, BSA, IPC)">Criminal Law (BNS / IPC)</option>
              <option value="Constitutional & Fundamental Rights">Constitutional & Fundamental Rights</option>
              <option value="Property & Tenancy Disputes">Property & Land Disputes</option>
              <option value="Family, Marriage & Succession Law">Family Law (Hindu, Muslim, Special Marriage)</option>
              <option value="Consumer & Contract Law">Consumer Protection & Contracts</option>
              <option value="Cyber Law & Digital Personal Data">Cybercrime & IT Act</option>
              <option value="Labour & Industrial Relations">Labour & Employment</option>
              <option value="Motor Vehicles Act & Traffic Law">Motor Vehicles & Accident Claims</option>
            </select>
          </div>

          <div class="form-group">
            <label for="researchQuery" data-i18n="researchQueryLabel">Research Topic or Legal Section *</label>
            <input type="text" id="researchQuery" placeholder="e.g., Anticipatory bail grounds under BNSS, Cheque bounce Section 138" required>
          </div>

          <button type="submit" id="researchSubmitBtn" class="primary-btn full-width">
            <span>Find Legislation & Rulings</span> 🔍
          </button>
        </form>
      </div>

      <div id="researchResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="researchResultTitle">Research Findings</h3>
          <button class="action-btn" onclick="copyToClipboard('researchContent')">📋 Copy</button>
        </div>
        <div id="researchContent" class="formatted-view"></div>
      </div>
    </section>

    <!-- Screen 5: Case Document Analysis -->
    <section id="analyzeScreen" class="screen">
      <div class="screen-header">
        <button class="back-btn" onclick="navigateTo('home')">&larr; <span data-i18n="backHome">Home</span></button>
        <h2 data-i18n="analyzeTitle">Case Document Analysis</h2>
      </div>

      <div class="form-card">
        <div class="privacy-notice">
          🔒 <strong>Confidentiality Warning:</strong> Do not upload documents containing unredacted Aadhaar numbers, bank passwords, or sensitive biometric details.
        </div>

        <form id="analyzeForm">
          <div class="form-group">
            <label for="documentFile" data-i18n="uploadLabel">Upload Legal File (.txt or text-based documents)</label>
            <input type="file" id="documentFile" accept=".txt,.doc,.docx,.pdf">
          </div>

          <div class="divider-text"><span>OR</span></div>

          <div class="form-group">
            <label for="documentText" data-i18n="pasteLabel">Paste Notice / Order Text Here</label>
            <textarea id="documentText" rows="6" placeholder="Paste the text of the legal notice, agreement, police complaint, or court order here..."></textarea>
          </div>

          <button type="submit" id="analyzeSubmitBtn" class="primary-btn full-width">
            <span>Analyze Legal Document</span> 📑
          </button>
        </form>
      </div>

      <div id="analyzeResultArea" class="result-card hidden">
        <div class="result-header">
          <h3 data-i18n="analysisResultTitle">Analysis & Advocate Questions</h3>
          <button class="action-btn" onclick="copyToClipboard('analyzeContent')">📋 Copy</button>
        </div>
        <div id="analyzeContent" class="formatted-view"></div>
      </div>
    </section>

  </main>

  <script src="app.js"></script>
</body>
</html>
:root {
  --navy-primary: #0a1931;
  --navy-secondary: #152642;
  --navy-light: #1f3556;
  --gold-accent: #c5a059;
  --gold-hover: #dcb36d;
  --bg-page: #f4f6fa;
  --card-bg: #ffffff;
  --text-dark: #1e293b;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --shadow: 0 4px 14px rgba(10, 25, 49, 0.08);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  -webkit-tap-highlight-color: transparent;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--bg-page);
  color: var(--text-dark);
  line-height: 1.5;
  padding-bottom: 40px;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, var(--navy-primary) 0%, var(--navy-secondary) 100%);
  color: #ffffff;
  border-bottom: 3px solid var(--gold-accent);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 12px 16px;
}

.header-inner {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-emblem {
  font-size: 26px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--gold-accent);
}

.brand-title {
  font-family: 'Cinzel', serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.brand-tagline {
  font-size: 0.72rem;
  color: var(--gold-accent);
}

.lang-selector {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 1px solid var(--gold-accent);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.lang-selector option {
  background: var(--navy-primary);
  color: #fff;
}

/* Setup Notice Banner */
.api-banner {
  background: #fff3cd;
  color: #856404;
  border-bottom: 1px solid #ffeeba;
  padding: 10px 16px;
  font-size: 0.85rem;
}

.banner-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.banner-content code {
  background: #f8e5b9;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: #856404;
}

/* Mandatory Legal Disclaimer Banner */
.disclaimer-banner {
  background: #eef2f8;
  border-left: 4px solid var(--gold-accent);
  border-bottom: 1px solid var(--border-color);
  padding: 10px 16px;
  font-size: 0.76rem;
  color: var(--text-muted);
}

.disclaimer-content {
  max-width: 900px;
  margin: 0 auto;
}

.disclaimer-content strong {
  color: var(--navy-primary);
}

/* Main Container */
.main-content {
  max-width: 900px;
  margin: 16px auto;
  padding: 0 16px;
}

.screen {
  display: none;
  animation: fadeIn 0.22s ease-in-out;
}

.screen.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Welcome Box */
.welcome-box {
  background: #ffffff;
  padding: 20px;
  border-radius: var(--radius-md);
  margin-bottom: 18px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-color);
  text-align: center;
}

.welcome-box h2 {
  font-size: 1.25rem;
  color: var(--navy-primary);
  margin-bottom: 6px;
}

.welcome-box p {
  font-size: 0.88rem;
  color: var(--text-muted);
}

/* 4 Large Action Cards */
.action-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  margin-bottom: 24px;
}

@media (min-width: 600px) {
  .action-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.action-card {
  display: flex;
  align-items: center;
  text-align: left;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 18px;
  cursor: pointer;
  box-shadow: var(--shadow);
  transition: all 0.2s ease;
  width: 100%;
}

.action-card:hover, .action-card:active {
  border-color: var(--gold-accent);
  transform: translateY(-2px);
  background: #fdfdfd;
}

.card-icon {
  font-size: 2rem;
  background: #f0f4f9;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  margin-right: 14px;
  flex-shrink: 0;
}

.card-text {
  flex: 1;
}

.card-text h3 {
  font-size: 1.05rem;
  color: var(--navy-primary);
  margin-bottom: 4px;
}

.card-text p {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.35;
}

.card-arrow {
  color: var(--gold-accent);
  font-size: 1.4rem;
  font-weight: bold;
  padding-left: 8px;
}

/* Official Links Bar */
.official-links-card {
  background: #ffffff;
  padding: 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
}

.official-links-card h4 {
  font-size: 0.85rem;
  color: var(--navy-primary);
  margin-bottom: 10px;
}

.portal-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.portal-badges a {
  background: #f1f5f9;
  color: var(--navy-light);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid #cbd5e1;
}

.portal-badges a:hover {
  background: var(--navy-light);
  color: #fff;
  border-color: var(--navy-light);
}

/* Screen Headers */
.screen-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 16px;
}

.screen-header h2 {
  font-size: 1.25rem;
  color: var(--navy-primary);
}

.back-btn {
  background: #e2e8f0;
  border: none;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  color: var(--navy-primary);
}

.state-picker {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.state-picker select {
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  font-size: 0.85rem;
  background: #fff;
}

/* Chat Screen */
.chat-container {
  background: #ffffff;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 240px);
  min-height: 480px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 90%;
}

.ai-msg {
  align-self: flex-start;
}

.user-msg {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--navy-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.user-msg .msg-avatar {
  background: var(--gold-accent);
}

.msg-body {
  background: #f1f5f9;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-line;
  word-break: break-word;
}

.user-msg .msg-body {
  background: var(--navy-primary);
  color: #ffffff;
}

.typing-indicator {
  padding: 8px 16px;
  font-size: 0.8rem;
  color: var(--gold-accent);
  font-style: italic;
}

.chat-input-bar {
  display: flex;
  padding: 10px;
  gap: 8px;
  border-top: 1px solid var(--border-color);
  background: #fafafa;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

.chat-input-bar textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  resize: none;
  outline: none;
}

.chat-input-bar textarea:focus {
  border-color: var(--navy-light);
}

/* Forms & Cards */
.form-card {
  background: #ffffff;
  padding: 18px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--navy-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  outline: none;
  background: #fff;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  border-color: var(--navy-light);
  box-shadow: 0 0 0 2px rgba(10, 25, 49, 0.08);
}

.helper-text {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.primary-btn {
  background: linear-gradient(135deg, var(--navy-primary) 0%, var(--navy-secondary) 100%);
  color: #ffffff;
  border: 1px solid var(--gold-accent);
  padding: 12px 18px;
  border-radius: var(--radius-sm);
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.2s ease;
}

.primary-btn:hover {
  opacity: 0.95;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.full-width {
  width: 100%;
}

/* Results Display */
.result-card {
  background: #ffffff;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  padding: 18px;
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 8px;
}

.result-header h3 {
  font-size: 1.1rem;
  color: var(--navy-primary);
}

.result-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 500;
}

.action-btn:hover {
  background: #e2e8f0;
}

.code-view {
  white-space: pre-wrap;
  word-break: break-word;
  background: #f8fafc;
  padding: 14px;
  border-radius: var(--radius-sm);
  font-family: monospace;
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--text-dark);
  border: 1px solid #e2e8f0;
  max-height: 500px;
  overflow-y: auto;
}

.formatted-view {
  font-size: 0.92rem;
  line-height: 1.6;
  white-space: pre-line;
  color: var(--text-dark);
}

/* Privacy & Alert Notice */
.privacy-notice {
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #1e40af;
  margin-bottom: 16px;
}

.divider-text {
  text-align: center;
  position: relative;
  margin: 16px 0;
}

.divider-text::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 1px solid var(--border-color);
  z-index: 1;
}

.divider-text span {
  position: relative;
  z-index: 2;
  background: #fff;
  padding: 0 10px;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.hidden {
  display: none !important;
}
// State Management
let currentLanguage = 'en';
const conversationHistory = [];

// Bilingual UI Text
const translations = {
  en: {
    tagline: "Your AI-Powered Indian Legal Assistant",
    disclaimerTitle: "Legal Disclaimer:",
    disclaimerText: "AI Vakeel provides general legal information and drafting assistance, not professional legal advice. AI-generated answers may contain errors. Verify current laws and citations through official sources and consult a qualified Indian advocate before making important legal decisions or filing documents.",
    welcomeTitle: "Namaste! How can AI Vakeel assist you today?",
    welcomeSub: "Select a service below to get instant guidance on Indian Law, prepare legal drafts, or analyze court documents.",
    card1Title: "1. Ask a Legal Question",
    card1Desc: "Get simplified answers on Criminal, Civil, Property, Family, Consumer & Cyber Law.",
    card2Title: "2. Draft a Legal Document",
    card2Desc: "Prepare ready-to-use RTI, Legal Notices, Complaints, Agreements & Affidavits.",
    card3Title: "3. Research Indian Law",
    card3Desc: "Find authentic sections from India Code, BNS/BNSS, and Supreme Court rulings.",
    card4Title: "4. Analyse a Case",
    card4Desc: "Upload or paste legal notices or orders to extract key dates, risks, and advocate questions.",
    backHome: "Home",
    chatTitle: "Legal AI Consultation",
    stateLabel: "Jurisdiction / State:",
    chatGreeting: "Namaste! I am AI Vakeel. You can ask me any question about Indian law (e.g., criminal complaints, tenant rights, consumer disputes, divorce, cheque bounce, or traffic challans). Which issue can I help you understand?",
    draftTitle: "Legal Document Generator",
    docTypeLabel: "Select Document Type *",
    draftDetailsLabel: "Document Facts & Specifics *",
    draftHelper: "Do not share sensitive passwords, OTPs, or biometric info.",
    draftResultTitle: "Generated Legal Draft",
    researchTitle: "Indian Legal Research",
    categoryLabel: "Legal Domain",
    researchQueryLabel: "Research Topic or Legal Section *",
    researchResultTitle: "Research Findings",
    analyzeTitle: "Case Document Analysis",
    uploadLabel: "Upload Legal File (.txt or text-based documents)",
    pasteLabel: "Paste Notice / Order Text Here",
    analysisResultTitle: "Analysis & Advocate Questions",
    officialLinksTitle: "Official Indian Legal Portals:"
  },
  hi: {
    tagline: "आपका एआई-संचालित भारतीय कानूनी सहायक",
    disclaimerTitle: "कानूनी अस्वीकरण (Disclaimer):",
    disclaimerText: "AI Vakeel केवल सामान्य कानूनी जानकारी और ड्राफ्टिंग सहायता प्रदान करता है, पेशेवर कानूनी सलाह नहीं। एआई द्वारा उत्पन्न उत्तरों में त्रुटियाँ हो सकती हैं। आधिकारिक स्रोतों के माध्यम से कानूनों और धाराओं की पुष्टि करें और किसी भी महत्वपूर्ण कानूनी निर्णय या कोर्ट में दस्तावेज़ दाखिल करने से पहले किसी योग्य भारतीय वकील (Advocate) से परामर्श लें।",
    welcomeTitle: "नमस्ते! AI Vakeel आज आपकी क्या सहायता कर सकता है?",
    welcomeSub: "भारतीय कानून समझने, कानूनी ड्राफ्ट तैयार करने या अदालती दस्तावेज़ों का विश्लेषण करने के लिए नीचे किसी सेवा का चयन करें।",
    card1Title: "1. कानूनी प्रश्न पूछें (Ask Legal AI)",
    card1Desc: "आपराधिक, दीवानी, संपत्ति, पारिवारिक, उपभोक्ता और साइबर कानून पर सरल उत्तर प्राप्त करें।",
    card2Title: "2. कानूनी दस्तावेज़ तैयार करें",
    card2Desc: "RTI, कानूनी नोटिस, पुलिस शिकायत, रेंट एग्रीमेंट और हलफनामा तैयार करें।",
    card3Title: "3. भारतीय कानून में रिसर्च करें",
    card3Desc: "इंडिया कोड (India Code), बीएनएस/बीएनएसएस और सुप्रीम कोर्ट के फैसलों की धाराएं खोजें।",
    card4Title: "4. केस दस्तावेज़ का विश्लेषण करें",
    card4Desc: "कानूनी नोटिस या अदालती आदेश की समीक्षा करें, तारीखें, जोखिम और आगे के कदम समझें।",
    backHome: "होम",
    chatTitle: "कानूनी एआई परामर्श (Chat)",
    stateLabel: "राज्य / अधिकार क्षेत्र:",
    chatGreeting: "नमस्ते! मैं AI Vakeel हूँ। आप मुझसे भारतीय कानून से जुड़ा कोई भी सवाल पूछ सकते हैं (जैसे- पुलिस शिकायत, किरायेदार विवाद, उपभोक्ता संरक्षण, चेक बाउंस, या साइबर फ्रॉड)। मैं आपकी क्या सहायता करूँ?",
    draftTitle: "कानूनी ड्राफ्ट जनरेटर",
    docTypeLabel: "दस्तावेज़ का प्रकार चुनें *",
    draftDetailsLabel: "मामले का विवरण और मुख्य तथ्य *",
    draftHelper: "कृपया आधार नंबर, पासवर्ड या संवेदनशील व्यक्तिगत जानकारी साझा न करें।",
    draftResultTitle: "तैयार किया गया कानूनी ड्राफ्ट",
    researchTitle: "भारतीय कानूनी अनुसंधान (Research)",
    categoryLabel: "कानूनी श्रेणी",
    researchQueryLabel: "रिसर्च विषय या कानूनी धारा *",
    researchResultTitle: "रिसर्च रिपोर्ट",
    analyzeTitle: "केस दस्तावेज़ विश्लेषण",
    uploadLabel: "दस्तावेज़ फाइल अपलोड करें (.txt या टेक्स्ट)",
    pasteLabel: "नोटिस या अदालती आदेश का टेक्स्ट यहाँ पेस्ट करें",
    analysisResultTitle: "विश्लेषण और वकील से पूछने योग्य सवाल",
    officialLinksTitle: "आधिकारिक भारतीय कानूनी पोर्टल:"
  }
};

// Navigation controller
function navigateTo(screenId) {
  const screens = ['home', 'chat', 'draft', 'research', 'analyze'];
  screens.forEach(s => {
    const el = document.getElementById(s + 'Screen');
    if (el) el.classList.remove('active');
  });
  const target = document.getElementById(screenId + 'Screen');
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

// Language switch controller
function setLanguage(lang) {
  currentLanguage = lang;
  const dict = translations[lang] || translations.en;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  const chatInput = document.getElementById('chatInput');
  if (chatInput) {
    chatInput.placeholder = lang === 'hi' 
      ? "अपना कानूनी सवाल यहाँ हिन्दी या अंग्रेज़ी में लिखें..." 
      : "Ask your legal question in Hindi or English...";
  }
}

// Initial setup on window load
document.addEventListener('DOMContentLoaded', async () => {
  const langSelect = document.getElementById('langSelect');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => setLanguage(e.target.value));
  }

  const dismissBtn = document.getElementById('dismissBannerBtn');
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      document.getElementById('apiKeyBanner').classList.add('hidden');
    });
  }

  // Check backend server status
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (!data.aiConfigured) {
      document.getElementById('apiKeyBanner').classList.remove('hidden');
    }
  } catch (err) {
    console.warn('Backend status check warning:', err);
  }
});

// 1. Legal Chatbot Form
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const chatTyping = document.getElementById('chatTyping');

if (chatForm) {
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage(query, 'user');
    chatInput.value = '';
    chatTyping.classList.remove('hidden');

    const state = document.getElementById('chatState').value;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: query,
          conversationHistory,
          language: currentLanguage,
          state
        })
      });

      const data = await response.json();
      chatTyping.classList.add('hidden');

      if (!response.ok) {
        if (data.error === 'OPENAI_API_KEY_MISSING') {
          appendMessage(`⚠️ **OpenAI API Key Missing**: ${data.fallbackNotice || 'Please add your OPENAI_API_KEY in Replit Secrets.'}`, 'ai');
          return;
        }
        appendMessage(`❌ Error: ${data.message || 'Something went wrong.'}`, 'ai');
        return;
      }

      appendMessage(data.reply, 'ai');
      conversationHistory.push({ role: 'user', content: query });
      conversationHistory.push({ role: 'assistant', content: data.reply });
    } catch (err) {
      chatTyping.classList.add('hidden');
      appendMessage(`❌ Network error: Could not reach AI Vakeel server.`, 'ai');
    }
  });
}

function appendMessage(text, sender) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = sender === 'user' ? '👤' : '⚖️';

  const body = document.createElement('div');
  body.className = 'msg-body';
  body.textContent = text;

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(body);
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 2. Legal Document Generator
const draftForm = document.getElementById('draftForm');
if (draftForm) {
  draftForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const docType = document.getElementById('draftDocType').value;
    const state = document.getElementById('draftState').value;
    const details = document.getElementById('draftDetails').value;
    const btn = document.getElementById('draftSubmitBtn');
    const resultArea = document.getElementById('draftResultArea');
    const contentBox = document.getElementById('draftContent');

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'ड्राफ्ट तैयार हो रहा है...' : 'Generating Draft...';

    try {
      const res = await fetch('/api/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ docType, state, details, language: currentLanguage })
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Generate Legal Draft</span> 📜`;

      if (!res.ok) {
        alert(data.message || 'Failed to generate document draft.');
        return;
      }

      contentBox.textContent = data.draft;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Generate Legal Draft</span> 📜`;
      alert('Network error connecting to draft engine.');
    }
  });
}

// 3. Legal Research
const researchForm = document.getElementById('researchForm');
if (researchForm) {
  researchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = document.getElementById('researchQuery').value;
    const category = document.getElementById('researchCategory').value;
    const btn = document.getElementById('researchSubmitBtn');
    const resultArea = document.getElementById('researchResultArea');
    const contentBox = document.getElementById('researchContent');

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'रिसर्च जारी है...' : 'Searching Statutes & Judgments...';

    try {
      const res = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, category, language: currentLanguage })
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Find Legislation & Rulings</span> 🔍`;

      if (!res.ok) {
        alert(data.message || 'Error conducting research.');
        return;
      }

      contentBox.textContent = data.research;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Find Legislation & Rulings</span> 🔍`;
      alert('Network error executing legal research.');
    }
  });
}

// 4. Case Document Analysis
const analyzeForm = document.getElementById('analyzeForm');
if (analyzeForm) {
  analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('documentFile');
    const textInput = document.getElementById('documentText');
    const btn = document.getElementById('analyzeSubmitBtn');
    const resultArea = document.getElementById('analyzeResultArea');
    const contentBox = document.getElementById('analyzeContent');

    const formData = new FormData();
    if (fileInput.files.length > 0) {
      formData.append('documentFile', fileInput.files[0]);
    }
    formData.append('documentText', textInput.value);
    formData.append('language', currentLanguage);

    btn.disabled = true;
    btn.innerText = currentLanguage === 'hi' ? 'दस्तावेज़ का विश्लेषण हो रहा है...' : 'Analyzing Legal Document...';

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      btn.disabled = false;
      btn.innerHTML = `<span>Analyze Legal Document</span> 📑`;

      if (!res.ok) {
        alert(data.message || data.error || 'Failed to analyze document.');
        return;
      }

      contentBox.textContent = data.analysis;
      resultArea.classList.remove('hidden');
      resultArea.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
      btn.disabled = false;
      btn.innerHTML = `<span>Analyze Legal Document</span> 📑`;
      alert('Network error analyzing document.');
    }
  });
}

// Utility: Copy to Clipboard
function copyToClipboard(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText || el.textContent;

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      alert(currentLanguage === 'hi' ? 'सफलतापूर्वक कॉपी किया गया!' : 'Copied to clipboard successfully!');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
    alert(currentLanguage === 'hi' ? 'सफलतापूर्वक कॉपी किया गया!' : 'Copied to clipboard successfully!');
  } catch (err) {
    alert('Copy failed. Please manually select and copy text.');
  }
  document.body.removeChild(textArea);
}

// Utility: Print Document
function printElement(elementId) {
  const content = document.getElementById(elementId).innerText;
  const printWindow = window.open('', '_blank');
  printWindow.document.write(`
    <html>
      <head>
        <title>AI Vakeel - Legal Document</title>
        <style>
          body { font-family: serif; padding: 40px; line-height: 1.6; color: #111; font-size: 14pt; }
          pre { white-space: pre-wrap; font-family: serif; }
        </style>
      </head>
      <body>
        <pre>${content}</pre>
      </body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}
{
  "name": "ai-vakeel",
  "version": "1.0.0",
  "description": "Your AI-Powered Indian Legal Assistant",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.19.2",
    "multer": "^1.4.5-lts.1",
    "openai": "^4.56.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}

