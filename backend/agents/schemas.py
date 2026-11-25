from typing import Literal
from pydantic import BaseModel, Field


# 1. Destination Agent output

class PlaceRecommendation(BaseModel):
    name: str = Field(description="Name of the recommended place")
    category: str = Field(description="Type of place, such as beach or museum")
    description: str = Field(description="Why this place is worth visiting")
    area: str = Field(description="Area or location of the place")
    estimated_cost_inr_per_person: float = Field(
        description="Estimated entry or activity cost per person in INR"
    )
    visit_duration_hours: float = Field(
        description="Estimated time needed to visit this place"
    )


class DestinationAgentResult(BaseModel):
    destination: str
    places: list[PlaceRecommendation]
    important_notes: list[str]


# 2. Budget Agent output

class BudgetAllocation(BaseModel):
    category: str = Field(
        description="Expense category such as food, transport or accommodation"
    )
    estimated_amount_inr: float
    explanation: str


class BudgetAgentResult(BaseModel):
    total_budget_inr: float
    estimated_total_cost_inr: float
    daily_budget_inr: float
    allocations: list[BudgetAllocation]
    is_within_budget: bool
    notes: list[str]


# 3. Itinerary Agent output

class PlannedActivity(BaseModel):
    title: str
    description: str
    location: str
    estimated_cost_inr_total: float = Field(
        description="Estimated activity cost for all travellers in INR"
    )
    duration_hours: float


class DayPlan(BaseModel):
    day_number: int
    date: str
    morning: list[PlannedActivity]
    afternoon: list[PlannedActivity]
    evening: list[PlannedActivity]


class ItineraryAgentResult(BaseModel):
    title: str
    days: list[DayPlan]
    estimated_total_cost_inr: float
    notes: list[str]


# 4. Review Agent output

class ReviewIssue(BaseModel):
    category: str = Field(
        description="Type of issue: budget, distance, schedule, duplicate or requirements"
    )
    is_correctable: bool = Field(
        default=True,
        description=(
            "True if the Budget or Itinerary agent can realistically fix this issue "
            "without faking costs. False if it is an unavoidable user constraint "
            "(e.g., total budget is genuinely too low for the destination/duration, "
            "or trip duration is too short for the route/requests)."
        ),
    )
    target_agent: Literal["budget", "itinerary", "none"] = Field(
        default="itinerary",
        description=(
            "Which agent should fix this issue: 'budget', 'itinerary', "
            "or 'none' if is_correctable is False."
        ),
    )
    description: str
    suggested_correction: str = Field(
        description="Actionable fix for the target agent, or practical advice for the user if unavoidable"
    )
    affected_day: int | None = None


class ReviewAgentResult(BaseModel):
    approved: bool
    summary: str
    issues: list[ReviewIssue]
    unavoidable_constraints: list[str] = Field(
        default_factory=list,
        description="Clear explanations of constraints that cannot be fixed automatically, with practical alternatives for the user"
    )