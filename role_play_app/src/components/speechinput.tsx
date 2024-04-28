"use client"
import { useState, useRef, useEffect, FC } from 'react';

interface SpeechInputProps {
  onTranscript: (transcript: string) => void;
}

const SpeechInput: FC<SpeechInputProps> = ({ onTranscript }) => {
  const [isListening, setIsListening] = useState<boolean>(false);
  const speechRecognition = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      speechRecognition.current = new SpeechRecognition();
      speechRecognition.current.continuous = false;
      speechRecognition.current.lang = 'ja-JP';
      speechRecognition.current.interimResults = false;
      speechRecognition.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        onTranscript(transcript); // 親コンポーネントにトランスクリプトを送信
        setIsListening(false);
      };
      speechRecognition.current.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('SpeechRecognition error:', event.error);
        setIsListening(false);
      };
    } else {
      console.error('このブラウザには音声認識機能がありません');
    }
  }, [onTranscript]);

  const toggleListening = () => {
    if (isListening) {
      speechRecognition.current?.stop();
      setIsListening(false);
    } else {
      speechRecognition.current?.start();
      setIsListening(true);
    }
  };

  return (
    <button
      onClick={toggleListening}
      className={`ml-2 ${isListening ? 'bg-red-500' : 'bg-green-500'} hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline`}
    >
      {isListening ? 'Stop' : 'Speak'}
    </button>
  );
};

export default SpeechInput;
