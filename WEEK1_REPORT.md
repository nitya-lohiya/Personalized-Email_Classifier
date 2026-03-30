# Week 1: Data Preparation Report

## What We Did
1. Downloaded 10,780 training + 2,697 test emails from HuggingFace
2. Studied 6 original categories
3. Mapped to 3 priorities (High/Medium/Low)
4. Verified data quality

## Dataset Summary
- Total: 13,477 emails
- Training: 10,780 (80%)
- Testing: 2,697 (20%)
- Average email length: 125 characters
- Shortest: 55 chars | Longest: 1,890 chars

## Priority Mapping

### High Priority (3,594 training emails)
**Categories:** verify_code, updates
**Why High?** Time-sensitive, requires immediate action
**Examples:**
- "Two-step verification code: 426706"
- "Payment received: Invoice INV-7891"

### Medium Priority (3,596 training emails)
**Categories:** social_media, forum
**Why Medium?** Important but can wait hours
**Examples:**
- "Memories from this week in 2021"
- "Your post was moved to Programming Help"

### Low Priority (3,590 training emails)
**Categories:** promotions, spam
**Why Low?** Can ignore or delete
**Examples:**
- "Anniversary Special: Buy one get one free"
- "Your $5000 refund is processed. Claim: bit.ly/fakeprize"

## Data Quality
- No missing values
- Balanced classes (~3,594 each)
- Clean text
- Good variety across categories
