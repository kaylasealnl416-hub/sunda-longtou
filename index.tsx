
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { 
  Flame, Search, Activity, BarChart3, MessageSquare, Zap, 
  ChevronRight, RefreshCcw, ExternalLink, Target, Trophy, 
  AlertTriangle, Info, Calendar, Save, Download, FileSpreadsheet,
  ArrowUpRight, ArrowDownRight, TrendingUp, ShieldCheck, 
  Crosshair, BrainCircuit, Sparkles, Globe, Link as LinkIcon,
  ChevronDown, PenTool, GitCompare, X, Skull, TrendingDown,
  Layers, Radio, Gauge, Share2
} from 'lucide-react';
import { GoogleGenAI } from "@google/genai";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, BarChart, Bar, Cell, Legend
} from 'recharts';
import html2canvas from 'html2canvas';

// --- Types & Constants ---
const STORAGE_KEY = 'dragon_faith_reviews_v23';

interface LadderData {
  count: number;
  concept?: string;
  stock?: string;
  promoRate?: number; // 晋级率
}

interface MarketReview {
  date: string;
  auUp: number;
  auDn: number;
  prem: string; 
  trend: string; 
  vol: string;
  vDelta: string;
  upCount: number;
  dnCount: number;
  lUp: number;
  lDn: number;
  brokenRate: number;
  promotionRate: number;
  yesterdayGain: number; 
  nuclearCount: number;  
  mainSectorSentiment: string; // 主线板块情绪
  sectors: { name: string; count: number }[];
  limitDownSector: { name: string; count: number };
  ladder: Record<string, LadderData>;
  highBoard: string;
  dragon: string;
  dragonStatus: string;
  midArmy: string;
  midStatus: string;
  subLeader: string;
  filler: string;
  reflection: string;
  score: number;
  stage: string;
  aiAnalysis: string;
}

const INITIAL_REVIEW: MarketReview = {
  date: new Date().toISOString().split('T')[0],
  auUp: 0, auDn: 0, prem: 'normal',
  trend: 'normal', vol: '', vDelta: '', upCount: 0, dnCount: 0,
  lUp: 0, lDn: 0, brokenRate: 0, promotionRate: 0,
  yesterdayGain: 0,
  nuclearCount: 0,
  mainSectorSentiment: '--', 
  sectors: [{ name: '', count: 0 }, { name: '', count: 0 }, { name: '', count: 0 }],
  limitDownSector: { name: '', count: 0 },
  ladder: {
    '5': { count: 0, concept: '', stock: '', promoRate: 0 },
    '4': { count: 0, concept: '', stock: '', promoRate: 0 },
    '3': { count: 0, concept: '', stock: '', promoRate: 0 },
    '2': { count: 0, concept: '', stock: '', promoRate: 0 },
    '1': { count: 0, concept: '', stock: '', promoRate: 0 },
  },
  highBoard: '',
  dragon: '', dragonStatus: 'broken',
  midArmy: '', midStatus: 'trend_up',
  subLeader: '', filler: '',
  reflection: '',
  score: 0,
  stage: '--',
  aiAnalysis: ''
};

const calculateScore = (d: MarketReview) => {
  let score = 50;
  if (d.trend === 'v_reversal') score += 20;
  if (d.trend === 'a_drop') score -= 25; 
  if (d.yesterdayGain > 5) score += 15;
  if (d.yesterdayGain < -2) score -= 20;
  if (d.nuclearCount > 10) score -= 15;
  if (d.lUp > 80) score += 10;
  if (d.lUp < 20) score -= 10;
  if (d.lDn > 15) score -= 20;
  if (d.promotionRate > 50) score += 10;
  
  const finalScore = Math.max(0, Math.min(100, score));
  let stage = '震荡/修复';
  if (finalScore >= 80) stage = '高潮/分歧预警';
  else if (finalScore <= 35) stage = '冰点/恐慌退潮';
  else if (finalScore > 35 && finalScore < 50 && d.yesterdayGain > 0) stage = '回暖初期';
  
  return { score: finalScore, stage };
};

interface GroundingSource {
  web?: { uri: string; title: string };
  maps?: { uri: string; title: string };
}

const App = () => {
  const [review, setReview] = useState<MarketReview>(INITIAL_REVIEW);
  const [history, setHistory] = useState<MarketReview[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [sources, setSources] = useState<GroundingSource[]>([]);
  const [compareDate, setCompareDate] = useState<string>("");
  const captureRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as MarketReview[];
        setHistory(parsed);
        const today = parsed.find(r => r.date === INITIAL_REVIEW.date);
        if (today) setReview(today);
      }
    } catch (e) {
      console.error("Failed to load storage", e);
    }
  }, []);

  const historyData = useMemo(() => {
    return [...history].reverse().slice(-7);
  }, [history]);

  const handleSave = () => {
    const { score, stage } = calculateScore(review);
    const updated = { ...review, score, stage };
    const newHistory = [updated, ...history.filter(h => h.date !== updated.date)].sort((a,b) => b.date.localeCompare(a.date));
    setHistory(newHistory);
    setReview(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    alert("数据已同步至终端。");
  };

  const fetchTodayData = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("正在检索收盘核心微观情报 (包含溢价与核按钮数据)...");
    
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const prompt = `
        搜索分析 A 股 ${review.date} 的收盘情绪指标。
        
        [DATA_BLOCK]
        UP/DOWN: 上涨家数/下跌家数
        LIMIT_U/D: 涨停(非ST)/跌停家数
        BROKEN_RATE: 炸板率 %
        PROMO_RATE: 连板晋级率 %
        YEST_GAIN: 昨日涨停股今日平均收益溢价 %
        NUCLEAR: 今日跌幅超7%或天地板的家数
        VOL: 成交额(万亿)
        DRAGON: 核心龙头(高度/地位)
        LADDER_PROMO: 5板晋级率, 4板晋级率, 3板晋级率, 2板晋级率
        [/DATA_BLOCK]
        
        基于龙头信仰逻辑，给出今日的情绪周期定义。
      `;

      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: prompt,
        config: { tools: [{ googleSearch: {} }] }
      });

      const text = response.text || "";
      const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
      if (chunks) {
        setSources(chunks as GroundingSource[]);
      }

      const match = text.match(/\[DATA_BLOCK\]([\s\S]*?)\[\/DATA_BLOCK\]/);
      
      if (match) {
        const dataStr = match[1];
        const lines = dataStr.split('\n').map(l => l.trim()).filter(l => l);
        const parsed: any = {};
        lines.forEach(line => {
          const [key, val] = line.split(':').map(s => s.trim());
          parsed[key] = val;
        });

        const newReview = { ...review };
        if (parsed['UP/DOWN']) {
          const [u, d] = parsed['UP/DOWN'].split('/').map((n:string) => parseInt(n));
          newReview.upCount = u; newReview.dnCount = d;
        }
        if (parsed.YEST_GAIN) newReview.yesterdayGain = parseFloat(parsed.YEST_GAIN);
        if (parsed.NUCLEAR) newReview.nuclearCount = parseInt(parsed.NUCLEAR);
        if (parsed['LIMIT_U/D']) {
           const [u, d] = parsed['LIMIT_U/D'].split('/').map((n:string) => parseInt(n));
           newReview.lUp = u; newReview.lDn = d;
        }

        const { score, stage } = calculateScore(newReview);
        newReview.score = score;
        newReview.stage = stage;
        newReview.aiAnalysis = text.replace(/\[DATA_BLOCK\][\s\S]*?\[\/DATA_BLOCK\]/, "").trim();
        setReview(newReview);
      }
    } catch (e) {
      console.error(e);
      alert("搜索失败，请手动录入。");
    } finally {
      setIsLoading(false);
    }
  };

  const callAI = async (mode: 'full' | 'polish' | 'limitDown' | 'ladderAnalysis' | 'sectorInterlinkage' = 'full', level?: string) => {
    if (isLoading) return;
    setIsLoading(true);
    
    const messages = {
      full: "正在进行深度信仰研判...",
      polish: "正在优化操盘反思...",
      limitDown: "正在通过风险雷达穿透跌停原因...",
      ladderAnalysis: `正在深度解析 ${level} 板梯队晋级逻辑...`,
      sectorInterlinkage: "正在穿透主线板块间的联动与虹吸博弈..."
    };
    
    setStatusMsg(messages[mode]);
    setSources([]);
    
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      let prompt = "";
      
      if (mode === 'full') {
        prompt = `
          你是一位精通《龙头信仰》的游资教练。
          当前数据：溢价 ${review.yesterdayGain}%，核按钮 ${review.nuclearCount}家，连板涨停 ${review.lUp}，跌停 ${review.lDn}。
          
          研判要求：
          1. 核心矛盾：赚钱效应与亏钱效应是否背离？
          2. 周期定位：是“混沌期”、“主升期”还是“退潮期”？
          3. 信仰博弈：总龙目前的封板力度和明日预期。
          4. 请额外给出一个 [MAIN_SENTIMENT]活跃/分化/退潮[/MAIN_SENTIMENT] 标签，用于标记当前最活跃主线板块的情绪状态。
        `;
      } else if (mode === 'polish') {
        prompt = `
          重写反思：${review.reflection}
          要求：使用游资语录风格，强调对周期的尊重。
        `;
      } else if (mode === 'limitDown') {
        prompt = `
          任务：深度分析今日 A 股市场跌停家数（当前：${review.lDn}家）背后的根本原因与情绪杀伤力。
          1. 检索今日跌停板个股名单（含非ST与ST），并精准识别其中的“核按钮”标的（天地板、大高开低走）以及“趋势中军”（大市值容量标的）的破位情况。
          2. 判别成因：是个股利空、板块主线崩溃（瓦解）、还是系统性流动性衰竭。
          3. 连锁反应分析：重点研判这些核心跌停标的是否引发了全市场赚钱效应的坍塌（即：是否会带动明天更剧烈的核按钮）。
          4. 信仰研判：基于“龙头信仰”逻辑，判定当前是“恐慌冰点”还是“退潮中继”。
          日期：${review.date}。要求：风格尖锐刻刻，直击本质，Markdown 格式。
        `;
      } else if (mode === 'ladderAnalysis' && level) {
        const lData = review.ladder[level];
        prompt = `
          任务：分析 A 股今日 ${level} 板（及以上）梯队的晋级质量。
          当前数据：该梯队共 ${lData?.count} 家，晋级率约为 ${lData?.promoRate}%，核心标的为 [${lData?.stock}]。
          
          研判要求：
          1. 判定状态：该梯队目前是“强一致加速”、“分化博弈”还是“退潮坍塌”？
          2. 梯队逻辑：分析标的 [${lData?.stock}] 是否具备领涨地位，及其对下方低位板的带动效应（补涨逻辑）。
          3. 风险预警：若明日晋级失败，对市场情绪的影响。
          4. 信仰建议：此位置应格局、减仓还是止损？
          日期：${review.date}。使用 Markdown，语气专业且果断。
        `;
      } else if (mode === 'sectorInterlinkage') {
        prompt = `
          任务：穿透分析今日 A 股主线板块间的联动效应。
          当前主线情绪判定为：[${review.mainSectorSentiment}]。核心标的：[${review.dragon}]。
          
          研判要求：
          1. 联动与吸血：分析当前最强板块（龙头板块）是对其他板块产生了“溢出带动效应”（一强带多强）还是“虹吸效应”（虹吸全场流动性导致其余崩塌）。
          2. 翘翘板效应：识别今日是否存在明显的资金在某两个特定板块间的反复横跳（如 AI 与 金融，或 固态电池 与 机器人）。
          3. 板块地位：哪个板块是真主线，哪个是掩护龙头的补涨分支，哪个是抽血大户。
          4. 压制研判：主线龙头的放量/断板是否会直接引发次主流板块的恐慌性抛售。
          日期：${review.date}。使用 Markdown，逻辑严密。
        `;
      }

      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: prompt,
        config: { tools: (mode === 'full' || mode === 'limitDown' || mode === 'ladderAnalysis' || mode === 'sectorInterlinkage') ? [{ googleSearch: {} }] : [] }
      });

      const text = response.text || "";
      const chunks = response.candidates?.[0]?.groundingMetadata?.groundingChunks;
      if (chunks) {
        setSources(chunks as GroundingSource[]);
      }

      if (mode !== 'polish') {
        let updatedReview = { ...review, aiAnalysis: text };
        
        // 解析主线情绪标签 (仅在全面研判时)
        if (mode === 'full') {
          const sentimentMatch = text.match(/\[MAIN_SENTIMENT\](活跃|分化|退潮)\[\/MAIN_SENTIMENT\]/);
          if (sentimentMatch) {
            updatedReview.mainSectorSentiment = sentimentMatch[1];
            updatedReview.aiAnalysis = text.replace(/\[MAIN_SENTIMENT\].*?\[\/MAIN_SENTIMENT\]/, "").trim();
          }
        }
        
        setReview(updatedReview);
      } else {
        setReview(prev => ({ ...prev, reflection: text }));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen pb-20">
      <header className="sticky top-0 z-50 glass border-b border-white/5 h-16 flex items-center px-6 justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center shadow-lg shadow-red-600/20">
            <Flame className="text-white fill-white" size={18} />
          </div>
          <h1 className="text-lg font-black tracking-tight flex items-center gap-2">
            <span className="text-white">龙头信仰</span>
            <span className="text-red-500">v24.2</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-xl border border-white/10">
            <Calendar size={14} className="text-gray-500" />
            <input type="date" value={review.date} onChange={e => setReview({...review, date: e.target.value})} className="bg-transparent border-none text-xs font-mono outline-none text-gray-300" />
          </div>
          <button onClick={fetchTodayData} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50">
            <Globe size={14} /> 获取情报
          </button>
          <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-red-600/20">
            <Save size={14} /> 保存复盘
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 mt-8 grid grid-cols-12 gap-8">
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <section className="glass rounded-3xl p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between mb-6">
               <div className="flex items-center gap-2">
                 <Zap className="text-yellow-400" size={18} />
                 <h2 className="font-bold text-sm uppercase tracking-widest text-gray-400">01 情绪微观监控</h2>
               </div>
               <div className="text-[10px] font-bold text-red-500 bg-red-500/10 px-2 py-0.5 rounded">核心信仰指标</div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-gray-500">昨停今日溢价 (%)</label>
                <div className="relative">
                  <input type="number" step="0.1" value={review.yesterdayGain} onChange={e => setReview({...review, yesterdayGain: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-red-500/50 font-bold" />
                  <TrendingUp className={`absolute right-3 top-2.5 size-4 ${review.yesterdayGain > 0 ? 'text-red-500' : 'text-green-500 rotate-180'}`} />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-gray-500">大回撤/核按钮 (家)</label>
                <div className="relative">
                  <input type="number" value={review.nuclearCount} onChange={e => setReview({...review, nuclearCount: +e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-green-500/50 font-bold" />
                  <Skull className={`absolute right-3 top-2.5 size-4 ${review.nuclearCount > 5 ? 'text-red-500' : 'text-gray-600'}`} />
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-red-400">非ST涨停</label>
                <input type="number" value={review.lUp} onChange={e => setReview({...review, lUp: +e.target.value})} className="w-full bg-red-500/5 border border-red-500/10 rounded-xl px-4 py-2 text-sm outline-none font-bold text-red-400" />
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-bold text-green-400">跌停家数</label>
                  <button 
                    onClick={() => callAI('limitDown')} 
                    disabled={isLoading || review.lDn === 0}
                    className="group flex items-center gap-1.5 text-[9px] font-black text-green-500 hover:text-red-500 transition-all duration-300 disabled:opacity-30"
                  >
                    <Radio size={11} className={`transition-transform ${isLoading ? 'animate-spin' : 'group-hover:scale-125'}`} /> 风险穿透
                  </button>
                </div>
                <div className="relative">
                  <input type="number" value={review.lDn} onChange={e => setReview({...review, lDn: +e.target.value})} className="w-full bg-green-500/5 border border-green-500/10 rounded-xl px-4 py-2 text-sm outline-none font-bold text-green-400 cursor-pointer" />
                  <AlertTriangle className={`absolute right-3 top-2.5 size-4 transition-colors ${review.lDn > 10 ? 'text-red-500 animate-pulse' : 'text-green-800'}`} />
                </div>
              </div>

              {/* 主线板块情绪显示区域：增加点击穿透板块联动功能 */}
              <div className="col-span-2 mt-2 pt-3 border-t border-white/5">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1">
                    <Layers size={12} className="text-purple-400" /> 主线板块情绪
                  </label>
                  <button 
                    onClick={() => callAI('sectorInterlinkage')}
                    disabled={isLoading || review.mainSectorSentiment === '--'}
                    className="text-[9px] font-black text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1 uppercase disabled:opacity-30"
                  >
                    <GitCompare size={10} /> 联动博弈穿透
                  </button>
                </div>
                <div 
                  onClick={() => callAI('sectorInterlinkage')}
                  className={`w-full py-3 px-4 rounded-2xl flex items-center justify-between transition-all duration-300 border cursor-pointer hover:scale-[1.01] active:scale-95 group
                  ${review.mainSectorSentiment === '活跃' ? 'bg-red-500/10 border-red-500/20 text-red-500 shadow-lg shadow-red-500/5' : 
                    review.mainSectorSentiment === '分化' ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-500 shadow-lg shadow-yellow-500/5' :
                    review.mainSectorSentiment === '退潮' ? 'bg-green-500/10 border-green-500/20 text-green-500 shadow-lg shadow-green-500/5' :
                    'bg-white/5 border-white/10 text-gray-500'}
                `}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full animate-pulse
                      ${review.mainSectorSentiment === '活跃' ? 'bg-red-500' : 
                        review.mainSectorSentiment === '分化' ? 'bg-yellow-500' :
                        review.mainSectorSentiment === '退潮' ? 'bg-green-500' :
                        'bg-gray-700'}
                    `} />
                    <span className="text-sm font-black tracking-widest uppercase">
                      {review.mainSectorSentiment || '--'}
                    </span>
                  </div>
                  <Share2 size={12} className="text-current opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </div>
          </section>

          <section className="glass rounded-3xl p-6">
            <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-3">
              <Target className="text-blue-500" size={18} />
              <h2 className="font-bold text-sm uppercase tracking-widest text-gray-400">02 空间梯队晋级</h2>
            </div>
            <div className="space-y-3">
              {['5', '4', '3', '2', '1'].map(lvl => (
                <div key={lvl} className="flex items-center gap-2 group">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-black
                    ${lvl === '5' ? 'bg-red-500/20 text-red-500' : 'bg-white/5 text-gray-400'}
                  `}>
                    {lvl === '5' ? '5+' : lvl}
                  </div>
                  <div className="flex-1 grid grid-cols-12 gap-2">
                    <div className="col-span-3">
                      <input type="number" value={review.ladder[lvl]?.count || 0} placeholder="家" onChange={e => {
                        const nl = {...review.ladder}; nl[lvl] = { ...nl[lvl], count: +e.target.value }; setReview({...review, ladder: nl});
                      }} className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-center outline-none" title="今日连板家数" />
                    </div>
                    
                    {/* 晋级率显示与点击 AI 分析 */}
                    <div className="col-span-3">
                      <button 
                        onClick={() => callAI('ladderAnalysis', lvl)}
                        disabled={isLoading}
                        className="w-full h-full bg-white/5 border border-white/10 hover:border-yellow-500/50 hover:bg-yellow-500/5 rounded-lg flex items-center justify-center gap-1 transition-all group/btn disabled:opacity-50"
                        title={`点击分析 ${lvl} 板梯队质量`}
                      >
                        <span className="text-[10px] font-bold text-yellow-500">
                          {review.ladder[lvl]?.promoRate || 0}%
                        </span>
                        <Gauge size={10} className="text-yellow-600 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
                      </button>
                    </div>

                    <div className="col-span-6">
                      <input value={review.ladder[lvl]?.stock || ''} placeholder="核心标的" onChange={e => {
                        const nl = {...review.ladder}; nl[lvl] = { ...nl[lvl], stock: e.target.value }; setReview({...review, ladder: nl});
                      }} className="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs outline-none group-hover:border-blue-500/50 transition-all font-bold text-gray-300" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="col-span-12 lg:col-span-8 space-y-8">
           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <section className="glass rounded-3xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none rotate-12">
                   <Trophy size={80} />
                </div>
                <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-3">
                  <Trophy className="text-yellow-500" size={18} />
                  <h2 className="font-bold text-sm uppercase tracking-widest text-gray-400">03 总龙与趋势中军</h2>
                </div>
                <div className="space-y-5">
                   <div className="p-4 bg-red-500/5 rounded-2xl border border-red-500/10 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black text-red-500 uppercase tracking-widest">情绪总龙头 (Dragon)</span>
                        <select value={review.dragonStatus} onChange={e => setReview({...review, dragonStatus: e.target.value})} className="bg-transparent text-[10px] font-bold text-red-400 outline-none">
                          <option value="broken">分歧/断板</option>
                          <option value="accelerate">一致加速</option>
                          <option value="revive">反包/二春</option>
                        </select>
                      </div>
                      <input value={review.dragon} onChange={e => setReview({...review, dragon: e.target.value})} placeholder="输入当前最高标..." className="w-full bg-transparent border-none text-2xl font-black text-red-500 outline-none" />
                   </div>
                   <div className="p-4 bg-blue-500/5 rounded-2xl border border-blue-500/10 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">主线容量中军 (Army)</span>
                        <select value={review.midStatus} onChange={e => setReview({...review, midStatus: e.target.value})} className="bg-transparent text-[10px] font-bold text-blue-400 outline-none">
                          <option value="trend_up">趋势主升</option>
                          <option value="shock">平台震荡</option>
                          <option value="broken_trend">破位阴跌</option>
                        </select>
                      </div>
                      <input value={review.midArmy} onChange={e => setReview({...review, midArmy: e.target.value})} placeholder="输入板块权重..." className="w-full bg-transparent border-none text-2xl font-black text-blue-500 outline-none" />
                   </div>
                </div>
              </section>

              <section className="glass rounded-3xl p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-6 border-b border-white/5 pb-3">
                  <PenTool className="text-orange-400" size={18} />
                  <h2 className="font-bold text-sm uppercase tracking-widest text-gray-400">04 操盘手日志</h2>
                </div>
                <textarea value={review.reflection} onChange={e => setReview({...review, reflection: e.target.value})} placeholder="记录信仰或恐惧..." className="flex-1 w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-sm outline-none focus:border-orange-500/30 resize-none custom-scrollbar font-sans" />
                <button onClick={() => callAI('polish')} className="mt-3 text-[10px] font-bold text-gray-500 hover:text-orange-400 transition-colors flex items-center gap-1 self-end">
                   <Sparkles size={12} /> 信仰重构优化
                </button>
              </section>
           </div>

           <section className="glass rounded-3xl p-8 border border-purple-500/20 shadow-2xl relative">
              <div className="flex items-center justify-between mb-8">
                 <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-2xl bg-purple-600/20 flex items-center justify-center border border-purple-500/30">
                     <BrainCircuit className="text-purple-400" size={24} />
                   </div>
                   <div>
                     <h2 className="text-xl font-black tracking-tight text-white uppercase">AI 信仰决策终端</h2>
                     <span className="text-[10px] font-bold text-purple-400 tracking-widest uppercase">{review.stage}</span>
                   </div>
                 </div>
                 <div className="flex gap-3">
                    <div className="px-4 py-2 bg-black/40 border border-white/10 rounded-xl flex flex-col items-center">
                       <span className="text-[9px] text-gray-500 font-bold">周期得分</span>
                       <span className={`text-lg font-black ${review.score > 70 ? 'text-red-500' : 'text-green-500'}`}>{review.score}</span>
                    </div>
                    <button onClick={() => callAI('full')} disabled={isLoading} className="px-6 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-black transition-all flex items-center gap-2">
                      {isLoading ? <RefreshCcw className="animate-spin" size={14} /> : <Zap size={14} />} 深度研判
                    </button>
                 </div>
              </div>
              <div className="min-h-[300px] bg-black/40 rounded-2xl border border-white/5 p-6 overflow-y-auto custom-scrollbar">
                 <div className="prose prose-invert max-w-none prose-sm whitespace-pre-wrap text-gray-300">
                    {isLoading ? (
                      <div className="flex flex-col items-center justify-center py-20 space-y-4">
                        <RefreshCcw className="animate-spin text-purple-500" size={32} />
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-widest animate-pulse">{statusMsg}</span>
                      </div>
                    ) : (
                      review.aiAnalysis || "等待指挥部决策..."
                    )}
                 </div>
                 {sources.length > 0 && !isLoading && (
                   <div className="mt-4 pt-4 border-t border-white/10">
                     <p className="text-[10px] font-bold text-gray-500 mb-2 uppercase tracking-widest flex items-center gap-1">
                       <LinkIcon size={10} /> 研判情报来源:
                     </p>
                     <div className="flex flex-wrap gap-2">
                       {sources.map((s, idx) => s.web && (
                         <a key={idx} href={s.web.uri} target="_blank" rel="noopener noreferrer" className="text-[10px] text-purple-400 hover:text-purple-300 underline flex items-center gap-1">
                           {s.web.title || '情报源'} <ExternalLink size={8} />
                         </a>
                       ))}
                     </div>
                   </div>
                 )}
              </div>
           </section>

           <section className="glass rounded-3xl p-6">
              <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-3">
                <div className="flex items-center gap-2">
                  <BarChart3 className="text-gray-400" size={18} />
                  <h2 className="font-bold text-sm uppercase tracking-widest text-gray-400">05 情绪分值走势</h2>
                </div>
                <div className="flex gap-2">
                   <select value={compareDate} onChange={e => setCompareDate(e.target.value)} className="bg-white/5 text-[10px] font-bold text-gray-400 outline-none rounded px-2">
                      <option value="">对比历史数据</option>
                      {history.map(h => <option key={h.date} value={h.date}>{h.date}</option>)}
                   </select>
                </div>
              </div>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={historyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                    <XAxis dataKey="date" hide />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333', fontSize: '10px' }} />
                    <Line type="monotone" dataKey="score" stroke="#ef4444" strokeWidth={3} dot={{ r: 4, fill: '#ef4444' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
           </section>
        </div>
      </main>

      <div style={{ position: 'fixed', left: '-9999px', top: 0 }}>
        <div ref={captureRef} className="w-[1000px] bg-[#0a0a0c] p-12 text-white font-sans border-[10px] border-red-600/10">
           <h1 className="text-4xl font-black italic mb-8">龙头信仰复盘报告 <span className="text-red-500 font-mono text-2xl">{review.date}</span></h1>
        </div>
      </div>
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
