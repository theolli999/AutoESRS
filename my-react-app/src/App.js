import React, { useState } from 'react';
import './App.css';

function App() {
    const [data, setData] = useState([]);
    const [question1, setQuestion1] = useState('');
    const [question2, setQuestion2] = useState('');
    const [question3, setQuestion3] = useState('');
    const [loading, setLoading] = useState(false);
    const [popupVisible, setPopupVisible] = useState(false);
    const [popupData, setPopupData] = useState('');

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
                    sources: result.sources,
                    data: result.data
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

    const handleInfoClick = (item) => {
        // Instead of alert(), show custom popup with item.data
        setPopupData(item.data);
        setPopupVisible(true);
    }

    const handleClosePopup = () => {
        setPopupVisible(false);
        setPopupData('');
    }

    return (
        <div className="App">
            <div className="container">
                <header className="app-header">
                    <h1>AutoESRS</h1>
                    <p>Transforming the world</p>
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
                                <div className="question-header">
                                    <h3>{item.question}</h3>
                                    <div className="info" onClick={() => handleInfoClick(item)}>i</div>
                                </div>
                                <p>{item.answer}</p>
                                <p className="sources">
                                    {item.sources ? item.sources.join(', ') : 'No sources available'}
                                </p>
                            </li>
                        ))}
                    </ul>
                </section>
            </div>
            {popupVisible && (
                <div className="popup-overlay" onClick={handleClosePopup}>
                    <div className="popup-content" onClick={(e) => e.stopPropagation()}>
                        <button className="close-popup" onClick={handleClosePopup}>X</button>
                        <div className="popup-data">{popupData}</div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;