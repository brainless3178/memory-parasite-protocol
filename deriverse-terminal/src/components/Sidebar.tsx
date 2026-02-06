'use client';

import React from 'react';
import {
    LayoutDashboard,
    BookOpen,
    TrendingUp,
    Target,
    Activity,
    ShieldAlert,
    ShieldCheck,
    MessageSquareText
} from 'lucide-react';
import { useStore } from '@/lib/store';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'infections', label: 'Ecosystem Map', icon: Activity },
    { id: 'agent-replies', label: 'Agent Replies', icon: MessageSquareText },
    { id: 'community', label: 'Community Signal', icon: BookOpen },
    { id: 'analytics', label: 'Deep Analytics', icon: TrendingUp },
    { id: 'reasoning', label: 'Brain Stream', icon: ShieldAlert },
    { id: 'emergence', label: 'Emergence Log', icon: Target },
    { id: 'safety', label: 'Safety Protocol', icon: ShieldCheck },
];

export const Sidebar = () => {
    const { activeView, setActiveView } = useStore();

    return (
        <aside className="fixed left-0 top-0 h-screen w-64 bg-surface border-r border-border 
                      flex flex-col overflow-hidden z-40">
            {/* Logo */}
            <div className="p-6 border-b border-border">
                <h1 className="text-xl heading text-text-primary tracking-tight">
                    DERIVERSE
                    <span className="block text-xs font-normal text-neutral tracking-wider mt-1">
                        ANALYTICS TERMINAL
                    </span>
                </h1>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setActiveView(item.id)}
                        className={cn(
                            "relative w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group",
                            activeView === item.id
                                ? 'bg-elevated text-neutral'
                                : 'text-text-secondary hover:bg-elevated hover:text-text-primary'
                        )}
                    >
                        {/* Active indicator */}
                        {activeView === item.id && (
                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-neutral rounded-r-full shadow-[0_0_12px_var(--glow-neutral)]" />
                        )}

                        <item.icon className="w-5 h-5" />
                        <span className="font-['Outfit'] font-medium text-sm">{item.label}</span>

                        {/* Hover glow */}
                        <div className="absolute inset-0 bg-neutral/5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                ))}
            </nav>

            {/* Connection Status */}
            <div className="p-4 border-t border-border">
                <div className="flex items-center gap-2 px-3 py-2 bg-elevated rounded-lg">
                    <div className="relative">
                        <div className="w-2 h-2 bg-profit rounded-full animate-pulse" />
                        <div className="absolute inset-0 w-2 h-2 bg-profit rounded-full animate-ping" />
                    </div>
                    <span className="text-xs font-['IBM_Plex_Mono'] text-text-secondary font-bold">
                        PROTOCOL SYNCED
                    </span>
                </div>
            </div>
        </aside>
    );
};
