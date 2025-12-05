from config import TAX_SLABS

def compute_tax(parsed: dict):
    gross = parsed.get("gross_salary") or 0.0
    allowances = parsed.get("allowances") or 0.0
    exemptions = parsed.get("exemptions") or 0.0
    already_paid = parsed.get("tax_already_paid") or 0.0

    taxable_income = max(0.0, gross + allowances - exemptions)
    remaining = taxable_income
    tax_due = 0.0
    breakdown = []
    prev_limit = 0.0

    for slab in TAX_SLABS:
        limit = slab["limit"]
        rate = slab["rate"]
        if limit is None:
            taxable_at = remaining
        else:
            taxable_at = max(0.0, min(remaining, limit - prev_limit))
        amt = taxable_at * rate
        if taxable_at > 0:
            breakdown.append({"taxable_at": taxable_at, "rate": rate, "amount": amt})
        tax_due += amt
        remaining -= taxable_at
        if limit is not None:
            prev_limit = limit
        if remaining <= 0:
            break

    tax_payable = max(0.0, tax_due - already_paid)

    return {
        "taxable_income": taxable_income,
        "tax_due_before_credits": tax_due,
        "tax_already_paid": already_paid,
        "tax_payable": tax_payable,
        "breakdown": breakdown
    }