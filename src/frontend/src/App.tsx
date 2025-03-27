import { useState } from 'react';
import { Header } from './components/Layouts/Header';
import { ChatBox } from './components/Chat/ChatBox';
import { DocumentUploader } from './components/DocumentUploader';
import { SettingsModal } from './components/Settings/SettingsModal';

function App() {
  const [showUploader, setShowUploader] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [apiKey, setApiKey] = useState('');

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onUploadClick={() => setShowUploader(true)} onSettingsClick={() => setShowSettings(true)}/>
      <ChatBox uploadedFiles={[]} selectedFiles={[]} onFileSelect={() => {}} onUploadClick={() => {}} />
      
      {showUploader && (
        <DocumentUploader
          onClose={() => setShowUploader(false)}
        />
      )}
      {showSettings && (
        <SettingsModal
          isOpen={showSettings}
          onClose={() => setShowSettings(false)}
          apiKey={apiKey}
          onSaveApiKey={setApiKey}
        />
      )}
    </div>
  );
}

export default App;