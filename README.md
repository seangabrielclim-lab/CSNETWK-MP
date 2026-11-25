**CSNETWK Machine Project: 7WD — A Peer-to-Peer UDP Protocol for the Board Game 7 Wonders**

**Members:**
Derk Cheng
Craig Xander Hing
Sean Gabriel Lim
Elijah Rexson Mayor

**Programming Language:** Python

**Build and run instructions, including how to enable verbose mode**
> Prerequisites
 - Text
 - Text

> Running peer instances
 - Text
 - Text

> Toggle & enable verbose mode
 - Text
 - Text

**Work Distribution Matrix**
Derk Cheng
- Randomness Ceremony & Ring/Wonder/Guild derivation (commit-reveal)
 > filename.py
 > filename.py
 > filename.py

- Draft Turn engine (commit-reveal, hand pass, all Ages and turns)
 > filename.py
 > filename.py
 > filename.py

- Peer disconnection consensus & error handling
 > filename.py
 > filename.py
 > filename.py

Craig Xander Hing
- Resource Trading logic
 > filename.py
 > filename.py
 > filename.py

- Message serialisation/deserialisation (all message types) 
 > filename.py
 > filename.py
 > filename.py

- Testing & interoperability 
 > filename.py
 > filename.py
 > filename.py

Sean Gabriel Lim
- UDP socket handling, message framing, and per-peer channel management
 > filename.py
 > filename.py
 > filename.py

- Lobby Phase: presence gossip, roster convergence, session formation 
 > constants.py
 > MP.py
 > states.py

Elijah Rexson Mayor
- Military Resolution & End-of-Game scoring consensus
 > military_scoring.py
 > scoring_constants.py

- Verbose mode (message logging, toggle on/off)
 > name_messages.py
 > verboseLogger.py

**AI Usage:**
AI-assisted tools were used during the creation of this laboratory experiment to help with:
1. How it was used - AI-assisted tool
2. How it was used - AI-assisted tool
3. How it was used - AI-assisted tool

**Any known limitations or deviations from the RFC**
> Protocol-level constraints
 - Text
 - Text

> Integration & execution limits
 - Text
 - Text
 - Text
