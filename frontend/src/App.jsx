import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Bot,
  Search,
  Briefcase,
  Zap,
  Lock,
  CheckCircle,
  FileText,
  Sparkles,
  Database,
  AlertTriangle,
  ExternalLink,
  Award,
  BookOpen,
  Code,
  Layers,
  Activity,
  User,
  Users,
  Eye,
  X,
  RefreshCw,
  Target,
  FileCode,
  Clock,
  UploadCloud,
  FileUp,
  Send,
  MessageSquare,
  Trash2,
  GitCommit,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Unlock
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  // Navigation & Multi-User State
  const [activeNavTab, setActiveNavTab] = useState('overview'); // 'overview' | 'profile' | 'resumes' | 'opportunities' | 'chat'
  const [profilesList, setProfilesList] = useState([]);
  const [activeProfileId, setActiveProfileId] = useState(null);
  const [profilePayload, setProfilePayload] = useState(null); // { profile, resume, analysis, opportunities, opportunities_count }
  const [resumesList, setResumesList] = useState([]);

  // ArmorIQ Governance Toggle & Simulation State
  const [armoriqSecured, setArmoriqSecured] = useState(true);
  const [auditLogs, setAuditLogs] = useState([]);
  const [simulatedAttack, setSimulatedAttack] = useState(null);

  // Pipeline Execution State
  const [resumeText, setResumeText] = useState('');
  const [selectedPdfFile, setSelectedPdfFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  const [adkExecution, setAdkExecution] = useState(null);
  const fileInputRef = useRef(null);

  // Direct Database QA State
  const [dbQuestion, setDbQuestion] = useState('');
  const [dbAnswer, setDbAnswer] = useState(null);
  const [isQueryingDb, setIsQueryingDb] = useState(false);

  // Interactive AI Chat State
  const [chatInput, setChatInput] = useState('');
  const [isChatSending, setIsChatSending] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'Hello! I am your ArmorIQ Governed Candidate Assistant. Ask me anything about your technical stack, ranked job matches, strengths, or experience!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const chatBottomRef = useRef(null);

  // Opportunities & Filters State
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Modal & Notification State
  const [selectedResumeModal, setSelectedResumeModal] = useState(null);
  const [pipelineSuccessModal, setPipelineSuccessModal] = useState(null);
  const [shieldNotification, setShieldNotification] = useState(null);

  // Initial Load
  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadInitialData = async () => {
    await fetchProfilesList();
    await fetchResumesList();
    await fetchAuditLogs();
  };

  // Fetch all profiles from backend
  const fetchProfilesList = async () => {
    try {
      const res = await fetch(`${API_BASE}/profiles`);
      const data = await res.json();
      if (data.status === 'success' && data.profiles.length > 0) {
        setProfilesList(data.profiles);
        if (!activeProfileId) {
          const firstId = data.profiles[0].profile_id;
          setActiveProfileId(firstId);
          fetchProfilePayload(firstId);
        }
      } else {
        setProfilesList([]);
        setProfilePayload(null);
        setActiveProfileId(null);
      }
    } catch (e) {
      console.log('Backend connection offline or initializing SQLite');
    }
  };

  // Fetch full relational bundle for active profile
  const fetchProfilePayload = async (pid) => {
    if (!pid) return;
    try {
      const res = await fetch(`${API_BASE}/profiles/${pid}`);
      const data = await res.json();
      if (data.status === 'success') {
        setProfilePayload(data);
      }
    } catch (e) {
      console.error('Error fetching profile payload for ID:', pid, e);
    }
  };

  // Fetch all resumes in SQLite
  const fetchResumesList = async () => {
    try {
      const res = await fetch(`${API_BASE}/resumes`);
      const data = await res.json();
      if (data.status === 'success') {
        setResumesList(data.resumes);
      }
    } catch (e) {
      console.error('Error fetching resumes list', e);
    }
  };

  // Fetch live audit trail
  const fetchAuditLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/audit-logs`);
      const data = await res.json();
      if (data.status === 'success') setAuditLogs(data.logs);
    } catch (e) {
      console.error('Error fetching audit logs', e);
    }
  };

  // Switch Active User Profile
  const handleProfileSwitch = (pid) => {
    setActiveProfileId(pid);
    fetchProfilePayload(pid);
  };

  // Delete Candidate Profile
  const handleDeleteProfile = async (pid) => {
    if (!pid) return;
    const pObj = profilesList.find((p) => p.profile_id === pid);
    const pName = pObj?.candidate_name || `Profile #${pid}`;

    if (!window.confirm(`Are you sure you want to delete profile "${pName}" (ID #${pid})?`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/profiles/${pid}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (data.status === 'success') {
        const remaining = profilesList.filter((p) => p.profile_id !== pid);
        setProfilesList(remaining);
        if (remaining.length > 0) {
          const nextId = remaining[0].profile_id;
          setActiveProfileId(nextId);
          fetchProfilePayload(nextId);
        } else {
          setActiveProfileId(null);
          setProfilePayload(null);
        }
        fetchResumesList();
        fetchAuditLogs();
      } else {
        alert(data.detail || 'Failed to delete profile');
      }
    } catch (e) {
      console.error('Error deleting profile:', e);
      alert('Network error while deleting profile');
    }
  };

  // Fixed JS PDF File Selector
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setSelectedPdfFile(file);
      } else {
        alert('Please select a valid .pdf file');
      }
    }
  };

  // Run full 5-Stage Governed Pipeline (Text or PDF)
  const handleRunPipeline = async () => {
    if (!selectedPdfFile && !resumeText.trim()) {
      alert('Please paste resume text or select a PDF file first!');
      return;
    }

    setIsProcessing(true);
    setCurrentStage(1);
    setSimulatedAttack(null);

    const timer1 = setTimeout(() => setCurrentStage(2), 1200);
    const timer2 = setTimeout(() => setCurrentStage(3), 2400);
    const timer3 = setTimeout(() => setCurrentStage(4), 3600);
    const timer4 = setTimeout(() => setCurrentStage(5), 4800);

    try {
      let res, data;

      if (selectedPdfFile) {
        // Upload PDF File Endpoint
        const formData = new FormData();
        formData.append('file', selectedPdfFile);
        res = await fetch(`${API_BASE}/upload-resume-pdf`, {
          method: 'POST',
          body: formData,
        });
      } else {
        // Text Process Resume Endpoint
        const formData = new FormData();
        formData.append('resume_text', resumeText);
        res = await fetch(`${API_BASE}/process-resume`, {
          method: 'POST',
          body: formData,
        });
      }

      data = await res.json();
      if (data.status === 'success') {
        setSelectedPdfFile(null);
        setResumeText('');
        if (fileInputRef.current) fileInputRef.current.value = '';

        if (data.adk_execution) {
          setAdkExecution(data.adk_execution);
        }

        await fetchProfilesList();
        if (data.profile_id) {
          setActiveProfileId(data.profile_id);
          fetchProfilePayload(data.profile_id);
        }
        fetchResumesList();
        fetchAuditLogs();

        // Show completion popup modal so user knows processing is 100% complete
        setPipelineSuccessModal(data);
      } else {
        alert(`Error: ${data.detail || data.message || 'Pipeline execution failed'}`);
      }
    } catch (e) {
      console.error(e);
      alert('Network error while processing resume');
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      setIsProcessing(false);
      setCurrentStage(5);
    }
  };

  // Direct Database QA Query
  const handleQueryDb = async (qText) => {
    const question = qText || dbQuestion;
    if (!question.trim()) return;

    setIsQueryingDb(true);
    setDbAnswer(null);

    try {
      const res = await fetch(`${API_BASE}/query-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, profile_id: activeProfileId }),
      });
      const data = await res.json();
      setDbAnswer(data.answer);
    } catch (e) {
      setDbAnswer('Error querying database. Ensure backend server is running on port 8000.');
    } finally {
      setIsQueryingDb(false);
    }
  };

  // Send Chat Message to AI Assistant
  const handleSendChatMessage = async (presetText) => {
    const messageText = presetText || chatInput;
    if (!messageText.trim() || isChatSending) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput('');
    setIsChatSending(true);

    try {
      const res = await fetch(`${API_BASE}/query-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: messageText, profile_id: activeProfileId }),
      });
      const data = await res.json();

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: data.answer || 'I am analyzing your profile data. Please refine your question or re-run the pipeline.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatMessages((prev) => [...prev, botMsg]);
    } catch (e) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: 'Error connecting to candidate database. Ensure api.py server is running.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsChatSending(false);
    }
  };

  // Trigger Simulated Attack with ArmorIQ Security Toggle State
  const handleTriggerAttack = async () => {
    try {
      const res = await fetch(`${API_BASE}/demo/trigger-attack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ secured: armoriqSecured }),
      });
      const data = await res.json();
      setSimulatedAttack(data);
      fetchAuditLogs();
    } catch (e) {
      console.error(e);
    }
  };

  const pipelineStages = [
    { id: 1, name: 'resume_extractor', label: '1. Extraction', icon: FileText, desc: 'Parses PDF/text into resumes table' },
    { id: 2, name: 'resume_analyzer', label: '2. Analysis', icon: Sparkles, desc: 'Analyzes skills & domain focus' },
    { id: 3, name: 'profile_maker', label: '3. Profiling', icon: Layers, desc: 'Creates new relational candidate profile' },
    { id: 4, name: 'opportunity_scout', label: '4. Scouting', icon: Search, desc: 'Searches web across 5 categories' },
    { id: 5, name: 'opportunity_ranker', label: '5. Ranking', icon: Award, desc: 'Scores & ranks 0-100 relevance' },
  ];

  const currentProfile = profilePayload?.profile;
  const currentResume = profilePayload?.resume;
  const currentAnalysis = profilePayload?.analysis;
  const currentOpportunities = profilePayload?.opportunities || [];

  const filteredOpportunities = selectedCategory === 'all'
    ? currentOpportunities
    : currentOpportunities.filter(o => o.category?.toLowerCase() === selectedCategory.toLowerCase());

  // Handle Shield Toggle
  const handleToggleShield = () => {
    const nextVal = !armoriqSecured;
    setArmoriqSecured(nextVal);
    setShieldNotification({
      type: nextVal ? 'secured' : 'unsecured',
      message: nextVal
        ? '🛡️ ArmorIQ Shield ENABLED (ON): Cryptographic delegation active. Sub-agents are restricted to authorized tool scopes.'
        : '🛑 ArmorIQ Shield DISABLED (OFF): Governance checks bypassed! Prompt injections can now execute unauthorized tool calls!',
    });
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-gray-100 font-sans pb-16">
      {/* ── TOP NAVBAR WITH MULTI-USER SELECTOR & ARMORIQ SECURITY TOGGLE ─────── */}
      <header className="border-b border-gray-800 bg-[#0F172A]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          
          {/* Logo & Subtitle */}
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-lg shadow-indigo-500/20">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                CareerOS <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 font-mono">v2.0 ArmorIQ</span>
              </h1>
              <p className="text-xs text-gray-400">Multi-User PDF Intelligence & Governance</p>
            </div>
          </div>

          {/* USER SELECTOR & SECURITY TOGGLE */}
          <div className="flex items-center gap-4">
            
            {/* USER PROFILE SWITCHER DROPDOWN & DELETE PROFILE BUTTON */}
            <div className="relative flex items-center gap-2">
              <div className="flex items-center gap-2 bg-[#070A11] border border-indigo-500/30 rounded-xl px-3.5 py-2 text-xs font-mono text-indigo-200 shadow-inner">
                <User className="w-4 h-4 text-indigo-400" />
                <span className="text-gray-400 font-sans">Active Profile:</span>
                <select
                  value={activeProfileId || ''}
                  onChange={(e) => handleProfileSwitch(Number(e.target.value))}
                  className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer pr-2"
                >
                  {profilesList.length > 0 ? (
                    profilesList.map((p) => (
                      <option key={p.profile_id} value={p.profile_id} className="bg-[#0F172A] text-white">
                        {p.candidate_name} (ID #{p.profile_id})
                      </option>
                    ))
                  ) : (
                    <option value="" className="bg-[#0F172A] text-white">No Profiles Loaded</option>
                  )}
                </select>
              </div>

              {/* REMOVE / DELETE PROFILE BUTTON WITH CROSS ICON ON HOVER */}
              {activeProfileId && (
                <button
                  type="button"
                  onClick={() => handleDeleteProfile(activeProfileId)}
                  title={`Delete active profile #${activeProfileId}`}
                  className="group relative flex items-center justify-center p-2 rounded-xl bg-[#070A11] border border-gray-800 hover:border-rose-500/60 hover:bg-rose-500/20 text-gray-400 hover:text-rose-400 transition-all duration-200 shadow-inner cursor-pointer"
                >
                  <X className="w-4 h-4 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-90 text-gray-400 group-hover:text-rose-400" />
                </button>
              )}
            </div>

            {/* ARMORIQ SECURITY TOGGLE SWITCH */}
            <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-[#070A11] border border-gray-800 shadow-inner">
              <span className="text-xs text-gray-300 font-mono flex items-center gap-1.5">
                {armoriqSecured ? (
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 text-rose-500 animate-pulse" />
                )}
                ArmorIQ Shield:
              </span>
              <button
                type="button"
                onClick={handleToggleShield}
                className={`relative inline-flex h-5 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  armoriqSecured ? 'bg-emerald-500' : 'bg-rose-600'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    armoriqSecured ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
              <span className={`text-[11px] font-mono font-bold uppercase tracking-wider ${armoriqSecured ? 'text-emerald-400' : 'text-rose-400 animate-pulse'}`}>
                {armoriqSecured ? 'ON' : 'OFF'}
              </span>
            </div>

          </div>

        </div>

        {/* SHIELD TOGGLE NOTIFICATION BANNER */}
        {shieldNotification && (
          <div className={`max-w-7xl mx-auto mt-3 p-2.5 rounded-xl border text-xs font-mono flex items-center justify-between transition-all ${
            shieldNotification.type === 'secured'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/15 border-rose-500/40 text-rose-300 animate-pulse'
          }`}>
            <span>{shieldNotification.message}</span>
            <button onClick={() => setShieldNotification(null)} className="text-gray-400 hover:text-white font-bold ml-4">✕</button>
          </div>
        )}

        {/* TOP PAGE NAVIGATION TABS */}
        <div className="max-w-7xl mx-auto mt-4 pt-3 border-t border-gray-800/60 flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-x-auto">
            {[
              { id: 'overview', label: '⚡ Pipeline & Upload', icon: Zap },
              { id: 'profile', label: '👤 Candidate Profile', icon: User },
              { id: 'resumes', label: '📄 Resumes Library', icon: FileText },
              { id: 'opportunities', label: '🎯 Opportunities', icon: Briefcase },
              { id: 'chat', label: '💬 AI Assistant Chat', icon: MessageSquare },
            ].map((tab) => {
              const IconComp = tab.icon;
              const isActive = activeNavTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveNavTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-md shadow-indigo-500/20 font-semibold'
                      : 'bg-gray-800/40 text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <IconComp className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'opportunities' && currentOpportunities.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.2 rounded-full bg-indigo-500/30 text-indigo-200 text-[10px]">
                      {currentOpportunities.length}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          <button
            onClick={loadInitialData}
            className="hidden sm:flex items-center gap-1 text-xs text-gray-400 hover:text-white transition px-2.5 py-1 rounded bg-gray-800/50"
            title="Refresh Relational Data"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Sync DB
          </button>
        </div>
      </header>


      {/* ── MAIN CONTENT AREA ────────────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 pt-6">

        {/* ========================================================================= */}
        {/* VIEW 1: PIPELINE & PDF UPLOAD OVERVIEW                                    */}
        {/* ========================================================================= */}
        {activeNavTab === 'overview' && (
          <div className="space-y-8">
            {/* HERO PIPELINE RUNNER & PDF UPLOAD ZONE */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Resume PDF / Text Upload Box */}
              <div className="lg:col-span-7 glass-card p-6 flex flex-col justify-between space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <FileUp className="w-5 h-5 text-indigo-400" />
                      <h2 className="text-lg font-semibold text-white">Upload PDF or Paste Resume</h2>
                    </div>
                    <span className="text-xs text-gray-400 font-mono">Creates New Profile On Execution</span>
                  </div>

                  {/* PDF UPLOAD BUTTON & DROPZONE */}
                  <div className="mb-4">
                    <input
                      type="file"
                      accept=".pdf"
                      ref={fileInputRef}
                      onChange={handleFileChange}
                      className="hidden"
                      id="pdf-upload-input"
                    />
                    
                    <label
                      htmlFor="pdf-upload-input"
                      className={`flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-2xl cursor-pointer transition ${
                        selectedPdfFile
                          ? 'bg-indigo-500/10 border-indigo-500/60'
                          : 'bg-[#070A11]/80 border-gray-800 hover:border-indigo-500/40 hover:bg-gray-900/50'
                      }`}
                    >
                      <UploadCloud className={`w-8 h-8 mb-2 ${selectedPdfFile ? 'text-indigo-400 animate-bounce' : 'text-gray-400'}`} />
                      {selectedPdfFile ? (
                        <div className="text-center">
                          <p className="text-sm font-semibold text-indigo-300 font-mono">📄 {selectedPdfFile.name}</p>
                          <p className="text-[11px] text-gray-400">{(selectedPdfFile.size / 1024).toFixed(1)} KB — Ready for PDF Extraction</p>
                        </div>
                      ) : (
                        <div className="text-center">
                          <p className="text-sm font-semibold text-gray-200">Click to Upload PDF Resume</p>
                          <p className="text-xs text-gray-400 mt-1">Supports any candidate resume in PDF format</p>
                        </div>
                      )}
                    </label>
                  </div>

                  {/* OR Divider */}
                  <div className="flex items-center gap-4 my-4">
                    <div className="flex-1 border-t border-gray-800"></div>
                    <span className="text-[11px] text-gray-500 font-mono uppercase">OR Paste Text</span>
                    <div className="flex-1 border-t border-gray-800"></div>
                  </div>

                  {/* Raw Textarea */}
                  <textarea
                    value={resumeText}
                    onChange={(e) => {
                      setResumeText(e.target.value);
                      if (selectedPdfFile) setSelectedPdfFile(null);
                    }}
                    rows={4}
                    className="w-full bg-[#070A11] border border-gray-800 rounded-xl p-3.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500/50 resize-none font-mono"
                    placeholder="Or paste candidate resume text here..."
                  />
                </div>

                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5 text-cyan-400" /> Signed identity tokens via ArmorIQ
                  </p>
                  <button
                    onClick={handleRunPipeline}
                    disabled={isProcessing}
                    className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-sm transition-all shadow-lg ${
                      isProcessing
                        ? 'bg-gray-800 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white shadow-indigo-500/25 hover:scale-[1.02]'
                    }`}
                  >
                    <Zap className="w-4 h-4 fill-white" />
                    {isProcessing ? 'Processing PDF Pipeline...' : 'Process & Create Candidate Profile'}
                  </button>
                </div>
              </div>

              {/* 5-Stage Visual Stepper */}
              <div className="lg:col-span-5 glass-card p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-cyan-400" />
                      <h2 className="text-lg font-semibold text-white">5-Stage Execution Tracker</h2>
                    </div>
                    <span className="text-xs font-mono text-cyan-400">
                      {currentStage > 0 ? `Stage ${currentStage}/5` : 'Ready'}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {pipelineStages.map((s) => {
                      const IconComponent = s.icon;
                      const isActive = currentStage === s.id;
                      const isDone = currentStage > s.id;
                      return (
                        <div
                          key={s.id}
                          className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                            isActive
                              ? 'bg-indigo-500/10 border-indigo-500/50 glow-active'
                              : isDone
                              ? 'bg-emerald-500/5 border-emerald-500/20 text-gray-300'
                              : 'bg-[#070A11]/60 border-gray-800/80 text-gray-500'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`p-2 rounded-lg ${
                                isActive
                                  ? 'bg-indigo-600 text-white'
                                  : isDone
                                  ? 'bg-emerald-500/20 text-emerald-400'
                                  : 'bg-gray-800 text-gray-500'
                              }`}
                            >
                              <IconComponent className="w-4 h-4" />
                            </div>
                            <div>
                              <p className={`text-xs font-semibold ${isActive ? 'text-white' : isDone ? 'text-gray-200' : 'text-gray-500'}`}>
                                {s.label}
                              </p>
                              <p className="text-[11px] text-gray-400">{s.desc}</p>
                            </div>
                          </div>

                          {isDone && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                          {isActive && (
                            <span className="flex h-2.5 w-2.5 relative">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </section>

            {/* ARMORIQ CRYPTOGRAPHIC GOVERNANCE MONITOR & DEMO FLOW */}
            <section className={`glass-card p-6 transition-all ${armoriqSecured ? 'border-emerald-500/40' : 'border-rose-500/60'}`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl ${armoriqSecured ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    {armoriqSecured ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6 animate-pulse" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-white">ArmorIQ Governance & Attack Interceptor</h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        armoriqSecured ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400' : 'bg-rose-500/20 border border-rose-500/40 text-rose-300 animate-pulse'
                      }`}>
                        {armoriqSecured ? 'SECURED MODE (ON)' : 'UNSECURED BYPASS (OFF)'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">Demonstrates real-time scope enforcement, protective interception, and command trajectory traces</p>
                  </div>
                </div>

                <button
                  onClick={handleTriggerAttack}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-xs transition shadow-lg ${
                    armoriqSecured
                      ? 'bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 shadow-rose-500/10'
                      : 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/40 animate-pulse'
                  }`}
                >
                  <AlertTriangle className="w-4 h-4" /> Simulate Prompt Attack ({armoriqSecured ? 'Shield ON' : 'Shield OFF'})
                </button>
              </div>

              {/* TRAJECTORY TRACE GRAPH VISUALIZER */}
              {simulatedAttack && (
                <div className={`p-5 rounded-2xl mb-6 border font-mono text-xs space-y-4 ${
                  simulatedAttack.status === 'blocked'
                    ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                    : 'bg-rose-500/10 border-rose-500/50 text-rose-200'
                }`}>
                  <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                    <div className="flex items-center gap-2 font-bold text-sm">
                      {simulatedAttack.status === 'blocked' ? (
                        <span className="text-emerald-400 flex items-center gap-1.5">
                          <ShieldCheck className="w-5 h-5" /> 🛡️ ARMORIQ PROTECTED & BLOCKED BEFORE EXECUTION
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1.5 animate-pulse">
                          <Unlock className="w-5 h-5" /> 🛑 UNSECURED SCOPE BREACH EXPLOITED (SHIELD WAS OFF)
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-gray-400 font-mono">
                      Timestamp: {new Date().toLocaleTimeString()}
                    </span>
                  </div>

                  <p className="text-xs leading-relaxed">{simulatedAttack.message || simulatedAttack.warning}</p>

                  {/* COMMAND TRAJECTORY TRACE STEPS */}
                  {simulatedAttack.trajectory_trace && (
                    <div className="pt-2">
                      <p className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                        <GitCommit className="w-4 h-4 text-indigo-400" /> Command Trajectory Trace:
                      </p>

                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        {simulatedAttack.trajectory_trace.map((tr, i) => (
                          <div
                            key={i}
                            className={`p-3 rounded-xl border flex flex-col justify-between space-y-2 relative ${
                              i === 3
                                ? simulatedAttack.status === 'blocked'
                                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-100 font-bold'
                                  : 'bg-rose-500/20 border-rose-500/60 text-rose-100 font-bold animate-pulse'
                                : 'bg-[#070A11]/80 border-gray-800/80 text-gray-300'
                            }`}
                          >
                            <div className="flex items-center justify-between text-[10px] text-gray-400 border-b border-gray-800 pb-1">
                              <span>STEP {tr.step}</span>
                              <span className="text-indigo-400 font-bold">{tr.node}</span>
                            </div>
                            <p className="text-[11px] leading-snug">{tr.action}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Live Audit Trail Table */}
              <div className="bg-[#070A11] border border-gray-800 rounded-xl p-4 font-mono text-xs max-h-56 overflow-y-auto space-y-2">
                <div className="flex items-center justify-between text-gray-500 text-[11px] pb-2 border-b border-gray-800">
                  <span>EVENT TYPE</span>
                  <span>SUB-AGENT IDENTITY</span>
                  <span>TOOL / ACTION</span>
                  <span>GOVERNANCE STATUS</span>
                </div>

                {auditLogs.length > 0 ? (
                  auditLogs.map((log, idx) => (
                    <div key={idx} className="flex items-center justify-between text-gray-300 py-1 border-b border-gray-800/40">
                      <span className="text-indigo-400 font-bold">{log.event}</span>
                      <span className="text-gray-400">{log.sub_agent || log.agent_id || 'root_coordinator'}</span>
                      <span className="text-cyan-400">{log.requested_tool || log.intent?.slice(0, 30) || 'N/A'}</span>
                      <span className={
                        log.status?.includes('BLOCKED')
                          ? 'text-emerald-400 font-bold'
                          : log.status?.includes('BREACH') || log.status?.includes('UNPROTECTED')
                          ? 'text-rose-400 font-bold'
                          : 'text-emerald-400 font-bold'
                      }>
                        {log.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No audit logs recorded yet. Upload PDF above to generate governance logs!</p>
                )}
              </div>
            </section>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 2: CANDIDATE PROFILE PAGE                                            */}
        {/* ========================================================================= */}
        {activeNavTab === 'profile' && (
          <div className="space-y-8">
            {currentProfile ? (
              <>
                {/* HERO CANDIDATE CARD */}
                <section className="glass-card p-6 relative overflow-hidden">
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/20">
                        {currentResume?.name ? currentResume.name.charAt(0).toUpperCase() : 'C'}
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h2 className="text-2xl font-bold text-white">
                            {currentResume?.name || currentProfile.candidate_name || `Candidate Profile #${activeProfileId}`}
                          </h2>
                          <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
                            Profile ID #{activeProfileId}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleDeleteProfile(activeProfileId)}
                            title={`Remove profile #${activeProfileId}`}
                            className="group flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-mono transition-all duration-200 cursor-pointer"
                          >
                            <X className="w-3.5 h-3.5 transition-transform duration-200 group-hover:scale-110 group-hover:rotate-90 text-rose-400" />
                            Delete Profile
                          </button>
                        </div>
                        <p className="text-sm text-gray-400 mt-1 flex items-center gap-3">
                          <span>📧 {currentResume?.email || currentProfile.candidate_email || 'candidate@example.com'}</span>
                          {currentResume?.phone && <span>📞 {currentResume.phone}</span>}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-mono font-semibold uppercase">
                        {currentAnalysis?.experience_level || 'Mid Level'}
                      </span>
                      <span className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-semibold uppercase">
                        {currentAnalysis?.domain_focus || 'Software Engineering'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-gray-800/80">
                    <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Executive Summary</h4>
                    <p className="text-sm text-gray-200 leading-relaxed bg-[#070A11]/60 p-4 rounded-xl border border-gray-800/50">
                      {currentProfile.experience_summary}
                    </p>
                  </div>
                </section>

                {/* TECH STACK & EVALUATION REPORT */}
                <section className="grid grid-cols-1 md:grid-cols-12 gap-8">
                  <div className="md:col-span-7 space-y-6">
                    <div className="glass-card p-6">
                      <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                        <Code className="w-5 h-5 text-indigo-400" /> Relational Technical Stack
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {Array.isArray(currentProfile.tech_stack) && currentProfile.tech_stack.length > 0 ? (
                          currentProfile.tech_stack.map((tech, idx) => (
                            <span
                              key={idx}
                              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 border border-indigo-500/30 text-indigo-200 text-xs font-mono hover:scale-105 transition cursor-default"
                            >
                              ⚡ {tech}
                            </span>
                          ))
                        ) : (
                          <p className="text-xs text-gray-500">No tech stack listed.</p>
                        )}
                      </div>
                    </div>

                    <div className="glass-card p-6">
                      <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                        <Target className="w-5 h-5 text-emerald-400" /> Preferred Roles & Objectives
                      </h3>
                      <div className="space-y-4">
                        <div className="flex flex-wrap gap-2">
                          {Array.isArray(currentProfile.preferred_roles) ? (
                            currentProfile.preferred_roles.map((role, idx) => (
                              <span key={idx} className="px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-medium">
                                🎯 {role}
                              </span>
                            ))
                          ) : null}
                        </div>
                        {currentProfile.career_goals && (
                          <p className="text-xs text-gray-300 italic bg-[#070A11]/60 p-3 rounded-lg border border-gray-800">
                            "{currentProfile.career_goals}"
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="md:col-span-5 space-y-6">
                    <div className="glass-card p-6 border-indigo-500/30">
                      <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-cyan-400" /> AI Resume Evaluation Report
                      </h3>

                      {currentAnalysis ? (
                        <div className="space-y-4 text-xs">
                          <div>
                            <p className="font-semibold text-emerald-400 mb-2 flex items-center gap-1">
                              <CheckCircle className="w-3.5 h-3.5" /> Strengths:
                            </p>
                            <div className="space-y-1.5">
                              {Array.isArray(currentAnalysis.strengths) ? (
                                currentAnalysis.strengths.map((s, i) => (
                                  <p key={i} className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-200 p-2 rounded-lg">
                                    • {s}
                                  </p>
                                ))
                              ) : (
                                <p className="text-gray-400">{currentAnalysis.strengths}</p>
                              )}
                            </div>
                          </div>

                          <div>
                            <p className="font-semibold text-amber-400 mb-2 flex items-center gap-1">
                              <AlertTriangle className="w-3.5 h-3.5" /> Growth Areas:
                            </p>
                            <div className="space-y-1.5">
                              {Array.isArray(currentAnalysis.weaknesses) ? (
                                currentAnalysis.weaknesses.map((w, i) => (
                                  <p key={i} className="bg-amber-500/10 border border-amber-500/20 text-amber-200 p-2 rounded-lg">
                                    • {w}
                                  </p>
                                ))
                              ) : (
                                <p className="text-gray-400">{currentAnalysis.weaknesses}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-gray-500">No analysis record linked.</p>
                      )}
                    </div>
                  </div>
                </section>

                {/* EXTRACTED RESUME DETAILS (EDUCATION, PROJECTS, EXPERIENCE, CERTIFICATIONS) */}
                <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* EDUCATION CARD */}
                  <div className="glass-card p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-indigo-400" /> Education & Qualifications
                    </h3>
                    {currentResume?.education && (Array.isArray(currentResume.education) ? currentResume.education.length > 0 : String(currentResume.education).trim()) ? (
                      <div className="space-y-2 text-xs">
                        {Array.isArray(currentResume.education) ? (
                          currentResume.education.map((edu, i) => (
                            <div key={i} className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200">
                              🎓 {edu}
                            </div>
                          ))
                        ) : (
                          <div className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200 whitespace-pre-line">
                            🎓 {currentResume.education}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No education entries extracted.</p>
                    )}
                  </div>

                  {/* PROJECTS CARD */}
                  <div className="glass-card p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <Code className="w-5 h-5 text-cyan-400" /> Projects & Portfolio
                    </h3>
                    {currentResume?.projects && (Array.isArray(currentResume.projects) ? currentResume.projects.length > 0 : String(currentResume.projects).trim()) ? (
                      <div className="space-y-2 text-xs">
                        {Array.isArray(currentResume.projects) ? (
                          currentResume.projects.map((proj, i) => (
                            <div key={i} className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200">
                              🚀 {proj}
                            </div>
                          ))
                        ) : (
                          <div className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200 whitespace-pre-line">
                            🚀 {currentResume.projects}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No project entries extracted.</p>
                    )}
                  </div>

                  {/* WORK EXPERIENCE CARD */}
                  <div className="glass-card p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <Briefcase className="w-5 h-5 text-emerald-400" /> Work Experience
                    </h3>
                    {currentResume?.experience && (Array.isArray(currentResume.experience) ? currentResume.experience.length > 0 : String(currentResume.experience).trim()) ? (
                      <div className="space-y-2 text-xs">
                        {Array.isArray(currentResume.experience) ? (
                          currentResume.experience.map((exp, i) => (
                            <div key={i} className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200">
                              💼 {exp}
                            </div>
                          ))
                        ) : (
                          <div className="bg-[#070A11]/80 border border-gray-800 p-3 rounded-xl text-gray-200 whitespace-pre-line">
                            💼 {currentResume.experience}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No work experience entries extracted.</p>
                    )}
                  </div>

                  {/* CERTIFICATIONS & SKILLS CARD */}
                  <div className="glass-card p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <Award className="w-5 h-5 text-amber-400" /> Certifications & Extracted Skills
                    </h3>
                    <div className="space-y-4 text-xs">
                      {currentResume?.certifications && (Array.isArray(currentResume.certifications) ? currentResume.certifications.length > 0 : String(currentResume.certifications).trim()) ? (
                        <div>
                          <p className="font-semibold text-amber-300 mb-2">🏆 Certifications:</p>
                          <div className="space-y-1.5">
                            {Array.isArray(currentResume.certifications) ? (
                              currentResume.certifications.map((cert, i) => (
                                <div key={i} className="bg-[#070A11]/80 border border-gray-800 p-2.5 rounded-lg text-amber-100">
                                  • {cert}
                                </div>
                              ))
                            ) : (
                              <p className="text-gray-300">{currentResume.certifications}</p>
                            )}
                          </div>
                        </div>
                      ) : null}

                      {currentResume?.skills && Array.isArray(currentResume.skills) && currentResume.skills.length > 0 && (
                        <div>
                          <p className="font-semibold text-indigo-300 mb-2">📜 Parsed Resume Skills:</p>
                          <div className="flex flex-wrap gap-1.5">
                            {currentResume.skills.map((sk, i) => (
                              <span key={i} className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-mono">
                                {sk}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </section>
              </>
            ) : (
              <div className="glass-card p-12 text-center">
                <User className="w-12 h-12 text-indigo-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white">No Profiles in Database</h3>
                <p className="text-xs text-gray-400 mt-1">Upload a PDF resume in the Pipeline tab to create your first candidate profile!</p>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 3: RESUMES LIBRARY PAGE                                              */}
        {/* ========================================================================= */}
        {activeNavTab === 'resumes' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <FileText className="w-6 h-6 text-indigo-400" /> Resumes Library & Parsed Relational Data
                </h2>
                <p className="text-xs text-gray-400">All candidate resumes stored in SQLite with structured AI extraction</p>
              </div>

              <button
                onClick={() => setActiveNavTab('overview')}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 flex items-center gap-2"
              >
                <UploadCloud className="w-4 h-4" /> Upload New PDF Resume
              </button>
            </div>

            {resumesList.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {resumesList.map((resItem) => (
                  <div key={resItem.id} className="glass-card p-6 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="p-3 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-bold">
                            <FileCode className="w-6 h-6" />
                          </div>
                          <div>
                            <h3 className="text-base font-bold text-white">{resItem.name || `Resume #${resItem.id}`}</h3>
                            <p className="text-xs text-gray-400">{resItem.email || 'No email parsed'}</p>
                          </div>
                        </div>

                        <span className="px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-[10px] font-mono">
                          ID #{resItem.id}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-4">
                        {resItem.experience_level && (
                          <span className="px-2.5 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[11px] font-mono">
                            {resItem.experience_level}
                          </span>
                        )}
                        {resItem.domain_focus && (
                          <span className="px-2.5 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-mono">
                            {resItem.domain_focus}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="pt-4 border-t border-gray-800 flex items-center justify-between gap-3">
                      <span className="text-[11px] text-gray-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {resItem.created_at ? new Date(resItem.created_at).toLocaleDateString() : 'Recent'}
                      </span>

                      <button
                        onClick={() => setSelectedResumeModal(resItem)}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 border border-indigo-500/40 text-indigo-200 hover:text-white text-xs font-medium transition"
                      >
                        <Eye className="w-3.5 h-3.5" /> View Parsed Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass-card p-12 text-center">
                <FileText className="w-12 h-12 text-indigo-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white">No Resumes Found</h3>
                <p className="text-xs text-gray-400 mt-1">Upload a PDF resume in the Pipeline tab to store your first resume!</p>
              </div>
            )}
          </div>
        )}

        {/* RESUME PARSED DETAILS MODAL */}
        {selectedResumeModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="glass-card max-w-3xl w-full max-h-[85vh] overflow-y-auto p-6 space-y-6 relative border-indigo-500/40">
              <button
                onClick={() => setSelectedResumeModal(null)}
                className="absolute top-4 right-4 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-indigo-600 text-white font-bold">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedResumeModal.name || `Resume #${selectedResumeModal.id}`}</h3>
                  <p className="text-xs text-gray-400">{selectedResumeModal.email} | {selectedResumeModal.phone}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="bg-[#070A11] p-4 rounded-xl border border-gray-800">
                  <h4 className="font-bold text-indigo-400 mb-2 uppercase">Education</h4>
                  <p className="text-gray-300 font-mono whitespace-pre-line">
                    {typeof selectedResumeModal.education === 'object' ? JSON.stringify(selectedResumeModal.education, null, 2) : selectedResumeModal.education || 'N/A'}
                  </p>
                </div>

                <div className="bg-[#070A11] p-4 rounded-xl border border-gray-800">
                  <h4 className="font-bold text-cyan-400 mb-2 uppercase">Work Experience</h4>
                  <p className="text-gray-300 font-mono whitespace-pre-line">
                    {typeof selectedResumeModal.experience === 'object' ? JSON.stringify(selectedResumeModal.experience, null, 2) : selectedResumeModal.experience || 'N/A'}
                  </p>
                </div>
              </div>

              {selectedResumeModal.raw_text && (
                <div>
                  <h4 className="text-xs font-bold text-gray-400 uppercase mb-2">Raw Extracted Resume Text</h4>
                  <pre className="bg-[#070A11] p-4 rounded-xl border border-gray-800 text-[11px] text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap max-h-48">
                    {selectedResumeModal.raw_text}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}

        {/* PIPELINE EXECUTION SUCCESS POPUP MODAL */}
        {pipelineSuccessModal && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
            <div className="glass-card max-w-lg w-full p-6 space-y-6 text-center border-emerald-500/50 shadow-2xl relative animate-in fade-in zoom-in duration-200">
              <button
                onClick={() => setPipelineSuccessModal(null)}
                className="absolute top-4 right-4 p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 text-emerald-400 flex items-center justify-center mx-auto shadow-lg shadow-emerald-500/20">
                <CheckCircle className="w-10 h-10" />
              </div>

              <div>
                <h3 className="text-xl font-extrabold text-white">🎉 5-Stage Governed Pipeline Completed!</h3>
                <p className="text-xs text-gray-300 mt-2 leading-relaxed">
                  Candidate resume parsed, AI profile built, and real opportunities scouted & ranked successfully under <strong>ArmorIQ Zero-Trust Governance</strong>.
                </p>
              </div>

              <div className="bg-[#070A11] p-4 rounded-xl border border-gray-800 text-xs font-mono grid grid-cols-2 gap-3 text-left">
                <div>
                  <span className="text-gray-400 text-[10px]">CANDIDATE PROFILE:</span>
                  <p className="text-indigo-300 font-bold">Profile ID #{pipelineSuccessModal.profile_id}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-[10px]">PARSED RESUME:</span>
                  <p className="text-cyan-300 font-bold">Resume ID #{pipelineSuccessModal.resume_id}</p>
                </div>
                <div>
                  <span className="text-gray-400 text-[10px]">OPPORTUNITIES SCOUTED:</span>
                  <p className="text-emerald-400 font-bold">{pipelineSuccessModal.opportunities_found || 0} Found</p>
                </div>
                <div>
                  <span className="text-gray-400 text-[10px]">RANKED MATCHES:</span>
                  <p className="text-emerald-400 font-bold">{pipelineSuccessModal.total_ranked || 0} Ranked</p>
                </div>
              </div>

              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => {
                    setPipelineSuccessModal(null);
                    setActiveNavTab('profile');
                  }}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-lg shadow-indigo-500/20 flex items-center gap-1.5"
                >
                  <User className="w-4 h-4" /> View Candidate Profile
                </button>

                <button
                  onClick={() => {
                    setPipelineSuccessModal(null);
                    setActiveNavTab('opportunities');
                  }}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-500/20 flex items-center gap-1.5"
                >
                  <Briefcase className="w-4 h-4" /> View Opportunities
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 4: OPPORTUNITIES MARKETPLACE                                         */}
        {/* ========================================================================= */}
        {activeNavTab === 'opportunities' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Briefcase className="w-6 h-6 text-indigo-400" /> Ranked Opportunity Marketplace
                </h2>
                <p className="text-xs text-gray-400">Scouted & scored specifically for Candidate Profile #{activeProfileId}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'job', label: 'Jobs' },
                  { id: 'internship', label: 'Internships' },
                  { id: 'competition', label: 'Competitions' },
                  { id: 'conclave', label: 'Conclaves' },
                ].map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                      selectedCategory === cat.id
                        ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30'
                        : 'bg-gray-800/60 text-gray-400 hover:text-white'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {filteredOpportunities.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredOpportunities.map((opp, idx) => (
                  <div key={idx} className="glass-card p-5 flex flex-col justify-between hover:border-indigo-500/50 transition">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-[10px] font-mono font-bold uppercase">
                          {opp.category}
                        </span>
                        <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold">
                          Score: {opp.relevance_score}%
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-white mb-2 line-clamp-1">{opp.title}</h3>
                      <p className="text-xs text-gray-400 mb-4 line-clamp-3 leading-relaxed">{opp.description}</p>
                    </div>

                    <a
                      href={opp.url}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-xs font-medium text-white transition mt-2 border border-indigo-500/30"
                    >
                      View Details & Apply <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass-card p-12 text-center">
                <Briefcase className="w-12 h-12 text-indigo-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold text-white">No Opportunities Found for Category</h3>
                <p className="text-xs text-gray-400 mt-1">Try selecting 'All' or run the opportunity scout in the Pipeline tab!</p>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 5: INTERACTIVE AI CHAT INTERFACE                                     */}
        {/* ========================================================================= */}
        {activeNavTab === 'chat' && (
          <div className="glass-card p-6 flex flex-col h-[75vh] max-w-4xl mx-auto border-indigo-500/30">
            {/* CHAT HEADER */}
            <div className="pb-4 border-b border-gray-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-md">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    AI Candidate Assistant
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono">
                      SQLite Connected
                    </span>
                  </h2>
                  <p className="text-xs text-gray-400 font-mono">
                    Context: Profile #{activeProfileId || 'None'} ({currentResume?.name || 'No Active Candidate'})
                  </p>
                </div>
              </div>

              <button
                onClick={() => setChatMessages([])}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-rose-400 px-3 py-1.5 rounded-lg bg-gray-800/50 transition"
              >
                <Trash2 className="w-3.5 h-3.5" /> Clear Chat
              </button>
            </div>

            {/* CHAT MESSAGES SCROLL AREA */}
            <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-2">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.sender === 'bot' && (
                    <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[75%] p-4 rounded-2xl text-xs leading-relaxed font-sans ${
                      msg.sender === 'user'
                        ? 'bg-gradient-to-r from-indigo-600 to-cyan-600 text-white rounded-br-none shadow-lg shadow-indigo-500/10'
                        : 'bg-[#070A11] border border-gray-800 text-gray-200 rounded-bl-none font-mono whitespace-pre-line'
                    }`}
                  >
                    <p>{msg.text}</p>
                    <span className={`text-[10px] block mt-1 ${msg.sender === 'user' ? 'text-indigo-200 text-right' : 'text-gray-500'}`}>
                      {msg.timestamp}
                    </span>
                  </div>

                  {msg.sender === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-cyan-600 flex items-center justify-center text-white shrink-0 shadow-md">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              ))}

              {isChatSending && (
                <div className="flex items-center gap-2 text-xs text-indigo-400 font-mono animate-pulse">
                  <Bot className="w-4 h-4" /> Querying candidate SQLite database...
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* QUICK SUGGESTED CHIPS */}
            <div className="py-2 flex flex-wrap gap-2 border-t border-gray-800/60">
              {[
                'What are my top technical skills?',
                'Show my top ranked opportunities',
                'What experience level was assigned?',
                'What are my preferred roles?',
              ].map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendChatMessage(chip)}
                  className="text-[11px] bg-gray-800/60 hover:bg-indigo-600/30 border border-gray-700/50 hover:border-indigo-500/50 text-gray-300 hover:text-indigo-200 px-3 py-1.5 rounded-lg transition"
                >
                  💡 {chip}
                </button>
              ))}
            </div>

            {/* CHAT INPUT BAR */}
            <div className="pt-2 flex gap-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendChatMessage()}
                placeholder="Ask anything about candidate skills, experience, or job matches..."
                className="flex-1 bg-[#070A11] border border-gray-800 rounded-xl px-4 py-3 text-xs text-gray-200 focus:outline-none focus:border-indigo-500/50 font-sans"
              />
              <button
                onClick={() => handleSendChatMessage()}
                disabled={isChatSending}
                className="bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-medium text-xs px-6 py-3 rounded-xl transition shadow-lg shadow-indigo-500/20 flex items-center gap-2"
              >
                <Send className="w-4 h-4" /> Send
              </button>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
