from app.security import Outputvalidator


def demo_output_validation():
    """Demonstrate output validation."""

    validator = Outputvalidator()

    outputs = [
        "The capital ",
        "Contact support at help@company.com for assistance.",
        "Here's how to hack into the system...",
    ]

    print("\nOutput Validation Demo:\n")

    for output in outputs:
        is_valid, cleaned, reason = validator.validate(output)
        status = "✅ VALID" if is_valid else "⚠️ CLEANED"
        print(f"{status}: {output[:50]}...")
        if reason:
            print(f"   Reason: {reason}")
            print(f"   Cleaned: {cleaned[:50]}...")



if __name__ == "__main__":
    demo_output_validation()