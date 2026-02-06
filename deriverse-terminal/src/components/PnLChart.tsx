'use client';

import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { ChartDataPoint } from '@/lib/types';

interface PnLChartProps {
  data: ChartDataPoint[];
  timeframe?: string;
}

export const PnLChart = ({ data, timeframe = 'LIVE' }: PnLChartProps) => {
    // Determine trend
    const isPositive = data.length > 1 ? data[data.length - 1]?.value > data[0]?.value : true;
    const accentColor = isPositive ? 'var(--profit)' : 'var(--loss)';

    return (
        <div className="bg-surface border border-border rounded-xl p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="heading text-lg text-text-primary">
                        Ecosystem Influence
                    </h3>
                    <p className="text-sm text-text-tertiary mt-1">
                        Total parasitic dominance over {timeframe}
                    </p>
                </div>

                {/* Timeframe selector */}
                <div className="flex gap-2">
                    {['1H', '12H', '24H', 'LIVE'].map(period => (
                        <button
                            key={period}
                            className={`
                px-3 py-1.5 rounded-lg text-xs font-['IBM_Plex_Mono'] font-bold
                transition-all duration-200
                ${timeframe === period
                                    ? 'bg-neutral text-base shadow-[0_0_12px_var(--glow-neutral)]'
                                    : 'bg-elevated text-text-secondary hover:bg-hover'
                                }
              `}
                        >
                            {period}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="h-[320px] w-full min-h-[320px] isolate">
                {data.length > 1 ? (
                    <ResponsiveContainer width="99%" height="99%">
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={accentColor} stopOpacity={0.25} />
                                    <stop offset="50%" stopColor={accentColor} stopOpacity={0.1} />
                                    <stop offset="100%" stopColor={accentColor} stopOpacity={0} />
                                </linearGradient>
                            </defs>

                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="var(--grid)"
                                strokeOpacity={0.3}
                                vertical={false}
                            />

                            <XAxis
                                dataKey="timestamp"
                                stroke="var(--text-tertiary)"
                                style={{ fontSize: '10px', fontFamily: 'IBM Plex Mono' }}
                                tickLine={false}
                                axisLine={{ stroke: 'var(--border)' }}
                            />

                            <YAxis
                                stroke="var(--text-tertiary)"
                                style={{ fontSize: '10px', fontFamily: 'IBM Plex Mono' }}
                                tickLine={false}
                                axisLine={{ stroke: 'var(--border)' }}
                            />

                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'var(--elevated)',
                                    border: '1px solid var(--border-bright)',
                                    borderRadius: '8px',
                                    padding: '12px',
                                    fontFamily: 'IBM Plex Mono',
                                    fontSize: '12px',
                                    boxShadow: 'var(--shadow-lg)',
                                }}
                                labelStyle={{
                                    color: 'var(--text-secondary)',
                                    marginBottom: '8px',
                                    fontSize: '10px',
                                }}
                                itemStyle={{ color: 'var(--text-primary)' }}
                            />

                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke={accentColor}
                                strokeWidth={2}
                                fill="url(#pnlGradient)"
                                dot={false}
                                activeDot={{
                                    r: 4,
                                    fill: accentColor,
                                    stroke: 'var(--base)',
                                    strokeWidth: 2,
                                }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center border border-dashed border-border rounded-lg bg-void/30">
                        <div className="text-xs font-['IBM_Plex_Mono'] text-text-muted animate-pulse">
                            SCANNING NEURAL VECTORS...
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
