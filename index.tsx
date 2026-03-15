import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Flame, Zap, BarChart3, Target, Trophy, BrainCircuit,
  History, TrendingUp, TrendingDown, Layers, Activity,
  ArrowUpRight, Scale, Save, RefreshCcw, ArrowRight,
  ShieldAlert, Wand2, DatabaseZap, X, FileUp, Calendar, Timer, Waves,
  ChevronDown, MessageSquareCode, Radio, Cpu, Plus, TrendingDownIcon,
  Wallet, Trash2, DollarSign, Percent, ArrowDownRight, Camera, Crosshair
} from 'lucide-react';
import html2canvas from 'html2canvas';
import { GoogleGenAI } from "@google/genai";
import * as XLSX from 'xlsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, Legend, Cell, PieChart, Pie
} from 'recharts';

// --- Types & Constants ---
const STORAGE_KEY = 'dragon_faith_system_v32_0';
const TRADE_STORAGE_KEY = 'dragon_faith_trades_v1';
const POSITION_STORAGE_KEY = 'dragon_faith_positions_v1';

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
  isExcel?: boolean;
}

interface MarketReview {
  date: string;
  indices: IndexData[];
  totalVol: number;
  volDelta: number;
  limitUpTotal: number;
  limitDownTotal: number;
  brokenRate: number;
  upDownCount: { up: number; down: number };
  topSectors: SectorTrack[];
  persistentSectors: { name: string; days: number }[];
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

type TradeType = '追涨' | '低吸' | '反包' | '潜伏' | '止盈' | '止损';
type TradeAction = 'buy' | 'sell';

interface TradeRecord {
  id: string;
  date: string;
  stockCode: string;
  stockName?: string;
  action: TradeAction;
  type: TradeType;
  price: number;
  quantity: number;
  profit?: number;
  profitRate?: number;
  notes?: string;
  linkedDragon?: string;
}

interface TradeStats {
  totalTrades: number;
  winCount: number;
  loseCount: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  profitLossRatio: number;
  bestTrade: number;
  worstTrade: number;
  currentCycle: string;
}

interface Position {
  id: string;
  stockCode: string;
  stockName?: string;
  buyDate: string;
  buyPrice: number;
  buyType: TradeType;
  quantity: number;
  currentPrice?: number;
  profit?: number;
  profitRate?: number;
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
  upDownCount: { up: 0, down: 0 },
  topSectors: [
    { name: '', gain: 0, limitUps: 0, volume: 0 },
    { name: '', gain: 0, limitUps: 0, volume: 0 },
    { name: '', gain: 0, limitUps: 0, volume: 0 }
  ],
  persistentSectors: [],
  ladder: {
    '5+': { count: 0, stock: '', concept: '', promoRate: 0 },
    '5': { count: 0, stock: '', concept: '', promoRate: 0 },
    '4': { count: 0, stock: '', concept: '', promoRate: 0 },
    '3': { count: 0, stock: '', concept: '', promoRate: 0 },
    '2': { count: 0, stock: '', concept: '', promoRate: 0 },
    '1': { count: 0, stock: '', concept: '', promoRate: 0 },
  },
  dragon: '', dragonStatus: 'accelerate', midArmy: '',
  watchlist: Array.from({ length: 6 }, () => ({ name: '', concept: '', plan: '' })),
  score: 50, stage: '待研判', aiAnalysis: '',
  customKeywords: '',
};

// ===== AI 盘手人设与量化技能库 (System Prompt) =====
const STOCK_TRADER_PERSONA = `你是一个名为『股市盘手』的顶级AI量化游资教练。你深谙A股超短线"情绪周期理论"，并且能够像量化交易机器一样，通过客观数据（涨跌停、晋级率、炸板率、量能）来推演市场极值。

【量化情绪判定引擎 (Quant-Sentiment Engine)】
1. 情绪指数建模 (Sentiment Scoring):
   - 情绪极度冰点：跌停数 > 15家，炸板率 > 35%，连板梯队晋级率全面低于 20%，或高标梯队出现 0 晋级（梯队断层）。
   - 情绪发酵/主升：涨停数稳步增加，(涨停数 - 跌停数) 差值迅速扩大，量能温和放大，出现完整的 1板->2板->3板->高标 的连续梯队，且中位股晋级率 > 40%。
   - 情绪高潮：涨停数 > 80家，炸板率 < 15%，龙头连续缩量一字板，后排杂毛全部鸡犬升天。
2. 涨停溢价与容错率监测 (Premium & Risk Tolerance):
   - 重点审视"高位梯队晋级率"。如果昨天的高标今天全部断板或核按钮（晋级率为0），说明"涨停溢价"为负，市场容错率极低，处于退潮期。
3. 绝对龙头锁定与辨识 (Dragon Locator):
   - 真正的龙头是穿越周期的。在量化判定为"退潮/冰点"时，依然能抗住分歧不补跌的，才是真龙。直接推翻用户填写的错误意淫龙头。
4. 仓位量化法则 (Position Sizing Rules):
   - 混沌/冰点期：建议仓位 0% - 10%（仅限首板或高低切试错）。
   - 试错/发酵期：建议仓位 20% - 40%（围绕主线前排）。
   - 主升期：建议仓位 60% - 80%（重仓锁死绝对龙头或核心中军）。
   - 高潮/分化/退潮期：坚决减仓至 0% - 20%，严禁追高。

【输出规范与语气】
- 语气：极度冷酷、数据驱动、一针见血、使用游资黑话（如：涨停溢价、高低切、退潮补跌、核按钮、主升浪、仓位管理）。
- 禁忌：绝不说"取决于市场表现"、"投资需谨慎"等废话。你的分析必须是非黑即白的。`;

// ===== 安全存储工具 =====
const safeStorage = {
  set: (key: string, value: unknown): boolean => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('[存储错误]', error);
      return false;
    }
  },
  get: (key: string, defaultValue?: unknown): unknown => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('[读取错误]', error);
      return defaultValue;
    }
  }
};

// ===== 交易复盘中心组件 =====
// ✅ 修复 BUG 1：接收 currentDate 属性，确保交易记录落在正确的复盘日期
const TradeManager = ({
  trades, positions, stats, buyDistribution, sellDistribution, currentStage, currentDate,
  onAddTrade, onAddPosition, onDeleteTrade, onUpdatePositionPrice, onClose
}: any) => {
  const [activeTab, setActiveTab] = useState<'record' | 'position' | 'stats'>('record');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    stockCode: '', action: 'buy' as 'buy' | 'sell', type: '追涨' as TradeType,
    price: 0, quantity: 0, notes: '', linkedDragon: ''
  });

  const handleSubmit = () => {
    if (!formData.stockCode || !formData.price || !formData.quantity) return;
    const tradeData = {
      date: currentDate, // ✅ 核心修复：绑定复盘界面的当前日期
      stockCode: formData.stockCode, action: formData.action, type: formData.type,
      price: formData.price, quantity: formData.quantity, notes: formData.notes, linkedDragon: formData.linkedDragon
    };
    onAddTrade(tradeData);
    if (formData.action === 'buy') {
      onAddPosition({
        stockCode: formData.stockCode, buyDate: tradeData.date, buyPrice: formData.price,
        buyType: formData.type, quantity: formData.quantity
      });
    }
    setFormData({ stockCode: '', action: 'buy', type: '追涨', price: 0, quantity: 0, notes: '', linkedDragon: '' });
    setShowAddForm(false);
  };

  const COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899'];

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-xl flex items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-6xl bg-[#0c0c10] border border-white/10 rounded-[2rem] p-6 my-8 relative">
        <button onClick={onClose} className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all text-gray-500 hover:text-white">
          <X size={20} />
        </button>

        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-xl shadow-emerald-600/20">
            <Wallet size={24} />
          </div>
          <div>
            <h2 className="text-xl font-black text-white uppercase">交易管理中枢</h2>
            <p className="text-xs text-gray-500 font-black uppercase tracking-widest">Trading Operations</p>
          </div>
        </div>

        <div className="flex gap-2 mb-6">
          {['record', 'position', 'stats'].map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${activeTab === tab ? 'bg-emerald-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}>
              {tab === 'record' ? '交易记录' : tab === 'position' ? '当前持仓' : '统计分析'}
            </button>
          ))}
        </div>

        {activeTab === 'record' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-black text-white">流水明细 <span className="text-[10px] text-gray-500 ml-2">当前归档日期: {currentDate}</span></h3>
              <button onClick={() => setShowAddForm(!showAddForm)} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-black flex items-center gap-2">
                <Plus size={14} /> 新增记录
              </button>
            </div>

            {showAddForm && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">标的</label><input type="text" value={formData.stockCode} onChange={e => setFormData({ ...formData, stockCode: e.target.value })} placeholder="输入名称/代码" className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none" /></div>
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">方向</label><select value={formData.action} onChange={e => setFormData({ ...formData, action: e.target.value as 'buy' | 'sell' })} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"><option value="buy">买入</option><option value="sell">卖出</option></select></div>
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">手法</label><select value={formData.type} onChange={e => setFormData({ ...formData, type: e.target.value as TradeType })} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"><option value="追涨">追涨</option><option value="低吸">低吸</option><option value="反包">反包</option><option value="潜伏">潜伏</option><option value="止盈">止盈</option><option value="止损">止损</option></select></div>
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">成交价</label><input type="number" step="0.01" value={formData.price || ''} onChange={e => setFormData({ ...formData, price: +e.target.value })} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none" /></div>
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">数量</label><input type="number" value={formData.quantity || ''} onChange={e => setFormData({ ...formData, quantity: +e.target.value })} className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none" /></div>
                  <div><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">关联龙头</label><input type="text" value={formData.linkedDragon} onChange={e => setFormData({ ...formData, linkedDragon: e.target.value })} placeholder="如：某龙头" className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none" /></div>
                  <div className="md:col-span-2"><label className="text-[10px] font-black text-gray-500 uppercase block mb-1">备注</label><input type="text" value={formData.notes} onChange={e => setFormData({ ...formData, notes: e.target.value })} placeholder="可选备注" className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none" /></div>
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowAddForm(false)} className="px-4 py-2 bg-white/10 text-gray-400 rounded-lg text-xs font-black">取消</button>
                  <button onClick={handleSubmit} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-black">确认录入</button>
                </div>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-3 px-3 text-gray-500 font-black uppercase">日期</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-black uppercase">代码</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-black uppercase">操作</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-black uppercase">类型</th>
                    <th className="text-right py-3 px-3 text-gray-500 font-black uppercase">价格</th>
                    <th className="text-right py-3 px-3 text-gray-500 font-black uppercase">数量</th>
                    <th className="text-right py-3 px-3 text-gray-500 font-black uppercase">盈亏</th>
                    <th className="text-center py-3 px-3 text-gray-500 font-black uppercase">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.length === 0 ? (
                    <tr><td colSpan={8} className="text-center py-8 text-gray-600 font-black">暂无交易记录</td></tr>
                  ) : (
                    trades.slice(0, 20).map((trade: any) => (
                      <tr key={trade.id} className="border-b border-white/5 hover:bg-white/5">
                        <td className="py-3 px-3 text-gray-400 font-black">{trade.date}</td>
                        <td className="py-3 px-3 text-white font-black">{trade.stockCode}</td>
                        <td className="py-3 px-3"><span className={`px-2 py-0.5 rounded text-[10px] font-black ${trade.action === 'buy' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>{trade.action === 'buy' ? '买入' : '卖出'}</span></td>
                        <td className="py-3 px-3 text-gray-400 font-black">{trade.type}</td>
                        <td className="py-3 px-3 text-right text-white font-black">{trade.price.toFixed(2)}</td>
                        <td className="py-3 px-3 text-right text-white font-black">{trade.quantity}</td>
                        <td className="py-3 px-3 text-right">
                          {trade.profitRate !== undefined && (<span className={`font-black ${trade.profitRate >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>{trade.profitRate >= 0 ? '+' : ''}{trade.profitRate.toFixed(2)}%</span>)}
                        </td>
                        <td className="py-3 px-3 text-center"><button onClick={() => onDeleteTrade(trade.id)} className="text-gray-600 hover:text-red-400 transition-colors"><Trash2 size={14} /></button></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'position' && (
          <div className="space-y-4">
            <h3 className="text-sm font-black text-white">当前持仓</h3>
            {positions.length === 0 ? (
              <div className="text-center py-12 text-gray-600 font-black">暂无持仓</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {positions.map((pos: any) => (
                  <div key={pos.id} className="bg-white/5 border border-white/10 rounded-xl p-4 border-l-4 border-l-red-500">
                    <div className="flex justify-between items-start mb-3">
                      <div><span className="text-lg font-black text-white">{pos.stockCode}</span><span className="text-xs text-gray-500 ml-2">{pos.buyType}</span></div>
                      <span className={`text-sm font-black ${(pos.profitRate || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>{(pos.profitRate || 0) >= 0 ? '+' : ''}{(pos.profitRate || 0).toFixed(2)}%</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div><span className="text-gray-500 block">买入价</span><span className="text-white font-black">{pos.buyPrice.toFixed(2)}</span></div>
                      <div><span className="text-gray-500 block">现价</span><span className="text-white font-black">{(pos.currentPrice || pos.buyPrice).toFixed(2)}</span></div>
                      <div><span className="text-gray-500 block">数量</span><span className="text-white font-black">{pos.quantity}</span></div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-white/5 flex justify-between text-xs">
                      <span className="text-gray-500">{pos.buyDate}</span>
                      <span className="text-gray-500">盈亏: <span className={(pos.profit || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}>{(pos.profit || 0) >= 0 ? '+' : ''}{(pos.profit || 0).toFixed(2)}</span></span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="space-y-6">
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2"><BarChart3 size={16} className="text-emerald-500" /> 战绩统计</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center"><div className="text-2xl font-black text-white">{stats.totalTrades}</div><div className="text-[10px] text-gray-500 uppercase font-black">总交易次数</div></div>
                <div className="text-center"><div className="text-2xl font-black text-red-400">{stats.winRate.toFixed(1)}%</div><div className="text-[10px] text-gray-500 uppercase font-black">胜率</div></div>
                <div className="text-center"><div className="text-2xl font-black text-blue-400">{stats.profitLossRatio.toFixed(2)}:1</div><div className="text-[10px] text-gray-500 uppercase font-black">盈亏比</div></div>
                <div className="text-center"><div className="text-2xl font-black text-emerald-400">+{stats.avgProfit.toFixed(1)}%</div><div className="text-[10px] text-gray-500 uppercase font-black">平均盈利</div></div>
                <div className="text-center"><div className="text-2xl font-black text-gray-400">{currentStage || '待研判'}</div><div className="text-[10px] text-gray-500 uppercase font-black">当前周期</div></div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2"><ArrowUpRight size={16} className="text-red-500" /> 买点类型分布</h3>
                {buyDistribution.length === 0 ? <div className="text-center py-8 text-gray-600 font-black text-xs">暂无数据</div> : (
                  <div className="flex items-center gap-4">
                    <div className="w-32 h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart><Pie data={buyDistribution} dataKey="count" nameKey="type" cx="50%" cy="50%" innerRadius={30} outerRadius={50}>{buyDistribution.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}</Pie></PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-2">
                      {buyDistribution.map((item: any, index: number) => (
                        <div key={item.type} className="flex items-center justify-between">
                          <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} /><span className="text-xs text-gray-400 font-black">{item.type}</span></div>
                          <span className="text-xs text-white font-black">{item.percentage.toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2"><ArrowDownRight size={16} className="text-emerald-500" /> 卖点类型分布</h3>
                {sellDistribution.length === 0 ? <div className="text-center py-8 text-gray-600 font-black text-xs">暂无数据</div> : (
                  <div className="flex items-center gap-4">
                    <div className="w-32 h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart><Pie data={sellDistribution} dataKey="count" nameKey="type" cx="50%" cy="50%" innerRadius={30} outerRadius={50}>{sellDistribution.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}</Pie></PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-2">
                      {sellDistribution.map((item: any, index: number) => (
                        <div key={item.type} className="flex items-center justify-between">
                          <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} /><span className="text-xs text-gray-400 font-black">{item.type}</span></div>
                          <span className="text-xs text-white font-black">{item.percentage.toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <div className="text-[10px] text-gray-500 uppercase font-black mb-2">最佳交易</div>
                <div className="text-xl font-black text-red-400">+{stats.bestTrade.toFixed(2)}%</div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                <div className="text-[10px] text-gray-500 uppercase font-black mb-2">最差交易</div>
                <div className="text-xl font-black text-emerald-400">-{stats.worstTrade.toFixed(2)}%</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [review, setReview] = useState<MarketReview>(INITIAL_REVIEW);
  const [history, setHistory] = useState<MarketReview[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [showFileManager, setShowFileManager] = useState(false);
  const [showTradeManager, setShowTradeManager] = useState(false);
  const [aiProvider, setAiProvider] = useState<'gemini' | 'zhipu' | 'minimax' | 'qianwen'>('zhipu');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileImportRef = useRef<HTMLInputElement>(null);

  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [toasts, setToasts] = useState<{ id: string; msg: string; type: 'ok' | 'err' | 'info' }[]>([]);

  const showToast = (msg: string, type: 'ok' | 'err' | 'info' = 'info') => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  };

  useEffect(() => {
    const savedTrades = localStorage.getItem(TRADE_STORAGE_KEY);
    if (savedTrades) setTrades(JSON.parse(savedTrades));
    const savedPositions = localStorage.getItem(POSITION_STORAGE_KEY);
    if (savedPositions) setPositions(JSON.parse(savedPositions));
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) setHistory(JSON.parse(savedHistory));
  }, []);

  const todaysTrades = useMemo(() => trades.filter(t => t.date === review.date), [trades, review.date]);

  const persistentSectors = useMemo(() => {
    const last5 = history.slice(0, 5);
    const currentSectors = review.topSectors.map(s => s.name.trim()).filter(Boolean);
    const historicalSectors = last5.flatMap(h => (h.topSectors || []).map(s => s.name ? s.name.trim() : '').filter(Boolean));
    const allSectors = [...currentSectors, ...historicalSectors];
    const counts: Record<string, number> = {};
    allSectors.forEach(name => { if(name) counts[name] = (counts[name] || 0) + 1; });
    return Object.entries(counts).filter(([_, count]) => count >= 2).sort((a, b) => b[1] - a[1]).map(([name, days]) => ({ name, days }));
  }, [history, review.topSectors]);

  // 交易统计
  const tradeStats = useMemo((): TradeStats => {
    const sellTrades = trades.filter(t => t.action === 'sell' && t.profit !== undefined);
    if (sellTrades.length === 0) return { totalTrades: 0, winCount: 0, loseCount: 0, winRate: 0, avgProfit: 0, avgLoss: 0, profitLossRatio: 0, bestTrade: 0, worstTrade: 0, currentCycle: review.stage || '待研判' };
    const wins = sellTrades.filter(t => (t.profit || 0) > 0);
    const losses = sellTrades.filter(t => (t.profit || 0) <= 0);
    const profits = wins.map(t => t.profitRate || 0);
    const lossesRates = losses.map(t => Math.abs(t.profitRate || 0));
    return {
      totalTrades: sellTrades.length, winCount: wins.length, loseCount: losses.length,
      winRate: (wins.length / sellTrades.length) * 100,
      avgProfit: profits.length > 0 ? profits.reduce((a, b) => a + b, 0) / profits.length : 0,
      avgLoss: lossesRates.length > 0 ? lossesRates.reduce((a, b) => a + b, 0) / lossesRates.length : 0,
      profitLossRatio: lossesRates.length > 0 && profits.length > 0 ? (profits.reduce((a, b) => a + b, 0) / profits.length) / (lossesRates.reduce((a, b) => a + b, 0) / lossesRates.length) : 0,
      bestTrade: profits.length > 0 ? Math.max(...profits) : 0,
      worstTrade: lossesRates.length > 0 ? Math.min(...lossesRates) : 0, currentCycle: review.stage || '待研判'
    };
  }, [trades, review.stage]);

  const buyTypeDistribution = useMemo(() => {
    const buyTrades = trades.filter(t => t.action === 'buy');
    if (buyTrades.length === 0) return [];
    const types: Record<string, number> = {};
    buyTrades.forEach(t => types[t.type] = (types[t.type] || 0) + 1);
    return Object.entries(types).map(([type, count]) => ({ type, count, percentage: (count / buyTrades.length) * 100 }));
  }, [trades]);

  const sellTypeDistribution = useMemo(() => {
    const sellTrades = trades.filter(t => t.action === 'sell');
    if (sellTrades.length === 0) return [];
    const types: Record<string, number> = {};
    sellTrades.forEach(t => types[t.type] = (types[t.type] || 0) + 1);
    return Object.entries(types).map(([type, count]) => ({ type, count, percentage: (count / sellTrades.length) * 100 }));
  }, [trades]);

  // 图表数据
  const chartData = useMemo(() => {
    return [...history].reverse().map(h => ({
      date: h.date.substring(5),
      score: h.score,
      volume: h.totalVol,
      stage: h.stage
    }));
  }, [history]);

  const exportAllData = () => {
    const backup = { history, trades, positions };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `龙头信仰_全量备份_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const importAllData = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        if (data.history) { setHistory(data.history); safeStorage.set(STORAGE_KEY, data.history); }
        if (data.trades) { setTrades(data.trades); safeStorage.set(TRADE_STORAGE_KEY, data.trades); }
        if (data.positions) { setPositions(data.positions); safeStorage.set(POSITION_STORAGE_KEY, data.positions); }
        showToast('数据恢复成功', 'ok');
      } catch (err) {
        showToast('备份文件格式错误', 'err');
      }
    };
    reader.readAsText(file);
    if (fileImportRef.current) fileImportRef.current.value = '';
  };

  const parseExcelFile = (file: File): Promise<any> => {
    return new Promise((resolve, reject) => {
      const isOldExcel = file.name.toLowerCase().endsWith('.xls');
      if (isOldExcel) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = e.target?.result;
            const workbook = XLSX.read(data, { type: 'array' });
            const result: any = {};
            workbook.SheetNames.forEach(sheetName => {
              const sheet = workbook.Sheets[sheetName];
              const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
              result[sheetName] = jsonData;
            });
            resolve(result);
          } catch (error) { reject(error); }
        };
        reader.onerror = reject; reader.readAsArrayBuffer(file);
      } else {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = e.target?.result;
            const workbook = XLSX.read(data, { type: 'array' });
            const result: any = {};
            workbook.SheetNames.forEach(sheetName => {
              const sheet = workbook.Sheets[sheetName];
              const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1 });
              result[sheetName] = jsonData;
            });
            resolve(result);
          } catch (error) { reject(error); }
        };
        reader.onerror = reject; reader.readAsArrayBuffer(file);
      }
    });
  };

  const extractMarketData = (excelData: any, historyData?: MarketReview[]): Partial<MarketReview> => {
    const result: any = {};
    const findSheet = (keywords: string[]): any[] => {
      const keys = Object.keys(excelData);
      for (const kw of keywords) {
        const found = keys.find(k => k.includes(kw));
        if (found) {
          const data = excelData[found] as any;
          if (Array.isArray(data)) return data;
          if (data && typeof data === 'object') {
            const values = Object.values(data);
            if (Array.isArray(values[0])) return values[0];
          }
        }
      }
      return [];
    };
    const findColIndex = (header: any[], keywords: string[]): number => {
      if (!Array.isArray(header)) return -1;
      for (let i = 0; i < header.length; i++) {
        if (keywords.some(kw => String(header[i] || '').includes(kw))) return i;
      }
      return -1;
    };

    const indexSheet = findSheet(['沪深京主要指数', '沪深京', '指数']);
    if (indexSheet && indexSheet.length > 1) {
      const indexKeys = [
        { key: '上证指数', display: '上证' }, { key: '深证成指', display: '深成' },
        { key: '创业板指', display: '创业' }, { key: '科创50', display: '科创' },
        { key: '沪深300', display: '沪深300' }, { key: '中证1000', display: '中证1000' },
        { key: '中证2000', display: '中证2000' }, { key: '微盘股', display: '微盘股' },
      ];
      const headerRow = indexSheet[0];
      const nameIdx = findColIndex(headerRow, ['名称']);
      const priceIdx = findColIndex(headerRow, ['现价', '最新']);
      const changeIdx = findColIndex(headerRow, ['涨跌幅']);

      const rowDataList: any[] = [];
      indexSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const name = nameIdx >= 0 ? String(rowArr[nameIdx] || '').trim() : String(rowArr[1] || '').trim();
        if (!name) return;
        const value = priceIdx >= 0 ? Math.round(parseFloat(String(rowArr[priceIdx])) || 0) : Math.round(parseFloat(String(rowArr[2])) || 0);
        const change = changeIdx >= 0 ? parseFloat(String(rowArr[changeIdx])) || 0 : parseFloat(String(rowArr[4])) || 0;
        rowDataList.push({ name, value, change });
      });

      result.indices = indexKeys.map(({ key, display }) => {
        const exactMatch = rowDataList.find(r => r.name === key);
        if (exactMatch) return { name: display, value: exactMatch.value, change: exactMatch.change, ma5Status: 'above' };
        const fuzzyMatch = rowDataList.find(r => r.name.includes(key) || key.includes(r.name));
        if (fuzzyMatch) return { name: display, value: fuzzyMatch.value, change: fuzzyMatch.change, ma5Status: 'above' };
        return { name: display, value: 0, change: 0, ma5Status: 'above' };
      });
    }

    const allStockSheet = findSheet(['全部Ａ股', 'Ａ股', 'A股', '全部A股']);
    if (allStockSheet && allStockSheet.length > 1) {
      let upCount = 0, downCount = 0, limitUp = 0, limitDown = 0, totalAmount = 0;
      const headerRow = allStockSheet[0];
      const nameIdx = findColIndex(headerRow, ['名称', '股票名称', '证券简称']);
      const codeIdx = findColIndex(headerRow, ['代码', '证券代码']);
      const changeIdx = findColIndex(headerRow, ['涨幅%', '涨幅']);
      const amountIdx = findColIndex(headerRow, ['总金额', '成交额', '金额', '总成交']);
      const change10Idx = findColIndex(headerRow, ['10日涨幅%', '10日涨跌幅%']);
      const turnoverZIdx = findColIndex(headerRow, ['换手Z']);

      const stockData: any[] = [];
      allStockSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const stockName = nameIdx >= 0 ? String(rowArr[nameIdx] || '') : String(rowArr[1] || '');
        const stockCode = codeIdx >= 0 ? String(rowArr[codeIdx] || '') : String(rowArr[0] || '');
        const isST = /^(ST|\*ST|S[PT]?|S\-)/i.test(stockName) || /^(ST|\*ST|S[PT]?|S\-)/i.test(stockCode) || /S[0-9]{3}/i.test(stockCode);
        if (isST) return;

        const change = changeIdx >= 0 ? parseFloat(String(rowArr[changeIdx])) || 0 : parseFloat(String(rowArr[3])) || 0;
        const amount = amountIdx >= 0 ? parseFloat(String(rowArr[amountIdx]).replace(/,/g, '')) || 0 : 0;
        const change10 = change10Idx >= 0 ? parseFloat(String(rowArr[change10Idx])) || 0 : 0;
        const turnoverZ = turnoverZIdx >= 0 ? parseFloat(String(rowArr[turnoverZIdx])) || 0 : 0;

        if (change > 0) upCount++;
        if (change < 0) downCount++;
        if (change >= 9.8) limitUp++;
        if (change <= -9.8) limitDown++;
        totalAmount += amount;

        stockData.push({ name: stockName, code: stockCode, change10, turnoverZ, amount });
      });

      result.totalVol = Math.round(totalAmount / 100000000 * 100) / 100;
      if (historyData && historyData.length > 0 && historyData[0].totalVol > 0) {
        result.volDelta = Math.round((result.totalVol - historyData[0].totalVol) * 100) / 100;
      }
      result.limitUpTotal = limitUp; result.limitDownTotal = limitDown; result.upDownCount = { up: upCount, down: downCount };

      if (change10Idx >= 0 && turnoverZIdx >= 0 && amountIdx >= 0) {
        const top40 = stockData.sort((a, b) => b.change10 - a.change10).slice(0, 40);
        const filtered = top40.filter(s => s.turnoverZ < 30);
        if (filtered.length > 0) result.midArmy = filtered.sort((a, b) => b.amount - a.amount)[0].name;
      }
    }

    const shortTermSheet = findSheet(['短线宝']);
    if (shortTermSheet && shortTermSheet.length > 1) {
      const ladder: Record<string, any> = {
        '5+': { count: 0, stock: '', concept: '', promoRate: 0 },
        '5': { count: 0, stock: '', concept: '', promoRate: 0 },
        '4': { count: 0, stock: '', concept: '', promoRate: 0 },
        '3': { count: 0, stock: '', concept: '', promoRate: 0 },
        '2': { count: 0, stock: '', concept: '', promoRate: 0 },
        '1': { count: 0, stock: '', concept: '', promoRate: 0 },
      };

      let brokenCount = 0;
      const headerRow = shortTermSheet[0];
      const nameIdx = findColIndex(headerRow, ['名称']);
      const daysIdx = findColIndex(headerRow, ['连板天']);
      const brokenIdx = findColIndex(headerRow, ['封板___开板数', '开板']);
      const lastSealIdx = findColIndex(headerRow, ['封板___最后', '最后']);

      const stocksByBoard: Record<string, any[]> = {};
      shortTermSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const name = nameIdx >= 0 ? String(rowArr[nameIdx] || '') : String(rowArr[1] || '');
        const lastSealTime = lastSealIdx >= 0 ? String(rowArr[lastSealIdx] || '') : '';
        const daysVal = daysIdx >= 0 ? rowArr[daysIdx] : rowArr[5];
        const days = typeof daysVal === 'number' ? daysVal : (daysVal && daysVal !== '--  ' ? parseInt(String(daysVal).replace(/[^0-9]/g, '')) || 0 : 0);

        if (days >= 1) {
          let key = days >= 6 ? '5+' : String(days);
          if (!stocksByBoard[key]) { stocksByBoard[key] = []; if(!ladder[key]) ladder[key] = { count: 0, stock: '', concept: '', promoRate: 0 }; }
          stocksByBoard[key].push({ name, days, lastSealTime });
          ladder[key].count++;
        }
        const broken = brokenIdx >= 0 ? parseFloat(String(rowArr[brokenIdx])) || 0 : 0;
        if (broken > 0) brokenCount++;
      });

      const parseTime = (timeStr: string): number => {
        if (!timeStr || timeStr === '--  ' || timeStr === '') return 999999;
        const match = timeStr.match(/(\d{1,2}):(\d{2})/);
        if (match) return parseInt(match[1]) * 60 + parseInt(match[2]);
        const num = parseFloat(timeStr);
        if (!isNaN(num)) return num * 100000;
        return 999999;
      };

      Object.keys(stocksByBoard).forEach(key => {
        const sorted = stocksByBoard[key].sort((a, b) => {
          if (b.days !== a.days) return b.days - a.days;
          return parseTime(a.lastSealTime) - parseTime(b.lastSealTime);
        });
        ladder[key] = { count: sorted.length, stock: sorted[0]?.name || '', concept: '', promoRate: 0 };
      });

      result.brokenRate = result.limitUpTotal ? parseFloat(((brokenCount / (result.limitUpTotal + brokenCount)) * 100).toFixed(1)) : 0;
      result.ladder = ladder;
    }

    const sectorSheet = findSheet(['板块指数', '板块', '行业', '概念', '题材']);
    if (sectorSheet && sectorSheet.length > 1) {
      const headerRow = sectorSheet[0];
      const nameIdx = findColIndex(headerRow, ['名称', '板块名称']);
      const gainIdx = findColIndex(headerRow, ['涨幅', '涨跌幅']);
      const limitIdx = findColIndex(headerRow, ['涨停数', '涨停']);
      const volIdx = findColIndex(headerRow, ['成交额', '金额', '总金额']);

      const sectorData: any[] = [];
      sectorSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const name = nameIdx >= 0 ? String(rowArr[nameIdx] || '').trim() : String(rowArr[1] || '').trim();
        if (!name) return;
        const gain = gainIdx >= 0 ? parseFloat(String(rowArr[gainIdx])) || 0 : 0;
        const limitUps = limitIdx >= 0 ? parseInt(String(rowArr[limitIdx])) || 0 : 0;
        const volume = volIdx >= 0 ? parseFloat(String(rowArr[volIdx]).replace(/,/g, '')) || 0 : 0;
        sectorData.push({ name, gain, limitUps, volume });
      });

      result.topSectors = sectorData.sort((a, b) => b.limitUps - a.limitUps).slice(0, 3).map(s => ({
          name: s.name, gain: s.gain, limitUps: s.limitUps, volume: Math.round(s.volume / 10000)
      }));
    }
    return result;
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles: UploadedFile[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        try {
          const excelData = await parseExcelFile(file);
          newFiles.push({ name: file.name, mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', data: JSON.stringify(excelData), isExcel: true });
        } catch (error) { showToast(`解析 ${file.name} 失败`, 'err'); }
      } else {
        const reader = new FileReader();
        const base64Promise = new Promise<string>((resolve) => {
          reader.onload = () => resolve(reader.result?.toString().split(',')[1] || '');
          reader.readAsDataURL(file);
        });
        const base64 = await base64Promise;
        newFiles.push({ name: file.name, mimeType: file.type, data: base64, preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined });
      }
    }
    setUploadedFiles(prev => [...prev, ...newFiles].slice(-10));
  };

  const handleSave = () => {
    const calculatePersistentSectors = (historyData: MarketReview[], currentReview: MarketReview) => {
      const last5 = [currentReview, ...historyData.slice(0, 4)];
      const sectorCounts: Record<string, number> = {};
      last5.forEach(day => { day.topSectors?.forEach(sector => { if (sector.name) sectorCounts[sector.name] = (sectorCounts[sector.name] || 0) + 1; }); });
      return Object.entries(sectorCounts).filter(([_, count]) => count >= 2).sort((a, b) => b[1] - a[1]).map(([name, days]) => ({ name, days }));
    };
    const persistent = calculatePersistentSectors(history, review);
    const updatedReview = { ...review, persistentSectors: persistent };
    const newHistory = [updatedReview, ...history.filter(h => h.date !== review.date)].sort((a,b) => b.date.localeCompare(a.date));
    setHistory(newHistory);
    safeStorage.set(STORAGE_KEY, newHistory);
    setIsDirty(false);
    showToast('今日复盘已归档至信仰库', 'ok');
  };

  const handleSnapshot = async () => {
    setIsLoading(true); setStatusMsg("正在生成网页快照...");
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      const fullWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
      const fullHeight = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
      const canvas = await html2canvas(document.documentElement, {
        scale: 2, useCORS: true, logging: false, backgroundColor: '#0a0a0a',
        width: fullWidth, height: fullHeight, x: 0, y: 0, scrollY: 0, scrollX: 0,
        windowWidth: fullWidth, windowHeight: fullHeight,
      });
      const blob = await new Promise<Blob>((resolve) => canvas.toBlob((b) => resolve(b!), 'image/png'));
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url; link.download = `龙头信仰_${review.date}.png`; link.click();
      URL.revokeObjectURL(url);
    } catch (error) { showToast('网页快照生成失败，请重试', 'err'); } finally { setIsLoading(false); }
  };

  const addTrade = (trade: Omit<TradeRecord, 'id'>) => {
    const newTrades = [{ ...trade, id: Date.now().toString() }, ...trades];
    setTrades(newTrades); safeStorage.set(TRADE_STORAGE_KEY, newTrades);
    if (trade.action === 'sell') {
      setPositions(prev => {
        // FIFO：仅移除最早的一条匹配持仓，支持同标的多次买入
        const idx = prev.findIndex(p => p.stockCode === trade.stockCode);
        if (idx === -1) return prev;
        const np = [...prev.slice(0, idx), ...prev.slice(idx + 1)];
        safeStorage.set(POSITION_STORAGE_KEY, np);
        return np;
      });
    }
  };

  const addPosition = (pos: Omit<Position, 'id'>) => {
    const np = [...positions, { ...pos, id: Date.now().toString() }];
    setPositions(np); safeStorage.set(POSITION_STORAGE_KEY, np);
  };

  const deleteTrade = (id: string) => {
    const newTrades = trades.filter(t => t.id !== id);
    setTrades(newTrades); safeStorage.set(TRADE_STORAGE_KEY, newTrades);
  };

  const updatePositionPrice = (stockCode: string, currentPrice: number) => {
    setPositions(prev => {
      const np = prev.map(p => {
        if (p.stockCode === stockCode) {
          const profit = (currentPrice - p.buyPrice) * p.quantity;
          const profitRate = ((currentPrice - p.buyPrice) / p.buyPrice) * 100;
          return { ...p, currentPrice, profit, profitRate };
        }
        return p;
      });
      safeStorage.set(POSITION_STORAGE_KEY, np);
      return np;
    });
  };

  // 剥离 AI 回包中的 markdown 代码块包装，提升 JSON.parse 容错率
  const stripMarkdownJson = (text: string): string => {
    const match = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    return match ? match[1].trim() : text.trim();
  };

  const callAIProvider = async (prompt: string, files?: UploadedFile[]) => {
    if (aiProvider === 'zhipu') {
      const apiKey = import.meta.env.VITE_ZHIPU_API_KEY;
      if (!apiKey) throw new Error("智谱 API Key 未配置，请在 Vercel 控制台 → Settings → Environment Variables 添加 VITE_ZHIPU_API_KEY");
      if (files && files.length > 0) {
        showToast('智谱不支持图片/文件附件，已忽略附件仅做文本分析', 'info');
      }
      const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
        body: JSON.stringify({
          model: "glm-4-flash",
          messages: [
            { role: "system", content: STOCK_TRADER_PERSONA },
            { role: "user", content: prompt }
          ]
        })
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error.message);
      return stripMarkdownJson(data.choices?.[0]?.message?.content || "");
    } else if (aiProvider === 'minimax') {
      const apiKey = import.meta.env.VITE_MINIMAX_API_KEY;
      if (!apiKey) throw new Error("MiniMax API Key 未配置，请在 Vercel 控制台 → Settings → Environment Variables 添加 VITE_MINIMAX_API_KEY");
      if (files && files.length > 0) showToast('MiniMax 不支持图片/文件附件，已忽略附件仅做文本分析', 'info');
      const response = await fetch('https://api.minimax.chat/v1/text/chatcompletion_v2', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
        body: JSON.stringify({
          model: "MiniMax-Text-01",
          messages: [
            { role: "system", content: STOCK_TRADER_PERSONA },
            { role: "user", content: prompt }
          ]
        })
      });
      const data = await response.json();
      if (data.base_resp?.status_code && data.base_resp.status_code !== 0) throw new Error(data.base_resp.status_msg);
      return stripMarkdownJson(data.choices?.[0]?.message?.content || "");
    } else if (aiProvider === 'qianwen') {
      const apiKey = import.meta.env.VITE_QIANWEN_API_KEY;
      if (!apiKey) throw new Error("千问 API Key 未配置，请在 Vercel 控制台 → Settings → Environment Variables 添加 VITE_QIANWEN_API_KEY");
      if (files && files.length > 0) showToast('千问不支持图片/文件附件，已忽略附件仅做文本分析', 'info');
      const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
        body: JSON.stringify({
          model: "qwen-turbo",
          messages: [
            { role: "system", content: STOCK_TRADER_PERSONA },
            { role: "user", content: prompt }
          ]
        })
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error.message);
      return stripMarkdownJson(data.choices?.[0]?.message?.content || "");
    } else {
      const apiKey = import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_API_KEY;
      if (!apiKey) throw new Error("Gemini API Key 未配置，请在 Vercel 控制台 → Settings → Environment Variables 添加 VITE_GEMINI_API_KEY");
      const ai = new GoogleGenAI({ apiKey });
      const config = { responseMimeType: "text/plain", systemInstruction: STOCK_TRADER_PERSONA };
      if (files && files.length > 0) {
        const parts: any[] = [{ text: prompt }];
        files.forEach(file => parts.push({ inlineData: { mimeType: file.mimeType, data: file.data } }));
        const response = await ai.models.generateContent({ model: "gemini-2.0-flash", contents: { parts }, config });
        return stripMarkdownJson(response.text || "");
      } else {
        const response = await ai.models.generateContent({ model: "gemini-2.0-flash", contents: prompt, config });
        return stripMarkdownJson(response.text || "");
      }
    }
  };

  const autoFillMarketData = async () => {
    if (isLoading || uploadedFiles.length === 0) return;
    setIsLoading(true); setStatusMsg("正在解析Excel数据...");
    const excelFiles = uploadedFiles.filter(f => f.mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || f.name.endsWith('.xlsx') || f.name.endsWith('.xls'));
    if (excelFiles.length > 0 && excelFiles[0]?.data) {
      try {
        const allExcelData: Record<string, any> = {};
        for (const file of excelFiles) {
          try {
            const parsedData = JSON.parse(file.data);
            let matched = false;
            if (file.name.includes('短线宝')) { allExcelData['短线宝'] = parsedData; matched = true; }
            else if (file.name.includes('板块') || file.name.includes('行业') || file.name.includes('概念')) { allExcelData['板块指数'] = parsedData; matched = true; }
            else if (file.name.includes('Ａ股') || file.name.includes('A股') || file.name.includes('两融')) { allExcelData['全部Ａ股'] = parsedData; matched = true; }
            else if (file.name.includes('沪深京') || file.name.includes('大盘') || file.name.includes('指数')) { allExcelData['沪深京主要指数'] = parsedData; matched = true; }
            if (!matched && Object.keys(parsedData).length > 0) allExcelData['全部Ａ股'] = parsedData;
          } catch (e) { console.error('[Excel文件解析错误]', (e as Error).message); }
        }
        if (Object.keys(allExcelData).length > 0) {
          const extractedData = extractMarketData(allExcelData, history);
          const ladder = extractedData.ladder || {};
          let dragonStock = ladder['5+']?.stock || ladder['5']?.stock || ladder['4']?.stock || ladder['3']?.stock || ladder['2']?.stock || ladder['1']?.stock || '';
          setReview(prev => ({ ...prev, ...extractedData, dragon: dragonStock || prev.dragon, midArmy: extractedData.midArmy || prev.midArmy, aiAnalysis: `✅ Excel数据解析完成！\n- 涨停数: ${extractedData.limitUpTotal}家\n- 跌停数: ${extractedData.limitDownTotal}家\n- 上涨家数: ${extractedData.upDownCount?.up || 0}家\n- 下跌家数: ${extractedData.upDownCount?.down || 0}家\n- 炸板率: ${extractedData.brokenRate}%\n\n请手动补充或确认梯队核心，随后启动盘手研判。` }));
          setShowFileManager(false); setIsLoading(false); return;
        }
      } catch (e) { setStatusMsg(`Excel数据提取失败: ${(e as Error).message}`); }
    }

    setStatusMsg("正在通过AI解构原始信源数据...");
    try {
      const prompt = `你是一个精通A股复盘的数据专家。解析附件内容并填充复盘JSON。指数部分仅提取收盘点位。请直接输出JSON，不要其他内容。`;
      const responseText = await callAIProvider(prompt, uploadedFiles);
      const data = JSON.parse(responseText || "{}");
      setReview(prev => ({ ...prev, ...data, aiAnalysis: "信源同步完成。建议立即进行周期定性分析。" }));
      setShowFileManager(false);
    } catch (e) { showToast('自动填充失败，请检查文件格式', 'err'); } finally { setIsLoading(false); }
  };

  // ✅ 核心业务引擎：量化情绪周期分析
  const analyzeSentimentCycle = async () => {
    if (isLoading) return;
    setIsLoading(true); setStatusMsg("盘手正在启动量化情绪引擎进行深度推演...");
    try {
      // ✅ 修复 2：绝对安全的降维排序法则（防止 NaN 和超出 5板的乱序）
      const ladderSummary = (Object.entries(review.ladder) as [string, typeof review.ladder[string]][])
        .filter(([_, data]) => data.stock || data.count > 0)
        .sort((a, b) => {
          const numA = a[0] === '5+' ? 999 : parseInt(a[0]) || 0;
          const numB = b[0] === '5+' ? 999 : parseInt(b[0]) || 0;
          return numB - numA;
        })
        .map(([lvl, data]) => `[${lvl}板]: 核心【${data.stock || '空缺'}】 (共${data.count}家, 晋级率${data.promoRate}%)`)
        .join('\n  ');

      const sectorSummary = review.topSectors
        .filter(s => s.name)
        .map(s => `${s.name} (涨停${s.limitUps}家, 量能${s.volume}亿, 板块涨幅${s.gain}%)`)
        .join(' | ');

      const prompt = `作为顶级量化『股市盘手』，请基于以下今日A股收盘核心数据，执行最高级别的复盘推演与仓位指导。

### 【今日量化数据扫描】
- 水位因子：成交额 ${review.totalVol} 万亿 (较昨日 ${review.volDelta >= 0 ? '+' : ''}${review.volDelta} 万亿)。
- 情绪因子：涨停 ${review.limitUpTotal} 家，跌停 ${review.limitDownTotal} 家，炸板率 ${review.brokenRate}%。净多头差值：${review.limitUpTotal - review.limitDownTotal}家。
- 资金聚焦主线：${sectorSummary || '无明显聚集效应'}。
- 空间连板阵型 (观测断层与溢价)：
  ${ladderSummary || '梯队严重断层/无连板效应'}
- 我锁定的核心资产：情绪龙头【${review.dragon || '未确认'}】(状态: ${review.dragonStatus})；容量中军【${review.midArmy || '未确认'}】。
- 我的今日实盘操作：${todaysTrades.length > 0 ? todaysTrades.map(t => `${t.action === 'buy' ? '买入' : '卖出'} ${t.stockCode} (${t.type})`).join('；') : '今日严格空仓防守'}。

---
### 【量化推演指令】（严格按以下Markdown格式输出）

#### 🔴 周期定性节点
(必须且仅能输出一个词：【启动期】/【发酵期】/【高潮期】/【分化期】/【退潮期】/【冰点期】/【混沌期】。请结合涨跌停差值、炸板率、量能变化，给出量化视角的定性理由。)

#### ⚔️ 阵型与情绪溢价分析
(运用连板梯队数据，分析今天的"涨停溢价"。哪个梯位的晋级率出现了严重断层？是高位A杀退潮，还是低位试错活跃？哪条题材是真主线？)

#### 🐉 绝对龙头指引
(基于提供的数据，对我填写的龙头进行量化审视。我选的对吗？如果市场处于退潮，它明天是被核按钮还是能弱转强？指出全场真正具备"空间/容量"统治力的标的。)

#### ⚖️ 知行合一拷问
(结合量化周期，无情审视我今天的实盘操作[${todaysTrades.length > 0 ? '见上文' : '空仓'}]。在当前的周期阶段做这种操作，盈亏比是否合理？如果是退潮期追高，请狠狠羞辱我的纪律；做对则简短肯定。)

#### 🛡️ 明日量化仓位与剧本 (Script & Sizing)
(必须给出明确的实战指导。
1. 建议总仓位限制：（如：0-1成 / 3成 / 8成）。
2. 具体交易剧本：方向上聚焦哪个梯位？手法是做龙头弱转强，做高低切、还是坚决空仓避险？给出清晰的买卖触发条件。)`;

      const res = await callAIProvider(prompt);

      // ✅ 修复 3：放宽正则表达式边界，提升容错率
      const stageMatch = res.match(/(启动|发酵|高潮|分化|退潮|冰点|混沌)期/);
      const stage = stageMatch ? `${stageMatch[1]}期` : "混沌期";

      setReview(prev => ({ ...prev, stage, aiAnalysis: res }));
    } catch (e) {
      showToast('研判推演异常: ' + (e as Error).message, 'err');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060608] text-[#d1d5db] font-sans">
      <header className="sticky top-0 z-[100] bg-black/50 backdrop-blur-xl border-b border-white/5 h-16 flex items-center px-8 justify-between shadow-2xl">
         <div className="flex items-center gap-2 group cursor-default">
            <div className="w-8 h-8 bg-red-600 rounded-lg flex items-center justify-center shadow-lg shadow-red-600/20 group-hover:rotate-12 transition-transform">
              <Flame size={18} className="text-white fill-white" />
            </div>
            <div>
              <h1 className="text-lg font-black tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">龙头信仰 <span className="text-red-500 text-[10px]">V32.0 Quant</span></h1>
              <div className="flex items-center gap-1.5 -mt-1">
                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[9px] font-black text-gray-500 uppercase">Decision terminal</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-xl border border-white/10">
            <Calendar size={12} className="text-gray-500" />
            <input type="date" value={review.date} onChange={e => { setReview({...review, date: e.target.value}); setIsDirty(true); }} className="bg-transparent border-none text-[11px] font-black outline-none text-gray-300" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowFileManager(true)} className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-[11px] font-black flex items-center gap-2 transition-all">
              <FileUp size={14} /> 信源库
            </button>
            <button onClick={handleSave} className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-red-600/30 flex items-center gap-2 transition-all">
              <Save size={14} /> 存档记录
            </button>
            <button onClick={handleSnapshot} className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-orange-600/30 flex items-center gap-2 transition-all">
              <Camera size={14} /> 网页快照
            </button>
            <button onClick={() => setShowTradeManager(true)} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all">
              <Wallet size={14} /> 交易中心
            </button>
            <div className="flex items-center gap-1.5 bg-white/5 px-3 py-1.5 rounded-xl border border-white/10">
              <span className="text-[9px] font-black text-gray-500 uppercase mr-1">AI引擎:</span>
              {([
                { id: 'zhipu',   label: '智谱', color: 'bg-purple-500/20 text-purple-400 border-purple-500/40' },
                { id: 'minimax', label: 'MiniMax', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40' },
                { id: 'qianwen', label: '千问', color: 'bg-orange-500/20 text-orange-400 border-orange-500/40' },
                { id: 'gemini',  label: 'Gemini', color: 'bg-blue-500/20 text-blue-400 border-blue-500/40' },
              ] as const).map(p => (
                <button key={p.id} onClick={() => setAiProvider(p.id)}
                  className={`px-2 py-0.5 rounded-lg text-[10px] font-black border transition-all ${aiProvider === p.id ? p.color : 'bg-transparent text-gray-600 border-transparent hover:text-gray-400'}`}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1720px] mx-auto px-8 py-10">
        <div className="grid grid-cols-12 gap-10">

          <div className="col-span-12 xl:col-span-4 space-y-10">
            <section className="relative">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">01</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">宏观指数数据</h2>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {review.indices.map((idx, i) => (
                  <div key={i} className="bg-white/[0.03] border border-white/5 p-3 rounded-xl flex flex-col items-center justify-center group hover:bg-white/5 transition-all">
                    <span className="text-[9px] font-black text-gray-600 mb-1">{idx.name}</span>
                    <input type="number" step="0.01" value={idx.value} onChange={e => { const ni = [...review.indices]; ni[i].value = +e.target.value; setReview({...review, indices: ni}); }} className="bg-transparent w-full text-center text-sm font-black text-white outline-none placeholder:text-gray-800" placeholder="点位" />
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white/[0.02] rounded-3xl p-6 border border-white/5 space-y-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">02</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">市场情绪计速器</h2>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-red-500/5 border border-red-500/10 p-5 rounded-2xl flex flex-col">
                  <span className="text-[10px] font-black text-red-500/60 uppercase mb-1">今日涨停</span>
                  <input type="number" value={review.limitUpTotal} onChange={e => { setReview({...review, limitUpTotal: +e.target.value}); setIsDirty(true); }} className="bg-transparent text-3xl font-black text-red-500 outline-none w-full" />
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

              <div className="pt-2 border-t border-white/5 mt-2">
                <div className="flex justify-between items-center mb-3">
                  <label className="text-[10px] font-black text-gray-500 uppercase flex items-center gap-2"><Activity size={10}/> 情绪信仰主观分 (0-100)</label>
                  <span className={`text-lg font-black ${review.score >= 60 ? 'text-red-500' : review.score <= 40 ? 'text-emerald-500' : 'text-yellow-500'}`}>{review.score}</span>
                </div>
                <input type="range" min="0" max="100" value={review.score} onChange={e => setReview({...review, score: +e.target.value})} className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer" />
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">03</div>
                <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">题材主线识别</h2>
              </div>
              <div className="space-y-3">
                {review.topSectors.map((sector, i) => (
                  <div key={i} className="bg-white/[0.02] border border-white/5 p-5 rounded-2xl group hover:border-purple-500/20 transition-all">
                    <input placeholder="板块名称..." value={sector.name} onChange={e => { const ns = [...review.topSectors]; ns[i] = { ...ns[i], name: e.target.value }; setReview({...review, topSectors: ns}); }} className="bg-transparent text-sm font-black outline-none w-full mb-3" />
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">涨幅%</span>
                        <input type="number" step="0.1" value={sector.gain} onChange={e => { const ns = [...review.topSectors]; ns[i] = { ...ns[i], gain: +e.target.value }; setReview({...review, topSectors: ns}); }} className="bg-transparent text-[11px] font-black text-red-500 outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">涨停数</span>
                        <input type="number" value={sector.limitUps} onChange={e => { const ns = [...review.topSectors]; ns[i] = { ...ns[i], limitUps: +e.target.value }; setReview({...review, topSectors: ns}); }} className="bg-transparent text-[11px] font-black text-white outline-none w-full text-center" />
                      </div>
                      <div className="bg-black/40 p-2 text-center rounded-lg border border-white/5">
                        <span className="text-[8px] text-gray-600 block mb-1">量能亿</span>
                        <input type="number" value={sector.volume} onChange={e => { const ns = [...review.topSectors]; ns[i] = { ...ns[i], volume: +e.target.value }; setReview({...review, topSectors: ns}); }} className="bg-transparent text-[11px] font-black text-blue-400 outline-none w-full text-center" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-2xl mt-4">
                <div className="flex items-center gap-2 mb-3">
                  <Timer size={12} className="text-emerald-500" />
                  <span className="text-[10px] font-black text-emerald-500 uppercase">5日持续性主线 (出现≥2次)</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {persistentSectors && persistentSectors.length > 0 ? persistentSectors.map((item: any) => (
                    item && item.name ? (
                      <span key={item.name} className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-[11px] font-black text-emerald-400">
                        {item.name} <span className="text-[9px] opacity-60 ml-1">{item.days}天</span>
                      </span>
                    ) : null
                  )) : (
                    <span className="text-[10px] text-gray-600 italic">暂无数据，需保存历史记录后显示</span>
                  )}
                </div>
              </div>
            </section>
          </div>

          <div className="col-span-12 xl:col-span-8 space-y-10">
            <div className="grid grid-cols-12 gap-10">
              <div className="col-span-12 lg:col-span-7 space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">04</div>
                    <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">连板晋级梯队 (支持手工补充)</h2>
                  </div>
                  <span className="text-[9px] text-gray-600">多只标的用逗号或空格分隔</span>
                </div>
                <div className="flex flex-col gap-3">
                  {['5+', '5', '4', '3', '2', '1'].map(lvl => (
                    <div key={lvl} className="flex gap-4 group">
                      <div className={`w-14 h-12 flex items-center justify-center rounded-xl border font-black text-xs ${lvl === '5+' ? 'bg-red-600/10 border-red-500/50 text-red-500' : 'bg-white/5 border-white/10 text-gray-500'}`}>
                        {lvl === '5+' ? '5B+' : `${lvl}B`}
                      </div>
                      <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-xl p-3 flex items-center gap-4 hover:border-indigo-500/30 transition-all focus-within:border-indigo-500/50 focus-within:bg-white/5">
                        <textarea
                          placeholder={`${lvl}B核心标的 (自动识别最早封板，可手动补充其他强力跟风)`}
                          value={review.ladder[lvl]?.stock || ''}
                          onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], stock: e.target.value}; setReview({...review, ladder: nl}); }}
                          className="bg-transparent text-xs font-black text-white outline-none w-full resize-none h-6 overflow-hidden mt-1 placeholder:text-gray-700 leading-relaxed"
                        />
                        <div className="flex items-center gap-4 min-w-[120px] pl-2 border-l border-white/10">
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">家数</span>
                            <input type="number" value={review.ladder[lvl]?.count || 0} onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], count: +e.target.value}; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-blue-400 outline-none w-10" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">晋级%</span>
                            <input type="number" value={review.ladder[lvl]?.promoRate || 0} onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], promoRate: +e.target.value}; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-yellow-500 outline-none w-10" />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="col-span-12 lg:col-span-5 space-y-6">
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-md bg-white/5 flex items-center justify-center text-gray-500 text-xs font-black border border-white/10">05</div>
                  <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-gray-500">灵魂标的监测</h2>
                </div>

                <div className="bg-gradient-to-br from-red-600/10 to-transparent border border-red-500/20 p-5 rounded-3xl relative overflow-hidden group">
                  <span className="text-[9px] font-black text-red-500 uppercase flex items-center gap-2 mb-2"><Trophy size={10}/> 情绪总龙头</span>
                  <input value={review.dragon} onChange={e => { setReview({...review, dragon: e.target.value}); setIsDirty(true); }} className="bg-transparent w-full text-2xl font-black text-red-500 outline-none mb-3 relative z-10" placeholder="寻龙中..." />
                  <select value={review.dragonStatus} onChange={e => setReview({...review, dragonStatus: e.target.value as any})} className="bg-black/40 text-[10px] font-black text-red-500 outline-none p-2 rounded-lg border border-red-500/20 w-full cursor-pointer">
                    <option value="accelerate">一致加速</option><option value="divergence">分歧转强</option><option value="broken">破位退潮</option><option value="revive">反包穿越</option>
                  </select>
                </div>

                <div className="bg-gradient-to-br from-blue-600/10 to-transparent border border-blue-500/20 p-5 rounded-3xl relative overflow-hidden group">
                  <span className="text-[9px] font-black text-blue-500 uppercase flex items-center gap-2 mb-2"><Crosshair size={10}/> 容量中军</span>
                  <input value={review.midArmy} onChange={e => setReview({...review, midArmy: e.target.value})} className="bg-transparent w-full text-xl font-black text-blue-500 outline-none" placeholder="容量中军..." />
                </div>

                <div className="bg-white/[0.02] border border-emerald-500/20 p-5 rounded-3xl">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[9px] font-black text-emerald-500 uppercase flex items-center gap-2"><Crosshair size={10}/> 今日实盘动作映射</span>
                    <span className="text-[8px] text-gray-500 bg-black/40 px-2 py-0.5 rounded border border-white/5">数据联动</span>
                  </div>
                  {todaysTrades.length === 0 ? (
                    <div className="text-center py-4 border border-dashed border-white/10 rounded-xl">
                      <span className="text-[10px] font-black text-gray-600 uppercase">今日知行合一：空仓防守 / 未录入</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {todaysTrades.map((t, idx) => (
                        <div key={idx} className={`flex items-center justify-between p-2 rounded-lg border ${t.action === 'buy' ? 'bg-red-500/5 border-red-500/10' : 'bg-emerald-500/5 border-emerald-500/10'}`}>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${t.action === 'buy' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>{t.action === 'buy' ? '买' : '卖'}</span>
                            <span className="text-xs font-black text-white">{t.stockCode}</span>
                          </div>
                          <span className="text-[10px] text-gray-500 font-bold">{t.type}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <section className="bg-[#0c0c10] rounded-[2.5rem] border border-white/5 p-10 relative overflow-hidden">
              <div className="flex items-center justify-between mb-8 relative z-10">
                <div className="flex items-center gap-6">
                  <div className="w-14 h-14 rounded-2xl bg-purple-600 flex items-center justify-center text-white shadow-xl shadow-purple-600/20"><BrainCircuit size={28} /></div>
                  <div className="flex flex-col"><h2 className="text-xl font-black text-white uppercase tracking-tight">『股市盘手』深度推演</h2><span className="text-[10px] font-black text-purple-500 uppercase mt-1">GEMS Persona Agent</span></div>
                </div>
                <button onClick={analyzeSentimentCycle} disabled={isLoading} className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-[11px] font-black shadow-xl shadow-purple-600/20 flex items-center gap-2 transition-all">
                  <Waves size={14} /> 启动量化盘手引擎
                </button>
              </div>

              <div className="bg-black/60 rounded-3xl border border-white/5 p-8 min-h-[300px] relative font-mono">
                {isLoading && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0c0c10]/90 z-20 rounded-3xl">
                    <RefreshCcw className="animate-spin text-purple-500 mb-4" size={40} />
                    <span className="text-[10px] font-black text-purple-400 uppercase tracking-[0.2em]">{statusMsg}</span>
                  </div>
                )}
                {review.aiAnalysis ? (
                  <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{review.aiAnalysis}</div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 opacity-20"><MessageSquareCode size={48} className="mb-4" /><p className="text-[10px] font-black uppercase tracking-widest">等待盘手下达量化指令...</p></div>
                )}
              </div>
            </section>
          </div>
        </div>

        {/* --- 全景数据大屏与存档 --- */}
        <section className="mt-24 border-t border-white/5 pt-16 pb-32 space-y-12">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-4">
              <Activity size={24} className="text-purple-500" />
              <h2 className="text-2xl font-black text-white uppercase italic tracking-tighter">全景周期图谱 & 信仰存档</h2>
            </div>
            <div className="flex gap-3">
              <input type="file" ref={fileImportRef} onChange={importAllData} className="hidden" accept=".json" />
              <button onClick={() => fileImportRef.current?.click()} className="px-4 py-2 bg-white/5 hover:bg-white/10 text-gray-300 rounded-xl text-[11px] font-black border border-white/10 transition-all">
                📥 导入恢复
              </button>
              <button onClick={exportAllData} className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 border border-indigo-500/30 rounded-xl text-[11px] font-black transition-all">
                💾 一键导出备份
              </button>
            </div>
          </div>

          {chartData.length >= 2 ? (
            <div className="bg-[#0c0c10] border border-white/5 rounded-[2rem] p-8 h-[360px] flex gap-8">
              <div className="flex-1 flex flex-col">
                <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">信仰分波动曲线 (周期感知)</span>
                <div className="flex-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
                      <XAxis dataKey="date" stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis domain={[0, 100]} stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} width={30} />
                      <RechartsTooltip contentStyle={{ backgroundColor: '#000000e6', border: '1px solid #ffffff1a', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }} itemStyle={{ color: '#ef4444' }} />
                      <Area type="monotone" dataKey="score" name="信仰分" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="w-[30%] flex flex-col border-l border-white/5 pl-8">
                <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-4">市场量能水位 (万亿)</span>
                <div className="flex-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#ffffff0a" vertical={false} />
                      <XAxis dataKey="date" stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} />
                      <YAxis stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} domain={['auto', 'auto']} width={30}/>
                      <RechartsTooltip cursor={{fill: '#ffffff05'}} contentStyle={{ backgroundColor: '#000000e6', border: '1px solid #ffffff1a', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold' }} />
                      <Bar dataKey="volume" name="成交量" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-[#0c0c10] border border-white/5 rounded-[2rem] p-8 h-[200px] flex items-center justify-center text-gray-600 font-black text-xs">
              需要积累至少 2 天的复盘存档才能生成周期图谱...
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6 pt-6">
            {history.map((h) => (
              <div key={h.date} onClick={() => { if (isDirty) showToast('当前复盘有未归档修改', 'err'); setReview(h); setIsDirty(false); }} className={`p-6 rounded-3xl border cursor-pointer transition-all hover:scale-[1.02] flex flex-col justify-between h-48 relative overflow-hidden ${review.date === h.date ? 'bg-red-600/10 border-red-500' : 'bg-white/[0.02] border-white/5 hover:border-white/10'}`}>
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

      {/* 弹窗部分 */}
      {showFileManager && (
        <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-xl flex items-center justify-center p-8">
          <div className="w-full max-w-5xl bg-[#0c0c10] border border-white/10 rounded-[3rem] p-10 relative">
            <button onClick={() => setShowFileManager(false)} className="absolute top-8 right-8 w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all text-gray-500 hover:text-white"><X size={20} /></button>
            <div className="flex items-center gap-6 mb-12">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/20 text-indigo-500 shadow-xl"><DatabaseZap size={32} /></div>
              <div><h3 className="text-3xl font-black text-white uppercase tracking-tight">信源文件池</h3><p className="text-xs text-gray-500 font-black uppercase mt-1 tracking-widest">Analysis Resource Pool</p></div>
            </div>
            <div className="grid grid-cols-12 gap-10">
              <div className="col-span-4">
                <div onClick={() => fileInputRef.current?.click()} className="aspect-square border-2 border-dashed border-white/10 rounded-[2.5rem] flex flex-col items-center justify-center gap-4 cursor-pointer hover:border-indigo-500/40 hover:bg-indigo-500/5 transition-all text-center group">
                  <div className="w-14 h-14 bg-indigo-500/10 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform"><FileUp size={28} className="text-indigo-500" /></div>
                  <span className="text-sm font-black text-white">注入复盘数据源</span>
                  <input type="file" ref={fileInputRef} multiple onChange={handleFileChange} className="hidden" accept="image/*,.pdf,.txt,.xlsx,.xls" />
                </div>
              </div>
              <div className="col-span-8 flex flex-col">
                <div className="flex-1 bg-black/40 border border-white/5 rounded-[2.5rem] p-8 h-[400px] overflow-y-auto">
                  {uploadedFiles.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-800 opacity-30"><Radio size={48} className="mb-4" /><p className="text-xs font-black uppercase tracking-widest">No active source feeds</p></div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {uploadedFiles.map((f, i) => (
                        <div key={i} className="group bg-white/5 border border-white/10 p-4 rounded-2xl flex items-center gap-4 hover:border-indigo-500/40 relative transition-all">
                          <div className="w-12 h-12 rounded-xl bg-black/40 overflow-hidden border border-white/5 flex items-center justify-center">
                            {f.preview ? <img src={f.preview} className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" /> : <DatabaseZap size={20} className="text-indigo-400" />}
                          </div>
                          <p className="text-[11px] font-black text-gray-400 truncate flex-1 uppercase tracking-tighter">{f.name}</p>
                          <button onClick={() => { if (uploadedFiles[i].preview) URL.revokeObjectURL(uploadedFiles[i].preview!); setUploadedFiles(prev => prev.filter((_, idx) => idx !== i)); }} className="w-6 h-6 bg-red-500/80 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all shadow-lg"><X size={12}/></button>
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

      {showTradeManager && (
        <TradeManager
          trades={trades} positions={positions} stats={tradeStats}
          buyDistribution={buyTypeDistribution} sellDistribution={sellTypeDistribution}
          currentStage={review.stage}
          currentDate={review.date}
          onAddTrade={addTrade} onAddPosition={addPosition} onDeleteTrade={deleteTrade}
          onUpdatePositionPrice={updatePositionPrice} onClose={() => setShowTradeManager(false)}
        />
      )}

      {/* Toast 通知系统 */}
      <div className="fixed bottom-6 right-6 z-[999] flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => (
          <div key={t.id} className={`px-5 py-3 rounded-xl text-xs font-black text-white shadow-2xl backdrop-blur-xl border pointer-events-auto
            ${t.type === 'ok' ? 'bg-emerald-700/95 border-emerald-500/50' : t.type === 'err' ? 'bg-red-700/95 border-red-500/50' : 'bg-indigo-700/95 border-indigo-500/50'}`}>
            {t.msg}
          </div>
        ))}
      </div>
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
