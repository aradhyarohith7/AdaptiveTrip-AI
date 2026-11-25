
import { useEffect, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const interests = [
  "Beaches",
  "Sightseeing",
  "Adventure",
  "Food",
  "Nature",
  "Shopping",
];

function formatCurrency(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN")}`;
}

function formatDate(value) {
  if (!value) return "Not specified";

  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getTripDays(startDate, endDate) {
  if (!startDate || !endDate) return "—";

  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  const difference = Math.round((end - start) / (1000 * 60 * 60 * 24));

  return difference >= 0 ? difference + 1 : "—";
}

function App() {
  const [form, setForm] = useState({
    origin: "Mysuru",
    destination: "",
    startDate: "",
    endDate: "",
    budget: "15000",
    travellers: "2",
    travelStyle: "Budget-friendly",
    interests: ["Beaches", "Sightseeing"],
  });

  const [message, setMessage] = useState("");
  const [savedTrips, setSavedTrips] = useState([]);
  const [loadingTrips, setLoadingTrips] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generatingTripId, setGeneratingTripId] = useState(null);

  // Holds the selected trip and its generated AI results.
  const [activeTrip, setActiveTrip] = useState(null);
  const [activePlan, setActivePlan] = useState(null);

  // Load saved trips from MongoDB through the backend.
  async function loadTrips(showError = true) {
    setLoadingTrips(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/trips`);

      if (!response.ok) {
        throw new Error("Could not retrieve saved trips.");
      }

      const data = await response.json();
      setSavedTrips(data.trips || []);
    } catch (error) {
      console.error(error);

      if (showError) {
        setMessage("Unable to retrieve saved trips. Check the backend.");
      }
    } finally {
      setLoadingTrips(false);
    }
  }

  // Automatically load saved trips when the page opens.
  useEffect(() => {
    loadTrips(false);
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previousForm) => ({
      ...previousForm,
      [name]: value,
    }));

    setMessage("");
  }

  function toggleInterest(interest) {
    setForm((previousForm) => {
      const alreadySelected = previousForm.interests.includes(interest);

      return {
        ...previousForm,
        interests: alreadySelected
          ? previousForm.interests.filter((item) => item !== interest)
          : [...previousForm.interests, interest],
      };
    });

    setMessage("");
  }

  // Save a new trip request.
  async function handleSubmit(event) {
    event.preventDefault();

    if (form.endDate < form.startDate) {
      setMessage("Your return date must be after your departure date.");
      return;
    }

    setIsSubmitting(true);
    setMessage("Saving your trip details...");

    try {
      const response = await fetch(`${API_BASE_URL}/api/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(form),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to save your trip.");
      }

      setMessage(data.message || "Trip saved successfully.");
      await loadTrips(false);
    } catch (error) {
      console.error(error);
      setMessage(error.message || "Could not connect to the backend.");
    } finally {
      setIsSubmitting(false);
    }
  }

  // Generate a new itinerary for a saved trip.
  async function generateItinerary(trip) {
    setGeneratingTripId(trip._id);
    setActiveTrip(trip);
    setActivePlan(null);
    setMessage("Your AI agents are preparing the travel plan...");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/trips/${trip._id}/generate-itinerary`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to generate the itinerary.");
      }

      setActivePlan(data);
      setMessage(data.message || "Your itinerary has been generated.");

      // Refresh saved trips so the latest plan is available there too.
      await loadTrips(false);
    } catch (error) {
      console.error(error);
      setMessage(error.message || "Unable to generate the itinerary.");
    } finally {
      setGeneratingTripId(null);
    }
  }

  // Display a previously generated plan from MongoDB.
  function viewSavedPlan(trip) {
    setActiveTrip(trip);

    setActivePlan({
      itinerary: trip.itinerary || "",
      destination: trip.aiPlan?.destination || null,
      budget: trip.aiPlan?.budget || null,
      review: trip.aiPlan?.review || null,
      correction_attempts: trip.aiPlan?.correction_attempts ?? 0,
    });

    setMessage("");
    document.getElementById("plan-results")?.scrollIntoView({
      behavior: "smooth",
    });
  }

  const budget = activePlan?.budget;
  const destination = activePlan?.destination;
  const review = activePlan?.review;

  const totalBudget = Number(
    budget?.total_budget_inr ?? activeTrip?.budget ?? 0
  );

  const estimatedCost = Number(budget?.estimated_total_cost_inr || 0);

  const budgetPercentage =
    totalBudget > 0
      ? Math.min((estimatedCost / totalBudget) * 100, 100)
      : 0;

  return (
    <div className="app-shell" id="top">
      <header className="navbar">
        <a href="#top" className="brand">
          <span className="brand-icon">✦</span>
          AdaptiveTrip <span className="brand-ai">AI</span>
        </a>

        <nav className="nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#planner">Plan your trip</a>
          <a href="#saved-trips">Saved trips</a>
        </nav>

        <a href="#planner" className="nav-button">
          Get started ↗
        </a>
      </header>

      <main>
        {/* Hero section */}
        <section className="hero">
          <div className="hero-content">
            <p className="eyebrow">✦ SMARTER TRAVEL. BETTER EXPERIENCES.</p>

            <h1>
              Your journey.
              <br />
              Your way.
              <br />
              <span>Intelligently planned.</span>
            </h1>

            <p className="hero-description">
              Plan personalised trips with specialised AI agents
              that work together to organise your destinations,
              budget and travel schedule.
            </p>

            <a href="#planner" className="primary-button">
              Start planning <span>→</span>
            </a>

            <div className="hero-points">
              <span>✦ Personalised planning</span>
              <span>✦ Budget analysis</span>
              <span>✦ AI plan review</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="hero-visual-card">
              <div className="hero-visual-top">
                <span>YOUR NEXT ADVENTURE</span>
                <span className="hero-sparkle">✦</span>
              </div>

              <div className="hero-visual-bottom">
                <p>Explore more.</p>
                <h2>Travel your way.</h2>
                <span>One journey. Carefully planned.</span>
              </div>
            </div>

            <div className="floating-card">
              <span className="floating-icon">✈</span>
              <div>
                <strong>Powered by multiple AI agents</strong>
                <p>Planning, budgeting and reviewing together.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Trip planning form */}
        <section className="planner-section" id="planner">
          <div className="section-heading">
            <p className="eyebrow">LET'S PLAN YOUR NEXT ADVENTURE</p>
            <h2>Where would you like to go?</h2>
            <p>Share your travel preferences to get started.</p>
          </div>

          <form className="planner-card" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="origin">Starting location</label>
                <input
                  id="origin"
                  name="origin"
                  value={form.origin}
                  onChange={handleChange}
                  placeholder="e.g. Mysuru"
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="destination">Destination</label>
                <input
                  id="destination"
                  name="destination"
                  value={form.destination}
                  onChange={handleChange}
                  placeholder="e.g. Goa"
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="startDate">Departure date</label>
                <input
                  id="startDate"
                  name="startDate"
                  type="date"
                  value={form.startDate}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="endDate">Return date</label>
                <input
                  id="endDate"
                  name="endDate"
                  type="date"
                  min={form.startDate || undefined}
                  value={form.endDate}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="budget">Total budget (₹)</label>
                <input
                  id="budget"
                  name="budget"
                  type="number"
                  min="1000"
                  value={form.budget}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="travellers">Number of travellers</label>
                <select
                  id="travellers"
                  name="travellers"
                  value={form.travellers}
                  onChange={handleChange}
                >
                  <option value="1">1 traveller</option>
                  <option value="2">2 travellers</option>
                  <option value="3">3 travellers</option>
                  <option value="4">4 travellers</option>
                  <option value="5">5 travellers</option>
                  <option value="6">6+ travellers</option>
                </select>
              </div>
            </div>

            <div className="form-field style-field">
              <label htmlFor="travelStyle">Your travel style</label>
              <select
                id="travelStyle"
                name="travelStyle"
                value={form.travelStyle}
                onChange={handleChange}
              >
                <option>Budget-friendly</option>
                <option>Comfortable</option>
                <option>Luxury</option>
                <option>Adventure</option>
              </select>
            </div>

            <div className="interest-section">
              <label>What are you interested in?</label>

              <div className="interest-list">
                {interests.map((interest) => (
                  <button
                    key={interest}
                    type="button"
                    className={
                      form.interests.includes(interest)
                        ? "interest-chip selected"
                        : "interest-chip"
                    }
                    onClick={() => toggleInterest(interest)}
                    aria-pressed={form.interests.includes(interest)}
                  >
                    {form.interests.includes(interest) ? "✓ " : "+ "}
                    {interest}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="submit-button"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Saving your trip..." : "Save my trip request"}
              <span>→</span>
            </button>

            {message && (
              <div className="form-message" role="status">
                {message}
              </div>
            )}
          </form>
        </section>

        {/* Saved trips */}
        <section className="saved-trips section-container" id="saved-trips">
          <div className="section-heading section-heading-row">
            <div>
              <p className="eyebrow">YOUR TRAVEL COLLECTION</p>
              <h2>Your saved trips</h2>
              <p>Open a previous plan or generate a new one.</p>
            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={() => loadTrips()}
              disabled={loadingTrips}
            >
              {loadingTrips ? "Refreshing..." : "↻ Refresh trips"}
            </button>
          </div>

          {loadingTrips && savedTrips.length === 0 ? (
            <p className="empty-state">Loading your saved trips...</p>
          ) : savedTrips.length === 0 ? (
            <div className="empty-state">
              <span>✈</span>
              <h3>No trips saved yet</h3>
              <p>Create your first trip request using the form above.</p>
            </div>
          ) : (
            <div className="saved-trip-list">
              {savedTrips.map((trip) => {
                const hasSavedPlan = Boolean(trip.itinerary);

                return (
                  <article className="saved-trip-card" key={trip._id}>
                    <div className="saved-trip-top">
                      <span className="trip-label">
                        {trip.travelStyle || "Personal trip"}
                      </span>

                      {hasSavedPlan && (
                        <span className="saved-status">Plan generated</span>
                      )}
                    </div>

                    <h3>
                      {trip.origin} <span>→</span> {trip.destination}
                    </h3>

                    <p className="saved-trip-dates">
                      {formatDate(trip.startDate)} – {formatDate(trip.endDate)}
                    </p>

                    <div className="saved-trip-details">
                      <span>Budget: {formatCurrency(trip.budget)}</span>
                      <span>Travellers: {trip.travellers}</span>
                    </div>

                    <div className="saved-trip-actions">
                      {hasSavedPlan && (
                        <button
                          type="button"
                          className="secondary-button"
                          onClick={() => viewSavedPlan(trip)}
                        >
                          View saved plan
                        </button>
                      )}

                      <button
                        type="button"
                        className="generate-button"
                        onClick={() => generateItinerary(trip)}
                        disabled={generatingTripId !== null}
                      >
                        {generatingTripId === trip._id
                          ? "Generating..."
                          : hasSavedPlan
                            ? "Regenerate plan"
                            : "Generate AI plan"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* Generated plan dashboard */}
        {activePlan && (
          <section className="plan-results section-container" id="plan-results">
            <div className="plan-heading">
              <div>
                <p className="eyebrow">YOUR PERSONAL TRAVEL PLAN</p>
                <h2>
                  {activePlan.itinerary
                    ? `${activeTrip?.destination || "Your"} trip plan`
                    : "Your AI travel plan"}
                </h2>
                <p>
                  {activeTrip?.origin} → {activeTrip?.destination}
                  {" · "}
                  {getTripDays(activeTrip?.startDate, activeTrip?.endDate)} days
                </p>
              </div>

              {review && (
                <span
                  className={
                    review.approved
                      ? "review-badge approved"
                      : "review-badge needs-attention"
                  }
                >
                  {review.approved ? "✓ AI review approved" : "Needs attention"}
                </span>
              )}
            </div>

            {/* Summary cards */}
            <div className="summary-grid">
              <article className="summary-card">
                <span className="summary-icon">₹</span>
                <p>Total budget</p>
                <h3>{formatCurrency(totalBudget)}</h3>
              </article>

              <article className="summary-card">
                <span className="summary-icon">◈</span>
                <p>Estimated trip cost</p>
                <h3>{formatCurrency(estimatedCost)}</h3>
              </article>

              <article className="summary-card">
                <span className="summary-icon">✈</span>
                <p>Travellers</p>
                <h3>{activeTrip?.travellers || "—"}</h3>
              </article>

              <article className="summary-card">
                <span className="summary-icon">↻</span>
                <p>Correction attempts</p>
                <h3>{activePlan.correction_attempts ?? 0}</h3>
              </article>
            </div>

            {/* Itinerary */}
            <section className="result-panel">
              <div className="result-panel-heading">
                <div>
                  <p className="eyebrow">DAY-BY-DAY SCHEDULE</p>
                  <h3>Your itinerary</h3>
                </div>
                <span className="panel-icon">▤</span>
              </div>

              {activePlan.itinerary ? (
                <pre className="itinerary-content">{activePlan.itinerary}</pre>
              ) : (
                <p className="no-data">No itinerary text is available.</p>
              )}
            </section>

            {/* Destination recommendations */}
            <section className="result-panel">
              <div className="result-panel-heading">
                <div>
                  <p className="eyebrow">DESTINATION AGENT</p>
                  <h3>Recommended places</h3>
                </div>
                <span className="panel-icon">⌖</span>
              </div>

              {destination?.places?.length > 0 ? (
                <div className="place-grid">
                  {destination.places.map((place, index) => (
                    <article className="place-card" key={`${place.name}-${index}`}>
                      <span className="place-number">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="place-category">{place.category}</span>
                      <h4>{place.name}</h4>
                      <p>{place.description}</p>

                      <div className="place-meta">
                        <span>⌖ {place.area || "Area not specified"}</span>
                        <span>
                          {formatCurrency(place.estimated_cost_inr_per_person)}
                          {" / person"}
                        </span>
                      </div>

                      <p className="place-duration">
                        Suggested visit: {place.visit_duration_hours} hours
                      </p>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="no-data">
                  Destination recommendations are not available for this plan.
                </p>
              )}

              {destination?.important_notes?.length > 0 && (
                <div className="notes-block">
                  <h4>Destination notes</h4>
                  {destination.important_notes.map((note, index) => (
                    <p key={index}>• {note}</p>
                  ))}
                </div>
              )}
            </section>

            {/* Budget breakdown */}
            <section className="result-panel">
              <div className="result-panel-heading">
                <div>
                  <p className="eyebrow">BUDGET AGENT</p>
                  <h3>Budget breakdown</h3>
                </div>
                <span className="panel-icon">₹</span>
              </div>

              {budget ? (
                <>
                  <div className="budget-overview">
                    <div>
                      <p>Estimated spending</p>
                      <h3>{formatCurrency(estimatedCost)}</h3>
                      <span>
                        of {formatCurrency(totalBudget)} total budget
                      </span>
                    </div>

                    <span
                      className={
                        budget.is_within_budget
                          ? "budget-status within"
                          : "budget-status exceeded"
                      }
                    >
                      {budget.is_within_budget
                        ? "Within budget"
                        : "Over budget"}
                    </span>
                  </div>

                  <div className="budget-progress">
                    <div
                      className="budget-progress-fill"
                      style={{ width: `${budgetPercentage}%` }}
                    />
                  </div>

                  <div className="budget-allocations">
                    {(budget.allocations || []).map((allocation, index) => {
                      const percentage =
                        estimatedCost > 0
                          ? Math.min(
                              (Number(allocation.estimated_amount_inr || 0) /
                                estimatedCost) *
                                100,
                              100
                            )
                          : 0;

                      return (
                        <div className="allocation-row" key={index}>
                          <div className="allocation-info">
                            <div>
                              <strong>{allocation.category}</strong>
                              <p>{allocation.explanation}</p>
                            </div>
                            <strong>
                              {formatCurrency(allocation.estimated_amount_inr)}
                            </strong>
                          </div>

                          <div className="allocation-track">
                            <div
                              className="allocation-fill"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="daily-budget">
                    <span>Estimated daily budget</span>
                    <strong>{formatCurrency(budget.daily_budget_inr)}</strong>
                  </div>

                  {budget.notes?.length > 0 && (
                    <div className="notes-block">
                      <h4>Budget notes</h4>
                      {budget.notes.map((note, index) => (
                        <p key={index}>• {note}</p>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className="no-data">Budget details are not available.</p>
              )}
            </section>

            {/* AI review */}
            <section className="result-panel review-panel">
              <div className="result-panel-heading">
                <div>
                  <p className="eyebrow">REVIEW AGENT</p>
                  <h3>AI plan review</h3>
                </div>
                <span className="panel-icon">✓</span>
              </div>

              {review ? (
                <>
                  <div
                    className={
                      review.approved
                        ? "review-summary approved-summary"
                        : "review-summary attention-summary"
                    }
                  >
                    <strong>
                      {review.approved
                        ? "Your plan passed the AI review"
                        : "The AI review found some issues"}
                    </strong>
                    <p>{review.summary}</p>
                  </div>

                  {review.issues?.length > 0 ? (
                    <div className="review-issues">
                      <h4>Issues identified</h4>

                      {review.issues.map((issue, index) => (
                        <article className="review-issue" key={index}>
                          <span className="issue-category">
                            {issue.category}
                          </span>
                          <p>{issue.description}</p>
                          <p>
                            <strong>Suggested correction:</strong>{" "}
                            {issue.suggested_correction}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="no-issues">
                      ✓ No issues were reported by the Review Agent.
                    </p>
                  )}
                </>
              ) : (
                <p className="no-data">Review details are not available.</p>
              )}
            </section>

            <p className="estimate-disclaimer">
              Travel costs and recommendations are AI-generated estimates.
              Confirm prices, opening hours, routes and availability before
              travelling.
            </p>
          </section>
        )}

        {/* How it works */}
        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <p className="eyebrow">TRAVEL PLANNING, REIMAGINED</p>
            <h2>More than just a travel planner.</h2>
            <p>Specialised AI agents work together on your travel plan.</p>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <span className="feature-icon">✦</span>
              <h3>Discover destinations</h3>
              <p>
                The Destination Agent recommends places based on your
                interests and travel preferences.
              </p>
            </article>

            <article className="feature-card">
              <span className="feature-icon">₹</span>
              <h3>Plan your budget</h3>
              <p>
                The Budget Agent estimates expenses and checks them
                against your available budget.
              </p>
            </article>

            <article className="feature-card">
              <span className="feature-icon">✓</span>
              <h3>Review your plan</h3>
              <p>
                The Review Agent checks the generated plan and can
                request corrections from other agents.
              </p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <a href="#top" className="brand">
          <span className="brand-icon">✦</span>
          AdaptiveTrip <span className="brand-ai">AI</span>
        </a>
        <p>Your journey, intelligently planned.</p>
      </footer>
    </div>
  );
}

export default App;
