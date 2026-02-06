'use client';

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { useSpring, animated } from '@react-spring/web';

interface AnimatedNumberProps {
    value: number;
    decimals?: number;
    prefix?: string;
    suffix?: string;
}

export const AnimatedNumber = ({ value, decimals = 2, prefix = '', suffix = '' }: AnimatedNumberProps) => {
    const { number } = useSpring({
        from: { number: 0 },
        number: value,
        delay: 200,
        config: { mass: 1, tension: 20, friction: 10 },
    });

    return (
        <animated.span>
            {number.to(n => `${prefix}${n.toFixed(decimals)}${suffix}`)}
        </animated.span>
    );
};

interface MetricCardProps {
    label: string;
    value: number;
    decimals?: number;
    prefix?: string;
    suffix?: string;
    change?: number;
    trend?: 'positive' | 'negative' | 'neutral';
}

export const MetricCard = ({
    label,
    value,
    decimals = 0,
    prefix = '',
    suffix = '',
    change,
    trend = 'neutral'
}: MetricCardProps) => {
    const trendColors = {
        positive: 'var(--profit)',
        negative: 'var(--loss)',
        neutral: 'var(--neutral)',
    };

    const color = trendColors[trend];

    return (
        <div className="group relative bg-surface border border-border rounded-xl p-5
                    hover:border-border-bright hover:shadow-lg transition-all duration-300">
            {/* Accent line */}
            <div
                className="absolute left-0 top-0 bottom-0 w-0.5 rounded-l-xl opacity-0 
                   group-hover:opacity-100 transition-opacity"
                style={{ backgroundColor: color }}
            />

            {/* Label */}
            <p className="label mb-2">
                {label}
            </p>

            {/* Value */}
            <div className="flex items-baseline gap-3">
                <p
                    className="metric-value text-3xl font-bold"
                    style={{ color }}
                >
                    <AnimatedNumber value={value} decimals={decimals} prefix={prefix} suffix={suffix} />
                </p>

                {change !== undefined && (
                    <div className="flex items-center gap-1">
                        {change > 0 ? (
                            <TrendingUp className="w-4 h-4" style={{ color }} />
                        ) : (
                            <TrendingDown className="w-4 h-4" style={{ color }} />
                        )}
                        <span className="metric-value text-sm font-bold" style={{ color }}>
                            {change > 0 ? '+' : ''}{change.toFixed(1)}%
                        </span>
                    </div>
                )}
            </div>

            {/* Hover glow */}
            <div
                className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 
                   transition-opacity pointer-events-none"
                style={{
                    boxShadow: `0 0 24px ${color}20`,
                }}
            />
        </div>
    );
};
