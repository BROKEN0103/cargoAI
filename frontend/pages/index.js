import { useState, useRef } from 'react';
import { useRouter } from 'next/router';
import { Upload, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { uploadImage } from '../services/api';

export default function Home() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [declaredCargo, setDeclaredCargo] = useState('General Goods');
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const fileInputRef = useRef(null);

  const categories = [
    "General Goods",
    "Electronics",
    "Food Items",
    "Furniture",
    "Chemicals",
    "Textiles"
  ];

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsScanning(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('declared_cargo', declaredCargo);
      
      const res = await axios.post('http://localhost:5000/api/scan-cargo', formData);
      router.push(`/results/${res.data.scan_id}`);
    } catch (err) {
      console.error(err);
      setError('Failed to scan cargo image. Ensure backend and ML services are running.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-12">
      <h1 className="text-3xl font-bold mb-2">Initiate Cargo Scan</h1>
      <p className="text-gray-400 mb-8">Upload X-ray or optical cargo imagery for AI risk analysis.</p>

      <div className="bg-gray-800 p-8 rounded-xl border border-gray-700 shadow-xl">
        {!preview ? (
          <div 
            onClick={() => fileInputRef.current.click()}
            className="border-2 border-dashed border-gray-600 rounded-lg p-16 text-center cursor-pointer hover:bg-gray-700/50 transition-colors flex flex-col items-center justify-center gap-4"
          >
            <div className="p-4 bg-gray-900 rounded-full text-blue-500">
              <Upload size={32} />
            </div>
            <div>
              <p className="text-lg font-medium">Click to upload cargo image</p>
              <p className="text-sm text-gray-500 mt-1">Supports PNG, JPG (Max 10MB)</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            <div className="grid grid-cols-1 gap-4">
               <div>
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 block ml-1">Declared Cargo Category</label>
                  <select 
                    value={declaredCargo}
                    onChange={(e) => setDeclaredCargo(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 outline-none"
                  >
                    {categories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
               </div>
            </div>
            <div className="relative rounded-lg overflow-hidden border border-gray-700 bg-gray-900 aspect-video flex items-center justify-center">
              <img src={preview} alt="Upload preview" className="max-h-full max-w-full object-contain" />
            </div>
            
            <div className="flex justify-between items-center bg-gray-900 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-green-500" size={20} />
                <span className="font-mono text-sm text-gray-300">{file.name}</span>
              </div>
              <button 
                onClick={() => { setFile(null); setPreview(null); }}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Remove
              </button>
            </div>

            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center gap-3 text-red-400 text-sm">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={isScanning}
              className={`w-full py-4 rounded-lg font-bold text-lg tracking-wide uppercase transition-all ${
                isScanning 
                  ? 'bg-blue-600/50 text-white cursor-not-allowed animate-pulse' 
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]'
              }`}
            >
              {isScanning ? 'Processing AI Models...' : 'Run Intelligence Scan'}
            </button>
          </div>
        )}
        <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileChange} accept="image/*" />
      </div>
    </div>
  );
}
