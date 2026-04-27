# Storyboard: Pricing Under Uncertainty - A Quantum Perspective

Adapted from the explainer and full workshop into a concise, high-engagement slide experience for a 15-20 minute presentation.

## Legend

| Symbol | Meaning |
| ------ | ------- |
| 🎙️ | Narrator voiceover script |
| 📝 | On-screen text |
| 🎨 | Visual description |
| 🖱️ | Interaction specification |
| ⚙️ | iSpring feature used |
| ➡️ | Transition / flow logic |
| ⏱️ | Estimated time |

## Presentation Goal

Help non-technical stakeholders understand that pricing is an expected-value problem, see the difference between classical and quantum estimation, and leave with a business-ready mental model they can reuse.

## Total Duration

Target runtime: 17-18 minutes

## Module 1: Hook - Why Pricing Feels Hard

### Slide 1 - Title and tension

🎙️ "We usually talk about pricing as if there were one correct number. In reality, pricing is a decision made in the middle of uncertainty. Today, we will see how quantum thinking helps us reason about that uncertainty more clearly."

📝

- Pricing Under Uncertainty
- A Quantum Perspective
- Same business question, smarter estimation

🎨 Full-bleed visual of a decision maker facing multiple future paths labeled demand, cost, usage, and risk.

🖱️ One-click entrance for each future path so the uncertainty builds progressively.

⚙️ iSpring narration with staged object animations.

➡️ Transition from the title into the business problem: too many possible futures, one price decision.

⏱️ 1 min

### Slide 2 - Lemonade stand analogy

🎙️ "Imagine you run a lemonade stand. Tomorrow could be hot, warm, or rainy. Each future changes how many cups you sell. The point is not to guess one future correctly. The point is to price fairly across all plausible futures."

📝

- Hot day: high demand
- Warm day: medium demand
- Rainy day: low demand
- Fair price = weighted average across futures

🎨 Bright, playful three-panel scene: sunny stand, cloudy stand, rainy stand. Each panel shows cups sold and mood.

🖱️ Click-to-reveal weather panels one by one, then reveal the weighted-average conclusion.

⚙️ iSpring visual interaction with layered reveals.

➡️ Flow from intuitive story to formal business framing.

⏱️ 1.5 min

## Module 2: The Core Business Idea

### Slide 3 - Pricing is a probability problem

🎙️ "We do not price based on what will happen. We price based on what might happen. That makes fair pricing an expected-value problem."

📝

- Fair Price = Expected Value = E[g(X)]
- X = uncertain outcome
- g(X) = business impact

🎨 Clean diagram with three blocks: uncertainty, business rule, expected value. Keep the formula centered and readable.

🖱️ Hover or click hotspots on X and g(X) to display plain-language definitions like demand, cost, revenue, margin, penalty.

⚙️ iSpring hotspots with popup callouts.

➡️ Transition from child-friendly analogy to executive language without changing the underlying logic.

⏱️ 1.5 min

### Slide 4 - Business examples

🎙️ "This is not just about finance. The same model works for API pricing, cloud cost exposure, SLA penalties, subscriptions, and usage-based products."

📝

- API pricing with uncertain usage
- Services with SLA penalties
- Subscription pricing with churn uncertainty
- Cloud cost variability

🎨 Four-card layout with icons for API, cloud, service desk, and subscription product.

🖱️ Clicking each card expands a one-line example of what the uncertain variable and payoff would be.

⚙️ iSpring accordion interaction.

➡️ Flow from abstract expected value to direct business relevance.

⏱️ 1.5 min

## Module 3: Classical vs Quantum Estimation

### Slide 5 - Classical Monte Carlo intuition

🎙️ "The classical approach is simple: simulate many futures, compute the business outcome for each one, and average the results. It works well, but accuracy improves slowly."

📝

- Simulate many scenarios
- Compute outcome each time
- Average the outcomes
- More precision requires many more simulations

🎨 Animated sequence of thousands of small scenario cards dropping into a calculator, then converging to an average.

🖱️ Presenter clicks through the three steps; the last click emphasizes the cost of needing more simulations.

⚙️ iSpring narration sync plus timeline animation.

➡️ Transition into why another estimation method is interesting.

⏱️ 2 min

### Slide 6 - What quantum changes

🎙️ "Quantum does not change what we calculate. It changes how efficiently we estimate it. The business logic stays the same. The estimation technique changes."

📝

- Same question
- Same payoff logic
- Different estimation technique
- Faster error reduction in theory

🎨 Side-by-side visual: left lane shows repeated classical sampling, right lane shows a quantum state representing many possibilities at once.

🖱️ A slider or click reveals the shared output at the bottom: same value, different path.

⚙️ iSpring comparison interaction.

➡️ Flow from contrast to reassurance: quantum is an estimation upgrade, not a business-model rewrite.

⏱️ 2 min

## Module 4: The 4-Block Mental Model

### Slide 7 - The four building blocks

🎙️ "Every pricing problem in this framework has four building blocks: uncertainty, payoff, encoding, and estimation. Once people understand these four blocks, the rest becomes much easier to follow."

📝

1. Uncertainty Model
2. Payoff Function
3. Encoding
4. Estimation

🎨 A horizontal pipeline with clear icons: dice cloud, profit curve, circuit loader, result gauge.

🖱️ Click each block to reveal one business translation.

⚙️ iSpring labeled graphic.

➡️ Transition into a concrete walkthrough using the same four-block structure.

⏱️ 2 min

### Slide 8 - Translate each block into business language

🎙️ "Here is the same model in business terms. Uncertainty is demand, cost, or usage. Payoff is margin, penalty, or benefit. Encoding loads possibilities into the model. Estimation extracts the fair value."

📝

- Uncertainty = what may change
- Payoff = how value responds
- Encoding = represent possibilities
- Estimation = compute fair value

🎨 Two-column table: technical term on the left, business meaning on the right. A subtle highlight moves row by row during narration.

🖱️ Auto-advance highlight per row, with optional manual replay button.

⚙️ iSpring timeline + narration bookmarks.

➡️ Flow into a live-demo-style story without requiring actual coding.

⏱️ 1.5 min

## Module 5: Demo Story Without Code Overload

### Slide 9 - Observe, do not code

🎙️ "In the real demo, we model uncertainty, define a payoff, and then compare classical and quantum estimates side by side. For this short presentation, the important point is what the audience should observe, not how to code it."

📝

- Model uncertainty
- Define payoff
- Estimate expected value
- Compare results side by side

🎨 Mock notebook screenshot or stylized UI panels showing distribution chart, payoff line, and two result cards.

🖱️ Click to zoom each panel in sequence: uncertainty chart, payoff chart, comparison result.

⚙️ iSpring screen-record style zoom regions or slide layers.

➡️ Transition from model structure to evidence that both methods answer the same business question.

⏱️ 1.5 min

### Slide 10 - Same question, same value

🎙️ "This is the key observation. Classical Monte Carlo and quantum amplitude estimation target the same expected value. We are not changing the problem. We are changing the estimation engine."

📝

- Classical result: reference baseline
- Quantum result: same decision target
- Interpretation matters more than the code

🎨 Two large result cards with matching value ranges and a central banner reading: Same question. Different estimator.

🖱️ Audience poll: ask which part changed, the business logic or the estimation method.

⚙️ iSpring quiz poll with instant feedback.

➡️ Use the poll result to reinforce the main learning point before moving to business translation.

⏱️ 2 min

## Module 6: Business Takeaways and Close

### Slide 11 - Where this matters

🎙️ "If you work on digital products, services, or operations, this is already your world. Demand shifts, costs move, incidents happen, and usage changes. Quantum Monte Carlo is best understood as a value-estimation engine for uncertainty."

📝

- Pricing is probabilistic
- Estimation drives confidence
- Quantum improves estimation, not logic
- The model applies beyond finance

🎨 Executive-style takeaway slide with icons and a restrained, modern layout.

🖱️ Final click reveals the phrase: value-estimation engine for uncertainty.

⚙️ iSpring narration + emphasis animation.

➡️ Transition into a crisp wrap-up and optional Q&A.

⏱️ 1.5 min

### Slide 12 - Closing line and next conversation

🎙️ "Even before quantum computers outperform classical systems in practice, this way of thinking already improves how we reason about value under uncertainty. That is the real takeaway."

📝

- Think in distributions, not single guesses
- Map uncertainty to payoff
- Compare estimators, keep logic constant
- Start with one pricing use case

🎨 Minimal closing slide with one strong quote and a subtle background of branching future paths converging into one decision.

🖱️ Optional final button: Explore use cases in pricing, services, and operations.

⚙️ iSpring branching button to appendix or follow-up slides if needed.

➡️ End presentation or jump into discussion based on audience interest.

⏱️ 1 min

## Optional Appendix Slides

Use only if time remains or questions become more tactical.

### Appendix A - Classical vs quantum one-sentence comparison

🎙️ "Classical Monte Carlo samples many futures one by one. Quantum amplitude estimation encodes probability information differently to improve estimation efficiency in theory."

📝

- Classical: many sampled futures
- Quantum: amplitude-based estimation

🎨 Split-screen summary graphic.

🖱️ None required.

⚙️ Static slide with narration.

➡️ Use only as a reinforcement slide.

⏱️ 45 sec

### Appendix B - Mapping template for your own business case

🎙️ "If you want to apply this internally, start by naming the uncertainty, the payoff rule, and the decision you are trying to support."

📝

- Uncertainty:
- Payoff:
- Estimation target:
- Decision supported:

🎨 Fill-in canvas for workshop follow-up.

🖱️ Clickable text fields if used interactively.

⚙️ iSpring form-style interaction.

➡️ Use as a bridge to discussion or a breakout session.

⏱️ 1 min

## Delivery Notes

- Keep the tone visual, conceptual, and business-oriented.
- Avoid deep math, hardware discussions, or benchmark debates.
- Emphasize that the logic of pricing stays constant across classical and quantum methods.
- If presenting live, pause briefly after Slide 6 and Slide 10 to let the audience restate the key idea in their own words.
- If converting to a self-paced deck, keep voiceover concise and let interactions do part of the teaching.
