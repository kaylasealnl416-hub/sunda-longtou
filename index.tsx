
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Flame, Zap, BarChart3, Target, Trophy, PenTool, BrainCircuit, 
  Sparkles, Globe, Link as LinkIcon, History, ShieldCheck, 
  TrendingUp, TrendingDown, Layers, Radio, Gauge, ExternalLink, 
  Activity, ArrowUpRight, Scale, Monitor, Save, RefreshCcw,
  ArrowUp, ArrowDown, Ghost, AlertTriangle, Fingerprint, Coins, Star, Crosshair,
  SearchCode, ShieldAlert, ThermometerSun, ZapOff, Wand2, Bot, DatabaseZap,
  LayoutDashboard, ChevronRight, Info, FileText, ClipboardList, CheckCircle2,
  Upload, X, FileUp, FileSearch, Calendar, Timer
} from 'lucide-react';
import { GoogleGenAI, Type } from "@google/genai";

// --- Types & Constants ---
const STORAGE_KEY = 'dragon_faith_system_v27_5';

interface IndexData {
  name: string;
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

interface GroundingSource {
  title: string;
  uri: string;
}

interface UploadedFile {
  name: string;
  mimeType: string;
  data: string; // base64
  preview?: string;
}

interface MarketReview {
  date: string;
  indices: IndexData[];
  totalVol: number;
  volDelta: number;
  volMA5: 'increasing' | 'decreasing';
  upCount: number;
  dnCount: number;
  topSectors: SectorTrack[];
  isMainLine: 'confirmed' | 'rotating' | 'random';
  ladder: Record<string, { count: number; stock: string; concept: string; promoRate: number }>;
  limitUpTotal: number;
  limitDownTotal: number;
  brokenRate: number;
  yesterdayGain: number;
  nuclearCount: number;
  dragon: string;
  dragonStatus: 'accelerate' | 'divergence' | 'broken' | 'revive';
  midArmy: string;
  watchlist: WatchStock[];
  reflection: string;
  score: number;
  stage: string;
  aiAnalysis: string;
  sources: GroundingSource[];
  rawContext?: string;
}

const INITIAL_REVIEW: MarketReview = {
  date: new Date().toISOString().split('T')[0],
  indices: [
    { name: '沪', change: 0, ma5Status: 'above' },
    { name: '深', change: 0, ma5Status: 'above' },
    { name: '创', change: 0, ma5Status: 'above' },
    { name: '科', change: 0, ma5Status: 'above' },
    { name: '300', change: 0, ma5Status: 'above' },
    { name: '1000', change: 0, ma5Status: 'above' },
    { name: '2000', change: 0, ma5Status: 'above' },
    { name: '微盘', change: 0, ma5Status: 'above' },
  ],
  totalVol: 0, volDelta: 0, volMA5: 'increasing',
  upCount: 0, dnCount: 0,
  topSectors: Array(3).fill({ name: '', gain: 0, limitUps: 0, volume: 0 }),
  isMainLine: 'confirmed',
  ladder: {
    '5': { count: 0, stock: '', concept: '', promoRate: 0 },
    '4': { count: 0, stock: '', concept: '', promoRate: 0 },
    '3': { count: 0, stock: '', concept: '', promoRate: 0 },
    '2': { count: 0, stock: '', concept: '', promoRate: 0 },
    '1': { count: 0, stock: '', concept: '', promoRate: 0 },
  },
  limitUpTotal: 0, limitDownTotal: 0,
  brokenRate: 0, yesterdayGain: 0, nuclearCount: 0,
  dragon: '', dragonStatus: 'accelerate', midArmy: '',
  watchlist: Array(9).fill({ name: '', concept: '', plan: '' }),
  reflection: '', score: 50, stage: '混沌期', aiAnalysis: '',
  sources: [],
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

  // 核心逻辑：计算过去 5 日重复出现的主线
  const persistentSectors = useMemo(() => {
    const last5 = history.slice(0, 5);
    const currentSectors = review.topSectors.map(s => s.name.trim()).filter(Boolean);
    const historicalSectors = last5.flatMap(h => h.topSectors.map(s => s.name.trim()).filter(Boolean));
    
    const allSectors = [...currentSectors, ...historicalSectors];
    const counts: Record<string, number> = {};
    allSectors.forEach(name => {
      counts[name] = (counts[name] || 0) + 1;
    });

    return Object.entries(counts)
      .filter(([name, count]) => count >= 2)
      .sort((a, b) => b[1] - a[1]);
  }, [history, review.topSectors]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newFiles: UploadedFile[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const base64 = await fileToBase64(file);
      newFiles.push({
        name: file.name,
        mimeType: file.type,
        data: base64,
        preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
      });
    }
    setUploadedFiles(prev => [...prev, ...newFiles].slice(-10));
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result?.toString().split(',')[1] || '');
      reader.onerror = error => reject(error);
    });
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    const updated = { ...review };
    const newHistory = [updated, ...history.filter(h => h.date !== updated.date)].sort((a,b) => b.date.localeCompare(a.date));
    setHistory(newHistory);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    alert(`${review.date} 信仰记录已归档。`);
  };

  const updateWatchlist = (index: number, field: keyof WatchStock, value: string) => {
    const nw = [...review.watchlist];
    nw[index] = { ...nw[index], [field]: value };
    setReview({ ...review, watchlist: nw });
  };

  const autoFillMarketData = async () => {
    if (isLoading) return;
    if (uploadedFiles.length === 0) {
      alert("请先上传数据信源。");
      return;
    }
    setIsLoading(true);
    setStatusMsg(`正在深度分析上传的 ${uploadedFiles.length} 个文件并合成市场数据...`);
    
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const parts: any[] = [];
      parts.push({
        text: `你是一个精通A股短线博弈的数据专家。现在是 ${review.date}。
        请【务必以我上传的文件内容作为唯一真相】进行解析填充。
        
        解析要求：
        1. 提取各指数精确涨跌幅、成交额及增减。
        2. 提取涨停数、跌停数、炸板率。
        3. 识别前三主线板块及其详细数据。
        4. 识别连板梯队（1-5B及以上）的具体标的、家数和晋级率。最高统计到5B+。
        5. 锁定核心总龙头和趋势中军。

        返回 JSON 格式：
        {
          "indices": {"沪": 涨跌%, "深": %, ...},
          "totalVol": 数值, "volDelta": 数值,
          "sentiment": {"limitUp": 数量, "limitDown": 数量, "brokenRate": %},
          "sectors": [{"name": "板块名", "gain": %, "limitUps": 数量, "volume": 亿}, ...],
          "dragon": "总龙头名称", "midArmy": "趋势中军名称",
          "ladder": {"5": {"stock": "股名", "count": 数量, "promoRate": %}, ...}
        }`
      });
      uploadedFiles.forEach(file => {
        parts.push({ inlineData: { mimeType: file.mimeType, data: file.data } });
      });

      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: { parts },
        config: { responseMimeType: "application/json" }
      });

      const data = JSON.parse(response.text || "{}");
      
      setReview((prev): MarketReview => {
        const newIndices: IndexData[] = prev.indices.map(idx => ({
          ...idx,
          change: data.indices?.[idx.name] ?? idx.change,
          ma5Status: ((data.indices?.[idx.name] ?? 0) >= 0 ? 'above' : 'below') as 'above' | 'below'
        }));
        const newSectors = prev.topSectors.map((s, i) => data.sectors?.[i] ? { ...data.sectors[i] } : s);
        const newLadder = { ...prev.ladder };
        if (data.ladder) {
          Object.keys(data.ladder).forEach(lvl => {
            if (newLadder[lvl]) newLadder[lvl] = { ...newLadder[lvl], ...data.ladder[lvl] };
          });
        }
        return {
          ...prev,
          indices: newIndices,
          totalVol: data.totalVol ?? prev.totalVol,
          volDelta: data.volDelta ?? prev.volDelta,
          limitUpTotal: data.sentiment?.limitUp ?? prev.limitUpTotal,
          limitDownTotal: data.sentiment?.limitDown ?? prev.limitDownTotal,
          brokenRate: data.sentiment?.brokenRate ?? prev.brokenRate,
          topSectors: newSectors,
          ladder: newLadder,
          dragon: data.dragon ?? prev.dragon,
          midArmy: data.midArmy ?? prev.midArmy,
          aiAnalysis: `【解析成功】基于 ${uploadedFiles.length} 个原始信源提炼。已聚焦 1-5B+ 核心梯队。`
        };
      });
      setShowFileManager(false);
    } catch (e) {
      alert("AI 深度解析异常。");
    } finally {
      setIsLoading(false);
    }
  };

  const callAI = async (target?: { type: 'stock' | 'sentiment' | 'optimization', name?: string, role?: string }) => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("正在调动 AI 指挥官进行全维度信仰研判...");
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      
      // 构建关于持续性板块的描述
      const persistenceText = persistentSectors.length > 0 
        ? `【主线持续性监控】：发现板块 ${persistentSectors.map(([n, c]) => `[${n}](5日内出现${c}次)`).join(', ')}。这些可能为近期真正的核心主线。` 
        : "【主线持续性监控】：暂无明显重复出现的主线板块。";

      const prompt = `
        作为资深游资指挥官，请针对 ${review.date} 盘面进行深度信仰研判。
        
        [实时数据]：成交 ${review.totalVol}T，涨停 ${review.limitUpTotal}/跌停 ${review.limitDownTotal}。
        [市场核心]：总龙[${review.dragon}]，中军[${review.midArmy}]。
        [梯队状态]：最高标[${review.ladder['5']?.stock || '无'}]，晋级率[${review.ladder['5']?.promoRate}%]。
        
        ${persistenceText}
        
        [研判要求]：
        1. 必须针对上述“持续性板块”进行深度定性：它们是真主线还是未来的过渡？
        2. 结合今日信仰评分 ${review.score}/100，判断明日盘面是加速还是分歧。
        3. 给出实战级别的买入/持仓/卖出建议。
      `;

      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: prompt
      });
      setReview(prev => ({ ...prev, aiAnalysis: response.text || "" }));
    } catch (e) {
      setReview(prev => ({ ...prev, aiAnalysis: "指挥官请求超时。" }));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen pb-20 bg-[#0a0a0c] text-[#e2e8f0] font-sans selection:bg-red-500/30">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-[100] glass border-b border-white/5 h-16 flex items-center px-8 justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-red-800 rounded-xl flex items-center justify-center shadow-lg shadow-red-600/20">
            <Flame className="text-white fill-white" size={22} />
          </div>
          <div className="flex flex-col text-left">
            <h1 className="text-xl font-black tracking-tighter leading-none bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">龙头信仰 <span className="text-xs text-red-500 ml-1 font-bold">V27.5 PRO</span></h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-[10px] font-bold text-gray-500 tracking-[0.1em] uppercase">Ground Truth Terminal</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-2xl border border-white/10 group hover:border-red-500/30 transition-all">
            <Calendar size={14} className="text-gray-500 group-hover:text-red-500 transition-colors" />
            <input 
              type="date" 
              value={review.date} 
              onChange={e => setReview({...review, date: e.target.value})} 
              className="bg-transparent border-none text-[11px] font-mono font-bold outline-none text-gray-300 cursor-pointer" 
            />
          </div>

          <div className="h-8 w-[1px] bg-white/10"></div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setShowFileManager(!showFileManager)} 
              className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-[11px] font-black transition-all border ${uploadedFiles.length > 0 ? 'bg-blue-600/20 border-blue-500 text-blue-400' : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'}`}
            >
              <FileUp size={14} /> {uploadedFiles.length > 0 ? `已加载 ${uploadedFiles.length} 信源` : '上传原始信源'}
            </button>
            <button onClick={autoFillMarketData} disabled={isLoading || uploadedFiles.length === 0} className="group flex items-center gap-2 px-5 py-2.5 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 rounded-2xl text-[11px] font-black transition-all active:scale-95 disabled:opacity-50">
              {isLoading ? <RefreshCcw className="animate-spin" size={14} /> : <DatabaseZap size={14} />} AI 自动填充
            </button>
            <button onClick={handleSave} className="flex items-center gap-2 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-2xl text-[11px] font-black transition-all active:scale-95 shadow-xl shadow-red-600/20">
              <Save size={14} /> 归档复盘
            </button>
          </div>
        </div>
      </header>

      {/* 文件管理器面板 */}
      {showFileManager && (
        <div className="fixed inset-0 z-[150] bg-black/80 backdrop-blur-md flex items-center justify-center p-6">
          <div className="w-full max-w-4xl bg-[#121215] border border-white/10 rounded-[3rem] p-10 shadow-2xl relative">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4 text-left">
                <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20">
                  <FileUp className="text-blue-500" size={24} />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-white uppercase tracking-tight">信源文件池</h3>
                  <p className="text-xs text-gray-500 font-bold uppercase mt-1">Multi-Source Analysis Pool</p>
                </div>
              </div>
              <button onClick={() => setShowFileManager(false)} className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all">
                <X size={20} className="text-gray-400" />
              </button>
            </div>
            <div className="grid grid-cols-12 gap-8">
              <div className="col-span-4">
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="aspect-square border-2 border-dashed border-white/10 rounded-[2.5rem] flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-blue-500/40 hover:bg-blue-500/5 transition-all text-center group"
                >
                  <Upload size={32} className="text-blue-500 group-hover:scale-110 transition-transform" />
                  <span className="block text-sm font-black text-white">点击上传截图/报表</span>
                  <input type="file" ref={fileInputRef} multiple onChange={handleFileChange} className="hidden" accept="image/*,.pdf,.txt" />
                </div>
              </div>
              <div className="col-span-8 flex flex-col">
                <div className="flex-1 bg-black/40 border border-white/5 rounded-[2.5rem] p-6 h-[400px] overflow-y-auto custom-scrollbar">
                  {uploadedFiles.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-700 opacity-40">
                      <FileText size={48} className="mb-4" />
                      <p className="text-xs font-bold uppercase tracking-widest">暂无文件上传</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {uploadedFiles.map((file, i) => (
                        <div key={i} className="group bg-white/5 border border-white/10 p-4 rounded-2xl flex items-center gap-4 hover:border-blue-500/40 transition-all relative">
                          <div className="w-12 h-12 rounded-xl bg-black/40 overflow-hidden border border-white/5 flex items-center justify-center">
                            {file.preview ? <img src={file.preview} className="w-full h-full object-cover" /> : <FileText size={20} className="text-blue-400" />}
                          </div>
                          <p className="text-xs font-black text-gray-300 truncate text-left flex-1">{file.name}</p>
                          <button onClick={() => removeFile(i)} className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all shadow-xl shadow-red-500/30"><X size={12} /></button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <button onClick={autoFillMarketData} disabled={isLoading || uploadedFiles.length === 0} className="mt-8 px-12 py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-black transition-all shadow-2xl shadow-emerald-600/30 active:scale-95 disabled:opacity-50 self-end">立即启动 AI 数据填充</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-[1780px] mx-auto px-8 mt-10">
        <div className="grid grid-cols-12 gap-8">
          
          {/* 左侧栏 */}
          <div className="col-span-12 xl:col-span-4 space-y-8 text-left">
            <section className="glass rounded-[2.5rem] p-8 border-l-[8px] border-red-500 shadow-2xl">
              <div className="flex items-center gap-3 mb-8">
                <Activity className="text-red-500" size={20} />
                <h2 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">01 宏观数据概览</h2>
              </div>
              <div className="grid grid-cols-4 gap-3.5 mb-8">
                {review.indices.map((idx, i) => (
                  <div key={i} className="bg-white/5 border border-white/5 p-3 rounded-[1.2rem] text-center">
                    <div className="text-[10px] text-gray-500 font-black mb-2 uppercase">{idx.name}</div>
                    <input type="number" step="0.01" value={idx.change} onChange={e => {
                        const ni = [...review.indices]; ni[i].change = +e.target.value; setReview({...review, indices: ni});
                    }} className={`bg-transparent w-full text-center text-xs font-black outline-none ${idx.change >= 0 ? 'text-red-500' : 'text-green-500'}`} />
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-6 p-6 bg-white/5 rounded-[1.5rem] border border-white/5">
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase flex items-center gap-2"><BarChart3 size={12}/> 成交量 (万亿)</label>
                  <input type="number" step="0.01" value={review.totalVol} onChange={e => setReview({...review, totalVol: +e.target.value})} className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 w-full text-sm font-black text-red-500 outline-none" />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase flex items-center gap-2"><ArrowUpRight size={12}/> 增减 (亿)</label>
                  <input type="number" value={review.volDelta} onChange={e => setReview({...review, volDelta: +e.target.value})} className={`bg-white/5 border border-white/10 rounded-xl px-4 py-3 w-full text-sm font-black outline-none ${review.volDelta >= 0 ? 'text-red-500' : 'text-blue-400'}`} />
                </div>
              </div>
            </section>

            <section className="glass rounded-[2.5rem] p-8 border-l-[8px] border-purple-500 shadow-2xl">
              <div className="flex items-center gap-3 mb-8">
                <Layers className="text-purple-500" size={20} />
                <h2 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">02 主线逻辑识别</h2>
              </div>
              <div className="space-y-4">
                {review.topSectors.map((sector, i) => (
                  <div key={i} className="bg-white/5 border border-white/5 p-6 rounded-[1.8rem] space-y-4">
                    <input placeholder="板块名称..." value={sector.name} onChange={e => {
                      const ns = [...review.topSectors]; ns[i].name = e.target.value; setReview({...review, topSectors: ns});
                    }} className="bg-transparent text-lg font-black outline-none w-full" />
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-black/40 p-2 text-center rounded-xl border border-white/5">
                        <span className="text-[9px] text-gray-600 block mb-1">涨跌%</span>
                        <input type="number" value={sector.gain} step="0.1" onChange={e => {
                          const ns = [...review.topSectors]; ns[i].gain = +e.target.value; setReview({...review, topSectors: ns});
                        }} className="bg-transparent text-xs font-black text-red-500 outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-xl border border-white/5">
                        <span className="text-[9px] text-gray-600 block mb-1">涨停#</span>
                        <input type="number" value={sector.limitUps} onChange={e => {
                          const ns = [...review.topSectors]; ns[i].limitUps = +e.target.value; setReview({...review, topSectors: ns});
                        }} className="bg-transparent text-xs font-black text-white outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-xl border border-white/5">
                        <span className="text-[9px] text-gray-600 block mb-1">量能亿</span>
                        <input type="number" value={sector.volume} onChange={e => {
                          const ns = [...review.topSectors]; ns[i].volume = +e.target.value; setReview({...review, topSectors: ns});
                        }} className="bg-transparent text-xs font-black text-blue-400 outline-none w-full text-center" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* 右侧主内容区 */}
          <div className="col-span-12 xl:col-span-8 space-y-8 text-left">
            <section className="glass rounded-[2.5rem] p-10 border-l-[8px] border-blue-500 shadow-2xl">
              <div className="flex items-center gap-3 mb-10">
                <Scale className="text-blue-500" size={20} />
                <h2 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">03 市场情绪 & 连板梯队</h2>
              </div>
              <div className="grid grid-cols-12 gap-8">
                <div className="col-span-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-red-500/5 border border-red-500/10 p-5 rounded-2xl">
                      <span className="text-[10px] font-black text-red-500/60 block mb-1">今日涨停</span>
                      <input type="number" value={review.limitUpTotal} onChange={e => setReview({...review, limitUpTotal: +e.target.value})} className="bg-transparent text-3xl font-black text-red-500 outline-none w-full" />
                    </div>
                    <div className="bg-green-500/5 border border-green-500/10 p-5 rounded-2xl">
                      <span className="text-[10px] font-black text-green-500/60 block mb-1">今日跌停</span>
                      <input type="number" value={review.limitDownTotal} onChange={e => setReview({...review, limitDownTotal: +e.target.value})} className="bg-transparent text-3xl font-black text-green-500 outline-none w-full" />
                    </div>
                  </div>
                  <div className="bg-white/5 border border-white/5 p-4 rounded-2xl flex justify-between items-center">
                    <span className="text-[11px] font-black text-gray-400">炸板率 %</span>
                    <input type="number" value={review.brokenRate} onChange={e => setReview({...review, brokenRate: +e.target.value})} className="bg-transparent text-right font-black text-yellow-500 outline-none w-16" />
                  </div>
                </div>
                <div className="col-span-8 flex flex-col gap-3">
                  {['5', '4', '3', '2', '1'].map(lvl => (
                    <div key={lvl} className="flex gap-4 group">
                      <div className="w-14 text-center py-3 rounded-xl border border-white/10 bg-white/5 text-xs font-black text-blue-400">{lvl === '5' ? '5B+' : lvl + 'B'}</div>
                      <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl p-4 flex items-center gap-6 group-hover:bg-white/[0.08] transition-all">
                        <input placeholder={`${lvl === '5' ? '最高标' : lvl + '板核心'}...`} value={review.ladder[lvl]?.stock} onChange={e => {
                          const nl = {...review.ladder}; nl[lvl].stock = e.target.value; setReview({...review, ladder: nl});
                        }} className="bg-transparent text-sm font-black text-white outline-none w-full" />
                        <div className="flex items-center gap-4 min-w-[150px]">
                          <span className="text-[10px] text-gray-600 font-bold">家数:</span>
                          <input type="number" value={review.ladder[lvl]?.count} onChange={e => {
                            const nl = {...review.ladder}; nl[lvl].count = +e.target.value; setReview({...review, ladder: nl});
                          }} className="bg-transparent w-8 text-xs font-black text-blue-400 outline-none" />
                          <span className="text-[10px] text-gray-600 font-bold ml-2">晋级:</span>
                          <input type="number" value={review.ladder[lvl]?.promoRate} onChange={e => {
                            const nl = {...review.ladder}; nl[lvl].promoRate = +e.target.value; setReview({...review, ladder: nl});
                          }} className="bg-transparent w-8 text-xs font-black text-yellow-500 outline-none" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <div className="grid grid-cols-12 gap-8">
               <section className="col-span-5 glass rounded-[2.5rem] p-8 border-l-[8px] border-yellow-500 shadow-2xl">
                  <div className="flex items-center gap-3 mb-8">
                    <Trophy className="text-yellow-500" size={20} />
                    <h2 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">04 灵魂标的</h2>
                  </div>
                  <div className="space-y-6">
                    <div className="bg-red-500/5 border border-red-500/10 p-6 rounded-[2rem] relative">
                      <span className="text-[10px] font-black text-red-500 uppercase block mb-3">情绪总龙头</span>
                      <input value={review.dragon} onChange={e => setReview({...review, dragon: e.target.value})} className="bg-transparent w-full text-2xl font-black text-red-500 outline-none mb-3" />
                      <select value={review.dragonStatus} onChange={e => setReview({...review, dragonStatus: e.target.value as any})} className="bg-black/20 text-[11px] font-black text-red-500 outline-none p-2 rounded-xl border border-red-500/10 w-full cursor-pointer">
                        <option value="accelerate">一致加速</option>
                        <option value="divergence">分歧转强</option>
                        <option value="broken">破位退潮</option>
                        <option value="revive">反包穿越</option>
                      </select>
                    </div>
                    <div className="bg-blue-500/5 border border-blue-500/10 p-6 rounded-[2rem]">
                      <span className="text-[10px] font-black text-blue-500 uppercase block mb-3">趋势中军</span>
                      <input value={review.midArmy} onChange={e => setReview({...review, midArmy: e.target.value})} className="bg-transparent w-full text-2xl font-black text-blue-500 outline-none" />
                    </div>
                  </div>
               </section>
               <section className="col-span-7 glass rounded-[2.5rem] p-8 border-l-[8px] border-emerald-500 shadow-2xl">
                  <div className="flex items-center gap-3 mb-8">
                    <Crosshair className="text-emerald-500" size={20} />
                    <h2 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">05 核心备选</h2>
                  </div>
                  <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                    {review.watchlist.map((stock, i) => (
                      <div key={i} className="bg-[#121215] border border-white/5 p-4 rounded-[1.8rem]">
                        <input placeholder="股票名" value={stock.name} onChange={e => updateWatchlist(i, 'name', e.target.value)} className="bg-transparent w-full text-xs font-black text-white outline-none mb-2 border-b border-white/5 pb-1" />
                        <input placeholder="逻辑" value={stock.concept} onChange={e => updateWatchlist(i, 'concept', e.target.value)} className="bg-transparent w-full text-[9px] font-bold text-emerald-500/70 outline-none mb-2" />
                        <textarea placeholder="计划..." value={stock.plan} onChange={e => updateWatchlist(i, 'plan', e.target.value)} className="bg-black/20 w-full text-[9px] h-12 p-2 rounded-xl text-gray-400 outline-none resize-none border border-white/5" />
                      </div>
                    ))}
                  </div>
               </section>
            </div>

            {/* AI 指挥官集成研判区 */}
            <section className="glass rounded-[3rem] p-10 border border-purple-500/20 shadow-2xl">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center text-white border border-white/20 shadow-2xl">
                    <BrainCircuit size={32} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter">AI 指挥官·全维研判</h2>
                    <span className="text-[10px] font-black text-purple-400 uppercase tracking-widest">Global Faith Decision Engine</span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => callAI({type: 'optimization'})} disabled={isLoading} className="px-6 py-4 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 rounded-2xl text-xs font-black transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2">
                    <Wand2 size={16} /> 策略优化
                  </button>
                  <button onClick={() => callAI()} disabled={isLoading} className="px-6 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-2xl text-xs font-black shadow-xl shadow-purple-600/20 active:scale-95 disabled:opacity-50 flex items-center gap-2">
                    <Zap size={16} /> 启动研判
                  </button>
                </div>
              </div>

              {/* 主线持续性监控提示器 (新增) */}
              <div className="mb-8 p-6 bg-emerald-500/5 rounded-[2rem] border border-emerald-500/10">
                <div className="flex items-center gap-3 mb-4">
                   <Timer size={14} className="text-emerald-500" />
                   <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">5日主线持续性监控 (出现≥2次)</span>
                </div>
                <div className="flex flex-wrap gap-3">
                   {persistentSectors.length > 0 ? (
                      persistentSectors.map(([name, count]) => (
                        <div key={name} className="flex items-center gap-3 bg-emerald-500/10 px-4 py-2 rounded-xl border border-emerald-500/20">
                           <span className="text-xs font-black text-emerald-400">{name}</span>
                           <span className="text-[10px] font-bold bg-emerald-500/20 px-1.5 rounded text-emerald-300">活跃{count}天</span>
                        </div>
                      ))
                   ) : (
                      <span className="text-[11px] text-gray-600 font-bold italic">暂无具有高持续性的观测板块...</span>
                   )}
                </div>
              </div>

              {/* 核心信仰分控制 */}
              <div className="mb-8 p-8 bg-white/5 rounded-[2.5rem] border border-white/10 flex items-center gap-12 group transition-all hover:border-purple-500/30">
                <div className="flex flex-col items-center border-r border-white/10 pr-12">
                  <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em] mb-2">综合信仰分</span>
                  <div className="flex items-baseline gap-1">
                    <span className={`text-5xl font-black transition-all duration-500 ${review.score > 70 ? 'text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.4)]' : review.score > 40 ? 'text-yellow-500' : 'text-green-500'}`}>{review.score}</span>
                    <span className="text-xs font-black text-gray-700">%</span>
                  </div>
                </div>
                <div className="flex-1 flex flex-col gap-4">
                   <div className="flex items-center gap-6">
                      <button onClick={() => setReview({...review, score: Math.max(0, review.score-5)})} className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 font-black transition-all active:scale-90">-5</button>
                      <div className="flex-1 h-3 bg-black/50 rounded-full border border-white/10 p-[2px] relative">
                         <div className={`h-full transition-all duration-700 rounded-full ${review.score > 70 ? 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]' : review.score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${review.score}%` }}></div>
                         <div className="absolute top-0 left-1/2 w-0.5 h-full bg-white/10"></div>
                      </div>
                      <button onClick={() => setReview({...review, score: Math.min(100, review.score+5)})} className="w-12 h-12 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 font-black transition-all active:scale-90">+5</button>
                   </div>
                   <div className="flex justify-between px-2 text-[9px] font-black text-gray-600 uppercase tracking-widest">
                      <span>冰点/分歧</span>
                      <span>主升/狂热</span>
                   </div>
                </div>
              </div>
              
              <div className="bg-black/40 rounded-[2.5rem] border border-white/5 p-8 custom-scrollbar min-h-[400px] relative backdrop-blur-sm">
                {isLoading && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0a0a0c]/80 backdrop-blur-xl z-[150] rounded-[2.5rem]">
                     <RefreshCcw className="animate-spin text-purple-500 mb-6" size={48} />
                     <span className="text-sm font-black text-purple-400 uppercase tracking-widest">{statusMsg}</span>
                  </div>
                )}
                <div className="prose prose-invert max-w-none font-sans text-gray-300">
                  {review.aiAnalysis ? (
                    <div dangerouslySetInnerHTML={{ __html: review.aiAnalysis.replace(/\n/g, '<br/>') }} />
                  ) : (
                    <div className="flex flex-col items-center justify-center py-24 opacity-30">
                      <ShieldAlert size={64} className="mb-6" />
                      <p className="italic font-bold tracking-widest uppercase text-center">上传文件并填充数据，启动 AI 指挥官综合研判</p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* 信仰档案库 */}
        <section className="mt-20 border-t border-white/5 pt-16 pb-32 text-left">
          <div className="flex items-center gap-5 mb-12 px-2">
            <History className="text-gray-500" size={24} />
            <h2 className="text-3xl font-black text-white uppercase italic tracking-tighter">信仰档案库</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {history.map((h) => (
              <div key={h.date} onClick={() => setReview(h)} className={`p-8 rounded-[2.5rem] border transition-all cursor-pointer h-64 flex flex-col justify-between relative overflow-hidden ${review.date === h.date ? 'bg-red-600/10 border-red-500' : 'bg-[#121215] border-white/5 hover:border-white/20'}`}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-black text-gray-600">{h.date}</span>
                  {review.date === h.date && <div className="p-1 bg-red-500 rounded text-white"><CheckCircle2 size={12} /></div>}
                </div>
                <div className="flex flex-col">
                  <span className={`text-5xl font-black ${review.date === h.date ? 'text-red-500' : 'text-white'}`}>{h.score}</span>
                  <span className="text-[11px] font-black text-red-500/80 uppercase truncate mt-4">{h.dragon || '无高度标'}</span>
                </div>
                <div className="border-t border-white/5 pt-5 text-[10px] text-gray-600 flex justify-between uppercase font-black">
                  <span>涨停:{h.limitUpTotal}</span>
                  <span>成交:{h.totalVol}T</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
