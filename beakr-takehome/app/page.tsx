"use client";

import { useState, useCallback, useRef, useEffect } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
};

type EnrolledDocument = {
  filename: string;
  file_hash: string;
  file_type: string;
  version: number;
  first_seen?: string;
  last_seen?: string;
};

export default function Home() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  
  const [documents, setDocuments] = useState<EnrolledDocument[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch("http://localhost:8000/api/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed with status ${response.status}`);
      }

      const data = await response.json();
      setUploadResult(data);
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || "An error occurred during upload");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isTyping) return;

    const userMessage: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setIsTyping(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: userMessage.content }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I encountered an error searching the database." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-zinc-950 font-sans text-zinc-900 dark:text-zinc-100">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 p-4 px-8 flex items-center justify-between">
        <h1 className="text-xl font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
          Beakr Knowledge Base
        </h1>
      </header>

      <main className="flex-1 flex flex-col md:flex-row max-w-[90rem] w-full mx-auto p-4 gap-6 py-6">
        
        {/* Left Column: Upload Status */}
        <section className="w-full md:w-1/3 flex flex-col gap-6">
          <div className="bg-white dark:bg-zinc-900 rounded-3xl p-8 shadow-sm border border-zinc-200 dark:border-zinc-800 flex flex-col">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Upload Document
            </h2>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById("fileInput")?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300
                ${isDragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-inner' : 'border-zinc-300 dark:border-zinc-700/80 bg-zinc-50/50 dark:bg-zinc-800/30 hover:bg-zinc-100 dark:hover:bg-zinc-800/80'}
              `}
            >
              <input id="fileInput" type="file" className="hidden" accept=".pdf,.docx,.xlsx" onChange={handleFileSelect} />
              <div className={`w-14 h-14 mb-4 rounded-full flex items-center justify-center transition-colors duration-300 ${isDragging ? 'bg-blue-600 text-white' : 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400'}`}>
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
              </div>
              <p className="font-semibold text-base">Drag & drop or click to browse</p>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2 font-medium">PDF, DOCX, XLSX</p>
            </div>

            {isUploading && (
              <div className="mt-6 p-5 text-sm flex flex-col items-center justify-center text-blue-700 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/40 rounded-xl animate-pulse">
                <div className="flex space-x-2 mb-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
                <span className="font-medium">Parsing and embedding document...</span>
              </div>
            )}
            
            {uploadError && (
              <div className="mt-6 p-5 text-sm flex items-start gap-3 text-red-700 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800/40 rounded-xl">
                 <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <div className="flex flex-col">
                  <span className="font-semibold">Upload Failed</span>
                  <span className="opacity-90 mt-0.5">{uploadError}</span>
                </div>
              </div>
            )}
            
            {uploadResult && !isUploading && (
              <div className="mt-6 p-5 text-sm flex flex-col gap-1 text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800/30 rounded-xl">
                <p className="font-bold flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                  Ingestion Complete!
                </p>
                <p className="opacity-80 mt-1"><span className="font-bold">{uploadResult.chunks_processed}</span> semantic chunks extracted and stored in Vector DB.</p>
              </div>
            )}
          </div>

          {/* Below the Upload Box: Indexed Documents */}
          <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-200 dark:border-zinc-800 flex flex-col flex-1 h-[calc(100vh-28rem)] max-h-[400px]">
            <h3 className="text-md font-semibold mb-4 flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
              Indexed Database
            </h3>
            
            <div className="flex-1 overflow-y-auto pr-1 scrollbar-thin">
              {isLoadingDocs ? (
                <div className="flex justify-center items-center h-full">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : documents.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-zinc-400 h-full text-center px-4">
                    <svg className="w-8 h-8 mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" /></svg>
                    <p className="text-sm">No documents parsed yet.</p>
                </div>
              ) : (
                <ul className="space-y-3">
                  {documents.map((doc, i) => (
                     <li key={i} className="flex items-center gap-4 p-3.5 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800/80 hover:border-blue-200 dark:hover:border-blue-900/50 transition-colors group">
                       <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0 shadow-sm">
                         <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                       </div>
                       <div className="flex flex-col overflow-hidden w-full">
                         <div className="flex items-center justify-between">
                           <span className="font-semibold text-zinc-700 dark:text-zinc-200 truncate text-[13px]">{doc.filename}</span>
                           <span className="text-[10px] bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded-full font-bold ml-2">v{doc.version}</span>
                         </div>
                         <div className="flex flex-col gap-0.5 mt-1">
                            <span className="text-[9px] text-zinc-400 font-mono truncate">ID: {doc.file_hash.substring(0, 12)}...</span>
                            {doc.last_seen && (
                              <span className="text-[9px] text-zinc-500 italic">Updated: {new Date(doc.last_seen).toLocaleString()}</span>
                            )}
                         </div>
                       </div>
                     </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>

        {/* Right Column: Chat Interface */}
        <section className="w-full md:w-2/3 flex flex-col bg-white dark:bg-zinc-900 rounded-3xl shadow-sm border border-zinc-200 dark:border-zinc-800 overflow-hidden h-[calc(100vh-7rem)]">
          
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 bg-zinc-50/30 dark:bg-zinc-900/30">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-400 space-y-5 px-4 text-center">
                <div className="w-20 h-20 bg-zinc-100 dark:bg-zinc-800 rounded-full flex items-center justify-center mb-2">
                  <svg className="w-10 h-10 text-zinc-300 dark:text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-zinc-700 dark:text-zinc-300">Ready to Answer</h3>
                <p className="max-w-md text-zinc-500">Drop a document on the left, then ask questions here to instantly retrieve relevant facts and snippets.</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-5 py-4 ${msg.role === 'user' ? 'bg-blue-600 text-white shadow-md rounded-tr-sm' : 'bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 shadow-sm rounded-tl-sm'}`}>
                    <div className="prose dark:prose-invert max-w-none text-[15px] leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>
                  
                  {/* Source Citations for Assistant Messages */}
                  {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 w-full max-w-[95%] flex flex-col gap-2">
                      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-widest pl-1 font-sans">Retrieved Context</p>
                      <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-thin">
                        {msg.sources.map((src, i) => (
                          <div key={i} className="min-w-[300px] max-w-[300px] flex-shrink-0 bg-white dark:bg-zinc-800 rounded-xl p-4 border border-zinc-200 dark:border-zinc-700 shadow-sm">
                            <div className="flex items-center justify-between mb-3 border-b border-zinc-100 dark:border-zinc-700/50 pb-2">
                                <span className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-semibold text-[11px] uppercase tracking-wide truncate">
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                    {src.metadata.filename}
                                </span>
                                <span className="text-[10px] text-zinc-400 font-mono bg-zinc-100 dark:bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-800">
                                    Dist: {(src.similarity_distance || 0).toFixed(3)}
                                </span>
                            </div>
                            {src.metadata.headings && (
                                <span className="text-[10px] font-bold text-zinc-500 uppercase block mb-2 tracking-wide truncate border-l-2 border-blue-400 pl-2">
                                   {src.metadata.headings.replace(/ > /g, ' • ')}
                                </span>
                            )}
                            <div className="text-zinc-600 dark:text-zinc-400 text-xs leading-relaxed max-h-[120px] overflow-y-auto pr-1">
                                {src.chunk_type === 'table' ? (
                                    <pre className="whitespace-pre-wrap font-mono text-[10px] opacity-80">{src.text}</pre>
                                ) : (
                                    <p className="line-clamp-4">{src.text}</p>
                                )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
            
            {isTyping && (
              <div className="flex items-start">
                <div className="bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-5 shadow-sm rounded-tl-sm flex items-center gap-3">
                  <div className="flex space-x-1.5">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-xs text-zinc-500 font-medium">Synthesizing...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 md:p-6 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800">
            <form onSubmit={handleSendMessage} className="relative flex items-center shadow-sm max-w-4xl mx-auto">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about your documents..."
                className="w-full bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/50 rounded-full pl-6 pr-14 py-4 text-[15px] focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder:text-zinc-400"
                disabled={isTyping}
              />
              <button 
                type="submit" 
                disabled={!query.trim() || isTyping}
                className="absolute right-2 p-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-300 disabled:dark:bg-zinc-800 text-white rounded-full transition-colors flex items-center justify-center shadow-md disabled:shadow-none"
              >
                <svg className="w-5 h-5 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </form>
          </div>

        </section>
      </main>
    </div>
  );
}
