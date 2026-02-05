'use client';

import React, { useMemo, useRef, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Force graph can only run on client
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

export const EcosystemMap = ({ agents, infections }: { agents: any[], infections: any[] }) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

    useEffect(() => {
        if (containerRef.current) {
            setDimensions({
                width: containerRef.current.clientWidth,
                height: containerRef.current.clientHeight
            });
        }
    }, []);

    const graphData = useMemo(() => {
        const nodes = agents.map(a => ({
            id: a.agent_id,
            name: a.name,
            val: 20,
            group: a.agent_id === 'agent_a' ? 1 : 2
        }));

        // Group infections by unique pairs to set link strength
        const links: any[] = [];
        const pairMap = new Map();

        infections.filter(i => i.accepted).forEach(inf => {
            const key = `${inf.attacker_id}-${inf.target_id}`;
            if (!pairMap.has(key)) {
                pairMap.set(key, { source: inf.attacker_id, target: inf.target_id, value: 0 });
            }
            pairMap.get(key).value += (inf.influence_score || 0.1);
        });

        pairMap.forEach(v => links.push(v));

        return { nodes, links };
    }, [agents, infections]);

    return (
        <div ref={containerRef} className="w-full h-full min-h-[500px] relative bg-void/50 rounded-2xl border border-border overflow-hidden">
            <div className="absolute top-4 left-4 z-20">
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-2 h-2 bg-neutral rounded-full animate-pulse" />
                    <span className="label text-[10px] text-text-primary">Ecosystem Neural Mapping v1.0</span>
                </div>
                <p className="text-[9px] text-text-tertiary uppercase font-['IBM_Plex_Mono']">
                    Tracking {agents.length} nodes & {graphData.links.length} influence vectors
                </p>
            </div>

            <ForceGraph2D
                graphData={graphData}
                width={dimensions.width}
                height={dimensions.height}
                backgroundColor="rgba(0,0,0,0)"
                nodeRelSize={6}
                nodeLabel={(node: any) => `<div class="bg-elevated p-2 border border-border rounded text-[10px] text-neutral font-bold">${node.name} [${node.id}]</div>`}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                    const label = node.id.toUpperCase();
                    const fontSize = 12 / globalScale;
                    ctx.font = `${fontSize}px "IBM Plex Mono"`;

                    // Draw outer glow
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 4, 0, 2 * Math.PI, false);
                    ctx.fillStyle = node.group === 1 ? '#00d4ff' : '#00ffaa';
                    ctx.shadowBlur = 10;
                    ctx.shadowColor = ctx.fillStyle;
                    ctx.fill();

                    // Draw text
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#e4e9f0';
                    ctx.fillText(label, node.x, node.y + 8);
                }}
                linkColor={() => 'rgba(0, 212, 255, 0.2)'}
                linkWidth={(link: any) => Math.sqrt(link.value) * 3}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.01}
                linkDirectionalParticleWidth={2}
                linkDirectionalParticleColor={() => '#CCFF00'}
                d3VelocityDecay={0.3}
            />
        </div>
    );
};
