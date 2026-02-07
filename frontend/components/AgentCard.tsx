import React from 'react';
import Link from 'next/link';

interface Agent {
    id: string;
    name: string;
    created_at: string;
    conversation_model: string;
    system_prompt: string;
}

interface AgentCardProps {
    agent: Agent;
    onDelete: (id: string) => void;
    onStartCall: (id: string) => void;
}

export default function AgentCard({ agent, onDelete, onStartCall }: AgentCardProps) {
    return (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-200 hover:border-blue-300">
            <div className="flex justify-between items-center mb-3">
                <h3 className="text-xl font-semibold text-gray-900 truncate">
                    {agent.name}
                </h3>
                <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ml-2">
                    {agent.conversation_model}
                </span>
            </div>

            <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-2">
                {agent.system_prompt.substring(0, 100)}...
            </p>

            <div className="mt-4 pt-4 border-t border-gray-200">
                <span className="text-gray-400 text-xs block mb-3">
                    Created: {new Date(agent.created_at).toLocaleDateString()}
                </span>

                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={() => onStartCall(agent.id)}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                        Start Call
                    </button>

                    <Link href={`/agents/edit/${agent.id}`}>
                        <button className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200">
                            Edit
                        </button>
                    </Link>

                    <button
                        onClick={() => onDelete(agent.id)}
                        className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>
    );
}
