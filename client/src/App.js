import React, { useState } from 'react';
import './index.css';
import './styles.css';
import { Card, CardContent } from './components/ui/card'; // Adjust path or install library

function App() {
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [transcript, setTranscript] = useState('');
  const [framesCount, setFramesCount] = useState(null);
  const [emotionData, setEmotionData] = useState(null);
  const [feedbackSummary, setFeedbackSummary] = useState('');
  const [wpm, setWpm] = useState(0);
  const [fillerCount, setFillerCount] = useState({});
  const [totalFiller, setTotalFiller] = useState(0);

  const fillerWords = ['uh', 'um', 'like', 'you know', 'actually', 'basically'];

  const calculateWPM = (transcript, durationInSeconds) => {
    const wordCount = transcript.trim().split(/\s+/).length;
    const minutes = durationInSeconds / 60;
    return Math.round(wordCount / minutes);
  };

  const countFillerWords = (transcript) => {
    const lowerText = transcript.toLowerCase();
    let totalFillerCount = 0;
    const fillerCount = {};

    fillerWords.forEach((word) => {
      const regex = new RegExp(`\\b${word}\\b`, 'g');
      const count = (lowerText.match(regex) || []).length;
      fillerCount[word] = count;
      totalFillerCount += count;
    });

    return { fillerCount, totalFillerCount };
  };

  const handleUpload = async () => {
    if (!video) {
      setMessage('Please select a video file.');
      return;
    }
    if (!video.type.startsWith('video/')) {
      setMessage('Please upload a valid video file.');
      return;
    }

    setLoading(true);
    setAudioUrl('');
    setTranscript('');
    setFramesCount(null);
    setEmotionData(null);
    setFeedbackSummary('');
    setMessage('');

    const formData = new FormData();
    formData.append('video', video);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message || 'Processing complete.');
        setAudioUrl(`http://localhost:5000/${data.audio_file}`);
        setTranscript(data.transcript || '');
        setFramesCount(data.frames_extracted || 0);
        if (data.transcript && data.duration) {
          setWpm(calculateWPM(data.transcript, data.duration));
          const { fillerCount, totalFillerCount } = countFillerWords(data.transcript);
          setFillerCount(fillerCount);
          setTotalFiller(totalFillerCount);
        }
        // Fetch feedback summary
        const summary = await getFeedbackSummary(data.transcript);
        setFeedbackSummary(summary);
        await analyzeEmotions();
      } else {
        setMessage(data.error || 'Upload failed.');
      }
    } catch (error) {
      console.error('Upload Error:', error);
      setMessage('Upload failed due to a network error.');
    } finally {
      setLoading(false);
    }
  };

  const getFeedbackSummary = async (transcript) => {
    try {
      const res = await fetch('http://localhost:5000/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript }),
      });
      const data = await res.json();
      if (res.ok && data?.choices?.[0]?.message?.content) {
        return data.choices[0].message.content;
      } else {
        setMessage('Failed to fetch feedback summary.');
        return 'No feedback available.';
      }
    } catch (error) {
      console.error('Feedback Error:', error);
      setMessage('Feedback fetch failed due to a network error.');
      return 'Error fetching feedback.';
    }
  };

  const analyzeEmotions = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:5000/analyze-emotions', {
        method: 'POST',
      });
      const data = await res.json();

      if (res.ok && data?.percentage_summary && typeof data.percentage_summary === 'object') {
        setEmotionData(data);
      } else {
        setMessage('Emotion analysis failed.');
      }
    } catch (error) {
      console.error('Emotion Analysis Error:', error);
      setMessage('Emotion analysis failed due to a network error.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8">
      <div className="bg-gradient-card border border-border/50 p-8 rounded-2xl shadow-medium backdrop-blur-sm w-full max-w-2xl animate-fade-in-up">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-primary bg-clip-text text-transparent mb-3">
            🎥 AI Interview Feedback
          </h1>
          <p className="text-muted-foreground text-lg">
            Upload your interview video for intelligent analysis and feedback
          </p>
        </div>

        <div className="space-y-6">
          <div className="relative">
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setVideo(e.target.files?.[0] || null)}
              className="w-full p-4 border-2 border-dashed border-muted-foreground/30 rounded-xl bg-muted/30 hover:border-primary/50 transition-colors file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
            />
            {video && (
              <div className="mt-2 text-sm text-success font-medium">
                ✓ {video.name} selected
              </div>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={loading}
            aria-label={loading ? 'Processing video' : 'Upload and analyze video'}
            className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-300 ${
              loading
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-gradient-primary text-primary-foreground hover:shadow-glow transform hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {loading ? (
              <div className="flex items-center justify-center gap-3">
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Processing...
              </div>
            ) : (
              'Upload & Analyze'
            )}
          </button>

          {message && (
            <div className="text-center p-4 rounded-xl bg-info/10 border border-info/20 text-info font-medium animate-fade-in-up">
              {message}
            </div>
          )}

          {audioUrl && (
            <div className="p-6 rounded-xl bg-gradient-accent border border-border/50 shadow-soft animate-fade-in-up">
              <h2 className="text-2xl font-bold text-foreground mb-4 flex items-center gap-2">
                🎧 <span>Extracted Audio</span>
              </h2>
              <audio
                controls
                src={audioUrl}
                className="w-full h-12 rounded-lg shadow-soft"
                style={{
                  filter: 'hue-rotate(270deg) saturate(1.2)',
                }}
                aria-label="Extracted audio playback"
              />
            </div>
          )}

          {transcript && (
            <div className="p-6 rounded-xl bg-gradient-accent border border-border/50 shadow-soft animate-fade-in-up">
              <h2 className="text-2xl font-bold text-foreground mb-4 flex items-center gap-2">
                📝 <span>Transcript</span>
              </h2>
              <div className="bg-card/80 p-6 rounded-lg border border-border/30 max-h-64 overflow-y-auto">
                <p className="text-card-foreground leading-relaxed whitespace-pre-wrap text-sm">
                  {transcript}
                </p>
              </div>
            </div>
          )}

          {emotionData && emotionData.percentage_summary && (
            <div className="p-6 rounded-xl bg-gradient-accent border border-border/50 shadow-soft animate-fade-in-up">
              <h2 className="text-2xl font-bold text-foreground mb-4 flex items-center gap-2">
                😊 <span>Emotion Analysis</span>
              </h2>
              <div className="grid gap-3">
                {Object.entries(emotionData.percentage_summary).map(([emotion, percent]) => (
                  <div
                    key={emotion}
                    className="flex items-center justify-between p-4 bg-card/80 rounded-lg border border-border/30"
                  >
                    <span className="font-medium text-card-foreground capitalize text-lg">{emotion}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-32 h-3 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-primary rounded-full transition-all duration-1000 ease-out"
                          style={{ width: `${percent}%` }}
                        ></div>
                      </div>
                      <span className="font-bold text-primary min-w-[4rem] text-right">{String(percent)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {transcript && (
            <Card className="mt-4 p-4 bg-slate-100">
              <h2 className="text-xl font-semibold mb-2">Speaking Analysis</h2>
              <p>
                <strong>Words Per Minute:</strong> {wpm}
              </p>
              <p>
                <strong>Total Filler Words:</strong> {totalFiller}
              </p>
              <ul className="list-disc ml-6">
                {Object.entries(fillerCount).map(([word, count]) => (
                  <li key={word}>
                    {word}: {count}
                  </li>
                ))}
              </ul>
              {totalFiller > 5 && (
                <p className="text-red-600 mt-2">
                  Try to reduce filler words to sound more confident and professional.
                </p>
              )}
            </Card>
          )}

          {feedbackSummary && (
            <Card className="mt-4 p-4 bg-emerald-100">
              <h2 className="text-xl font-semibold mb-2">AI Feedback Summary</h2>
              <p>{feedbackSummary}</p>
            </Card>
          )}

          {framesCount !== null && (
            <div className="text-center p-4 rounded-xl bg-success/10 border border-success/20 text-success font-medium animate-fade-in-up">
              📸 <strong>Total Frames Extracted:</strong> {framesCount}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;