import React, { useState, useEffect } from "react";
import "./RouteAnalysisForm.css";

const RouteAnalysisForm = () => {
    const [departureAirport, setDepartureAirport] = useState("");
    const [arrivalAirport, setArrivalAirport] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [routes, setRoutes] = useState([]);
    const [arrivalAirports, setArrivalAirports] = useState([]);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [summary, setSummary] = useState("");
    const [loading, setLoading] = useState(false);

    // Fetch available airports
    useEffect(() => {
        const fetchRoutes = async () => {
            try {
                const response = await fetch("http://127.0.0.1:8000/available-routes");
                const data = await response.json();

                if (data.departure_airports && data.arrival_airports) {
                    setRoutes(data.departure_airports);
                    setArrivalAirports(data.arrival_airports);
                } else {
                    console.error("Unexpected data format", data);
                }
            } catch (error) {
                console.error("Failed to fetch routes:", error);
            }
        };
        fetchRoutes();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch(
                `http://127.0.0.1:8000/route-analysis?departure_airport=${departureAirport}&arrival_airport=${arrivalAirport}&start_date=${startDate}&end_date=${endDate}`
            );
            const data = await response.json();
            setAnalysisResult(data);
            setSummary(data.summary || "");
        } catch (error) {
            console.error("Failed to fetch analysis:", error);
        } finally {
            setLoading(false);
        }
    };

    const renderRouteCoverage = (coverage) => {
        return Object.entries(coverage).map(([airline, percentage]) => (
            <p key={airline}>{airline}: {percentage}</p>
        ));
    };

    // Prettify AI Summary and Bold Titles
    const prettifySummary = (summary) => {
        // Replace markdown bold with HTML <strong> tags
        let formattedSummary = summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
        // Fix line breaks after numbers (e.g., 1.\n -> 1. )
        formattedSummary = formattedSummary.replace(/(\d+)\.\s*\n/g, '<hr><br><strong>$1.</strong> ');
    
        // Fix line breaks after section titles (like "Total Flights:")
        formattedSummary = formattedSummary.replace(/:\s*\n/g, ': <br>');
    
        // Preserve bullet points properly
        formattedSummary = formattedSummary.replace(/-\s/g, '• ');  // Replace "-" with "•"
    
        // Split by line and render paragraphs
        const lines = formattedSummary.split('\n');
    
        return (
            <div>
                {lines.map((line, index) => (
                    line.trim() !== "" ? 
                    <p key={index} dangerouslySetInnerHTML={{ __html: line }}></p> : 
                    <br key={index}/>
                ))}
            </div>
        );
    };
    

    return (
        <div className="container">
            <h1 className="section-title">Budget Airline Route Analysis Tool (B.A.R.A.T.)</h1>
            <p className="sub-title">Analyze route performance with real-time data and AI assistance.</p>

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Departure Airport:</label>
                    <select
                        value={departureAirport}
                        onChange={(e) => setDepartureAirport(e.target.value)}
                    >
                        <option value="">Select Departure</option>
                        {routes.map((airport, index) => (
                            <option key={index} value={airport}>
                                {airport}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Arrival Airport:</label>
                    <select
                        value={arrivalAirport}
                        onChange={(e) => setArrivalAirport(e.target.value)}
                    >
                        <option value="">Select Arrival</option>
                        {arrivalAirports.map((airport, index) => (
                            <option key={index} value={airport}>
                                {airport}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="form-group">
                    <label>Start Date:</label>
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        required
                    />
                </div>

                <div className="form-group">
                    <label>End Date:</label>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        required
                    />
                </div>

                <button type="submit" className="submit-button" disabled={loading}>
                    {loading ? <span className="spinner"></span> : "Get Analysis"}
                </button>
            </form>

            {analysisResult && (
                <div className="results-container">
                    <h2>Quick Metrics</h2>
                    {analysisResult.message ? (
                        <p>{analysisResult.message}</p>
                    ) : analysisResult.current_period && analysisResult.previous_period ? (
                        <div className="cards">
                            <div className="card">
                                <h3>Actual Period</h3>
                                <p>Total Flights: {analysisResult.current_period.total_flights}</p>
                                <p>Average Departure Delay: {analysisResult.current_period.average_departure_delay} minutes</p>
                                <p>Average Arrival Delay: {analysisResult.current_period.average_arrival_delay} minutes</p>
                                <h4>Route Coverage</h4>
                                {renderRouteCoverage(analysisResult.current_period.route_coverage)}
                            </div>

                            <div className="card">
                                <h3>Previous Period</h3>
                                <p>Total Flights: {analysisResult.previous_period.total_flights}</p>
                                <p>Average Departure Delay: {analysisResult.previous_period.average_departure_delay} minutes</p>
                                <p>Average Arrival Delay: {analysisResult.previous_period.average_arrival_delay} minutes</p>
                                <h4>Route Coverage</h4>
                                {renderRouteCoverage(analysisResult.previous_period.route_coverage)}
                            </div>

                            <div className="summary-card">
                                <h3>Detailed Analysis</h3>
                                {prettifySummary(summary)}
                            </div>
                        </div>
                    ) : (
                        <p>No data available for the selected route and period.</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default RouteAnalysisForm;
