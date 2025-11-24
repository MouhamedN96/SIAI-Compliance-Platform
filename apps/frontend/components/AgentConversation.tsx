'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle, CheckCircle, FileText } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  loading?: boolean;
  error?: boolean;
  findings?: any[];
}

interface AgentConversationProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  onFindingClick: (finding: any) => void;
}

export default function AgentConversation({
  messages,
  onSendMessage,
  onFindingClick,
}: AgentConversationProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !messages.some((m) => m.loading)) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    }).format(date);
  };

  return (
    <div className="h-full bg-white flex flex-col">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">Compliance Agent</h2>
        <p className="text-sm text-gray-500 mt-1">Ask questions about your documents</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.error
                  ? 'bg-red-50 border border-red-200'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.loading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">{message.content}</span>
                </div>
              ) : (
                <>
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  {message.findings && message.findings.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.findings.map((finding, idx) => (
                        <FindingCard
                          key={idx}
                          finding={finding}
                          onClick={() => onFindingClick(finding)}
                        />
                      ))}
                    </div>
                  )}
                </>
              )}
              <p className="text-xs mt-1 opacity-70">{formatTime(message.timestamp)}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about compliance issues..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={messages.some((m) => m.loading)}
          />
          <button
            type="submit"
            disabled={!input.trim() || messages.some((m) => m.loading)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

function FindingCard({ finding, onClick }: { finding: any; onClick: () => void }) {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-100 border-red-300 text-red-800';
      case 'medium':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'low':
        return 'bg-blue-100 border-blue-300 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-300 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return <AlertCircle className="w-4 h-4" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4" />;
      case 'low':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div
      onClick={onClick}
      className={`p-3 rounded-lg border cursor-pointer hover:shadow-md transition-shadow ${getSeverityColor(
        finding.severity || 'low'
      )}`}
    >
      <div className="flex items-start gap-2">
        {getSeverityIcon(finding.severity || 'low')}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase">
              {finding.framework || 'Compliance'}
            </span>
            <span className="text-xs opacity-75">•</span>
            <span className="text-xs font-medium">{finding.severity || 'Low'}</span>
          </div>
          <p className="text-sm font-medium">{finding.title || finding.issue}</p>
          {finding.description && (
            <p className="text-xs mt-1 opacity-75">{finding.description}</p>
          )}
          {finding.location && (
            <p className="text-xs mt-2 opacity-60">
              📄 Page {finding.location.page}, Line {finding.location.line}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
