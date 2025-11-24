'use client';

import { useState } from 'react';
import DocumentViewer from '@/components/DocumentViewer';
import AgentConversation from '@/components/AgentConversation';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable';

export default function Home() {
  const [currentDocument, setCurrentDocument] = useState<string | null>(null);
  const [highlights, setHighlights] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome to SIAI Compliance Platform. Upload a document to begin analysis.',
      timestamp: new Date(),
    },
  ]);

  const handleDocumentUpload = async (file: File) => {
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `Uploaded: ${file.name}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add loading message
    const loadingMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Analyzing document...',
      timestamp: new Date(),
      loading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      // Upload document to backend
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await fetch('http://localhost:8000/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      const { document_id } = await uploadResponse.json();

      // Set current document for viewer
      setCurrentDocument(URL.createObjectURL(file));

      // Trigger analysis
      const analyzeResponse = await fetch(
        `http://localhost:8000/documents/${document_id}/analyze`,
        {
          method: 'POST',
        }
      );

      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed');
      }

      // Get findings
      const findingsResponse = await fetch(
        `http://localhost:8000/documents/${document_id}/findings`
      );
      const findings = await findingsResponse.json();

      // Remove loading message
      setMessages((prev) => prev.filter((m) => !m.loading));

      // Add analysis complete message
      const completeMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Analysis complete. Found ${findings.length} compliance issues.`,
        timestamp: new Date(),
        findings: findings,
      };
      setMessages((prev) => [...prev, completeMessage]);

      // Set highlights for document viewer
      setHighlights(findings);
    } catch (error) {
      console.error('Error:', error);
      setMessages((prev) =>
        prev.filter((m) => !m.loading).concat({
          id: Date.now().toString(),
          role: 'assistant',
          content: 'Error analyzing document. Please try again.',
          timestamp: new Date(),
          error: true,
        })
      );
    }
  };

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add loading message
    const loadingMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'Thinking...',
      timestamp: new Date(),
      loading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    // TODO: Send message to backend agent
    // For now, simulate response
    setTimeout(() => {
      setMessages((prev) =>
        prev.filter((m) => !m.loading).concat({
          id: Date.now().toString(),
          role: 'assistant',
          content: 'This is a placeholder response. Agent integration coming next.',
          timestamp: new Date(),
        })
      );
    }, 1000);
  };

  const handleFindingClick = (finding: any) => {
    // Scroll document viewer to the finding location
    console.log('Navigate to finding:', finding);
    // TODO: Implement document navigation
  };

  return (
    <main className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">SI</span>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">SIAI Compliance Platform</h1>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            Settings
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="horizontal">
          {/* Document Viewer */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <DocumentViewer
              document={currentDocument}
              highlights={highlights}
              onUpload={handleDocumentUpload}
            />
          </ResizablePanel>

          <ResizableHandle className="w-1 bg-gray-200 hover:bg-blue-500 transition-colors" />

          {/* Agent Conversation */}
          <ResizablePanel defaultSize={50} minSize={30}>
            <AgentConversation
              messages={messages}
              onSendMessage={handleSendMessage}
              onFindingClick={handleFindingClick}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </main>
  );
}
