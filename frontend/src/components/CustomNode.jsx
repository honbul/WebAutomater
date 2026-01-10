import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { MousePointer2, Type, RefreshCw, Play } from 'lucide-react';

const icons = {
  click: MousePointer2,
  input: Type,
  loop: RefreshCw,
  start: Play
};

const CustomNode = ({ data, id }) => {
  const Icon = icons[data.type] || MousePointer2;
  const stepNumber = id.startsWith('step-') ? parseInt(id.split('-')[1]) + 1 : (data.type === 'start' ? 'S' : '');
  
  return (
    <div className="relative group">
      {stepNumber && (
        <div className="absolute -top-3 -left-3 w-6 h-6 bg-stone-800 text-white text-xs font-bold rounded-full flex items-center justify-center z-10 shadow-sm border-2 border-white">
          {stepNumber}
        </div>
      )}

      <div className="px-4 py-3 shadow-md rounded-md bg-white border-2 border-stone-200 min-w-[200px] flex items-center gap-3 transition-shadow hover:shadow-lg">
        <div className={`p-2 rounded-full ${data.type === 'start' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
          <Icon size={16} />
        </div>
        <div>
          <div className="text-xs font-bold text-gray-500 uppercase">{data.label}</div>
          <div className="text-sm font-medium text-gray-900 truncate max-w-[180px]">
            {data.details}
          </div>
        </div>
        
        <Handle type="target" position={Position.Top} className="w-16 !bg-stone-300" />
        <Handle type="source" position={Position.Bottom} className="w-16 !bg-stone-300" />
      </div>

      <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-max max-w-[300px] px-3 py-2 bg-stone-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
        <div className="font-bold mb-1 border-b border-stone-600 pb-1">Step {stepNumber}: {data.label}</div>
        <div className="font-mono bg-stone-900 px-1 py-0.5 rounded break-all">{data.fullSelector || data.details}</div>
        {data.value && <div className="mt-1 text-stone-300">Value: "{data.value}"</div>}
        {data.loopCount && <div className="mt-1 text-blue-300">Repeat: {data.loopCount} times</div>}
        <div className="absolute -top-1 left-1/2 -translate-x-1/2 border-4 border-transparent border-b-stone-800"></div>
      </div>
    </div>
  );
};

export default memo(CustomNode);
