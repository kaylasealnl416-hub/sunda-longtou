
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Flame, Zap, BarChart3, Target, Trophy, BrainCircuit,
  History, TrendingUp, TrendingDown, Layers, Activity,
  ArrowUpRight, Scale, Save, RefreshCcw, ArrowRight,
  ShieldAlert, Wand2, DatabaseZap, X, FileUp, Calendar, Timer, Waves,
  ChevronDown, MessageSquareCode, Radio, Cpu, Plus, TrendingDownIcon,
  Wallet, Trash2, DollarSign, Percent, ArrowDownRight, Camera
} from 'lucide-react';
import html2canvas from 'html2canvas';
import { GoogleGenAI } from "@google/genai";
import * as XLSX from 'xlsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, Legend, Cell, PieChart, Pie
} from 'recharts';

// --- Types & Constants ---
const STORAGE_KEY = 'dragon_faith_system_v28_0';
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
  persistentSectors: { name: string; days: number }[]; // 最近5天出现>=2次的板块
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

// --- 交易复盘数据类型 ---
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
  persistentSectors: [], // 最近5天出现>=2次的板块
  ladder: {
    '5+': { count: 0, stock: '', concept: '', promoRate: 0 },
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

// ===== 交易复盘中心组件 =====
const TradeManager = ({
  trades,
  positions,
  stats,
  buyDistribution,
  sellDistribution,
  currentStage,
  onAddTrade,
  onAddPosition,
  onDeleteTrade,
  onUpdatePositionPrice,
  onClose
}: {
  trades: TradeRecord[];
  positions: Position[];
  stats: TradeStats;
  buyDistribution: { type: string; count: number; percentage: number }[];
  sellDistribution: { type: string; count: number; percentage: number }[];
  currentStage: string;
  onAddTrade: (trade: Omit<TradeRecord, 'id'>) => void;
  onAddPosition: (position: Omit<Position, 'id'>) => void;
  onDeleteTrade: (id: string) => void;
  onUpdatePositionPrice: (stockCode: string, currentPrice: number) => void;
  onClose: () => void;
}) => {
  const [activeTab, setActiveTab] = useState<'record' | 'position' | 'stats'>('record');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    stockCode: '',
    action: 'buy' as 'buy' | 'sell',
    type: '追涨' as TradeType,
    price: 0,
    quantity: 0,
    notes: '',
    linkedDragon: ''
  });

  const handleSubmit = () => {
    if (!formData.stockCode || !formData.price || !formData.quantity) return;

    const tradeData = {
      date: new Date().toISOString().split('T')[0],
      stockCode: formData.stockCode,
      action: formData.action,
      type: formData.type,
      price: formData.price,
      quantity: formData.quantity,
      notes: formData.notes,
      linkedDragon: formData.linkedDragon
    };

    onAddTrade(tradeData);

    // 如果是买入，同时添加到持仓
    if (formData.action === 'buy') {
      onAddPosition({
        stockCode: formData.stockCode,
        buyDate: new Date().toISOString().split('T')[0],
        buyPrice: formData.price,
        buyType: formData.type,
        quantity: formData.quantity
      });
    }

    setFormData({
      stockCode: '',
      action: 'buy',
      type: '追涨',
      price: 0,
      quantity: 0,
      notes: '',
      linkedDragon: ''
    });
    setShowAddForm(false);
  };

  const COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899'];

  return (
    <div className="fixed inset-0 z-[200] bg-black/90 backdrop-blur-xl flex items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-6xl bg-[#0c0c10] border border-white/10 rounded-[2rem] p-6 my-8 relative">
        <button onClick={onClose} className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all text-gray-500 hover:text-white">
          <X size={20} />
        </button>

        {/* 标题 */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-xl shadow-emerald-600/20">
            <Wallet size={24} />
          </div>
          <div>
            <h2 className="text-xl font-black text-white uppercase">交易复盘中心</h2>
            <p className="text-xs text-gray-500 font-black uppercase tracking-widest">Trading Journal</p>
          </div>
        </div>

        {/* Tab 切换 */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('record')}
            className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${activeTab === 'record' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
          >
            交易记录
          </button>
          <button
            onClick={() => setActiveTab('position')}
            className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${activeTab === 'position' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
          >
            当前持仓
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${activeTab === 'stats' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
          >
            统计分析
          </button>
        </div>

        {/* 交易记录 Tab */}
        {activeTab === 'record' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-black text-white">交易记录</h3>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-black flex items-center gap-2"
              >
                <Plus size={14} /> 新增记录
              </button>
            </div>

            {showAddForm && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">股票代码</label>
                    <input
                      type="text"
                      value={formData.stockCode}
                      onChange={e => setFormData({ ...formData, stockCode: e.target.value })}
                      placeholder="600519"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">操作</label>
                    <select
                      value={formData.action}
                      onChange={e => setFormData({ ...formData, action: e.target.value as 'buy' | 'sell' })}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    >
                      <option value="buy">买入</option>
                      <option value="sell">卖出</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">类型</label>
                    <select
                      value={formData.type}
                      onChange={e => setFormData({ ...formData, type: e.target.value as TradeType })}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    >
                      <option value="追涨">追涨</option>
                      <option value="低吸">低吸</option>
                      <option value="反包">反包</option>
                      <option value="潜伏">潜伏</option>
                      <option value="止盈">止盈</option>
                      <option value="止损">止损</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">价格</label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.price || ''}
                      onChange={e => setFormData({ ...formData, price: +e.target.value })}
                      placeholder="0.00"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">数量</label>
                    <input
                      type="number"
                      value={formData.quantity || ''}
                      onChange={e => setFormData({ ...formData, quantity: +e.target.value })}
                      placeholder="0"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">关联龙头</label>
                    <input
                      type="text"
                      value={formData.linkedDragon}
                      onChange={e => setFormData({ ...formData, linkedDragon: e.target.value })}
                      placeholder="如：某龙头"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-[10px] font-black text-gray-500 uppercase block mb-1">备注</label>
                    <input
                      type="text"
                      value={formData.notes}
                      onChange={e => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="可选备注"
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs font-black text-white outline-none"
                    />
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={() => setShowAddForm(false)} className="px-4 py-2 bg-white/10 text-gray-400 rounded-lg text-xs font-black">取消</button>
                  <button onClick={handleSubmit} className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-black">确认添加</button>
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
                    <tr>
                      <td colSpan={8} className="text-center py-8 text-gray-600 font-black">暂无交易记录</td>
                    </tr>
                  ) : (
                    trades.slice(0, 20).map(trade => (
                      <tr key={trade.id} className="border-b border-white/5 hover:bg-white/5">
                        <td className="py-3 px-3 text-gray-400 font-black">{trade.date}</td>
                        <td className="py-3 px-3 text-white font-black">{trade.stockCode}</td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-black ${trade.action === 'buy' ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                            {trade.action === 'buy' ? '买入' : '卖出'}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-gray-400 font-black">{trade.type}</td>
                        <td className="py-3 px-3 text-right text-white font-black">{trade.price.toFixed(2)}</td>
                        <td className="py-3 px-3 text-right text-white font-black">{trade.quantity}</td>
                        <td className="py-3 px-3 text-right">
                          {trade.profitRate !== undefined && (
                            <span className={`font-black ${trade.profitRate >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                              {trade.profitRate >= 0 ? '+' : ''}{trade.profitRate.toFixed(2)}%
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <button onClick={() => onDeleteTrade(trade.id)} className="text-gray-600 hover:text-red-400 transition-colors">
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 当前持仓 Tab */}
        {activeTab === 'position' && (
          <div className="space-y-4">
            <h3 className="text-sm font-black text-white">当前持仓</h3>
            {positions.length === 0 ? (
              <div className="text-center py-12 text-gray-600 font-black">暂无持仓</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {positions.map(pos => (
                  <div key={pos.id} className="bg-white/5 border border-white/10 rounded-xl p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="text-lg font-black text-white">{pos.stockCode}</span>
                        <span className="text-xs text-gray-500 ml-2">{pos.buyType}</span>
                      </div>
                      <span className={`text-sm font-black ${(pos.profitRate || 0) >= 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {(pos.profitRate || 0) >= 0 ? '+' : ''}{(pos.profitRate || 0).toFixed(2)}%
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500 block">买入价</span>
                        <span className="text-white font-black">{pos.buyPrice.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block">现价</span>
                        <span className="text-white font-black">{(pos.currentPrice || pos.buyPrice).toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 block">数量</span>
                        <span className="text-white font-black">{pos.quantity}</span>
                      </div>
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

        {/* 统计分析 Tab */}
        {activeTab === 'stats' && (
          <div className="space-y-6">
            {/* 统计看板 */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2">
                <BarChart3 size={16} className="text-emerald-500" /> 战绩统计
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-black text-white">{stats.totalTrades}</div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">总交易次数</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-black text-red-400">{stats.winRate.toFixed(1)}%</div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">胜率</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-black text-blue-400">{stats.profitLossRatio.toFixed(2)}:1</div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">盈亏比</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-black text-emerald-400">+{stats.avgProfit.toFixed(1)}%</div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">平均盈利</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-black text-gray-400">{currentStage || '待研判'}</div>
                  <div className="text-[10px] text-gray-500 uppercase font-black">当前周期</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* 买点类型分布 */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2">
                  <ArrowUpRight size={16} className="text-red-500" /> 买点类型分布
                </h3>
                {buyDistribution.length === 0 ? (
                  <div className="text-center py-8 text-gray-600 font-black text-xs">暂无数据</div>
                ) : (
                  <div className="flex items-center gap-4">
                    <div className="w-32 h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={buyDistribution}
                            dataKey="count"
                            nameKey="type"
                            cx="50%"
                            cy="50%"
                            innerRadius={30}
                            outerRadius={50}
                          >
                            {buyDistribution.map((_, index) => (
                              <Cell key={index} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-2">
                      {buyDistribution.map((item, index) => (
                        <div key={item.type} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                            <span className="text-xs text-gray-400 font-black">{item.type}</span>
                          </div>
                          <span className="text-xs text-white font-black">{item.percentage.toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 卖点类型分布 */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-black text-white mb-4 flex items-center gap-2">
                  <ArrowDownRight size={16} className="text-emerald-500" /> 卖点类型分布
                </h3>
                {sellDistribution.length === 0 ? (
                  <div className="text-center py-8 text-gray-600 font-black text-xs">暂无数据</div>
                ) : (
                  <div className="flex items-center gap-4">
                    <div className="w-32 h-32">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={sellDistribution}
                            dataKey="count"
                            nameKey="type"
                            cx="50%"
                            cy="50%"
                            innerRadius={30}
                            outerRadius={50}
                          >
                            {sellDistribution.map((_, index) => (
                              <Cell key={index} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex-1 space-y-2">
                      {sellDistribution.map((item, index) => (
                        <div key={item.type} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                            <span className="text-xs text-gray-400 font-black">{item.type}</span>
                          </div>
                          <span className="text-xs text-white font-black">{item.percentage.toFixed(1)}%%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 最佳/最差交易 */}
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
  const [aiProvider, setAiProvider] = useState<'gemini' | 'zhipu'>('zhipu');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 交易记录状态
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);

  // 加载交易数据
  useEffect(() => {
    const savedTrades = localStorage.getItem(TRADE_STORAGE_KEY);
    if (savedTrades) setTrades(JSON.parse(savedTrades));
    const savedPositions = localStorage.getItem(POSITION_STORAGE_KEY);
    if (savedPositions) setPositions(JSON.parse(savedPositions));
  }, []);

  // 加载市场复盘数据
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const persistentSectors = useMemo(() => {
    const last5 = history.slice(0, 5);
    const currentSectors = review.topSectors.map(s => s.name.trim()).filter(Boolean);
    const historicalSectors = last5.flatMap(h => (h.topSectors || []).map(s => s.name ? s.name.trim() : '').filter(Boolean));
    const allSectors = [...currentSectors, ...historicalSectors];
    const counts: Record<string, number> = {};
    allSectors.forEach(name => { if(name) counts[name] = (counts[name] || 0) + 1; });
    return Object.entries(counts)
      .filter(([_, count]) => count >= 2)
      .sort((a, b) => b[1] - a[1])
      .map(([name, days]) => ({ name, days }));
  }, [history, review.topSectors]);

  // ===== Excel 解析函数 =====
  const parseExcelFile = (file: File): Promise<any> => {
    return new Promise((resolve, reject) => {
      // .xls 文件需要用 binary string 方式读取，.xlsx 用 array buffer
      const isOldExcel = file.name.toLowerCase().endsWith('.xls');

      if (isOldExcel) {
        // 老版 .xls 文件 - 先读取为 ArrayBuffer，再用 xlsx 处理
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const data = e.target?.result;
            // 尝试用自动检测编码读取
            const workbook = XLSX.read(data, { type: 'array', cellText: true });
            const result: any = {};

            workbook.SheetNames.forEach(sheetName => {
              const sheet = workbook.Sheets[sheetName];
              // 使用 sheet_to_json 带 cellText 选项
              const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
              result[sheetName] = jsonData;
            });

            resolve(result);
          } catch (error) {
            reject(error);
          }
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
      } else {
        // 新版 .xlsx 文件
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
          } catch (error) {
            reject(error);
          }
        };
        reader.onerror = reject;
        reader.readAsArrayBuffer(file);
      }
    });
  };

  // 从 Excel 数据中提取市场数据
  const extractMarketData = (excelData: any, historyData?: MarketReview[]): Partial<MarketReview> => {
    const result: any = {};

    // 辅助函数：查找包含关键字的 sheet（处理嵌套结构）
    const findSheet = (keywords: string[]): any[] => {
      const keys = Object.keys(excelData);
      for (const kw of keywords) {
        const found = keys.find(k => k.includes(kw));
        if (found) {
          const data = excelData[found] as any;
          // 处理可能是对象包装的情况
          if (Array.isArray(data)) return data;
          if (data && typeof data === 'object') {
            const values = Object.values(data);
            if (Array.isArray(values[0])) {
              return values[0];
            }
          }
        }
      }
      return [];
    };

    // 查找列索引
    const findColIndex = (header: any[], keywords: string[]): number => {
      if (!Array.isArray(header)) return -1;
      for (let i = 0; i < header.length; i++) {
        const h = String(header[i] || '');
        if (keywords.some(kw => h.includes(kw))) return i;
      }
      return -1;
    };

    console.log('Excel数据keys:', Object.keys(excelData));

    // 1. 从"沪深京主要指数"提取指数数据 - 模糊匹配
    const indexSheet = findSheet(['沪深京主要指数', '沪深京', '指数']);
    console.log('找到的指数sheet:', indexSheet.length > 0 ? '是' : '否', '行数:', indexSheet.length);
    if (indexSheet && indexSheet.length > 1) {
      // 模糊匹配：Excel名称包含关键字段即匹配
      const indexKeys = [
        { key: '上证指数', display: '上证' },
        { key: '深证成指', display: '深成' },
        { key: '创业板指', display: '创业' },
        { key: '科创50', display: '科创' },
        { key: '沪深300', display: '沪深300' },
        { key: '中证1000', display: '中证1000' },
        { key: '中证2000', display: '中证2000' },
        { key: '微盘股', display: '微盘股' },
      ];

      // 找到列索引
      const headerRow = indexSheet[0];
      const headerArr = Array.isArray(headerRow) ? headerRow : [];
      const nameIdx = findColIndex(headerArr, ['名称']);
      const priceIdx = findColIndex(headerArr, ['现价', '最新']);
      const changeIdx = findColIndex(headerArr, ['涨跌幅']);
      const upDownIdx = findColIndex(headerArr, ['涨跌家数', '上涨家数', '下跌家数']);

      // 先提取所有行数据
      const rowDataList: { name: string; value: number; change: number }[] = [];
      indexSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const name = nameIdx >= 0 ? String(rowArr[nameIdx] || '').trim() : String(rowArr[1] || '').trim();
        if (!name) return;

        const value = priceIdx >= 0 ? Math.round(parseFloat(String(rowArr[priceIdx])) || 0) : Math.round(parseFloat(String(rowArr[2])) || 0);
        const change = changeIdx >= 0 ? parseFloat(String(rowArr[changeIdx])) || 0 : parseFloat(String(rowArr[4])) || 0;
        rowDataList.push({ name, value, change });
      });

      console.log('指数sheet行数据:', rowDataList);

      // 模糊匹配：为每个目标指数找到最佳匹配行
      const matchedIndices = indexKeys.map(({ key, display }) => {
        // 优先精确匹配，然后模糊匹配
        const exactMatch = rowDataList.find(r => r.name === key);
        if (exactMatch) {
          return { name: display, value: exactMatch.value, change: exactMatch.change, ma5Status: 'above' as const };
        }

        // 模糊匹配：名称包含key或key包含名称
        const fuzzyMatch = rowDataList.find(r =>
          r.name.includes(key) || key.includes(r.name) ||
          r.name.replace(/[指数]/g, '').includes(key.replace(/[指数]/g, ''))
        );
        if (fuzzyMatch) {
          console.log(`模糊匹配 ${display}: ${fuzzyMatch.name} -> 值:${fuzzyMatch.value}, 涨跌幅:${fuzzyMatch.change}`);
          return { name: display, value: fuzzyMatch.value, change: fuzzyMatch.change, ma5Status: 'above' as const };
        }

        console.log(`未匹配 ${display} (key: ${key})`);
        return { name: display, value: 0, change: 0, ma5Status: 'above' as const };
      });

      // 提取涨跌家数（如果存在）
      if (upDownIdx >= 0) {
        const upDownRow = rowDataList.find(r => r.name.includes('沪深京') || r.name.includes('市场'));
        if (upDownRow) {
          // 尝试从整列获取总上涨/下跌家数
          console.log('涨跌家数列索引:', upDownIdx);
        }
      }

      console.log('提取的指数数据:', matchedIndices);
      result.indices = matchedIndices;
    }

    // 2. 从"全部Ａ股"统计涨跌停和成交额
    const allStockSheet = findSheet(['全部Ａ股', 'Ａ股', 'A股', '全部A股']);
    console.log('找到的全部A股sheet:', allStockSheet.length > 0 ? '是' : '否', '行数:', allStockSheet.length);
    if (allStockSheet && allStockSheet.length > 1) {
      let upCount = 0, downCount = 0, limitUp = 0, limitDown = 0, totalAmount = 0, stFiltered = 0;
      const headerRow = allStockSheet[0];
      const headerArr = Array.isArray(headerRow) ? headerRow : [];
      console.log('全部A股表头:', headerArr.slice(0, 30));

      const nameIdx = findColIndex(headerArr, ['名称', '股票名称', '证券简称']);
      const codeIdx = findColIndex(headerArr, ['代码', '证券代码']);
      const changeIdx = findColIndex(headerArr, ['涨幅%', '涨幅']);
      // 尝试多个可能的金额列名
      const amountIdx = findColIndex(headerArr, ['总金额', '成交额', '金额', '总成交']);
      // 趋势中军需要的列
      const change10Idx = findColIndex(headerArr, ['10日涨幅%', '10日涨幅', '10日涨跌幅%', '10日涨跌幅']);
      const turnoverZIdx = findColIndex(headerArr, ['换手Z']);
      console.log('列索引 - 名称:', nameIdx, '代码:', codeIdx, '涨幅:', changeIdx, '金额:', amountIdx, '10日涨幅:', change10Idx, '换手Z:', turnoverZIdx);
      console.log('全部A股表头:', headerArr);

      // 调试：显示前5个股票名称样本
      const sampleStocks = allStockSheet.slice(1, 6).map((row: any) => {
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        return {
          name: nameIdx >= 0 ? rowArr[nameIdx] : rowArr[1],
          code: codeIdx >= 0 ? rowArr[codeIdx] : rowArr[0],
          change: changeIdx >= 0 ? rowArr[changeIdx] : rowArr[3]
        };
      });
      console.log('股票名称样本:', sampleStocks);

      allStockSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);

        // 获取股票名称/代码用于过滤ST
        const stockName = nameIdx >= 0 ? String(rowArr[nameIdx] || '') : String(rowArr[1] || '');
        const stockCode = codeIdx >= 0 ? String(rowArr[codeIdx] || '') : String(rowArr[0] || '');

        // 过滤ST股票（名称或代码中包含ST、*ST、S*、S表示ST）
        // 匹配模式: ST, *ST, S*ST, SST, S开头(如S011)等
        const isST = /^(ST|\*ST|S[PT]?|S\-)/i.test(stockName) ||
                    /^(ST|\*ST|S[PT]?|S\-)/i.test(stockCode) ||
                    /S[0-9]{3}/i.test(stockCode); // S开头+3位数字

        const change = changeIdx >= 0 ? parseFloat(String(rowArr[changeIdx])) || 0 : parseFloat(String(rowArr[3])) || 0;

        // 如果是涨停且是ST股票，记录日志
        if (change >= 9.8 && isST) {
          console.log('过滤ST涨停股:', stockCode, stockName, '涨幅:', change);
          stFiltered++;
        }

        if (isST) {
          stFiltered++;
          return; // 跳过ST股票
        }
        const amount = amountIdx >= 0 ? parseFloat(String(rowArr[amountIdx]).replace(/,/g, '')) || 0 : 0;

        if (change > 0) upCount++;
        if (change < 0) downCount++;
        if (change >= 9.8) limitUp++;  // 9.8%及以上视为涨停
        if (change <= -9.8) {
          limitDown++;
          console.log('跌停股:', stockCode, stockName, '跌幅:', change);
        }
        totalAmount += amount;
      });

      // 成交额转换为万亿元（Excel金额单位是万元）
      // 万元 / 10000 = 亿元，亿元 / 10000 = 万亿元
      result.totalVol = Math.round(totalAmount / 100000000 * 100) / 100; // 万元 -> 万亿元，保留2位小数

      // 自动计算成交额增减（与昨天对比）
      if (historyData && historyData.length > 0) {
        // 找到最近一天的记录
        const yesterdayData = historyData[0]; // 历史记录按日期排序，最近的是昨天
        if (yesterdayData && yesterdayData.totalVol > 0) {
          result.volDelta = Math.round((result.totalVol - yesterdayData.totalVol) * 100) / 100;
          console.log('成交额增减计算: 今天', result.totalVol, '昨天', yesterdayData.totalVol, '增减', result.volDelta);
        }
      }

      result.limitUpTotal = limitUp;
      result.limitDownTotal = limitDown;
      result.upDownCount = { up: upCount, down: downCount };
      console.log('成交额(万亿元):', result.totalVol, '涨停:', limitUp, '跌停:', limitDown, '上涨家数:', upCount, '下跌家数:', downCount, '增减:', result.volDelta, '过滤ST股:', stFiltered);

      // 趋势中军：10日涨幅前40名中，换手Z<30的，总金额最大的
      if (change10Idx >= 0 && turnoverZIdx >= 0 && amountIdx >= 0) {
        // 先收集所有股票数据
        const stockData: { name: string; code: string; change10: number; turnoverZ: number; amount: number }[] = [];

        allStockSheet.slice(1).forEach((row: any) => {
          if (!row) return;
          const rowArr = Array.isArray(row) ? row : Object.values(row);
          const stockName = nameIdx >= 0 ? String(rowArr[nameIdx] || '') : String(rowArr[1] || '');
          const stockCode = codeIdx >= 0 ? String(rowArr[codeIdx] || '') : String(rowArr[0] || '');

          // 过滤ST
          const isST = /^(ST|\*ST|S[PT]?|S\-)/i.test(stockName) || /^(ST|\*ST|S[PT]?|S\-)/i.test(stockCode) || /S[0-9]{3}/i.test(stockCode);
          if (isST) return;

          const change10 = change10Idx >= 0 ? parseFloat(String(rowArr[change10Idx])) || 0 : 0;
          const turnoverZ = turnoverZIdx >= 0 ? parseFloat(String(rowArr[turnoverZIdx])) || 0 : 0;
          const amount = amountIdx >= 0 ? parseFloat(String(rowArr[amountIdx]).replace(/,/g, '')) || 0 : 0;

          stockData.push({ name: stockName, code: stockCode, change10, turnoverZ, amount });
        });

        // 按10日涨幅排序，取前40
        const top40 = stockData.sort((a, b) => b.change10 - a.change10).slice(0, 40);
        console.log('10日涨幅前40:', top40.slice(0, 5).map(s => ({ name: s.name, change10: s.change10, turnoverZ: s.turnoverZ })));

        // 筛选换手Z<30的
        const filtered = top40.filter(s => s.turnoverZ < 30);
        console.log('换手Z<30的:', filtered.slice(0, 5).map(s => ({ name: s.name, turnoverZ: s.turnoverZ, amount: s.amount })));

        // 取总金额最大的
        if (filtered.length > 0) {
          const midArmy = filtered.sort((a, b) => b.amount - a.amount)[0];
          result.midArmy = midArmy.name;
          console.log('趋势中军:', midArmy.name, '10日涨幅:', midArmy.change10, '换手Z:', midArmy.turnoverZ, '总金额:', midArmy.amount);
        }
      }
    }

    // 3. 从"短线宝"提取连板梯队
    const shortTermSheet = findSheet(['短线宝']);
    console.log('找到的短线宝sheet:', shortTermSheet.length > 0 ? '是' : '否', '行数:', shortTermSheet.length);
    if (shortTermSheet && shortTermSheet.length > 1) {
      const ladder: Record<string, { count: number; stock: string; concept: string; promoRate: number }> = {
        '5+': { count: 0, stock: '', concept: '', promoRate: 0 }, // 5板及以上
        '5': { count: 0, stock: '', concept: '', promoRate: 0 },
        '4': { count: 0, stock: '', concept: '', promoRate: 0 },
        '3': { count: 0, stock: '', concept: '', promoRate: 0 },
        '2': { count: 0, stock: '', concept: '', promoRate: 0 },
        '1': { count: 0, stock: '', concept: '', promoRate: 0 },
      };

      let brokenCount = 0;

      // 找到列索引
      const headerRow = shortTermSheet[0];
      const headerArr = Array.isArray(headerRow) ? headerRow : [];
      console.log('短线宝表头:', headerArr.slice(0, 15));

      const nameIdx = findColIndex(headerArr, ['名称']);
      const daysIdx = findColIndex(headerArr, ['连板天']);
      const brokenIdx = findColIndex(headerArr, ['封板___开板数', '开板']);
      const lastSealIdx = findColIndex(headerArr, ['封板___最后', '最后']);
      console.log('短线宝列 - 名称:', nameIdx, '连板天:', daysIdx, '封板开板:', brokenIdx, '封板最后:', lastSealIdx);

      // 找到金额列用于排序
      const amountIdx = findColIndex(headerArr, ['总金额', '成交额', '金额']);
      console.log('短线宝金额列:', amountIdx);

      // 先收集所有连板股票，包含封板最后时间
      const stocksByBoard: Record<string, { name: string; days: number; lastSealTime: string }[]> = {};

      shortTermSheet.slice(1).forEach((row: any) => {
        if (!row) return;
        const rowArr = Array.isArray(row) ? row : Object.values(row);
        const name = nameIdx >= 0 ? String(rowArr[nameIdx] || '') : String(rowArr[1] || '');
        const lastSealTime = lastSealIdx >= 0 ? String(rowArr[lastSealIdx] || '') : '';

        // 连板统计 - 只读"连板天"列
        const daysVal = daysIdx >= 0 ? rowArr[daysIdx] : rowArr[5];
        // 处理 "--  " 或空值情况
        const days = typeof daysVal === 'number' ? daysVal :
                     (daysVal && daysVal !== '--  ' ? parseInt(String(daysVal).replace(/[^0-9]/g, '')) || 0 : 0);

        if (days >= 1) {
          let key: string;
          if (days >= 6) {
            key = '5+'; // 6板及以上 -> 5B+
          } else if (days === 5) {
            key = '5';  // 5板 -> 5B
          } else {
            key = String(days); // 4,3,2,1板
          }

          if (!stocksByBoard[key]) {
            stocksByBoard[key] = [];
            // 初始化计数器
            ladder[key] = { count: 0, stock: '', concept: '', promoRate: 0 };
          }
          stocksByBoard[key].push({ name, days, lastSealTime });
          // 每出现一次就加1
          ladder[key].count++;
        }

        // 炸板统计
        const broken = brokenIdx >= 0 ? parseFloat(String(rowArr[brokenIdx])) || 0 : 0;
        if (broken > 0) brokenCount++;
      });

      // 辅助函数：解析时间，有时间的早封板排前面，没有时间的排最后
      const parseTime = (timeStr: string): number => {
        if (!timeStr || timeStr === '--  ' || timeStr === '') return 999999; // 没有时间的排最后
        // 尝试解析 HH:MM 格式
        const match = timeStr.match(/(\d{1,2}):(\d{2})/);
        if (match) {
          return parseInt(match[1]) * 60 + parseInt(match[2]);
        }
        // 如果是数字格式（如 0.545...），这是小数值，越小越早
        const num = parseFloat(timeStr);
        if (!isNaN(num)) return num * 100000; // 转换后乘大一点确保排最后
        return 999999;
      };

      // 按连板天数由高到低排序，天数相同的按封板最后时间早的排前面
      Object.keys(stocksByBoard).forEach(key => {
        const sorted = stocksByBoard[key].sort((a, b) => {
          // 先按连板天数降序
          if (b.days !== a.days) return b.days - a.days;
          // 天数相同时，按封板最后时间早的排前面
          return parseTime(a.lastSealTime) - parseTime(b.lastSealTime);
        });
        ladder[key] = {
          count: sorted.length,
          stock: sorted[0]?.name || '',
          concept: '',
          promoRate: 0
        };
      });

      console.log('连板梯队(按封板时间排序):', JSON.stringify(ladder));
      console.log('2B股票列表:', JSON.stringify(stocksByBoard['2']?.slice(0, 10)));
      console.log('4B股票列表:', JSON.stringify(stocksByBoard['4']?.slice(0, 10)));

      // 计算炸板率
      result.brokenRate = result.limitUpTotal ? ((brokenCount / (result.limitUpTotal + brokenCount)) * 100).toFixed(1) : '0';
      result.ladder = ladder;
      console.log('连板梯队:', ladder);
    }

    // 4. 从"板块指数"获取主线板块（按涨停数排序取前三）
    console.log('所有Excel数据keys:', Object.keys(excelData));
    const sectorSheet = findSheet(['板块指数', '板块', '行业', '概念', '题材']);
    console.log('找到的板块sheet:', sectorSheet.length > 0 ? '是' : '否', '行数:', sectorSheet.length);
    if (sectorSheet && sectorSheet.length > 1) {
      const headerRow = sectorSheet[0];
      const headerArr = Array.isArray(headerRow) ? headerRow : [];
      console.log('板块指数表头:', headerArr.slice(0, 10));

      const nameIdx = findColIndex(headerArr, ['名称', '板块名称']);
      const gainIdx = findColIndex(headerArr, ['涨幅', '涨跌幅']);
      const limitIdx = findColIndex(headerArr, ['涨停数', '涨停']);
      const volIdx = findColIndex(headerArr, ['成交额', '金额', '总金额']);
      console.log('板块指数列 - 名称:', nameIdx, '涨幅:', gainIdx, '涨停数:', limitIdx, '成交额:', volIdx);

      // 提取所有板块数据
      const sectorData: { name: string; gain: number; limitUps: number; volume: number }[] = [];
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

      // 按涨停数排序，取前三
      const top3 = sectorData
        .sort((a, b) => b.limitUps - a.limitUps)
        .slice(0, 3)
        .map(s => ({
          name: s.name,
          gain: s.gain,
          limitUps: s.limitUps,
          volume: Math.round(s.volume / 10000) // 转换为亿元
        }));

      console.log('主线板块(前三):', top3);
      result.topSectors = top3;
    }

    console.log('最终提取结果:', JSON.stringify(result));

    return result;
  };

  // 存储解析后的 Excel 数据
  const [excelDataCache, setExcelDataCache] = useState<Record<string, any>>({});

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles: UploadedFile[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // 检查是否是 Excel 文件
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        try {
          // 直接解析 Excel 并把原始数据存入 data 字段
          const excelData = await parseExcelFile(file);

          // 保存解析后的数据到 data 字段（JSON字符串形式）
          const jsonStr = JSON.stringify(excelData);

          newFiles.push({
            name: file.name,
            mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            data: jsonStr,  // 存储解析后的数据
            preview: undefined,
            isExcel: true
          });
          console.log('成功解析Excel:', file.name);
        } catch (error) {
          console.error('解析Excel失败:', error);
          alert(`解析 ${file.name} 失败: ${error}`);
        }
      } else {
        // 原有逻辑：图片、PDF、TXT
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
    }

    setUploadedFiles(prev => [...prev, ...newFiles].slice(-10));
  };

  const handleSave = () => {
    // 计算持续性主线：最近5天出现>=2次的板块
    const calculatePersistentSectors = (historyData: MarketReview[], currentReview: MarketReview): { name: string; days: number }[] => {
      // 合并当前和历史数据（最近5天）
      const last5 = [currentReview, ...historyData.slice(0, 4)];
      const sectorCounts: Record<string, number> = {};

      last5.forEach(day => {
        day.topSectors?.forEach(sector => {
          if (sector.name) {
            sectorCounts[sector.name] = (sectorCounts[sector.name] || 0) + 1;
          }
        });
      });

      // 筛选出现>=2次的板块
      const persistent = Object.entries(sectorCounts)
        .filter(([_, count]) => count >= 2)
        .sort((a, b) => b[1] - a[1])
        .map(([name, days]) => ({ name, days }));

      return persistent;
    };

    // 计算持续性主线
    const persistent = calculatePersistentSectors(history, review);

    // 更新当前review的persistentSectors
    const updatedReview = { ...review, persistentSectors: persistent };

    const newHistory = [updatedReview, ...history.filter(h => h.date !== review.date)].sort((a,b) => b.date.localeCompare(a.date));
    setHistory(newHistory);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    alert("今日复盘已成功归档至信仰库。");
  };

  // ===== 网页快照功能 =====
  const handleSnapshot = async () => {
    setIsLoading(true);
    setStatusMsg("正在生成网页快照...");
    try {
      // 等待一小段时间确保所有内容渲染完成
      await new Promise(resolve => setTimeout(resolve, 1500));

      // 记录当前滚动位置
      const originalScrollY = window.scrollY;
      const originalScrollX = window.scrollX;

      // 获取完整页面的宽高
      const fullWidth = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth);
      const fullHeight = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);

      console.log("页面完整尺寸:", fullWidth, fullHeight);

      // 使用html2canvas生成截图，捕获完整页面
      const canvas = await html2canvas(document.documentElement, {
        scale: 2,  // 提高清晰度
        useCORS: true,
        logging: false,
        backgroundColor: '#0a0a0a',  // 深色背景
        width: fullWidth,
        height: fullHeight,
        x: 0,
        y: 0,
        scrollY: 0,
        scrollX: 0,
        windowWidth: fullWidth,
        windowHeight: fullHeight,
        onclone: (clonedDoc) => {
          // 在克隆的文档中设置正确的尺寸
          const clonedElement = clonedDoc.documentElement;
          clonedElement.style.width = fullWidth + 'px';
          clonedElement.style.height = fullHeight + 'px';
          clonedElement.style.overflow = 'visible';
          // 确保body也设置正确
          if (clonedDoc.body) {
            clonedDoc.body.style.width = fullWidth + 'px';
            clonedDoc.body.style.height = fullHeight + 'px';
            clonedDoc.body.style.overflow = 'visible';
          }
        }
      });

      // 恢复原始滚动位置
      window.scrollTo(originalScrollX, originalScrollY);

      // 转换为blob
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((b) => resolve(b!), 'image/png');
      });

      // 创建下载链接
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      // 文件名格式：龙头信仰_2024-01-01.png
      const fileName = `龙头信仰_${review.date}.png`;
      link.download = fileName;
      link.click();

      // 清理
      URL.revokeObjectURL(url);
      setStatusMsg("网页快照已保存");
    } catch (error) {
      console.error("快照生成失败:", error);
      alert("网页快照生成失败，请重试");
    } finally {
      setIsLoading(false);
    }
  };

  // ===== 交易复盘功能 =====
  const addTrade = (trade: Omit<TradeRecord, 'id'>) => {
    const newTrade: TradeRecord = { ...trade, id: Date.now().toString() };
    const newTrades = [newTrade, ...trades];
    setTrades(newTrades);
    localStorage.setItem(TRADE_STORAGE_KEY, JSON.stringify(newTrades));

    // 如果是卖出，计算盈亏并从持仓中移除
    if (trade.action === 'sell') {
      setPositions(prev => {
        const newPositions = prev.filter(p => p.stockCode !== trade.stockCode);
        localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(newPositions));
        return newPositions;
      });
    }
  };

  const addPosition = (position: Omit<Position, 'id'>) => {
    const newPosition: Position = { ...position, id: Date.now().toString() };
    const newPositions = [...positions, newPosition];
    setPositions(newPositions);
    localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(newPositions));
  };

  const deleteTrade = (id: string) => {
    const newTrades = trades.filter(t => t.id !== id);
    setTrades(newTrades);
    localStorage.setItem(TRADE_STORAGE_KEY, JSON.stringify(newTrades));
  };

  const updatePositionPrice = (stockCode: string, currentPrice: number) => {
    setPositions(prev => {
      const newPositions = prev.map(p => {
        if (p.stockCode === stockCode) {
          const profit = (currentPrice - p.buyPrice) * p.quantity;
          const profitRate = ((currentPrice - p.buyPrice) / p.buyPrice) * 100;
          return { ...p, currentPrice, profit, profitRate };
        }
        return p;
      });
      localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(newPositions));
      return newPositions;
    });
  };

  // 计算交易统计
  const tradeStats = useMemo((): TradeStats => {
    const sellTrades = trades.filter(t => t.action === 'sell' && t.profit !== undefined);
    if (sellTrades.length === 0) {
      return {
        totalTrades: 0,
        winCount: 0,
        loseCount: 0,
        winRate: 0,
        avgProfit: 0,
        avgLoss: 0,
        profitLossRatio: 0,
        bestTrade: 0,
        worstTrade: 0,
        currentCycle: review.stage || '待研判'
      };
    }

    const wins = sellTrades.filter(t => (t.profit || 0) > 0);
    const losses = sellTrades.filter(t => (t.profit || 0) <= 0);
    const profits = wins.map(t => t.profitRate || 0);
    const lossesRates = losses.map(t => Math.abs(t.profitRate || 0));

    return {
      totalTrades: sellTrades.length,
      winCount: wins.length,
      loseCount: losses.length,
      winRate: (wins.length / sellTrades.length) * 100,
      avgProfit: profits.length > 0 ? profits.reduce((a, b) => a + b, 0) / profits.length : 0,
      avgLoss: lossesRates.length > 0 ? lossesRates.reduce((a, b) => a + b, 0) / lossesRates.length : 0,
      profitLossRatio: lossesRates.length > 0 && profits.length > 0
        ? (profits.reduce((a, b) => a + b, 0) / profits.length) / (lossesRates.reduce((a, b) => a + b, 0) / lossesRates.length)
        : 0,
      bestTrade: profits.length > 0 ? Math.max(...profits) : 0,
      worstTrade: lossesRates.length > 0 ? Math.min(...lossesRates) : 0,
      currentCycle: review.stage || '待研判'
    };
  }, [trades, review.stage]);

  // 买点类型分布
  const buyTypeDistribution = useMemo(() => {
    const buyTrades = trades.filter(t => t.action === 'buy');
    const total = buyTrades.length;
    if (total === 0) return [];
    const types: Record<string, number> = {};
    buyTrades.forEach(t => {
      types[t.type] = (types[t.type] || 0) + 1;
    });
    return Object.entries(types).map(([type, count]) => ({
      type,
      count,
      percentage: (count / total) * 100
    }));
  }, [trades]);

  // 卖出类型分布
  const sellTypeDistribution = useMemo(() => {
    const sellTrades = trades.filter(t => t.action === 'sell');
    const total = sellTrades.length;
    if (total === 0) return [];
    const types: Record<string, number> = {};
    sellTrades.forEach(t => {
      types[t.type] = (types[t.type] || 0) + 1;
    });
    return Object.entries(types).map(([type, count]) => ({
      type,
      count,
      percentage: (count / total) * 100
    }));
  }, [trades]);

  // AI 调用辅助函数
  const callAIProvider = async (prompt: string, files?: UploadedFile[]) => {
    console.log("AI Provider:", aiProvider);
    console.log("ZHIPU_API_KEY:", process.env.ZHIPU_API_KEY);
    if (aiProvider === 'zhipu') {
      // 使用智谱 AI - 通过 fetch 调用
      const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.ZHIPU_API_KEY}`
        },
        body: JSON.stringify({
          model: "glm-4-flash",
          messages: [{ role: "user", content: prompt }]
        })
      });
      const data = await response.json();
      console.log("智谱API响应:", data);
      if (data.error) {
        throw new Error(`智谱API错误: ${data.error.message || JSON.stringify(data.error)}`);
      }
      return data.choices?.[0]?.message?.content || "";
    } else {
      // 使用 Google Gemini
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      if (files && files.length > 0) {
        const parts: any[] = [{ text: prompt }];
        files.forEach(file => parts.push({ inlineData: { mimeType: file.mimeType, data: file.data } }));
        const response = await ai.models.generateContent({
          model: "gemini-2.0-flash",
          contents: { parts },
          config: { responseMimeType: "text/plain" }
        });
        return response.text || "";
      } else {
        const response = await ai.models.generateContent({
          model: "gemini-2.0-flash",
          contents: prompt
        });
        return response.text || "";
      }
    }
  };

  const autoFillMarketData = async () => {
    if (isLoading || uploadedFiles.length === 0) return;
    setIsLoading(true);

    // 检查是否有 Excel 文件（通过 mimeType 判断）
    const excelFiles = uploadedFiles.filter(f =>
      f.mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
    );

    console.log('上传的文件:', uploadedFiles.map(f => ({ name: f.name, isExcel: f.isExcel, hasData: !!f.data })));

    if (excelFiles.length > 0 && excelFiles[0]?.data) {
      setStatusMsg("正在解析Excel数据...");
      try {
        // 合并所有 Excel 数据
        const allExcelData: Record<string, any> = {};

        for (const file of excelFiles) {
          try {
            const parsedData = JSON.parse(file.data);
            console.log('解析文件:', file.name, '数据keys:', Object.keys(parsedData));

            let matched = false;
            // 调整匹配顺序：板块优先，因为"沪深京主要指数"会同时匹配"指数"关键字
            if (file.name.includes('短线宝')) {
              allExcelData['短线宝'] = parsedData;
              matched = true;
            } else if (file.name.includes('板块') || file.name.includes('行业') || file.name.includes('概念')) {
              allExcelData['板块指数'] = parsedData;
              matched = true;
            } else if (file.name.includes('Ａ股') || file.name.includes('A股') || file.name.includes('两融')) {
              allExcelData['全部Ａ股'] = parsedData;
              matched = true;
            } else if (file.name.includes('沪深京') || file.name.includes('大盘')) {
              allExcelData['沪深京主要指数'] = parsedData;
              matched = true;
            } else if (file.name.includes('指数')) {
              // 单独处理"指数"关键字（避免与板块冲突）
              allExcelData['沪深京主要指数'] = parsedData;
              matched = true;
            }

            if (!matched) {
              console.log('未匹配到关键字的文件:', file.name, '将其加入通用数据，用第一个sheet');
              // 未匹配的文件，尝试用第一个sheet的数据
              const keys = Object.keys(parsedData);
              if (keys.length > 0) {
                allExcelData['未匹配_' + file.name] = parsedData;
                // 同时也尝试加入到各个分类
                allExcelData['全部Ａ股'] = parsedData; // 尝试作为A股数据
              }
            }
          } catch (e) {
            console.error('解析JSON失败:', file.name, e);
          }
        }

        console.log('合并后的Excel数据:', Object.keys(allExcelData));
        console.log('沪深京数据样本:', JSON.stringify(allExcelData['沪深京主要指数']).substring(0, 500));

        if (Object.keys(allExcelData).length > 0) {
          const extractedData = extractMarketData(allExcelData, history);
          console.log('提取的数据:', extractedData);

          // 自动填充情绪总龙头：取连板最高的股票（5B+ > 5B > 4B > ...）
          const ladder = extractedData.ladder || {};
          let dragonStock = '';
          if (ladder['5+']?.stock) dragonStock = ladder['5+'].stock;
          else if (ladder['5']?.stock) dragonStock = ladder['5'].stock;
          else if (ladder['4']?.stock) dragonStock = ladder['4'].stock;
          else if (ladder['3']?.stock) dragonStock = ladder['3'].stock;
          else if (ladder['2']?.stock) dragonStock = ladder['2'].stock;
          else if (ladder['1']?.stock) dragonStock = ladder['1'].stock;

          setReview(prev => ({
            ...prev,
            ...extractedData,
            dragon: dragonStock || prev.dragon,
            midArmy: extractedData.midArmy || prev.midArmy,
            aiAnalysis: `✅ Excel数据解析完成！\n- 涨停数: ${extractedData.limitUpTotal}家\n- 跌停数: ${extractedData.limitDownTotal}家\n- 上涨家数: ${extractedData.upDownCount?.up || 0}家\n- 下跌家数: ${extractedData.upDownCount?.down || 0}家\n- 炸板率: ${extractedData.brokenRate}%\n\n建议立即进行周期定性分析。`
          }));
          setShowFileManager(false);
          setIsLoading(false);
          return;
        }
      } catch (e) {
        console.error('Excel解析失败:', e);
      }
    }

    // 如果没有 Excel 数据，使用 AI 解析
    setStatusMsg("正在通过AI解构原始信源数据...");
    try {
      const prompt = `你是一个精通A股复盘的数据专家。解析附件内容并填充复盘JSON。指数部分仅提取收盘点位。请直接输出JSON，不要其他内容。`;
      const responseText = await callAIProvider(prompt, uploadedFiles);
      const data = JSON.parse(responseText || "{}");
      setReview(prev => ({ ...prev, ...data, aiAnalysis: "信源同步完成。建议立即进行周期定性分析。" }));
      setShowFileManager(false);
    } catch (e) { alert("自动填充失败"); } finally { setIsLoading(false); }
  };

  const analyzeSentimentCycle = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("正在研判情绪周期阶段...");
    try {
      const ladderSummary = (Object.entries(review.ladder) as [string, typeof review.ladder[string]][])
        .filter(([_, data]) => data.stock || data.count > 0)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([lvl, data]) => `${lvl}板: ${data.stock || '无'}(${data.count}家, 晋级率${data.promoRate}%)`)
        .join('; ');

      const prompt = `你是一个精通A股短线情绪周期的专家。请根据以下数据进行深度研判：
1. 市场成交：${review.totalVol}万亿 (较昨日增减: ${review.volDelta}万亿)
2. 涨跌表现：涨停${review.limitUpTotal}家，跌停${review.limitDownTotal}家，炸板率${review.brokenRate}%，上涨${review.upDownCount?.up || 0}家，下跌${review.upDownCount?.down || 0}家
3. 核心标的：龙头[${review.dragon}] (状态: ${review.dragonStatus})，中军[${review.midArmy}]
4. 连板梯队：${ladderSummary || '无明显梯队'}
5. 用户关注/策略偏好：${review.customKeywords || '无'}

请按以下格式输出：
【情绪拆解】：(详细分析当前市场多空博弈情况，结合成交量和涨跌停家数)
【龙头点评】：(针对${review.dragon}及其${review.dragonStatus}状态对板块及市场情绪的影响进行分析)
【周期结论】：(必须从以下选项中选择一个：混沌期/活跃期/分化期/退潮期)
【操作建议】：(基于当前周期阶段的简短策略建议)`;

      const res = await callAIProvider(prompt);
      const stage = res.match(/【周期结论】：(混沌期|活跃期|分化期|退潮期)/)?.[1] || "混沌期";
      setReview(prev => ({ ...prev, stage, aiAnalysis: `【周期研判结论】: ${res}\n\n${prev.aiAnalysis}` }));
    } catch (e) {
      console.error("周期研判错误:", e);
      alert("周期研判异常: " + (e as Error).message);
    } finally { setIsLoading(false); }
  };

  const callAI = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setStatusMsg("AI指挥官生成实战策略中...");
    try {
      const prompt = `复盘时间:${review.date}。周期:${review.stage}。核心龙:[${review.dragon}]。成交${review.totalVol}T。${review.customKeywords ? `用户特别关注/策略偏好: ${review.customKeywords}。` : ''}请给出买入、卖出建议，使用【追涨】【低吸】【反包】【潜伏】标签。`;
      const responseText = await callAIProvider(prompt);
      setReview(prev => ({ ...prev, aiAnalysis: responseText }));
    } catch (e) {
      console.error("信仰研判错误:", e);
      alert("策略生成异常: " + (e as Error).message);
    } finally { setIsLoading(false); }
  };

  // ===== 黄金买点提示辅助函数 =====
  const getBuySuggestions = (dragonStatus: string, stage: string, score: number): string[] => {
    const suggestions: string[] = [];

    // 根据龙头状态判断
    if (dragonStatus === 'accelerate') {
      suggestions.push('持有');
      if (score > 70) suggestions.push('追涨');
    } else if (dragonStatus === 'divergence') {
      suggestions.push('低吸');
      suggestions.push('反包');
    } else if (dragonStatus === 'revive') {
      suggestions.push('反包');
      suggestions.push('低吸');
    } else if (dragonStatus === 'broken') {
      suggestions.push('观望');
    }

    // 根据周期阶段调整
    if (stage === '活跃期' && !suggestions.includes('观望')) {
      suggestions.push('追涨');
    } else if (stage === '退潮期') {
      suggestions.length = 0;
      suggestions.push('观望');
    } else if (stage === '分化期') {
      suggestions.push('低吸');
    }

    // 去除重复
    return [...new Set(suggestions)].slice(0, 3);
  };

  const getRiskLevel = (dragonStatus: string, stage: string, score: number): string => {
    if (stage === '退潮期' || dragonStatus === 'broken') return '高';
    if (stage === '分化期' || dragonStatus === 'accelerate') return '中';
    if (score > 70) return '高';
    if (score > 40) return '中';
    return '低';
  };

  const getTradingAdvice = (dragonStatus: string, stage: string, score: number): string => {
    if (stage === '退潮期') {
      return '当前处于退潮期，建议管住手，空仓观望，等待新周期开启。';
    }
    if (dragonStatus === 'broken') {
      return '龙头已破位下跌，及时止损，保护本金，等待下一个周期。';
    }
    if (dragonStatus === 'accelerate') {
      if (score > 70) {
        return '龙头处于一致加速阶段，持有者可继续持有，但不宜追高，随时准备止盈。';
      }
      return '龙头加速上涨中，可小仓位追涨，但要注意随时可能分歧。';
    }
    if (dragonStatus === 'divergence') {
      return '龙头分歧转强，是较好的上车机会，可考虑低吸或等待反包。';
    }
    if (dragonStatus === 'revive') {
      return '龙头反包穿越，可能开启第二波，可考虑小仓位参与反包。';
    }
    if (stage === '活跃期') {
      return '市场情绪活跃，可积极做多，聚焦龙头和补涨标的。';
    }
    if (stage === '分化期') {
      return '市场分化，注意轮动节奏，低吸为主，避免追高。';
    }
    return '市场方向不明，建议轻仓观望，等待信号明确。';
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
            <button onClick={handleSnapshot} className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-orange-600/30 flex items-center gap-2 transition-all">
              <Camera size={14} /> 网页快照
            </button>
            <button onClick={() => setShowTradeManager(true)} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[11px] font-black shadow-lg shadow-emerald-600/30 flex items-center gap-2 transition-all">
              <Wallet size={14} /> 交易复盘
            </button>
            <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-xl border border-white/10">
              <span className="text-[9px] font-black text-gray-500 uppercase">AI:</span>
              <button
                onClick={() => setAiProvider(aiProvider === 'gemini' ? 'zhipu' : 'gemini')}
                className={`px-2 py-1 rounded-lg text-[10px] font-black transition-all ${aiProvider === 'gemini' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}
              >
                {aiProvider === 'gemini' ? 'Google' : '智谱'}
              </button>
            </div>
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

              {/* 5日持续性主线 - 在第3个板块框下方 */}
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
                  {['5+', '5', '4', '3', '2', '1'].map(lvl => (
                    <div key={lvl} className="flex gap-4 group">
                      <div className={`w-14 h-12 flex items-center justify-center rounded-xl border font-black text-xs ${lvl === '5+' ? 'bg-red-600/10 border-red-500/50 text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.2)]' : 'bg-white/5 border-white/10 text-gray-500'}`}>
                        {lvl === '5+' ? '5B+' : `${lvl}B`}
                      </div>
                      <div className="flex-1 bg-white/[0.03] border border-white/5 rounded-xl p-3 flex items-center gap-4 hover:bg-white/5 transition-all">
                        <input placeholder={`${lvl}B核心标的...`} value={review.ladder[lvl]?.stock || ''} onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], stock: e.target.value}; setReview({...review, ladder: nl}); }} className="bg-transparent text-xs font-black text-white outline-none w-full" />
                        <div className="flex items-center gap-4 min-w-[120px]">
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">家数</span>
                            <input type="number" value={review.ladder[lvl]?.count || 0} onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], count: +e.target.value}; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-blue-400 outline-none" />
                          </div>
                          <div className="flex flex-col">
                            <span className="text-[8px] text-gray-600 font-black uppercase">晋级%</span>
                            <input type="number" value={review.ladder[lvl]?.promoRate || 0} onChange={e => { const nl = {...review.ladder}; nl[lvl] = {...nl[lvl], promoRate: +e.target.value}; setReview({...review, ladder: nl}); }} className="bg-transparent text-[11px] font-black text-yellow-500 outline-none" />
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
                    {persistentSectors && persistentSectors.length > 0 ? persistentSectors.map((item: any) => (
                      <span key={item?.name} className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-md text-[10px] font-black text-emerald-400">
                        {item?.name} <span className="text-[8px] opacity-50 ml-1">{item?.days}d</span>
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

              {/* 黄金买点提示 */}
              <div className="bg-gradient-to-r from-purple-900/20 to-red-900/20 border border-purple-500/20 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Target size={16} className="text-purple-400" />
                  <span className="text-[11px] font-black text-purple-400 uppercase">黄金买点提示</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* 龙头状态判断 */}
                  <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                    <span className="text-[9px] text-gray-500 uppercase block mb-2">龙头状态</span>
                    <span className={`text-sm font-black ${
                      review.dragonStatus === 'accelerate' ? 'text-red-400' :
                      review.dragonStatus === 'divergence' ? 'text-blue-400' :
                      review.dragonStatus === 'revive' ? 'text-yellow-400' :
                      'text-emerald-400'
                    }`}>
                      {review.dragonStatus === 'accelerate' ? '🔥 一致加速' :
                       review.dragonStatus === 'divergence' ? '💪 分歧转强' :
                       review.dragonStatus === 'revive' ? '⚡ 反包穿越' :
                       '📉 破位退潮'}
                    </span>
                  </div>
                  {/* 周期阶段 */}
                  <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                    <span className="text-[9px] text-gray-500 uppercase block mb-2">周期阶段</span>
                    <span className={`text-sm font-black ${
                      review.stage === '活跃期' ? 'text-red-400' :
                      review.stage === '分化期' ? 'text-yellow-400' :
                      review.stage === '退潮期' ? 'text-emerald-400' :
                      'text-gray-400'
                    }`}>
                      {review.stage || '待研判'}
                    </span>
                  </div>
                  {/* 买点建议 */}
                  <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                    <span className="text-[9px] text-gray-500 uppercase block mb-2">买点建议</span>
                    <div className="flex flex-wrap gap-1">
                      {getBuySuggestions(review.dragonStatus, review.stage, review.score).map(suggestion => (
                        <span key={suggestion} className={`px-2 py-0.5 rounded text-[10px] font-black ${
                          suggestion === '追涨' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                          suggestion === '低吸' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                          suggestion === '反包' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                          'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {suggestion}
                        </span>
                      ))}
                    </div>
                  </div>
                  {/* 风险提示 */}
                  <div className="bg-black/40 p-4 rounded-xl border border-white/5">
                    <span className="text-[9px] text-gray-500 uppercase block mb-2">风险提示</span>
                    <span className={`text-sm font-black ${
                      getRiskLevel(review.dragonStatus, review.stage, review.score) === '高' ? 'text-red-400' :
                      getRiskLevel(review.dragonStatus, review.stage, review.score) === '中' ? 'text-yellow-400' :
                      'text-emerald-400'
                    }`}>
                      {getRiskLevel(review.dragonStatus, review.stage, review.score)}风险
                    </span>
                  </div>
                </div>
                {/* 操作建议 */}
                <div className="mt-4 pt-4 border-t border-white/5">
                  <span className="text-[9px] text-gray-500 uppercase block mb-2">操作建议</span>
                  <p className="text-sm text-gray-300 font-medium">
                    {getTradingAdvice(review.dragonStatus, review.stage, review.score)}
                  </p>
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
                  <input type="file" ref={fileInputRef} multiple onChange={handleFileChange} className="hidden" accept="image/*,.pdf,.txt,.xlsx,.xls" />
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

      {/* 交易复盘中心弹窗 */}
      {showTradeManager && (
        <TradeManager
          trades={trades}
          positions={positions}
          stats={tradeStats}
          buyDistribution={buyTypeDistribution}
          sellDistribution={sellTypeDistribution}
          currentStage={review.stage}
          onAddTrade={addTrade}
          onAddPosition={addPosition}
          onDeleteTrade={deleteTrade}
          onUpdatePositionPrice={updatePositionPrice}
          onClose={() => setShowTradeManager(false)}
        />
      )}
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
