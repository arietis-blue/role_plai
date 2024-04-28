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

  // メッセージリストが更新された時に、自動的に最新のメッセージが表示されるようスクロールする
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    websocket.current = new WebSocket('ws://localhost:8000/ws');

    websocket.current.onmessage = (event: MessageEvent) => {
      console.log('Message from server:', event.data);
      setMessages(prevMessages => [...prevMessages, { text: event.data, fromServer: true }]);
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
    <div className="flex flex-col items-center justify-center min-h-screen bg-blue-100 p-4">
      <div className="w-full max-w-md">
        <div className="bg-white shadow-md rounded px-4 pt-6 pb-8 mb-4 flex flex-col h-[500px] overflow-y-auto">
          {messages.map((message, index) => (
            <div key={index} className={`my-2 p-2 rounded-lg ${message.fromServer ? 'bg-gray-300 ml-2 self-start' : 'bg-blue-500 text-white mr-2 self-end'}`}>
              {message.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="mt-4 flex">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="メッセージを入力"
            className="shadow appearance-none border rounded w-full py-2 px-3 text-grey-darker"
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
  );
};

export default Home;
