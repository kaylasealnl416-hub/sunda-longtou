
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Flame, Zap, BarChart3, Target, Trophy, BrainCircuit, 
  History, TrendingUp, TrendingDown, Layers, Activity, 
  ArrowUpRight, Scale, Save, RefreshCcw, ArrowRight,
  ShieldAlert, Wand2, DatabaseZap, X, FileUp, Calendar, Timer, Waves,
  ChevronDown, MessageSquareCode, Radio, Cpu
} from 'lucide-react';
import { GoogleGenAI } from "@google/genai";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, Legend, Cell
} from 'recharts';

// --- Types & Constants ---
const STORAGE_KEY = 'dragon_faith_system_v28_0';

interface IndexData {
  name: string;
  value: number;
  change: number;
  ma5Status: 'above' | 'below';
}

interface SectorTrack {
  name: string;
  gain: number;
  limitUps: number;
  volume: number; 
}

interface WatchStock {
  name: string;
  concept: string;
  plan: string;
}

interface UploadedFile {
  name: string;
  mimeType: string;
  data: string;
  preview?: string;
}

interface MarketReview {
  date: string;
  indices: IndexData[];
  totalVol: number;
  volDelta: number;
  limitUpTotal: number;
  limitDownTotal: number;
  brokenRate: number;
  topSectors: SectorTrack[];
  ladder: Record<string, { count: number; stock: string; concept: string; promoRate: number }>;
  dragon: string;
  dragonStatus: 'accelerate' | 'divergence' | 'broken' | 'revive';
  midArmy: string;
  watchlist: WatchStock[];
  score: number;
  stage: string; 
  aiAnalysis: string;
  customKeywords: string;
}

const INITIAL_REVIEW: MarketReview = {
  date: new Date().toISOString().split('T')[0],
  indices: [
    { name: '上证', value: 0, change: 0, ma5Status: 'above' },
    { name: '深成', value: 0, change: 0, ma5Status: 'above' },
    { name: '创业', value: 0, change: 0, ma5Status: 'above' },
    { name: '科创', value: 0, change: 0, ma5Status: 'above' },
    { name: '沪深300', value: 0, change: 0, ma5Status: 'above' },
    { name: '中证1000', value: 0, change: 0, ma5Status: 'above' },
    { name: '中证2000', value: 0, change: 0, ma5Status: 'above' },
    { name: '微盘股', value: 0, change: 0, ma5Status: 'above' },
  ],
  totalVol: 0, volDelta: 0,
  limitUpTotal: 0, limitDownTotal: 0,
  brokenRate: 0,
  topSectors: [
    { name: '', gain: 0, limitUps: 0, volume: 0 },
    { name: '', gain: 0, limitUps: 0, volume: 0 },
    { name: '', gain: 0, limitUps: 0, volume: 0 }
  ],
  ladder: {
    '5': { count: 0, stock: '', concept: '', promoRate: 0 },
    '4': { count: 0, stock: '', concept: '', promoRate: 0 },
    '3': { count: 0, stock: '', concept: '', promoRate: 0 },
    '2': { count: 0, stock: '', concept: '', promoRate: 0 },
    '1': { count: 0, stock: '', concept: '', promoRate: 0 },
  },
  dragon: '', dragonStatus: 'accelerate', midArmy: '',
  watchlist: Array(6).fill({ name: '', concept: '', plan: '' }),
  score: 50, stage: '待研判', aiAnalysis: '',
  customKeywords: '',
};

const App = () => {
  const [review, setReview] = useState<MarketReview>(INITIAL_REVIEW);
  const [history, setHistory] = useState<MarketReview[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [showFileManager, setShowFileManager] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const persistentSectors = useMemo(() => {
    const last5 = history.slice(0, 5);
    const currentSectors = review.topSectors.map(s => s.name.trim()).filter(Boolean);
    const historicalSectors = last5.flatMap(h => h.topSectors.map(s => s.name.trim()).filter(Boolean));
    const allSectors = [...currentSectors, ...historicalSectors];
    const counts: Record<string, number> = {};
    allSectors.forEach(name => { counts[name] = (counts[name] || 0) + 1; });
    return Object.entries(counts).filter(([_, count]) => count >= 2).sort((a, b) => b[1] - a[1]);
  }, [history, review.topSectors]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles: UploadedFile[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const reader = new FileReader();
      const base64Promise = new Promise<string>((resolve) => {
        reader.onload = () => resolve(reader.result?.toString().split(',')[1] || '');
        reader.readAsDataURL(file);
      });
      const base64 = await base64Promise;
      newFiles.push({
        name: file.name,
        mimeType: file.type,
        data: base64,
        preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
      });
    }
    setUploadedFiles(prev => [...prev, ...newFiles].slice(-10));
  };

  const handleSave = () => {
    const newHistory = [review, ...history.filter(h => h.date !== review.date)].sort((a,b) => b.date.localeCompare(a.date));
    setHistory(newHistory);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    alert("今日复盘已成功归档至信仰库。");
  };

  const autoFillMarketData = async () => {
    if (isLoading || uploadedFiles.length === 0) return;
    setIsLoading(true);
    setStatusMsg("正在通过AI解构原始信源数据...");
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const parts: any[] = [{ text: `你是一个精通A股复盘的数据专家。解析附件内容并填充复盘JSON。指数部分仅提取收盘点位。` }];
      uploadedFiles.forEach(file => parts.push({ inlineData: { mimeType: file.mimeType, data: file.data } }));
      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: { parts },
        config: { responseMimeType: "application/json" }
      });
      const data = JSON.parse(response.text || "{}");
      setReview(prev => ({ ...prev, ...data, aiAnalysis: "信源同步完成。建议立即进行周期定性分析。" }));
      setShowFileManager(false);
    } catch (e) { alert("自动填充失败"); } finally { setIsLoading(false); }
  };

  const analyzeSentimentCycle = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("正在研判情绪周期阶段...");
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      const ladderSummary = (Object.entries(review.ladder) as [string, typeof review.ladder[string]][])
        .filter(([_, data]) => data.stock || data.count > 0)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([lvl, data]) => `${lvl}板: ${data.stock || '无'}(${data.count}家, 晋级率${data.promoRate}%)`)
        .join('; ');

      const prompt = `你是一个精通A股短线情绪周期的专家。请根据以下数据进行深度研判：
1. 市场成交：${review.totalVol}T (较昨日增减: ${review.volDelta}亿)
2. 涨跌表现：涨停${review.limitUpTotal}家，跌停${review.limitDownTotal}家，炸板率${review.brokenRate}%
3. 核心标的：龙头[${review.dragon}] (状态: ${review.dragonStatus})，中军[${review.midArmy}]
4. 连板梯队：${ladderSummary || '无明显梯队'}
5. 用户关注/策略偏好：${review.customKeywords || '无'}

请按以下格式输出：
【情绪拆解】：(详细分析当前市场多空博弈情况，结合成交量和涨跌停家数)
【龙头点评】：(针对${review.dragon}及其${review.dragonStatus}状态对板块及市场情绪的影响进行分析)
【周期结论】：(必须从以下选项中选择一个：混沌期/活跃期/分化期/退潮期)
【操作建议】：(基于当前周期阶段的简短策略建议)`;

      const response = await ai.models.generateContent({ model: "gemini-3-pro-preview", contents: prompt });
      const res = response.text || "";
      const stage = res.match(/【周期结论】：(混沌期|活跃期|分化期|退潮期)/)?.[1] || "混沌期";
      setReview(prev => ({ ...prev, stage, aiAnalysis: `【周期研判结论】: ${res}\n\n${prev.aiAnalysis}` }));
    } catch (e) { alert("周期研判异常"); } finally { setIsLoading(false); }
  };

  const callAI = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("AI指挥官生成实战策略中...");
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const prompt = `复盘时间:${review.date}。周期:${review.stage}。核心龙:[${review.dragon}]。成交${review.totalVol}T。${review.customKeywords ? `用户特别关注/策略偏好: ${review.customKeywords}。` : ''}请给出买入、卖出建议，使用【追涨】【低吸】【反包】【潜伏】标签。`;
      const response = await ai.models.generateContent({ model: "gemini-3-pro-preview", contents: prompt });
      setReview(prev => ({ ...prev, aiAnalysis: response.text || "" }));
    } catch (e) { alert("策略生成异常"); } finally { setIsLoading(false); }
  };

  const renderFormattedAnalysis = (text: string) => {
    if (!text) return null;
    return text.split('\n').map((line, idx) => {
      const labelRegex = /(【[^】]+】)/g;
      const parts = line.split(labelRegex);
      return (
        <div key={idx} className="mb-2 leading-relaxed">
          {parts.map((part, pIdx) => {
            if (part.startsWith('【') && part.endsWith('】')) {
              const label = part.slice(1, -1);
              let color = "bg-gray-500/10 border-gray-500/30 text-gray-400";
              if (label === '追涨') color = "bg-red-500/20 border-red-500/30 text-red-400";
              if (label === '低吸') color = "bg-blue-500/20 border-blue-500/30 text-blue-400";
              if (label === '潜伏') color = "bg-emerald-500/20 border-emerald-500/30 text-emerald-400";
              if (label === '反包') color = "bg-yellow-500/20 border-yellow-500/30 text-yellow-400";
              if (label === '周期结论') color = "bg-indigo-500/20 border-indigo-500/30 text-indigo-400";
              return <span key={pIdx} className={`px-2 py-0.5 rounded border text-[10px] font-black mr-2 ${color}`}>{label}</span>;
            }
            return <span key={pIdx} className="text-gray-300 text-sm">{part}</span>;
          })}
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-[#060608] text-[#d1d5db] font-sans">
      {/* Header */}
      <header className="sticky top-0 z-[100] bg-black/50 backdrop-blur-xl border-b border-white/5 h-16 flex items-center px-8 justify-between shadow-2xl">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 group cursor-default">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center shadow-lg shadow-red-600/20 group-hover:rotate-12 transition-transform">
              <Flame size={18} className="text-white fill-white" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">龙头信仰 <span className="text-red-500 text-[10px]">V28.0 PRO</span></h1>
              <div className="flex items-center gap-1.5 -mt-1">
                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[9px] font-black text-gray-500 uppercase">Decision terminal</span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-xl border border-white/10">
            <Calendar size={12} className="text-gray-500" />
            <input type="date" value={review.date} onChange={e => setReview({...review, date: e.target.value})} className="bg-transparent border-none text-[11px] font-black outline-none text-gray-300" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowFileManager(true)} className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[11px] font-black flex items-center gap-2 transition-all">
              <FileUp size={14} /> 信源库
            </button>
            <button onClick={handleSave} className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-red-600/30 flex items-center gap-2 transition-all">
              <Save size={14} /> 存档记录
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1720px] mx-auto px-8 py-10">
        <div className="grid grid-cols-12 gap-10">
          
          {/* Column Left: Input & Data (Macro to Logic) */}
          <div className="col-span-12 xl:col-span-4 space-y-10">
            
            {/* 01 Macro Indices */}
            <section className="relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">01</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">宏观指数数据</h2>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {review.indices.map((idx, i) => (
                  <div key={i} className="bg-white/[0.03] border border-white/5 p-3 rounded-xl flex flex-col items-center justify-center group hover:bg-white/5 transition-all">
                    <span className="text-[9px] font-black text-gray-600 mb-1">{idx.name}</span>
                    <input 
                      type="number" step="0.01" value={idx.value} 
                      onChange={e => { const ni = [...review.indices]; ni[i].value = +e.target.value; setReview({...review, indices: ni}); }}
                      className="bg-transparent w-full text-center text-sm font-black text-white outline-none placeholder:text-gray-800"
                      placeholder="点位"
                    />
                  </div>
                ))}
              </div>
            </section>

            {/* 02 Market Sentiment Dash */}
            <section className="bg-white/[0.02] rounded-3xl p-6 border border-white/5 space-y-6">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">02</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">市场情绪计速器</h2>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-red-500/5 border border-red-500/10 p-5 rounded-2xl flex flex-col">
                  <span className="text-[10px] font-black text-red-500/60 uppercase mb-1">今日涨停</span>
                  <input type="number" value={review.limitUpTotal} onChange={e => setReview({...review, limitUpTotal: +e.target.value})} className="bg-transparent text-3xl font-black text-red-500 outline-none w-full" />
                </div>
                <div className="bg-green-500/5 border border-green-500/10 p-5 rounded-2xl flex flex-col">
                  <span className="text-[10px] font-black text-green-500/60 uppercase mb-1">今日跌停</span>
                  <input type="number" value={review.limitDownTotal} onChange={e => setReview({...review, limitDownTotal: +e.target.value})} className="bg-transparent text-3xl font-black text-green-500 outline-none w-full" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-gray-500 flex items-center gap-2"><BarChart3 size={10}/> 成交额(万亿)</label>
                  <input type="number" step="0.01" value={review.totalVol} onChange={e => setReview({...review, totalVol: +e.target.value})} className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 w-full text-sm font-black text-red-500 outline-none" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-gray-500 flex items-center gap-2"><ArrowUpRight size={10}/> 增减(亿)</label>
                  <input type="number" value={review.volDelta} onChange={e => setReview({...review, volDelta: +e.target.value})} className={`bg-white/5 border border-white/10 rounded-xl px-4 py-3 w-full text-sm font-black outline-none ${review.volDelta >= 0 ? 'text-red-500' : 'text-blue-400'}`} />
                </div>
              </div>
            </section>

            {/* 03 Main Logic Sectors */}
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">03</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">题材主线识别</h2>
              </div>
              <div className="space-y-3">
                {review.topSectors.map((sector, i) => (
                  <div key={i} className="bg-white/[0.02] border border-white/5 p-5 rounded-2xl group hover:border-purple-500/20 transition-all">
                    <input placeholder="板块名称..." value={sector.name} onChange={e => {
                      const ns = [...review.topSectors]; 
                      ns[i] = { ...ns[i], name: e.target.value }; 
                      setReview({...review, topSectors: ns});
                    }} className="bg-transparent text-sm font-black outline-none w-full mb-3" />
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">涨幅%</span>
                        <input type="number" step="0.1" value={sector.gain} onChange={e => { 
                          const ns = [...review.topSectors]; 
                          ns[i] = { ...ns[i], gain: +e.target.value }; 
                          setReview({...review, topSectors: ns}); 
                        }} className="bg-transparent text-[11px] font-black text-red-500 outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">涨停数</span>
                        <input type="number" value={sector.limitUps} onChange={e => { 
                          const ns = [...review.topSectors]; 
                          ns[i] = { ...ns[i], limitUps: +e.target.value }; 
                          setReview({...review, topSectors: ns}); 
                        }} className="bg-transparent text-[11px] font-black text-white outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">量能亿</span>
                        <input type="number" value={sector.volume} onChange={e => { 
                          const ns = [...review.topSectors]; 
                          ns[i] = { ...ns[i], volume: +e.target.value }; 
                          setReview({...review, topSectors: ns}); 
                        }} className="bg-transparent text-[11px] font-black text-blue-400 outline-none w-full text-center" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* Column Right: Strategy & Execution (Ladder to AI) */}
          <div className="col-span-12 xl:col-span-8 space-y-10">
            
            {/* Top Row: Ladder & Core */}
            <div className="grid grid-cols-12 gap-10">
              
              {/* 04 Sentiment Ladder */}
              <div className="col-span-12 lg:col-span-7 space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">04</div>
                  <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">连板晋级梯队</h2>
                </div>
                <div className="flex flex-col gap-3">
                  {['5', '4', '3', '2', '1'].map(lvl => (
                    <div key={lvl} className="flex gap-4 group">
                      <div className={`w-14 h-12 flex items-center justify-center rounded-xl border font-black text-xs ${lvl === '5' ? 'bg-red-600/10 border-red-500/50 text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.2)]' : 'bg-white/5 border-white/10 text-gray-500'}`}>
                        {lvl === '5' ? '5B+' : `${lvl}B`}
                      </div>
                      <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-xl p-3 flex items-center gap-4 hover:bg-white/5 transition-all">
                        <input placeholder={`${lvl}B核心标的...`} value={review.ladder[lvl]?.stock} onChange={e => { const nl = {...review.ladder}; nl[lvl].stock = e.target.value; setReview({...review, ladder: nl}); }} className="bg-transparent text-xs font-black text-white outline-none w-full" />
                        <div className="flex items-center gap-4 min-w-[120px]">
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">家数</span>
                            <input type="number" value={review.ladder[lvl]?.count} onChange={e => { const nl = {...review.ladder}; nl[lvl].count = +e.target.value; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-blue-400 outline-none" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">晋级%</span>
                            <input type="number" value={review.ladder[lvl]?.promoRate} onChange={e => { const nl = {...review.ladder}; nl[lvl].promoRate = +e.target.value; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-yellow-500 outline-none" />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 05 Core Targets */}
              <div className="col-span-12 lg:col-span-5 space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">05</div>
                  <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">灵魂标的监测</h2>
                </div>
                <div className="space-y-6">
                  <div className="bg-gradient-to-br from-red-600/10 to-transparent border border-red-500/20 p-6 rounded-3xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/5 blur-[50px] group-hover:bg-red-600/10 transition-all"></div>
                    <span className="text-[9px] font-black text-red-500 uppercase flex items-center gap-2 mb-3"><Trophy size={10}/> 情绪总龙头</span>
                    <input value={review.dragon} onChange={e => setReview({...review, dragon: e.target.value})} className="bg-transparent w-full text-2xl font-black text-red-500 outline-none mb-4 relative z-10" placeholder="寻龙中..." />
                    <select value={review.dragonStatus} onChange={e => setReview({...review, dragonStatus: e.target.value as any})} className="bg-black/40 text-[10px] font-black text-red-500 outline-none p-2 rounded-lg border border-red-500/20 w-full cursor-pointer hover:bg-black/60 transition-all">
                      <option value="accelerate">一致加速</option>
                      <option value="divergence">分歧转强</option>
                      <option value="broken">破位退潮</option>
                      <option value="revive">反包穿越</option>
                    </select>
                  </div>
                  <div className="bg-white/[0.03] border border-white/5 p-6 rounded-3xl group hover:border-blue-500/20 transition-all">
                    <span className="text-[9px] font-black text-blue-500 uppercase flex items-center gap-2 mb-3"><Radio size={10}/> 趋势中军</span>
                    <input value={review.midArmy} onChange={e => setReview({...review, midArmy: e.target.value})} className="bg-transparent w-full text-2xl font-black text-blue-500 outline-none" placeholder="标杆核心..." />
                  </div>
                </div>
              </div>
            </div>

            {/* 06 AI Decision Hub */}
            <section className="bg-[#0c0c10] rounded-[2.5rem] border border-white/5 p-10 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent"></div>
              
              {/* Hub Header */}
              <div className="flex items-center justify-between mb-10 relative z-10">
                <div className="flex items-center gap-6">
                  <div className="w-14 h-14 rounded-2xl bg-purple-600 flex items-center justify-center text-white shadow-xl shadow-purple-600/20">
                    <Cpu size={28} />
                  </div>
                  <div className="flex flex-col">
                    <div className="flex items-center gap-3">
                      <h2 className="text-xl font-black text-white uppercase tracking-tight">AI 信仰决策终端</h2>
                      {review.stage !== '待研判' && (
                        <div className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border ${
                          review.stage === '活跃期' ? 'bg-red-500/20 border-red-500/40 text-red-400' :
                          review.stage === '退潮期' ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400' :
                          review.stage === '分化期' ? 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400' :
                          'bg-blue-500/20 border-blue-500/40 text-blue-400'
                        }`}>
                          {review.stage}
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] font-black text-purple-500 uppercase tracking-widest mt-1">Ground Truth Logic Engine</span>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button onClick={analyzeSentimentCycle} disabled={isLoading} className="px-6 py-3 bg-white/5 hover:bg-white/10 text-indigo-400 border border-white/10 rounded-xl text-[11px] font-black flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50">
                    <Waves size={14} /> 周期定性
                  </button>
                  <button onClick={callAI} disabled={isLoading} className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-[11px] font-black shadow-xl shadow-purple-600/20 flex items-center gap-2 transition-all active:scale-95 disabled:opacity-50">
                    <Zap size={14} /> 信仰研判
                  </button>
                </div>
              </div>

              {/* Focus Area Input */}
              <div className="mb-8 relative z-10">
                <div className="flex items-center gap-2 mb-3">
                  <Wand2 size={12} className="text-purple-400" />
                  <span className="text-[9px] font-black text-purple-400 uppercase tracking-widest">AI 指导关键词 / 关注领域</span>
                </div>
                <input 
                  type="text" 
                  value={review.customKeywords} 
                  onChange={e => setReview({...review, customKeywords: e.target.value})}
                  placeholder="例如：关注低位补涨、半导体国产替代、核心龙头分歧机会..."
                  className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-xs font-medium text-gray-300 outline-none focus:border-purple-500/50 transition-all placeholder:text-gray-700"
                />
              </div>

              {/* Sub Header info */}
              <div className="grid grid-cols-2 gap-8 mb-8">
                <div className="bg-white/[0.02] border border-white/5 p-6 rounded-2xl">
                  <div className="flex items-center gap-2 mb-4">
                    <Timer size={12} className="text-emerald-500" />
                    <span className="text-[9px] font-black text-emerald-500 uppercase">5日主线活跃度</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {persistentSectors.length > 0 ? persistentSectors.map(([name, count]) => (
                      <span key={name} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-md text-[10px] font-black text-emerald-400">
                        {name} <span className="text-[8px] opacity-50 ml-1">{count}d</span>
                      </span>
                    )) : <span className="text-gray-600 text-[10px] italic font-bold">观测中...</span>}
                  </div>
                </div>
                <div className="bg-white/[0.02] border border-white/5 p-6 rounded-2xl flex items-center gap-10">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-black text-gray-600 uppercase mb-1">信仰分</span>
                    <div className="flex items-baseline gap-1">
                      <span className={`text-4xl font-black ${review.score > 70 ? 'text-red-500' : review.score > 40 ? 'text-yellow-500' : 'text-emerald-500'}`}>{review.score}</span>
                      <span className="text-[10px] text-gray-700 font-black">%</span>
                    </div>
                  </div>
                  <div className="flex-1 space-y-2">
                    <input type="range" min="0" max="100" value={review.score} onChange={e => setReview({...review, score: +e.target.value})} className="w-full accent-purple-600" />
                    <div className="flex justify-between text-[8px] font-black text-gray-700 uppercase"><span>冰点</span><span>博弈</span><span>主升</span></div>
                  </div>
                </div>
              </div>

              {/* Terminal Area */}
              <div className="bg-black/60 rounded-3xl border border-white/5 p-8 min-h-[400px] relative font-mono">
                {isLoading && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0c0c10]/90 z-20 rounded-3xl">
                    <RefreshCcw className="animate-spin text-purple-500 mb-4" size={40} />
                    <span className="text-[10px] font-black text-purple-400 uppercase tracking-[0.2em]">{statusMsg}</span>
                  </div>
                )}
                <div className="relative">
                   {review.aiAnalysis ? renderFormattedAnalysis(review.aiAnalysis) : (
                    <div className="flex flex-col items-center justify-center py-20 opacity-20">
                      <MessageSquareCode size={48} className="mb-4" />
                      <p className="text-[10px] font-black uppercase tracking-widest">Awaiting Command Input...</p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Data Visualization Section */}
        <section className="mt-24 space-y-10">
          <div className="flex items-center gap-4 mb-10">
            <BarChart3 size={24} className="text-purple-500" />
            <h2 className="text-2xl font-black text-white uppercase italic tracking-tighter">信仰数据可视化</h2>
          </div>

          {history.length < 2 ? (
            <div className="bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-20 flex flex-col items-center justify-center text-center">
              <Activity size={48} className="text-gray-800 mb-4" />
              <p className="text-gray-600 font-black uppercase tracking-widest text-xs">需要至少2条历史记录以生成趋势图表</p>
            </div>
          ) : (
            <div className="grid grid-cols-12 gap-10">
              {/* Volume & Sentiment Trend */}
              <div className="col-span-12 lg:col-span-8 bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8">
                <div className="flex items-center justify-between mb-8">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black text-purple-500 uppercase tracking-widest">Market Liquidity & Sentiment</span>
                    <h3 className="text-lg font-black text-white">成交量与涨跌停趋势</h3>
                  </div>
                </div>
                <div className="h-[350px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={[...history].reverse()}>
                      <defs>
                        <linearGradient id="colorVol" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                      <XAxis dataKey="date" stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#4b5563" fontSize={10} tickLine={false} axisLine={false} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: '#0c0c10', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '10px' }}
                        itemStyle={{ fontWeight: 'bold' }}
                      />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', paddingTop: '20px' }} />
                      <Area type="monotone" dataKey="totalVol" name="成交额(T)" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorVol)" strokeWidth={3} />
                      <Line type="monotone" dataKey="limitUpTotal" name="涨停数" stroke="#ef4444" strokeWidth={2} dot={{ r: 4, fill: '#ef4444' }} />
                      <Line type="monotone" dataKey="limitDownTotal" name="跌停数" stroke="#22c55e" strokeWidth={2} dot={{ r: 4, fill: '#22c55e' }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Sector Frequency */}
              <div className="col-span-12 lg:col-span-4 bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8">
                <div className="flex flex-col mb-8">
                  <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Hot Sector Rotation</span>
                  <h3 className="text-lg font-black text-white">题材活跃频次</h3>
                </div>
                <div className="h-[350px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart layout="vertical" data={persistentSectors.slice(0, 8).map(([name, count]) => ({ name, count }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" horizontal={false} />
                      <XAxis type="number" hide />
                      <YAxis dataKey="name" type="category" stroke="#9ca3af" fontSize={10} width={60} tickLine={false} axisLine={false} />
                      <RechartsTooltip 
                        cursor={{ fill: '#ffffff05' }}
                        contentStyle={{ backgroundColor: '#0c0c10', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '10px' }}
                      />
                      <Bar dataKey="count" name="活跃天数" radius={[0, 4, 4, 0]}>
                        {persistentSectors.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={index === 0 ? '#ef4444' : '#8b5cf6'} fillOpacity={0.8 - (index * 0.08)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Index Performance */}
              <div className="col-span-12 bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8">
                <div className="flex flex-col mb-8">
                  <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Benchmark Performance</span>
                  <h3 className="text-lg font-black text-white">主要指数走势对比</h3>
                </div>
                <div className="h-[400px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={[...history].reverse().map(h => {
                      const row: any = { date: h.date };
                      h.indices.forEach(idx => {
                        if (['上证', '创业', '科创'].includes(idx.name)) {
                          row[idx.name] = idx.value;
                        }
                      });
                      return row;
                    })}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" />
                      <XAxis dataKey="date" stroke="#4b5563" fontSize={10} tickLine={false} />
                      <YAxis stroke="#4b5563" fontSize={10} tickLine={false} domain={['auto', 'auto']} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: '#0c0c10', border: '1px solid #ffffff10', borderRadius: '12px', fontSize: '10px' }}
                      />
                      <Legend iconType="rect" wrapperStyle={{ fontSize: '10px', fontWeight: 'bold', paddingTop: '20px' }} />
                      <Line type="monotone" dataKey="上证" stroke="#ef4444" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="创业" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="科创" stroke="#a855f7" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Archives */}
        <section className="mt-24 border-t border-white/5 pt-16 pb-32">
          <div className="flex items-center gap-4 mb-10">
            <History size={24} className="text-gray-600" />
            <h2 className="text-2xl font-black text-white uppercase italic tracking-tighter">信仰记录存档</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6">
            {history.map((h) => (
              <div key={h.date} onClick={() => setReview(h)} className={`p-6 rounded-3xl border cursor-pointer transition-all hover:scale-[1.02] flex flex-col justify-between h-48 relative overflow-hidden ${review.date === h.date ? 'bg-red-600/10 border-red-500' : 'bg-white/[0.02] border-white/5 hover:border-white/10'}`}>
                <div className="flex justify-between items-start">
                  <span className="text-[10px] font-black text-gray-600">{h.date}</span>
                  <div className={`w-1.5 h-1.5 rounded-full ${h.score > 60 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
                </div>
                <div className="flex flex-col">
                   <span className="text-4xl font-black text-white mb-2">{h.score}<span className="text-[10px] opacity-30">%</span></span>
                   <span className="text-[11px] font-black text-red-500 truncate">{h.dragon || '无龙复盘'}</span>
                </div>
                <div className="flex justify-between items-center text-[9px] font-black text-gray-600 uppercase border-t border-white/5 pt-3">
                  <span>Vol: {h.totalVol}T</span>
                  <span>{h.stage}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* File Manager Popup */}
      {showFileManager && (
        <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-xl flex items-center justify-center p-8">
          <div className="w-full max-w-5xl bg-[#0c0c10] border border-white/10 rounded-[3rem] p-10 relative">
            <button onClick={() => setShowFileManager(false)} className="absolute top-8 right-8 w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all text-gray-500 hover:text-white">
              <X size={20} />
            </button>
            <div className="flex items-center gap-6 mb-12">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/20 text-indigo-500 shadow-xl">
                <DatabaseZap size={32} />
              </div>
              <div>
                <h3 className="text-3xl font-black text-white uppercase tracking-tight">信源文件池</h3>
                <p className="text-xs text-gray-500 font-black uppercase mt-1 tracking-widest">Analysis Resource Pool</p>
              </div>
            </div>
            
            <div className="grid grid-cols-12 gap-10">
              <div className="col-span-4">
                <div onClick={() => fileInputRef.current?.click()} className="aspect-square border-2 border-dashed border-white/10 rounded-[2.5rem] flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all text-center group">
                  <div className="w-14 h-14 bg-indigo-500/10 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                    <FileUp size={28} className="text-indigo-500" />
                  </div>
                  <span className="text-sm font-black text-white">注入复盘数据源</span>
                  <input type="file" ref={fileInputRef} multiple onChange={handleFileChange} className="hidden" accept="image/*,.pdf,.txt" />
                </div>
              </div>
              <div className="col-span-8 flex flex-col">
                <div className="flex-1 bg-black/40 border border-white/5 rounded-[2.5rem] p-8 h-[400px] overflow-y-auto custom-scrollbar">
                  {uploadedFiles.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-800 opacity-30">
                      <Radio size={48} className="mb-4" />
                      <p className="text-xs font-black uppercase tracking-widest">No active source feeds</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {uploadedFiles.map((f, i) => (
                        <div key={i} className="group bg-white/5 border border-white/10 p-4 rounded-2xl flex items-center gap-4 hover:border-indigo-500/40 relative transition-all">
                          <div className="w-12 h-12 rounded-xl bg-black/40 overflow-hidden border border-white/5 flex items-center justify-center">
                            {f.preview ? <img src={f.preview} className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" /> : <DatabaseZap size={20} className="text-indigo-400" />}
                          </div>
                          <p className="text-[11px] font-black text-gray-400 truncate flex-1 uppercase tracking-tighter">{f.name}</p>
                          <button onClick={() => setUploadedFiles(prev => prev.filter((_, idx) => idx !== i))} className="w-6 h-6 bg-red-500/80 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all shadow-lg"><X size={12}/></button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex justify-end mt-10">
                  <button onClick={autoFillMarketData} disabled={isLoading || uploadedFiles.length === 0} className="px-10 py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-black transition-all shadow-2xl shadow-emerald-600/30 active:scale-95 disabled:opacity-50">开始解构并填充复盘</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
