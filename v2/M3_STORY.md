# The Story of M3 Player-State: A Suspension Model That We Chose Not to Ship

*A narrative account of what we attempted, what the data taught us, which decisions
we made and on what principles, and where we ended up. Written for a human reader —
including the version of us who comes back to this in a few months and needs to
remember not just the result but the reasoning.*

For the terse, machine-facing version see [`M3_BUILD_PLAN.md`](M3_BUILD_PLAN.md)
(the batched build spec) and [`M3_BUILD_PROGRESS.md`](M3_BUILD_PROGRESS.md) (the
live ledger). For the decision record see [`M3_PLAYER_STATE_PLAN.md`](M3_PLAYER_STATE_PLAN.md).
This document is the prose.

---

## 1. What we set out to do

The idea came from Jorge, by way of friends who follow football far more closely
than either of us. The intuition was simple and, on its face, obviously correct:
the key plays and goals of a World Cup are produced by a small number of pivotal
players, and the *state* of those players ought to move our forecasts. Is a key
player injured? Suspended? Carrying a yellow card and one booking away from missing
the next match? Heating up or fading across the tournament? Each of these, the
intuition went, should change the numbers our model produces.

That intuition became a planned feature group for M3 — "player state" — to be added
by the end of the group stage. The goal was never in doubt. The entire story that
follows is about the distance between an intuition that is *obviously correct* and a
number you are *willing to put into a live production model*. That distance turned
out to be the whole point.

The governing principle, stated up front and never relaxed: **strict math. Any new
feature has to earn its place by improving the model's backtested accuracy before it
ships — exactly the way the home-advantage feature had to.** No coefficient was
allowed to come from football intuition, taste, or a number that felt right. If the
data could not support it, it would not ship, however plausible the story.

---

## 2. Narrowing the scope: what we deliberately chose *not* to do

The first real work was not coding. It was deciding what, of the four player-state
effects, we could honestly build *right now*.

Three of them — injury/availability, suspension, and yellow-card risk — are
**snapshots**: facts true at a moment in time. The fourth, **form trend**, is
different in kind. To know whether a player is heating up or fading you need their
performance *as a time series* — match by match, perhaps minute by minute — and with
only three group games per team, any trend you fit is mostly noise dressed up as
signal. We set form trend aside, explicitly, to revisit after the group stage. This
was the first application of a recurring discipline: **do not let a feature's
appeal outrun the data's ability to support it.**

Then availability fell too, and for a subtler reason that only became clear once we
looked at the data sources (Section 4). "A key player was announced unavailable
before kickoff" has no clean historical record — you cannot reconstruct, for a match
in 2019, what the team announced the day before. The only proxy is "the player
didn't appear," which silently conflates suspension, injury, rotation, and tactical
choice into one indistinguishable lump. We refused that proxy. Availability was
deferred to the moment we have a live feed that records it honestly.

That left **suspension and yellow-card risk** as the scope we would actually build.
And this narrowing turned out to be a gift, because suspension has a property the
others lack: it is *deterministic and reconstructable*. More on that shortly.

A principle worth naming here, because Jorge insisted on it across the project:
**surface intent, don't quietly translate it into one implementation.** When the
brief said "this should affect our forecasted values," we treated that as a goal to
be served, not a spec to be guessed at — and every time the path forked, we put the
fork in front of him rather than picking silently and burying the choice in code.

---

## 3. The question that shaped everything: how do you set the magnitude without knowing football?

Suppose a key player is suspended. We reduce the team's expected goals. *By how
much?* This is the question on which the whole feature lived or died, and Jorge put
his finger on exactly the right difficulty: he doesn't know football well enough to
hand-set that number, and — more importantly — he was unwilling to. A number pulled
from intuition is precisely what the strict-math discipline exists to forbid.

So the question became: **how do you let the data set the magnitude, and the bounds
on the magnitude, rather than a person?**

The answer, in one phrase, is *regularization with a prior estimated from history* —
or, in plainer terms: don't guess how much a suspension matters, **measure it across
hundreds of past matches where key players were absent, and let the size of that
historical effect, together with its uncertainty, become the bound.** A strong,
consistent effect survives; a noisy one shrinks toward zero on its own. No football
knowledge required anywhere in the chain.

That decision — to source a historical corpus and fit a partial-pooling model
against it — is what turned a few-days feature into a real piece of empirical work.
Jorge accepted the tradeoff with eyes open: **correctness over the calendar.** The
group-stage deadline would slip, because doing this honestly meant building a dataset
first, and datasets are always dirtier and slower than they look.

---

## 4. Sourcing: the discovery that changed the architecture twice

Here the project met its first hard contact with reality, and the principle that
governs all data work asserted itself: **the data is always dirtier than you think;
never write a parser before you have inspected the source with your own eyes.**

We did a focused reconnaissance of every plausible football data source —
StatsBomb's free event data, FBref, ESPN's hidden API, the paid API-Football,
Transfermarkt, Wikipedia, Kaggle mirrors. The reconnaissance produced one finding
that governed everything after it: **a labeled suspension — "this player missed this
match *because of cards*" — exists, machine-readable, in essentially one free place:
Transfermarkt.** Everywhere else, you get the *ingredients* (card events and
lineups) and must *infer* the suspension yourself, and that inference quietly
conflates suspension with injury and rotation — the same silent-failure trap that
sank availability.

That pointed us toward a **two-source architecture**: a statistics-and-lineups
"spine" joined to a suspension "overlay." And the join between them — matching
players across two systems with different IDs, by name and birthdate and nationality
— was flagged as the single largest risk in the whole build. Cross-source identity
joins are where data projects go to die.

Jorge chose to pay for API-Football Pro as the overlay, partly because it doubles as
the live 2026 feed. And then the second architectural shift happened — the one that
makes this a good story instead of a cautionary one. **We did not trust the vendor's
documentation; we ran a live probe against the real API before building anything.**

The probe returned something that looked, at first, like bad news: API-Football's
editorial suspension/injury labels are simply *absent* for historical international
tournaments. The `injuries` coverage flag is false for every World Cup, Euro, and
Copa in our window. The single-source dream appeared dead.

But the probe also confirmed the spine was completely present — card events,
lineups (including the full bench, so true absence is observable), and per-player
statistics, all in one ID space. And that reframed the entire problem in our favor:

**A card suspension does not need to be looked up. It is deterministic.** Two yellow
cards in separate matches, or a red, means a one-match ban, by published rule. We
have the cards. We have the rules. So we *derive* the suspension ourselves — which is
strictly *more* bulletproof than trusting any source's hand-entered label, and the
next match's full squad confirms the absence as a cross-check. The recon had
suggested re-implementing the disciplinary rules as a *check* on the overlay; the
probe promoted that rule engine to the *primary signal* and let us delete the
overlay, delete StatsBomb, and delete the cross-source join — the very risk we feared
most — entirely.

What had looked like a setback (`injuries=False`) was the doorway to a simpler,
single-source, more rigorous design. This is the reward for the discipline of
verifying against reality instead of against documentation.

---

## 5. Building the corpus, and the traps that were waiting in it

We pulled 290 finished matches across six tournaments — the 2018 and 2022 World
Cups, Euro 2020 and 2024, and the 2021 and 2024 Copa América — caching every raw API
response to disk so that the data would be fetched exactly once and every later step
would run against an immutable, auditable local record. Re-running anything costs
zero API calls. Raw responses are the ground truth; parsing happens downstream.

The corpus did not come clean. It never does. Three discoveries stand out, and each
is a small monument to the same principle: **find things by content, never assume
the shape.**

First, **Euro 2020 quietly contained 313 matches instead of 51.** API-Football had
bundled the entire qualifying campaign into the same season as the final tournament.
Had we trusted the count, we would have wasted hundreds of API calls fetching detail
for qualifier matches and polluted the corpus with the wrong competition. The fix was
to filter by the *content* of each round's name — excluding anything containing
"Qualifying" — which gives exactly 51 and is harmless for the tournaments that were
already clean. A count-check, which exists precisely to catch this, caught it.

Second, **the card feed represents a same-match second yellow as three events** —
two yellow cards *and* a red — not as a single distinct "second yellow." A naive
reading would have counted those two yellows toward the cross-match accumulation that
triggers a *future* ban, double-counting a dismissal that is already its own
punishment. We confirmed the representation against fourteen real cases in the data
before writing the accumulation logic, and encoded the correct rule: a match in which
a player sees red contributes nothing to the running yellow tally; the red is the
ban.

Third, and most instructive, was the **rule engine itself** — the deterministic
heart of the whole project. We verified the disciplinary rules against the actual
tournament regulations rather than assuming them, and that verification mattered: the
rules differ by edition. Every tournament in our corpus wipes accumulated yellows
only after the quarter-finals. But the 2026 World Cup — our actual target — changed
the rule, and now also wipes after the group stage. Encoding the wipe as a per-edition
configuration rather than a constant is the difference between a model that's right
and one that's subtly, invisibly wrong on the very tournament it's meant to serve.

---

## 6. The cross-check that earned its keep

When the rule engine first ran, it produced 181 suspensions and agreed with reality —
with which players were actually absent — only 47% of the time. That number is a
gift. A feature that cannot be checked is a feature you have to trust on faith; this
one could be checked against observed absences, and the check immediately said
*something is wrong.*

Two bugs were hiding, and the cross-check flushed both into the open.

The first: **card accumulation was leaking across tournaments.** Because we had
pooled each team's matches across all six editions into one timeline, a player who
picked up two yellows at the 2018 World Cup was being "banned" for his next match in
the data — which happened to be Euro 2020, two years later. Cristiano Ronaldo's trace
made it obvious at a glance. Keying the accumulation per *(team, edition)* fixed it,
and agreement jumped to 99%.

The second was subtler and, again, the data taught us the real rule. One case
remained — Derek Cornelius, flagged as banned for Canada's Copa 2024 semi-final, yet
he played it. The engine wasn't hallucinating his cards; he genuinely had two
yellows. But his second came *in the quarter-final*, and the post-quarter-final
amnesty wipes not just the running tally but a suspension that the tally had just
triggered. Our reset cleared the count but not the pending ban. We fixed it — a yellow
amnesty wipes a pending yellow-accumulation ban, though never a red-card ban — and
agreement reached **100%, all 68 suspensions matching observed absence.**

That is the signal we wanted: not an editorial label we hoped was accurate, but a
quantity we derived from first principles and then validated, exhaustively, against
what actually happened. Eight unit tests, including the Cornelius amnesty case as a
deliberate negative and a known red-card ban as a positive, lock it in place.

---

## 7. The thin-sample reality, and an honest model

With suspensions in hand, we computed each player's *as-of-date* importance — their
share of the team's goal involvement, measured only from matches played *before* the
one being predicted, so that no future information leaks backward. We verified that
strict point-in-time property explicitly; it held for every team-edition checked.

And here the data delivered its sobering truth. Of 68 suspensions, only **17 involved
a key attacking player** — someone with a non-zero goal-involvement weight. The rest
were defenders and squad players whose absence, under a goals-and-assists definition
of importance, registers as zero. Seventeen events is a thin foundation on which to
measure an effect. We said so plainly, in the ledger and to Jorge, *before* fitting
anything — because the honest move is to flag the likely outcome in advance, not to
discover it and quietly hope.

For the model, Jorge chose empirical-Bayes shrinkage over a full Bayesian framework
like PyMC. With seventeen events, the heavier machinery would have added ceremony
without rigor, and it would have meant a heavy new dependency in a production pipeline
that otherwise leans only on numpy and scikit-learn. We fit a Poisson model of team
goals where the regularization penalty *is* the partial pooling — team and opponent
strengths shrink toward the average, the suspension effect shrinks toward zero — and
we let cross-validation choose how hard to shrink. The data sets the bound, not us.

The result was real. A suspended key player of weight *w* multiplies the team's
expected goals by about `exp(-0.078·w)` — a few percent for a typical key player —
and the effect's confidence interval excluded zero. More convincingly, it stayed
negative and stable when we held each tournament out in turn, so it wasn't an artifact
of one competition. And when we added a control for knockout stage — the obvious
confounder, since suspensions cluster late and late matches score less — the effect
did not collapse. If anything it strengthened. The suspension was doing real work,
not standing in for "knockout football is cautious."

---

## 8. The gate, and the decision to walk away

Everything to this point had built toward one test: does applying this downweight
make the model's *match-outcome* predictions better, out of sample, by enough to
distinguish from noise?

We built the gate to be honest by construction. For each tournament, the effect
applied to its matches was the one *learned from the other five*, so the number being
scored never saw the matches scoring it. The baseline was identical in both arms; the
only difference was the downweight on the handful of matches with a suspended key
player. We compared the ranked-probability score of both, bootstrapped a confidence
interval on the difference, and ran a Diebold-Mariano test.

The verdict: the adjusted model was better — *in the right direction* — but the
improvement was not statistically distinguishable from noise. The difference in score
was about four parts in a hundred thousand, its interval grazed zero, the
Diebold-Mariano p-value was 0.14, and only sixteen of 290 matches were affected at
all. The effect is real in the goals, but too small and too rare to move the
prediction of who wins, draws, or loses.

So we did the thing the entire project was built to make possible: **we did not ship
it.** No fudging the threshold, no "it's directionally right, let's include it
anyway," no number nudged into the model on the strength of a good story. The
feature failed the gate, and the gate is the whole point. The same discipline that
rejected this effect is what makes the effects we *do* ship trustworthy.

This is worth sitting with, because it inverts the usual notion of success. We spent
real effort to build a thing and then declined to use it — and that is the correct
outcome, not a wasted one. A model earns its credibility from what it refuses to
include as much as from what it includes.

---

## 9. Where we ended, and what is waiting

Nothing was wired into the production model. The live `player_state.py` collector,
which surfaces who is suspended and who carries cards, continues to run as
information. The entire analytical machine — the cached corpus, the rule engine, the
weighting, the model, the gate — sits intact and dormant under `v2/m3/`, validated
and ready, asserting nothing the data cannot support.

And it is poised to be re-asked. The honest reading of the gate is not "there is no
effect" but "there is an effect, and we do not yet have enough events to prove it
moves outcomes." The 2026 World Cup will add roughly thirty to forty more suspension
events. The rule engine already knows 2026's new disciplinary rules. A seven-step
re-run recipe is written down. When the group stage is over, we run the gate again,
and the data — not our hopes — decides whether the feature graduates.

We also built the project to survive its own telling. Jorge had been burned before by
work lost when a long session compacted, so the plan was broken into small batches and
sub-batches, each checkpointed in a live ledger with an artifact inventory and a
recovery protocol. That scaffolding earned its keep during the build itself: the
cross-check caught bugs, the ledger caught every decision and number, and the whole
account survives independent of any one conversation.

---

## The principles, gathered in one place

Reading back, the same handful of commitments shaped every fork:

- **Strict math; nothing ships unless the data backs it.** The gate is sacred. A
  good story is not evidence.
- **No number from taste.** Magnitudes and their bounds are measured from history and
  shrunk by cross-validation, never hand-set.
- **The data is dirtier than you think; inspect before you parse.** Every trap in the
  corpus — the qualifier bundling, the triple-event red card, the cross-edition leak —
  was caught because we looked at the actual data, not at what we assumed it was.
- **Find by content, not by position or count.** Sources lie about their shape.
- **Verify against reality, not documentation.** The probe that found `injuries=False`
  also found the better architecture.
- **No silent failure, no silent drop.** Every anomaly is flagged; the cross-check
  exists so the model can be caught being wrong.
- **Surface intent; put the fork in front of the human.** Scope, sourcing, tooling,
  and the final ship/don't-ship were all Jorge's calls, made explicit, never buried.
- **Build to survive compaction.** Small batches, a live ledger, a recovery protocol.

The feature did not ship. The discipline did. That is the result.

*— Written 2026-06-26, the day the gate said no.*
