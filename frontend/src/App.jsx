import React, { useState, useEffect } from 'react';
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
  Terminal
} from 'lucide-react';

const API_BASE = 'http://localhost:5001/api';

export default function App() {
  // Resume & Pipeline State
  const [resumeText, setResumeText] = useState(
    'John Doe, john.doe@email.com, +91-9876543210. Education: B.Tech Computer Science from IIT Delhi (2024). Skills: Python, JavaScript, React, Node.js, Django, PostgreSQL, Docker, AWS, Git, Machine Learning, TensorFlow. Experience: Software Intern at Google (Summer 2023) - Built microservices. Junior Developer at TechStartup (2024) - Developed full-stack web apps with React and Django. Projects: AI Chatbot - Built NLP chatbot. E-commerce Platform - Full stack React app. Certifications: AWS Cloud Practitioner, Google TensorFlow Developer.'
  );
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);

  // Direct DB QA State
  const [dbQuestion, setDbQuestion] = useState('');
  const [dbAnswer, setDbAnswer] = useState(null);
  const [isQueryingDb, setIsQueryingDb] = useState(false);

  // Profile & Opportunities State
  const [profile, setProfile] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedTab, setSelectedTab] = useState('all');

  // ArmorIQ Governance & Audit State
  const [auditLogs, setAuditLogs] = useState([]);
  const [simulatedAttack, setSimulatedAttack] = useState(null);

  // Load initial data on mount
  useEffect(() => {
    fetchProfile();
    fetchOpportunities('all');
    fetchAuditLogs();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API_BASE}/profile/latest`);
      const data = await res.json();
      if (data.status === 'success') setProfile(data.profile);
    } catch (e) {
      console.log('Backend not connected yet or empty DB');
    }
  };

  const fetchOpportunities = async (cat) => {
    try {
      const res = await fetch(`${API_BASE}/opportunities/latest?category=${cat}`);
      const data = await res.json();
      if (data.status === 'success') setOpportunities(data.opportunities);
    } catch (e) {
      console.log('Error fetching opportunities');
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/audit-logs`);
      const data = await res.json();
      if (data.status === 'success') setAuditLogs(data.logs);
    } catch (e) {
      console.log('Error fetching audit logs');
    }
  };

  // Run full 5-stage pipeline
  const handleRunPipeline = async () => {
    setIsProcessing(true);
    setCurrentStage(1);
    setSimulatedAttack(null);

    // Simulate animated stepper progression
    const timer1 = setTimeout(() => setCurrentStage(2), 1200);
    const timer2 = setTimeout(() => setCurrentStage(3), 2400);
    const timer3 = setTimeout(() => setCurrentStage(4), 3600);
    const timer4 = setTimeout(() => setCurrentStage(5), 4800);

    try {
      const formData = new FormData();
      formData.append('resume_text', resumeText);

      const res = await fetch(`${API_BASE}/process-resume`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (data.status === 'success') {
        fetchProfile();
        fetchOpportunities(selectedTab);
        fetchAuditLogs();
      }
    } catch (e) {
      console.error(e);
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      setIsProcessing(false);
      setCurrentStage(5);
    }
  };

  // Direct DB QA Query (No pipeline execution)
  const handleQueryDb = async (qText) => {
    const question = qText || dbQuestion;
    if (!question.trim()) return;

    setIsQueryingDb(true);
    setDbAnswer(null);

    try {
      const res = await fetch(`${API_BASE}/query-db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setDbAnswer(data.answer);
    } catch (e) {
      setDbAnswer('Error querying database. Ensure backend server (api.py) is running on port 5000.');
    } finally {
      setIsQueryingDb(false);
    }
  };

  // Trigger Simulated Attack (Hackathon Scope Violation Demo)
  const handleTriggerAttack = async () => {
    try {
      const res = await fetch(`${API_BASE}/demo/trigger-attack`, { method: 'POST' });
      const data = await res.json();
      setSimulatedAttack(data);
      fetchAuditLogs();
    } catch (e) {
      console.error(e);
    }
  };

  const handleTabChange = (cat) => {
    setSelectedTab(cat);
    fetchOpportunities(cat);
  };

  const pipelineStages = [
    { id: 1, name: 'resume_extractor', label: '1. Extraction', icon: FileText, desc: 'Parses resume & stores in resumes table' },
    { id: 2, name: 'resume_analyzer', label: '2. Analysis', icon: Sparkles, desc: 'Analyzes skills & domain focus' },
    { id: 3, name: 'profile_maker', label: '3. Profiling', icon: Layers, desc: 'Builds candidate profile & search keys' },
    { id: 4, name: 'opportunity_scout', label: '4. Scouting', icon: Search, desc: 'Searches web across 5 categories' },
    { id: 5, name: 'opportunity_ranker', label: '5. Ranking', icon: Award, desc: 'Scores & ranks 0-100 relevance' },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-gray-100 font-sans pb-16">
      {/* ── HEADER ───────────────────────────────────────────────────────────── */}
      <header className="border-b border-gray-800 bg-[#0F172A]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-lg shadow-indigo-500/20">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                CareerOS <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 font-mono">v2.0 ArmorIQ Governed</span>
              </h1>
              <p className="text-xs text-gray-400">Problem 2 Track: Multi-Agent Delegation & Cryptographic Security</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
              <Shield className="w-4 h-4" /> ArmorIQ SDK Active
            </div>
            <a
              href="https://github.com/Krati-orbit/automatic-hack"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 text-xs text-gray-300 hover:text-white bg-gray-800/80 hover:bg-gray-700 px-3 py-2 rounded-lg transition"
            >
              <Code className="w-4 h-4 text-cyan-400" /> GitHub Repository
            </a>
          </div>
        </div>
      </header>

      {/* ── MAIN CONTENT CONTAINER ───────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 pt-8 space-y-8">

        {/* ── HERO & RESUME PIPELINE SECTION ───────────────────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Resume Upload Box */}
          <div className="lg:col-span-7 glass-card p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-400" />
                  <h2 className="text-lg font-semibold text-white">Candidate Resume Input</h2>
                </div>
                <span className="text-xs text-gray-400">Triggers Full 5-Stage Governed Pipeline</span>
              </div>
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={6}
                className="w-full bg-[#070A11] border border-gray-800 rounded-xl p-4 text-sm text-gray-200 focus:outline-none focus:border-indigo-500/50 resize-none font-mono"
                placeholder="Paste candidate resume text or markdown here..."
              />
            </div>

            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <Lock className="w-3.5 h-3.5 text-cyan-400" /> Signed by Keypair identities via ArmorIQ
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
                {isProcessing ? 'Processing Pipeline...' : 'Run ArmorIQ Pipeline'}
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

        {/* ── DIRECT DATABASE QA PROMPT BAR ────────────────────────────────────── */}
        <section className="glass-card p-6">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">Direct Database QA (No Pipeline Re-Run)</h2>
          </div>
          <p className="text-xs text-gray-400 mb-4">
            Ask questions about your profile, skills, strengths, or recommendations. Answers are read directly from SQLite without re-running the 5-stage pipeline!
          </p>

          <div className="flex gap-3 mb-4">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-gray-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={dbQuestion}
                onChange={(e) => setDbQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleQueryDb()}
                placeholder="Ask e.g. 'What are my top technical skills?' or 'Show my top matches'..."
                className="w-full bg-[#070A11] border border-gray-800 rounded-xl pl-11 pr-4 py-3 text-sm text-gray-200 focus:outline-none focus:border-emerald-500/50"
              />
            </div>
            <button
              onClick={() => handleQueryDb()}
              disabled={isQueryingDb}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm px-6 py-3 rounded-xl transition shadow-lg shadow-emerald-500/20"
            >
              {isQueryingDb ? 'Querying DB...' : 'Ask DB'}
            </button>
          </div>

          {/* Quick chips */}
          <div className="flex flex-wrap gap-2 mb-3">
            {[
              'What are my top technical skills?',
              'Show my top ranked opportunities',
              'What experience level was I assigned?',
              'What are my preferred roles?',
            ].map((chip, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setDbQuestion(chip);
                  handleQueryDb(chip);
                }}
                className="text-xs bg-gray-800/60 hover:bg-gray-700/80 border border-gray-700/50 text-gray-300 px-3 py-1.5 rounded-lg transition"
              >
                💡 {chip}
              </button>
            ))}
          </div>

          {/* DB Answer Display */}
          {dbAnswer && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-sm font-mono whitespace-pre-line">
              <span className="font-bold text-emerald-400">🤖 Candidate DB Response:</span>
              <p className="mt-1">{dbAnswer}</p>
            </div>
          )}
        </section>

        {/* ── CANDIDATE PROFILE SUMMARY CARD ──────────────────────────────────── */}
        {profile && (
          <section className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{profile.name || 'John Doe'}</h3>
                  <p className="text-xs text-gray-400">{profile.experience_summary}</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono font-semibold uppercase">
                {profile.preferred_roles?.[0] || 'Web Developer'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Technical Stack</p>
                <div className="flex flex-wrap gap-2">
                  {profile.tech_stack?.map((tech, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Preferred Roles & Goals</p>
                <div className="flex flex-wrap gap-2 mb-2">
                  {profile.preferred_roles?.map((role, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                      🎯 {role}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-300 italic">{profile.career_goals}</p>
              </div>
            </div>
          </section>
        )}

        {/* ── OPPORTUNITY MARKETPLACE ─────────────────────────────────────────── */}
        <section className="glass-card p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-indigo-400" /> Ranked Opportunity Marketplace
              </h2>
              <p className="text-xs text-gray-400">Scouted & ranked by relevance score (0-100) from SQLite</p>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'all', label: 'All' },
                { id: 'job', label: 'Jobs' },
                { id: 'internship', label: 'Internships' },
                { id: 'competition', label: 'Competitions' },
                { id: 'conclave', label: 'Conclaves' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    selectedTab === tab.id
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/30'
                      : 'bg-gray-800/60 text-gray-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Opportunities Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {opportunities.map((opp, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-[#070A11]/80 border border-gray-800/80 flex flex-col justify-between hover:border-indigo-500/40 transition">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[10px] font-mono uppercase font-bold">
                      {opp.category}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono font-bold">
                      Score: {opp.relevance_score}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-white mb-1 line-clamp-1">{opp.title}</h4>
                  <p className="text-xs text-gray-400 mb-3 line-clamp-2">{opp.description}</p>

                  {opp.match_reasons && (
                    <div className="space-y-1 mb-3">
                      {opp.match_reasons.map((r, i) => (
                        <p key={i} className="text-[11px] text-gray-300 flex items-center gap-1">
                          <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" /> {r}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                <a
                  href={opp.url}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg bg-gray-800 hover:bg-indigo-600 text-xs font-medium text-white transition mt-2"
                >
                  View Details <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            ))}
          </div>
        </section>

        {/* ── ARMORIQ GOVERNANCE & AUDIT MONITOR (HACKATHON DEMO) ──────────────── */}
        <section className="glass-card p-6 border-emerald-500/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400">
                <Shield className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  ArmorIQ Cryptographic Governance Monitor
                </h3>
                <p className="text-xs text-gray-400">Problem 2 Track: Keypair identities, signed delegation tokens, and real-time scope blocks</p>
              </div>
            </div>

            <button
              onClick={handleTriggerAttack}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 font-medium text-xs transition shadow-lg shadow-rose-500/10"
            >
              <AlertTriangle className="w-4 h-4 text-rose-400" /> Simulate Prompt Attack
            </button>
          </div>

          {/* Simulated Attack Block Output */}
          {simulatedAttack && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 text-rose-200 mb-6 font-mono text-xs space-y-2">
              <div className="flex items-center gap-2 font-bold text-rose-400">
                <Shield className="w-4 h-4" /> 🛑 ARMORIQ CRYPTOGRAPHIC BLOCK ENFORCED:
              </div>
              <p>{simulatedAttack.message}</p>
              <div className="text-[11px] text-gray-400 pt-2 border-t border-rose-500/20">
                Sub-Agent: <span className="text-white">{simulatedAttack.sub_agent}</span> | Attempted Unauthorized Tool: <span className="text-rose-400">{simulatedAttack.attempted_tool}</span>
              </div>
            </div>
          )}

          {/* Live Audit Log Table */}
          <div className="bg-[#070A11] border border-gray-800 rounded-xl p-4 font-mono text-xs max-h-60 overflow-y-auto space-y-2">
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
                  <span className={log.status?.includes('BLOCKED') ? 'text-rose-400 font-bold' : 'text-emerald-400 font-bold'}>
                    {log.status}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No audit logs available. Click 'Run ArmorIQ Pipeline' or 'Simulate Prompt Attack' above!</p>
            )}
          </div>
        </section>

      </main>
    </div>
  );
}
