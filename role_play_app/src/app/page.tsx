"use client"
import { useEffect, useState, useRef } from 'react';
import SpeechInput from '../components/speechinput';

interface Message {
  text: string;
  fromServer: boolean;
}

const Home: React.FC = () => {
  const [inputText, setInputText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const websocket = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  let speechSynth: SpeechSynthesis | null = null;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      speechSynth = window.speechSynthesis;
    }
    websocket.current = new WebSocket('ws://localhost:8000/ws');

    websocket.current.onmessage = (event: MessageEvent) => {
      console.log('Message from server:', event.data);
      setMessages(prevMessages => [...prevMessages, { text: event.data, fromServer: true }]);
      if (speechSynth && !speechSynth.speaking) {
        const utterance = new SpeechSynthesisUtterance(event.data);
        speechSynth.speak(utterance);
      }
    };

    websocket.current.onclose = () => console.log('WebSocket closed');
    websocket.current.onerror = (error) => console.log('WebSocket error:', error);

    return () => {
      websocket.current?.close();
    };
  }, []);

  const sendMessage = (): void => {
    if (websocket.current && inputText) {
      websocket.current.send(inputText);
      setMessages(prevMessages => [...prevMessages, { text: inputText, fromServer: false }]);
      setInputText('');
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="flex-1 flex justify-around items-center bg-gray-100">
        <img src="/images/interviewer.png" alt="Image 1" className="max-w-md h-auto" />
        <img src="/images/you.png" alt="Image 2" className="max-w-md h-auto" />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center bg-blue-100 p-4 w-full">
        <div className="w-full">
          <div className="bg-white shadow-md rounded-lg p-4 h-[300px] overflow-y-auto w-full flex flex-col">
            {messages.map((message, index) => (
              <div key={index} className={`my-2 p-2 rounded-lg ${message.fromServer ? 'bg-gray-300 self-start max-w-md' : 'bg-blue-500 text-white self-end max-w-md'}`}>
                {message.text}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div className="mt-4 flex w-full">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="メッセージを入力"
              className="shadow appearance-none border rounded py-2 px-3 text-gray-700 flex-grow"
            />
            <SpeechInput onTranscript={(transcript: string) => setInputText(transcript)} />
            <button
              onClick={sendMessage}
              className="ml-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
  
};

export default Home;
