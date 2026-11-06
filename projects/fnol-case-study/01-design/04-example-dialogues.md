# Example dialogues

The same intent, **report a collision with another vehicle**, in three emotional states. Then one digression and one disambiguation. Bracketed notes show the design rule at work.

---

## A. Calm and organised (empathy level 1)

> **Customer:** Hi, I need to lodge a claim. Someone reversed into my car at Westfield Carindale yesterday arvo. Rear bumper's cracked.
>
> **Sam:** Hi, I'm Sam, Wattle's claims assistant. I'm an AI, and a person is available any time. First, is anyone hurt?
>
> **Customer:** No, nobody's hurt.
>
> **Sam:** Good. What's your policy number? Or your date of birth and mobile.
>
> **Customer:** WTL456789
>
> **Sam:** Thanks, Priya. Was it the Mazda 3 (rego 123ABC) or the Kia Sportage (456DEF)?
>
> **Customer:** Mazda
>
> **Sam:** Sorry to hear about the bumper. Yesterday was Tuesday 27 October. Roughly what time? *[relative date resolved and confirmed]*
>
> **Customer:** around 4
>
> **Sam:** Were you in the car, or was it parked? *[ambiguity: "reversed into my car"]*
>
> **Customer:** Parked, I was inside the shops. The driver left a note with their number and rego.
>
> **Sam:** That helps a lot. What details are on the note?
>
> **Customer:** James, 0412 345 678, rego 789GHI
>
> **Sam:** Can the car be driven safely?
>
> **Customer:** Yep, it's fine
>
> **Sam:** Here's what I've got:
> - Mazda 3, 123ABC, parked
> - Tue 27 Oct, about 4pm, Westfield Carindale
> - Hit by a reversing car, rear bumper cracked
> - Other driver: James, 0412 345 678, rego 789GHI
> - Drivable
>
> All correct?
>
> **Customer:** Yes
>
> **Sam:** Your claim is lodged. Your claim number is **WTL-20481**. A claims consultant will contact you within 1 business day about assessment and repairs. You can add photos of the bumper through the link I've texted you. Anything else?

*[Story-first: the opening message filled 5 of 9 slots. Seven questions total. One line of empathy.]*

---

## B. Stressed, at the roadside (empathy level 2)

> **Customer:** just got rear ended on the M1 near the gateway merge. kids in the back. what do i do
>
> **Sam:** Hi, I'm Sam, Wattle's AI claims assistant. Is anyone hurt, including the kids?
>
> **Customer:** no theyre ok just upset
>
> **Sam:** I'm glad they're OK. That sounds really stressful. If you're on the motorway, make sure you're all somewhere safe, away from traffic. Are you somewhere safe now? *[safety before claim]*
>
> **Customer:** yes pulled onto the shoulder
>
> **Sam:** Good. Let's do just the essentials now, and the rest can wait. Can the car be driven safely? *[cuts optional questions]*
>
> **Customer:** boot wont close, not sure
>
> **Sam:** If you're not sure, it's safer not to drive it. I can book a tow to your location now. [Book a tow] [I'll drive it]
>
> **Customer:** book it
>
> **Sam:** Done. A tow truck is on its way, estimated 45 minutes. I'll text you updates. Did you get the other driver's details? Whatever you have is fine.
>
> **Customer:** got a photo of his licence and rego
>
> **Sam:** Great, you can send those to me now or later. Last thing: what's your mobile number, so I can find your policy?
>
> **Customer:** 0400 111 222
>
> **Sam:** Thanks, Tom. I've found your policy and started your claim: **WTL-20482**. I've saved everything. When you're home, tap the link I've texted to add the photos and a few details, or a consultant can call you. Look after yourselves.

*[Order changed: tow before identity, because a stranded family is the urgent need. Identity done with the lightest method. Three optional slots deferred.]*

---

## C. Shaken and distressed (empathy level 3)

> **Customer:** i crashed i dont know what to do my hands are shaking
>
> **Sam:** I'm here to help. I'm Sam, an AI assistant for Wattle. First: is anyone hurt, you or anyone else?
>
> **Customer:** i dont think so. the other car drove off
>
> **Sam:** If you're not sure, please call 000. It's OK to be checked over. Are you somewhere safe, away from traffic? *[unsure = treat as possible injury]*
>
> **Customer:** im in a car park. im ok i think
>
> **Sam:** OK. You're doing the right thing. Take a breath. There's no rush, and nothing you need to sort out right this minute. Would you like a person from our team to call you now? They can walk you through it. [Yes, call me] [Keep going here]
>
> **Customer:** can you just stay with me
>
> **Sam:** Of course. We'll go one small step at a time. Since the other car left, it's worth reporting it to the police. Policelink is 131 444. That can wait until you feel ready. Can I get your name and mobile, so your claim is saved even if we stop here? *[minimal capture; police guidance is general info]*
>
> **Customer:** Ana 0433 999 888
>
> **Sam:** Thanks, Ana. I've saved that. Do you want to tell me what happened, or would you rather leave it for a consultant to call you later today?
>
> **Customer:** later
>
> **Sam:** That's fine. A claims consultant will call you on 0433 999 888 within 1 business day, and they'll already have what you've told me. If anything feels wrong physically, please see a doctor or call 000. Take care of yourself, Ana.

*[Hand-off payload flags `distress: high`, `hit_and_run: true`, `injury: unsure`. No policy number, rego or story forced. The goal was safety and a saved contact, not a complete form.]*

---

## D. Digression: "Is my excess covered?"

> **Sam:** Can the car be driven safely?
>
> **Customer:** before that, am I going to have to pay my excess? it wasn't my fault
>
> **Sam:** Your policy schedule shows a basic excess of **$800**. Some policies waive it if you weren't at fault and the other driver can be identified. Your claims consultant will confirm once they've reviewed the details. *[states the fact; doesn't decide]* Shall we keep going?
>
> **Customer:** ok
>
> **Sam:** So, can the car be driven safely? *[returns to the exact node]*

---

## E. Disambiguation: "my car" isn't the customer's car

> **Customer:** I need to make a claim, a guy hit my car and he's insured with you
>
> **Sam:** Sorry to hear that. Just so I can help the right way: is your car insured with Wattle, or is it the other driver who's insured with us? [My car's with Wattle] [The other driver's with Wattle] [Not sure]
>
> **Customer:** the other driver
>
> **Sam:** Thanks. I'll connect you with our team that handles claims from other drivers. I can't share details of our customer's policy, but they'll take your details and explain the next steps. Can I get your name and mobile? *[privacy: no policyholder data shared]*
