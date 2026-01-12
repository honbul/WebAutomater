import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  applyEdgeChanges, 
  applyNodeChanges,
  addEdge,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';
import { Send, Play, Square, MessageSquare, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import CustomNode from './components/CustomNode';

const nodeTypes = {
  custom: CustomNode,
};

const API_URL = 'http://localhost:8002';

const INITIAL_NODES = [
  { 
    id: 'start', 
    type: 'custom', 
    position: { x: 250, y: 0 }, 
    data: { type: 'start', label: 'Start', details: 'Workflow Entry' } 
  }
];

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [recording, setRecording] = useState(false);
  const [url, setUrl] = useState('https://example.com');
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Hello! I can help you modify your scraping workflow. Just ask!' }
  ]);
  const [loading, setLoading] = useState(false);
  
  const [executionStatus, setExecutionStatus] = useState('idle'); 
  const [statusMessage, setStatusMessage] = useState('');

  // Polling for events when recording
  useEffect(() => {
    let interval;
    if (recording) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}/record/events`);
          updateGraphFromEvents(res.data);
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [recording]);

  const updateGraphFromEvents = (events) => {
    if (!events || events.length === 0) return;

    const newNodes = [...INITIAL_NODES];
    const newEdges = [];
    
    let lastNodeId = 'start';

    events.forEach((event, index) => {
      const id = `step-${index}`;
      const label = event.type === 'click' ? 'Click Element' : 'Input Text';
      const details = event.selector.split('>').pop() || event.selector;
      
      newNodes.push({
        id,
        type: 'custom',
        position: { x: 250, y: (index + 1) * 100 },
        data: { 
          type: event.type, 
          label: event.type, 
          details: details.length > 20 ? details.substring(0, 20) + '...' : details,
          fullSelector: event.selector,
          value: event.value
        }
      });

      newEdges.push({
        id: `e-${lastNodeId}-${id}`,
        source: lastNodeId,
        target: id,
        animated: true
      });

      lastNodeId = id;
    });

    setNodes(newNodes);
    setEdges(newEdges);
  };

  const validateUrl = (str) => {
    try {
      new URL(str);
      return true;
    } catch (_) {
      return false;
    }
  };

  const toggleRecording = async () => {
    setExecutionStatus('idle');
    setStatusMessage('');

    try {
      if (recording) {
        // Stop
        await axios.post(`${API_URL}/record/stop`);
        setRecording(false);
        setStatusMessage("Recording stopped.");
      } else {
        if (!validateUrl(url)) {
          setExecutionStatus('error');
          setStatusMessage("Invalid URL. Please enter a valid URL (e.g., https://example.com)");
          return;
        }

         // Start
         await axios.post(`${API_URL}/record/start`, { 
             url,
             enable_bypass_mode: window.enableBypass || false
         });
         setRecording(true);
        // Reset graph
        setNodes(INITIAL_NODES);
        setEdges([]);
        setStatusMessage("Recording started...");
      }
    } catch (e) {
      setExecutionStatus('error');
      setStatusMessage("Error communicating with backend: " + (e.response?.data?.detail || e.message));
    }
  };

  const runWorkflow = async () => {
    if (nodes.length <= 1) {
       setStatusMessage("Workflow is empty. Record some steps first.");
       return;
    }

    setExecutionStatus('running');
    setStatusMessage("Running workflow...");

    try {
      const currentWorkflow = [];
      let i = 0;
      
      const orderedNodes = nodes.filter(n => n.id !== 'start').sort((a, b) => {
        return a.position.y - b.position.y;
      });

      while (i < orderedNodes.length) {
        const node = orderedNodes[i];
        
        if (node.data.loopId) {
            const loopNodes = [];
            const loopId = node.data.loopId;
            const loopSelector = node.data.loopSelector;
            
            while (i < orderedNodes.length && orderedNodes[i].data.loopId === loopId) {
                loopNodes.push(orderedNodes[i]);
                i++;
            }
            
            currentWorkflow.push({
                type: 'loop',
                loop_selector: loopSelector,
                count: node.data.loopCount,
                inner_steps: loopNodes.map(n => ({
                    type: n.data.type,
                    selector: n.data.fullSelector || n.data.details,
                    value: n.data.value
                }))
            });
        } else {
            currentWorkflow.push({
                type: node.data.type,
                selector: node.data.fullSelector || node.data.details,
                value: node.data.value
            });
            i++;
        }
      }

      await axios.post(`${API_URL}/run`, {
        url: url,
        actions: currentWorkflow,
        enable_bypass_mode: window.enableBypass || false
      });
      
      setExecutionStatus('success');
      setStatusMessage("Workflow execution started successfully! Check the browser.");
      
      setTimeout(() => {
          if (executionStatus === 'success') setExecutionStatus('idle');
      }, 5000);

    } catch (e) {
      setExecutionStatus('error');
      setStatusMessage("Error running workflow: " + (e.response?.data?.detail || e.message));
    }
  };

  const applyAICommands = (commands) => {
      if (!commands || !Array.isArray(commands)) return;
      
      const newNodes = [...nodes];
      
      let workflowNodes = newNodes.filter(n => n.id !== 'start');
      const startNode = newNodes.find(n => n.id === 'start');
      let modificationSummary = [];
      
      commands.forEach(cmd => {
          if (cmd.command === 'WRAP_IN_LOOP') {
              const { start_index, end_index, loop_selector, count } = cmd;
              
              const loopLabel = count ? `Repeat ${count}x` : `Loop ${loop_selector || ''}`;
              modificationSummary.push(`Wrapped steps ${start_index+1}-${end_index+1} in loop: ${loopLabel}`);

              for (let i = start_index; i <= end_index; i++) {
                  if (workflowNodes[i]) {
                      workflowNodes[i].data = {
                          ...workflowNodes[i].data,
                          loopId: `loop-${Date.now()}`,
                          loopSelector: loop_selector,
                          loopCount: count,
                          originalLabel: workflowNodes[i].data.label,
                          label: `(Loop) ${workflowNodes[i].data.label}`,
                          details: count ? `Repeat ${count} times` : (loop_selector || workflowNodes[i].data.details)
                      };
                      workflowNodes[i].style = { ...workflowNodes[i].style, border: '2px solid #2563eb', background: '#eff6ff' };
                  }
              }
          }
          else if (cmd.command === 'CHANGE_SELECTOR') {
              const { step_index, new_selector } = cmd;
              if (workflowNodes[step_index]) {
                  const oldSelector = workflowNodes[step_index].data.fullSelector;
                  workflowNodes[step_index].data.fullSelector = new_selector;
                  workflowNodes[step_index].data.details = new_selector;
                  modificationSummary.push(`Updated step ${step_index+1} selector: ${oldSelector} -> ${new_selector}`);
                  
                  workflowNodes[step_index].style = { ...workflowNodes[step_index].style, border: '2px solid #eab308', background: '#fefce8' };
              }
          }
      });
      
      setNodes([startNode, ...workflowNodes]);
      
      if (modificationSummary.length > 0) {
          const summaryMsg = { role: 'system', content: 'Changes applied:\n' + modificationSummary.join('\n') };
          setMessages(prev => [...prev, summaryMsg]);
      }
  };

  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = { role: 'user', content: chatInput };
    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setLoading(true);

    try {
      const currentWorkflow = nodes
        .filter(n => n.id !== 'start')
        .map(n => ({
          type: n.data.type,
          selector: n.data.fullSelector || n.data.details
        }));

      const res = await axios.post(`${API_URL}/modify-workflow`, {
        current_flow: currentWorkflow,
        user_prompt: userMsg.content
      });

      const aiMsg = { role: 'ai', content: 'I have updated the workflow based on your request.' };
      setMessages(prev => [...prev, aiMsg]);

      console.log("AI Commands:", res.data);
      applyAICommands(res.data);

    } catch (e) {
      setMessages(prev => [...prev, { role: 'system', content: 'Error: ' + e.message }]);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="flex h-screen w-screen bg-stone-50 overflow-hidden">
      {/* Sidebar / Chat */}
      <div className="w-96 flex flex-col border-r border-stone-200 bg-white">
        <div className="p-4 border-b border-stone-200 font-bold text-lg flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center text-white">
            S
          </div>
          Scraper V2
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-3 rounded-lg text-sm ${
                m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-stone-100 text-stone-800'
              }`}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && <div className="text-stone-400 text-xs text-center animate-pulse">AI is thinking...</div>}
        </div>

        <div className="p-4 border-t border-stone-200">
           <div className="flex gap-2">
             <input 
               className="flex-1 border border-stone-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
               placeholder="Ask to modify workflow..."
               value={chatInput}
               onChange={e => setChatInput(e.target.value)}
               onKeyDown={e => e.key === 'Enter' && sendMessage()}
             />
             <button onClick={sendMessage} className="p-2 bg-stone-800 text-white rounded-md hover:bg-stone-700">
               <Send size={18} />
             </button>
           </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="h-16 border-b border-stone-200 bg-white flex items-center px-6 gap-4 shadow-sm z-10">
           <input 
             className="flex-1 max-w-md border border-stone-300 rounded-md px-3 py-2 text-sm"
             value={url}
             onChange={e => setUrl(e.target.value)}
             placeholder="https://example.com"
           />
           <button 
             onClick={toggleRecording}
             disabled={recording && executionStatus === 'running'}
             className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
               recording 
               ? 'bg-red-100 text-red-600 hover:bg-red-200 border border-red-200' 
               : 'bg-blue-600 text-white hover:bg-blue-700'
             }`}
           >
             {recording ? <><Square size={18} /> Stop Recording</> : <><Play size={18} /> Start Recording</>}
           </button>

           <button
             onClick={async () => {
                 const selector = prompt("Enter CSS selector (e.g., button#submit):", "body");
                 if (!selector) return;
                 
                 const id = `step-${nodes.length}`;
                 const newNode = {
                    id,
                    type: 'custom',
                    position: { x: 250, y: nodes.length * 100 },
                    data: { 
                      type: 'click', 
                      label: 'Click Element', 
                      details: selector,
                      fullSelector: selector,
                      value: ''
                    }
                 };
                 setNodes(nds => [...nds, newNode]);
                 setEdges(eds => [...edges, { id: `e-${nodes[nodes.length-1].id}-${id}`, source: nodes[nodes.length-1].id, target: id, animated: true }]);
                 
                 // Optionally sync with backend if recording is active
                 if (recording) {
                     try {
                         await axios.post(`${API_URL}/record/event`, {
                             type: 'click',
                             selector: selector,
                             value: ''
                         });
                     } catch (e) {
                         console.error("Failed to sync manual event", e);
                     }
                 }
             }}
             className="flex items-center gap-2 px-4 py-2 bg-stone-200 text-stone-700 rounded-md font-medium hover:bg-stone-300 transition-colors"
           >
             + Add Step
           </button>

           <div className="flex items-center gap-4 ml-auto">
             <label className="flex items-center gap-2 text-sm text-stone-700 font-medium cursor-pointer bg-stone-100 px-3 py-1.5 rounded-md border border-stone-200">
                 <input 
                     type="checkbox" 
                     className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                     onChange={(e) => window.enableBypass = e.target.checked}
                 />
                 Bypass Mode
             </label>

             <button 
               onClick={runWorkflow}
               disabled={executionStatus === 'running' || (nodes.length <= 1 && !recording)}
               className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
                   executionStatus === 'running' 
                   ? 'bg-green-800 text-white cursor-not-allowed'
                   : 'bg-green-600 text-white hover:bg-green-700'
               }`}
             >
               {executionStatus === 'running' ? <Loader2 size={18} className="animate-spin"/> : <Play size={18} />}
               {executionStatus === 'running' ? 'Running...' : 'Run Workflow'}
             </button>
           </div>
        </div>
        
        {/* Status Bar */}
        {(statusMessage || executionStatus !== 'idle') && (
            <div className={`px-6 py-2 text-sm flex items-center gap-2 ${
                executionStatus === 'error' ? 'bg-red-50 text-red-700 border-b border-red-100' :
                executionStatus === 'success' ? 'bg-green-50 text-green-700 border-b border-green-100' :
                'bg-blue-50 text-blue-700 border-b border-blue-100'
            }`}>
                {executionStatus === 'error' && <AlertCircle size={16} />}
                {executionStatus === 'success' && <CheckCircle2 size={16} />}
                {executionStatus === 'running' && <Loader2 size={16} className="animate-spin" />}
                {statusMessage}
            </div>
        )}

        {/* React Flow */}
        <div className="flex-1 bg-stone-50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#e7e5e4" gap={20} />
            <Controls />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
