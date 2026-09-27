from pydantic import BaseModel, Field
from app.agent.llm import llm
from typing import Literal


class ChoiceResult(BaseModel):
    rejected: bool = Field(
        description="True if the user doesn't want any of the given options and wants alternatives instead"
    )

    selected_index: int = Field(
        default=0,
        description="0-based index of the option the user means, if not rejected"
    )

    reasoning: str = Field(
        description="One short sentence explaining the interpretation"
    )
    
choice_llm = llm.with_structured_output(ChoiceResult)


def resolve_user_choice(
    user_response: str,
    options: list,
    context: str = ""
) -> tuple[bool, int]:

    if not user_response or not user_response.strip():
        return False, 0

    options_text = "\n".join(
        f"{i}: {opt.model_dump()}"
        for i, opt in enumerate(options)
    )

    prompt = f"""
    Context: {context}

    The user was shown these options:
    {options_text}

    The user replied: "{user_response}"

    Decide: are they picking one of these options, or rejecting
    all of them and wanting alternatives?

    Vague affirmations ("yes", "sounds good", "ok")
    mean they pick index 0.

    Explicit rejection ("none of these", "something else",
    "I don't like it", "show me other options", "cheaper please")
    means rejected=True.
    """

    result = choice_llm.invoke(prompt)

    if result.rejected:
        return True, -1

    index = (
        result.selected_index
        if 0 <= result.selected_index < len(options)
        else 0
    )

    return False, index

class ConfirmationResult(BaseModel):
    confirmed: bool = Field(
        description="True if the user agreed/said yes, False if they declined"
    )
    reasoning: str = Field(
        description="One short sentence explaining the interpretation"
    )


confirm_llm = llm.with_structured_output(ConfirmationResult)


def resolve_confirmation(user_response: str, context: str = "") -> bool:

    if not user_response or not user_response.strip():
        return True

    prompt = f"""
    Context: {context}

    The user was asked to confirm something.
    They replied: "{user_response}"

    Did they agree (yes) or decline (no)?
    """

    result = confirm_llm.invoke(prompt)

    return result.confirmed


class EditTargetResult(BaseModel):
    target: Literal[
        "transport",
        "hotel",
        "itinerary",
        "scooter",
        "return",
        "cancel",
    ] = Field(
        description=(
            "Which part of the trip the user wants to revisit, "
            "or 'cancel' to stop planning entirely"
        )
    )


edit_target_llm = llm.with_structured_output(EditTargetResult)


def resolve_edit_target(user_response: str) -> str:
    """Use the LLM to identify which part of the trip the user wants to change."""

    if not user_response or not user_response.strip():
        return "cancel"

    prompt = f"""
    The user was asked what they would like to change in their trip plan.

    Classify their response into exactly ONE of these categories:

    - transport
    - hotel
    - itinerary
    - scooter
    - return
    - cancel

    Understand typos, short replies, and natural language.

    Examples:
    "hotl" → hotel
    "hotel" → hotel
    "change my stay" → hotel
    "train" → transport
    "flight" → transport
    "change the activities" → itinerary
    "itinry" → itinerary
    "bike" → scooter
    "return journey" → return
    "go back" → return
    "stop everything" → cancel

    User response:
    "{user_response}"

    Reply with ONLY one category name.
    """

    result = llm.invoke(prompt)

    target = result.content.strip().lower()

    valid_targets = {
        "transport",
        "hotel",
        "itinerary",
        "scooter",
        "return",
        "cancel",
    }

    if target in valid_targets:
        return target

    return "cancel"