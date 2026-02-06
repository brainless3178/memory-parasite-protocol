'use client';

import React, { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Infection } from '@/lib/types';

const columns = [
    { key: 'timestamp', label: 'Invasion Time', width: '120px' },
    { key: 'direction', label: 'Vector', width: '100px' },
    { key: 'target', label: 'Specimen', width: '100px' },
    { key: 'suggestion', label: 'Payload Snippet', width: '1fr' },
    { key: 'tx', label: 'Proof [Tx]', width: '120px' },
    { key: 'status', label: 'Status', width: '100px' },
];

interface InfectionTableProps {
  infections: Infection[];
}

export const InfectionTable = ({ infections }: InfectionTableProps) => {
    const parentRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
        count: infections.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 60,
        overscan: 10,
    });

    return (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
            {/* Table Header */}
            <div className="grid gap-4 px-6 py-4 bg-elevated border-b border-border"
                style={{ gridTemplateColumns: '120px 100px 100px 1fr 120px 100px' }}>
                {columns.map(col => (
                    <div key={col.key} className="label">
                        {col.label}
                    </div>
                ))}
            </div>

            {/* Table Body - Virtualized */}
            <div
                ref={parentRef}
                className="h-[500px] overflow-auto scrollbar-thin scrollbar-thumb-border-bright"
            >
                <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
                    {rowVirtualizer.getVirtualItems().map(virtualRow => {
                        const inf = infections[virtualRow.index];
                        const isAccepted = inf.accepted;

                        return (
                            <div
                                key={virtualRow.key}
                                className="absolute top-0 left-0 w-full grid gap-4 px-6 py-4
                           border-b border-border hover:bg-elevated
                           transition-colors group items-center"
                                style={{
                                    height: `${virtualRow.size}px`,
                                    transform: `translateY(${virtualRow.start}px)`,
                                    gridTemplateColumns: '120px 100px 100px 1fr 120px 100px'
                                }}
                            >
                                {/* Timestamp */}
                                <div className="text-xs text-text-primary font-['IBM_Plex_Mono']">
                                    {new Date(inf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </div>

                                {/* Vector */}
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-['IBM_Plex_Mono'] text-neutral font-bold uppercase truncate">
                                        {inf.attacker_id}
                                    </span>
                                </div>

                                {/* Target */}
                                <div className="text-xs font-['IBM_Plex_Mono'] text-text-secondary truncate">
                                    {inf.target_id}
                                </div>

                                {/* Suggestion Snippet */}
                                <div className="text-xs text-text-tertiary truncate font-['IBM_Plex_Mono'] group-hover:text-text-primary transition-colors">
                                    {inf.suggestion}
                                </div>

                                {/* On-Chain Proof */}
                                <div className="text-xs font-['IBM_Plex_Mono'] text-text-muted flex flex-col gap-1">
                                    {(() => {
                                        const sigs = (inf.solana_tx_hash || '').split('|');
                                        const solSig = sigs.find(s => s.startsWith('sol_')) || (!sigs[0]?.startsWith('eth_') ? sigs[0] : null);
                                        const ethSig = sigs.find(s => s.startsWith('eth_'));

                                        return (
                                            <>
                                                {solSig && (
                                                    <a
                                                        href={`https://explorer.solana.com/tx/${solSig.replace('sol_', '')}?cluster=devnet`}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="hover:text-neutral flex items-center gap-1"
                                                    >
                                                        <span className="text-[10px] px-1.5 bg-neutral/10 rounded">SOL</span>
                                                        {solSig.replace('sol_', '').slice(0, 4)}...{solSig.replace('sol_', '').slice(-4)}
                                                    </a>
                                                )}
                                                {ethSig && (
                                                    <a
                                                        href={`https://basescan.org/tx/${ethSig.replace('eth_', '')}`}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="hover:text-blue-400 flex items-center gap-1"
                                                    >
                                                        <span className="text-[10px] px-1.5 bg-blue-500/10 text-blue-400 rounded">BASE</span>
                                                        {ethSig.replace('eth_', '').slice(0, 4)}...{ethSig.replace('eth_', '').slice(-4)}
                                                    </a>
                                                )}
                                                {!solSig && !ethSig && <span>0x...NULL</span>}
                                            </>
                                        );
                                    })()}
                                </div>

                                {/* Status */}
                                <span className={`
                  inline-flex items-center justify-center px-2 py-0.5 rounded text-xs font-bold font-['IBM_Plex_Mono']
                  ${isAccepted
                                        ? 'bg-profit/10 text-profit border border-profit/20 shadow-[0_0_8px_rgba(0,255,170,0.1)]'
                                        : 'bg-loss/10 text-loss border border-loss/20'
                                    }
                `}>
                                    {isAccepted ? 'MUTATED' : 'REJECTED'}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};
