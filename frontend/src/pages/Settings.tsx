
import React, { useState, useEffect } from 'react';
import { usePythonChat } from '@/contexts/PythonChatContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const Settings: React.FC = () => {
  const { llmConfig, updateLLMConfig } = usePythonChat();
  const [config, setConfig] = useState({ ...llmConfig });
  const [pythonStatus, setPythonStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  
  useEffect(() => {
    // Check Python backend connection
    fetch('http://localhost:5000/api')
      .then(response => {
        if (response.ok) {
          setPythonStatus('connected');
        } else {
          setPythonStatus('error');
        }
      })
      .catch(() => {
        setPythonStatus('error');
      });
  }, []);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateLLMConfig(config);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      
      <main className="flex-1">
        <div className="lloyds-container py-10">
          <h1 className="text-3xl font-bold mb-8 text-lloyds-darkGreen">Settings</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            <div className="md:col-span-8">
              <Card>
                <CardHeader>
                  <CardTitle>AI Model Configuration</CardTitle>
                  <CardDescription>
                    Configure the AI model for your RetireIQ assistant
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="provider">AI Provider</Label>
                      <Select 
                        value={config.provider} 
                        onValueChange={(value) => setConfig({ ...config, provider: value as any })}
                      >
                        <SelectTrigger id="provider">
                          <SelectValue placeholder="Select provider" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="openai">OpenAI</SelectItem>
                          <SelectItem value="anthropic">Anthropic</SelectItem>
                          <SelectItem value="perplexity">Perplexity</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="modelName">Model Name</Label>
                      <Select 
                        value={config.modelName} 
                        onValueChange={(value) => setConfig({ ...config, modelName: value })}
                      >
                        <SelectTrigger id="modelName">
                          <SelectValue placeholder="Select model" />
                        </SelectTrigger>
                        <SelectContent>
                          {config.provider === 'openai' && (
                            <>
                              <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                              <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                              <SelectItem value="gpt-4.5-preview">GPT-4.5 Preview</SelectItem>
                            </>
                          )}
                          {config.provider === 'anthropic' && (
                            <>
                              <SelectItem value="claude-3-haiku">Claude 3 Haiku</SelectItem>
                              <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                              <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            </>
                          )}
                          {config.provider === 'perplexity' && (
                            <>
                              <SelectItem value="llama-3.1-sonar-small-128k-online">Llama 3.1 Sonar Small</SelectItem>
                              <SelectItem value="llama-3.1-sonar-large-128k-online">Llama 3.1 Sonar Large</SelectItem>
                              <SelectItem value="llama-3.1-sonar-huge-128k-online">Llama 3.1 Sonar Huge</SelectItem>
                            </>
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="temperature">Temperature: {config.temperature.toFixed(1)}</Label>
                      <Slider
                        id="temperature"
                        value={[config.temperature]}
                        min={0}
                        max={1}
                        step={0.1}
                        onValueChange={(value) => setConfig({ ...config, temperature: value[0] })}
                      />
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>More deterministic</span>
                        <span>More creative</span>
                      </div>
                    </div>
                    
                    <Button type="submit" className="lloyds-button-primary w-full">Save Settings</Button>
                  </form>
                </CardContent>
              </Card>
            </div>
            
            <div className="md:col-span-4">
              <Card>
                <CardHeader>
                  <CardTitle>Python Backend Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2 mb-4">
                    <div className={`w-3 h-3 rounded-full ${
                      pythonStatus === 'connected' ? 'bg-green-500' : 
                      pythonStatus === 'error' ? 'bg-red-500' : 
                      'bg-yellow-500'
                    }`}></div>
                    <span>
                      {pythonStatus === 'connected' ? 'Connected' : 
                       pythonStatus === 'error' ? 'Not connected' : 
                       'Checking connection...'}
                    </span>
                  </div>
                  
                  {pythonStatus === 'error' && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                      <p className="font-medium mb-1">Python backend not detected</p>
                      <p>Please make sure the Python backend is running at http://localhost:5000</p>
                      <ol className="list-decimal ml-5 mt-2">
                        <li>Navigate to the python-backend directory</li>
                        <li>Run <code>python -m venv venv</code> to create a virtual environment</li>
                        <li>Activate the virtual environment</li>
                        <li>Run <code>pip install -r requirements.txt</code></li>
                        <li>Run <code>python app.py</code></li>
                      </ol>
                    </div>
                  )}
                  
                  {pythonStatus === 'connected' && (
                    <p className="text-sm text-gray-600">
                      Your RetireIQ Python backend is up and running. API endpoints are accessible and 
                      the system is operational.
                    </p>
                  )}
                  
                  <div className="mt-6">
                    <h3 className="font-medium text-lloyds-darkBlue mb-2">About the Python Backend</h3>
                    <p className="text-sm text-gray-600 mb-2">
                      The RetireIQ Python backend provides:
                    </p>
                    <ul className="text-sm text-gray-600 list-disc ml-5 space-y-1">
                      <li>User authentication and profile management</li>
                      <li>AI-powered retirement advice using LLMs</li>
                      <li>Chat history storage and management</li>
                      <li>LLM configuration and customization</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default Settings;
