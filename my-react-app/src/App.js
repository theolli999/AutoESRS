import React, { useState } from 'react';
import './App.css';

function App() {
    const [data, setData] = useState([]);
    const [question1, setQuestion1] = useState('');
    const [question2, setQuestion2] = useState('');
    const [question3, setQuestion3] = useState('');
    const [loading, setLoading] = useState(false);

    const handleClick = (e) => {
        e.preventDefault();
        setLoading(true);
        setData([]); // Nollställ tidigare data vid en ny begäran
    
        let questions = [question1, question2, question3].filter(question => question !== '');
        let pending = questions.length;
        
        questions.forEach(question => {
            fetch('http://localhost:8080/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            })
            .then(response => response.json())
            .then(result => {
                const responseData = {
                    question,
                    answer: result.answer,
                    sources: result.sources
                };
                setData(prevData => [...prevData, responseData]);
            })
            .catch(error => {
                console.error('Error:', error);
            })
            .finally(() => {
                pending--;
                if (pending === 0) {
                    setLoading(false);
                }
            });
        });
    }
    return (
        <div className="App">
            <div className="container">
                <header className="app-header">
                    <h1>AutoESRS</h1>
                    <p>Make years work in one day</p>
                </header>
                <form className="question-form" onSubmit={handleClick}>
                    <div className="form-group">
                        <input 
                            type="text"
                            value={question1}
                            onChange={e => setQuestion1(e.target.value)}
                            placeholder="Fråga 1" 
                        />
                    </div>
                    <div className="form-group">
                        <input 
                            type="text"
                            value={question2}
                            onChange={e => setQuestion2(e.target.value)}
                            placeholder="Fråga 2" 
                        />
                    </div>
                    <div className="form-group">
                        <input 
                            type="text"
                            value={question3}
                            onChange={e => setQuestion3(e.target.value)}
                            placeholder="Fråga 3" 
                        />
                    </div>
                    <button type="submit">Generate answers</button>
                </form>
                <section className="results">
                    {!loading && <h2>Answers</h2>}
                    {loading && <div className="loading"></div>}
                    <ul>
                        {data.map((item, index) => (
                            <li key={index} className="result-item">
                                <h3>{item.question}</h3>
                                <p>
                                    {item.answer}
                                </p>
                                <p className="sources">
                                    {item.sources ? item.sources.join(', ') : 'No sources available'}
                                </p>
                            </li>
                        ))}
                    </ul>
                </section>
            </div>
        </div>
    );
}

export default App;